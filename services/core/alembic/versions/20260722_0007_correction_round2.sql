-- Correction Round 2: grant resolution, durable service-auth nonces, schema integrity.

CREATE TABLE service_auth_nonce (
  nonce_digest VARCHAR(64) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_service_auth_nonce PRIMARY KEY (nonce_digest)
);

CREATE INDEX ix_service_auth_nonce_expires ON service_auth_nonce (expires_at);

-- Owned by migrate role so SECURITY DEFINER consumers can insert under RLS.
ALTER TABLE service_auth_nonce OWNER TO memdot_migrate;
REVOKE ALL ON TABLE service_auth_nonce FROM PUBLIC;
REVOKE ALL ON TABLE service_auth_nonce FROM memdot_core;
-- No direct DML for runtime; only via memdot_consume_service_auth_nonce.

CREATE OR REPLACE FUNCTION memdot_consume_service_auth_nonce(
  p_nonce_digest text,
  p_expires_at timestamptz
) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  -- Opportunistic cleanup; failures must not block atomic consume.
  DELETE FROM service_auth_nonce WHERE expires_at < now();
  BEGIN
    INSERT INTO service_auth_nonce (nonce_digest, expires_at)
    VALUES (p_nonce_digest, p_expires_at);
    RETURN true;
  EXCEPTION WHEN unique_violation THEN
    RETURN false;
  END;
END;
$$;

ALTER FUNCTION memdot_consume_service_auth_nonce(text, timestamptz) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_consume_service_auth_nonce(text, timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_consume_service_auth_nonce(text, timestamptz)
  TO memdot_core, memdot_test_admin;

-- Narrow grant lookup: never trust client-supplied account/actor without DB grant.
CREATE OR REPLACE FUNCTION memdot_resolve_external_grant(
  p_client_id text,
  p_account_id uuid DEFAULT NULL,
  p_actor_id uuid DEFAULT NULL
) RETURNS TABLE (
  grant_id uuid,
  account_id uuid,
  actor_id uuid,
  client_id text,
  scopes text,
  revoked_at timestamptz
)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public AS $$
BEGIN
  RETURN QUERY
  SELECT
    g.id,
    g.account_id,
    g.actor_id,
    g.client_id::text,
    g.scopes::text,
    g.revoked_at
  FROM external_client_grant g
  WHERE g.client_id = p_client_id
    AND (p_account_id IS NULL OR g.account_id = p_account_id)
    AND (p_actor_id IS NULL OR g.actor_id = p_actor_id)
    AND g.revoked_at IS NULL
  LIMIT 2;
END;
$$;

ALTER FUNCTION memdot_resolve_external_grant(text, uuid, uuid) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_resolve_external_grant(text, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_resolve_external_grant(text, uuid, uuid)
  TO memdot_core, memdot_test_admin;

-- Assessment attempt: Space boundary + owning FKs.
ALTER TABLE assessment_attempt
  ADD COLUMN IF NOT EXISTS space_id UUID;

UPDATE assessment_attempt aa
SET space_id = c.space_id
FROM course c
WHERE aa.course_id = c.id AND aa.account_id = c.account_id AND aa.space_id IS NULL;

ALTER TABLE assessment_attempt
  ALTER COLUMN space_id SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_assessment_attempt_space'
  ) THEN
    ALTER TABLE assessment_attempt
      ADD CONSTRAINT fk_assessment_attempt_space
      FOREIGN KEY (account_id, space_id) REFERENCES space (account_id, id);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_assessment_attempt_item'
  ) THEN
    ALTER TABLE assessment_attempt
      ADD CONSTRAINT fk_assessment_attempt_item
      FOREIGN KEY (account_id, assessment_item_id)
      REFERENCES assessment_item (account_id, id);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_assessment_attempt_user'
  ) THEN
    ALTER TABLE assessment_attempt
      ADD CONSTRAINT fk_assessment_attempt_user
      FOREIGN KEY (account_id, user_id) REFERENCES "user" (account_id, id);
  END IF;
END $$;

DROP POLICY IF EXISTS tenant_first_party ON assessment_attempt;
CREATE POLICY tenant_first_party ON assessment_attempt
  FOR ALL
  USING (
    memdot_rls_ok(account_id)
    AND current_setting('app.purpose', true) IN ('first_party', 'worker', 'migration')
  )
  WITH CHECK (
    memdot_rls_ok(account_id)
    AND current_setting('app.purpose', true) IN ('first_party', 'worker', 'migration')
  );

CREATE OR REPLACE FUNCTION memdot_validate_assessment_attempt()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM course c
    WHERE c.account_id = NEW.account_id AND c.id = NEW.course_id AND c.space_id = NEW.space_id
  ) OR NOT EXISTS (
    SELECT 1 FROM assessment_item i
    WHERE i.account_id = NEW.account_id AND i.id = NEW.assessment_item_id
      AND i.course_id = NEW.course_id AND i.space_id = NEW.space_id
  ) OR NOT EXISTS (
    SELECT 1 FROM assessment_revision r
    WHERE r.account_id = NEW.account_id AND r.id = NEW.assessment_revision_id
      AND r.assessment_item_id = NEW.assessment_item_id AND r.space_id = NEW.space_id
  ) THEN
    RAISE EXCEPTION 'assessment_attempt_target_mismatch';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS trg_validate_assessment_attempt ON assessment_attempt;
CREATE TRIGGER trg_validate_assessment_attempt
  BEFORE INSERT OR UPDATE OF space_id, course_id, assessment_item_id, assessment_revision_id
  ON assessment_attempt FOR EACH ROW EXECUTE FUNCTION memdot_validate_assessment_attempt();

-- Conversation turn linkage FKs.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_conversation_turn_parent'
  ) THEN
    ALTER TABLE conversation_turn
      ADD CONSTRAINT fk_conversation_turn_parent
      FOREIGN KEY (account_id, parent_turn_id)
      REFERENCES conversation_turn (account_id, id);
  END IF;
END $$;

CREATE OR REPLACE FUNCTION memdot_validate_conversation_turn_links()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.parent_turn_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM conversation_turn p
    WHERE p.account_id = NEW.account_id AND p.id = NEW.parent_turn_id
      AND p.conversation_id = NEW.conversation_id AND p.space_id = NEW.space_id
  ) THEN
    RAISE EXCEPTION 'conversation_parent_mismatch';
  END IF;
  IF NEW.context_receipt_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM context_receipt r
    WHERE r.account_id = NEW.account_id AND r.id = NEW.context_receipt_id
  ) THEN
    RAISE EXCEPTION 'conversation_receipt_mismatch';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS trg_validate_conversation_turn_links ON conversation_turn;
CREATE TRIGGER trg_validate_conversation_turn_links
  BEFORE INSERT OR UPDATE OF parent_turn_id, context_receipt_id, conversation_id, space_id
  ON conversation_turn FOR EACH ROW EXECUTE FUNCTION memdot_validate_conversation_turn_links();

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_conversation_turn_encrypted'
  ) THEN
    ALTER TABLE conversation_turn
      ADD CONSTRAINT ck_conversation_turn_encrypted
      CHECK (
        (
          (payload_ciphertext IS NULL AND payload_nonce IS NULL)
          OR (payload_ciphertext IS NOT NULL AND payload_nonce IS NOT NULL)
        )
        AND NOT (payload_ciphertext IS NULL AND payload_json ? 'content')
      );
  END IF;
END $$;

-- Deletion workflow ownership FKs.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_deletion_workflow_tombstone'
  ) THEN
    ALTER TABLE deletion_workflow
      ADD CONSTRAINT fk_deletion_workflow_tombstone
      FOREIGN KEY (account_id, tombstone_id)
      REFERENCES deletion_tombstone (account_id, id);
  END IF;
END $$;

-- Durable job binding column on outbox for exact job dispatch.
ALTER TABLE outbox_event
  ADD COLUMN IF NOT EXISTS durable_job_id UUID;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_outbox_durable_job'
  ) THEN
    ALTER TABLE outbox_event
      ADD CONSTRAINT fk_outbox_durable_job
      FOREIGN KEY (account_id, durable_job_id)
      REFERENCES durable_job (account_id, id);
  END IF;
END $$;

-- OSS semantic projection table (rebuildable pgvector-free dense vector as float8[]).
CREATE TABLE semantic_projection (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  profile_version VARCHAR(64) NOT NULL,
  canonical_type VARCHAR(64) NOT NULL,
  canonical_id UUID NOT NULL,
  canonical_revision_id UUID NOT NULL,
  embedding FLOAT8[] NOT NULL,
  payload_hash VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  indexed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_semantic_projection PRIMARY KEY (id),
  CONSTRAINT uq_semantic_projection_1 UNIQUE (account_id, id),
  CONSTRAINT uq_semantic_projection_canonical UNIQUE (
    account_id, profile_version, canonical_type, canonical_id, canonical_revision_id
  ),
  CONSTRAINT ck_semantic_projection_status CHECK (status IN ('active', 'tombstoned', 'superseded'))
);

ALTER TABLE semantic_projection ENABLE ROW LEVEL SECURITY;
ALTER TABLE semantic_projection FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_first_party ON semantic_projection
  FOR ALL USING (
    memdot_rls_ok(account_id)
    AND current_setting('app.purpose', true) IN ('first_party', 'worker', 'migration')
  ) WITH CHECK (
    memdot_rls_ok(account_id)
    AND current_setting('app.purpose', true) IN ('first_party', 'worker', 'migration')
  );
ALTER TABLE semantic_projection
  ADD CONSTRAINT fk_semantic_projection_space
  FOREIGN KEY (account_id, space_id) REFERENCES space (account_id, id);

ALTER TABLE notion_page_binding ADD COLUMN source_id UUID;
ALTER TABLE notion_page_binding
  ADD CONSTRAINT fk_notion_page_binding_source
  FOREIGN KEY (account_id, source_id) REFERENCES source (account_id, id);
ALTER TABLE semantic_projection OWNER TO memdot_migrate;
GRANT SELECT, INSERT, UPDATE, DELETE ON semantic_projection TO memdot_core, memdot_test_admin;
