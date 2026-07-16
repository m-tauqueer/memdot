-- Documents, memory, retrieval, and context receipt extensions (additive).

ALTER TABLE document_revision
  ADD COLUMN IF NOT EXISTS content_json JSONB,
  ADD COLUMN IF NOT EXISTS plain_text TEXT,
  ADD COLUMN IF NOT EXISTS author_actor_id UUID,
  ADD COLUMN IF NOT EXISTS proposal_id UUID;

ALTER TABLE proposal
  ADD COLUMN IF NOT EXISTS patch_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS memory_item (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  title VARCHAR(512) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_memory_item PRIMARY KEY (id),
  CONSTRAINT fk_memory_item_space FOREIGN KEY(account_id, space_id)
    REFERENCES space (account_id, id),
  CONSTRAINT uq_memory_item_1 UNIQUE (account_id, id),
  CONSTRAINT uq_memory_item_space_id UNIQUE (account_id, space_id, id)
);

CREATE TABLE IF NOT EXISTS memory_revision (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  memory_item_id UUID NOT NULL,
  base_revision_id UUID,
  assertion_text TEXT NOT NULL,
  truth_class VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL,
  content_sha256 VARCHAR(64) NOT NULL,
  provenance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_memory_revision PRIMARY KEY (id),
  CONSTRAINT fk_memory_revision_item FOREIGN KEY(account_id, memory_item_id)
    REFERENCES memory_item (account_id, id),
  CONSTRAINT fk_memory_revision_item_space FOREIGN KEY(account_id, space_id, memory_item_id)
    REFERENCES memory_item (account_id, space_id, id),
  CONSTRAINT uq_memory_revision_1 UNIQUE (account_id, id),
  CONSTRAINT uq_memory_revision_space_id UNIQUE (account_id, space_id, id),
  CONSTRAINT uq_memory_revision_pointer UNIQUE (account_id, space_id, memory_item_id, id),
  CONSTRAINT ck_memory_revision_status CHECK (
    status IN ('active', 'superseded', 'retracted')
  ),
  CONSTRAINT ck_memory_revision_sha_len CHECK (char_length(content_sha256) = 64)
);

CREATE TABLE IF NOT EXISTS current_memory_revision (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  memory_item_id UUID NOT NULL,
  revision_id UUID NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_current_memory_revision PRIMARY KEY (id),
  CONSTRAINT fk_current_memory_revision_item FOREIGN KEY(account_id, memory_item_id)
    REFERENCES memory_item (account_id, id),
  CONSTRAINT fk_current_memory_revision_revision FOREIGN KEY(account_id, revision_id)
    REFERENCES memory_revision (account_id, id),
  CONSTRAINT fk_current_memory_revision_same_item FOREIGN KEY(account_id, space_id, memory_item_id, revision_id)
    REFERENCES memory_revision (account_id, space_id, memory_item_id, id),
  CONSTRAINT uq_current_memory_revision_1 UNIQUE (account_id, memory_item_id)
);

CREATE TABLE IF NOT EXISTS projection (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  provider VARCHAR(64) NOT NULL,
  surface VARCHAR(64) NOT NULL,
  profile_version VARCHAR(64) NOT NULL,
  canonical_type VARCHAR(64) NOT NULL,
  canonical_id UUID NOT NULL,
  canonical_revision_id UUID NOT NULL,
  provider_document_id TEXT,
  payload_hash VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL,
  indexed_at TIMESTAMPTZ,
  tombstoned_at TIMESTAMPTZ,
  CONSTRAINT pk_projection PRIMARY KEY (id),
  CONSTRAINT fk_projection_space FOREIGN KEY(account_id, space_id)
    REFERENCES space (account_id, id),
  CONSTRAINT uq_projection_1 UNIQUE (account_id, id),
  CONSTRAINT uq_projection_canonical UNIQUE (
    account_id, provider, surface, canonical_type, canonical_id, canonical_revision_id
  ),
  CONSTRAINT ck_projection_payload_hash_len CHECK (char_length(payload_hash) = 64),
  CONSTRAINT ck_projection_status CHECK (status IN ('active', 'pending', 'tombstoned'))
);

CREATE TABLE IF NOT EXISTS context_receipt (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  query_hash VARCHAR(64) NOT NULL,
  purpose VARCHAR(64) NOT NULL,
  policy_version VARCHAR(64) NOT NULL,
  eligible_spaces JSONB NOT NULL DEFAULT '[]'::jsonb,
  provider_versions JSONB NOT NULL DEFAULT '{}'::jsonb,
  budget JSONB NOT NULL DEFAULT '{}'::jsonb,
  context_hash VARCHAR(64) NOT NULL,
  partial BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_context_receipt PRIMARY KEY (id),
  CONSTRAINT uq_context_receipt_1 UNIQUE (account_id, id),
  CONSTRAINT ck_context_receipt_query_hash_len CHECK (char_length(query_hash) = 64),
  CONSTRAINT ck_context_receipt_context_hash_len CHECK (char_length(context_hash) = 64)
);

CREATE TABLE IF NOT EXISTS context_receipt_item (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  receipt_id UUID NOT NULL,
  rank INTEGER NOT NULL,
  canonical_type VARCHAR(64) NOT NULL,
  canonical_id UUID NOT NULL,
  revision_id UUID NOT NULL,
  locator TEXT,
  selected BOOLEAN NOT NULL DEFAULT true,
  omit_reason VARCHAR(64),
  CONSTRAINT pk_context_receipt_item PRIMARY KEY (id),
  CONSTRAINT fk_context_receipt_item_receipt FOREIGN KEY(account_id, receipt_id)
    REFERENCES context_receipt (account_id, id),
  CONSTRAINT uq_context_receipt_item_1 UNIQUE (account_id, id),
  CONSTRAINT uq_context_receipt_item_rank UNIQUE (account_id, receipt_id, rank)
);

ALTER TABLE memory_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_item FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON memory_item;
CREATE POLICY tenant_first_party ON memory_item FOR ALL
  USING (memdot_rls_ok(account_id)) WITH CHECK (memdot_rls_ok(account_id));
DROP POLICY IF EXISTS tenant_external_read ON memory_item;
CREATE POLICY tenant_external_read ON memory_item FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE memory_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_revision FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON memory_revision;
CREATE POLICY tenant_first_party ON memory_revision FOR ALL
  USING (memdot_rls_ok(account_id)) WITH CHECK (memdot_rls_ok(account_id));
DROP POLICY IF EXISTS tenant_external_read ON memory_revision;
CREATE POLICY tenant_external_read ON memory_revision FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE current_memory_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE current_memory_revision FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON current_memory_revision;
CREATE POLICY tenant_first_party ON current_memory_revision FOR ALL
  USING (memdot_rls_ok(account_id)) WITH CHECK (memdot_rls_ok(account_id));
DROP POLICY IF EXISTS tenant_external_read ON current_memory_revision;
CREATE POLICY tenant_external_read ON current_memory_revision FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE projection ENABLE ROW LEVEL SECURITY;
ALTER TABLE projection FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON projection;
CREATE POLICY tenant_first_party ON projection FOR ALL
  USING (memdot_rls_ok(account_id)) WITH CHECK (memdot_rls_ok(account_id));
DROP POLICY IF EXISTS tenant_external_read ON projection;
CREATE POLICY tenant_external_read ON projection FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE context_receipt ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_receipt FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON context_receipt;
CREATE POLICY tenant_first_party ON context_receipt FOR ALL
  USING (memdot_rls_ok(account_id)) WITH CHECK (memdot_rls_ok(account_id));

ALTER TABLE context_receipt_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_receipt_item FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON context_receipt_item;
CREATE POLICY tenant_first_party ON context_receipt_item FOR ALL
  USING (memdot_rls_ok(account_id)) WITH CHECK (memdot_rls_ok(account_id));

GRANT SELECT, INSERT, UPDATE, DELETE ON
  memory_item, memory_revision, projection, context_receipt, context_receipt_item,
  current_memory_revision
  TO memdot_core, memdot_test_admin;
REVOKE INSERT, UPDATE, DELETE ON current_memory_revision FROM memdot_core;

ALTER TABLE memory_item OWNER TO memdot_migrate;
ALTER TABLE memory_revision OWNER TO memdot_migrate;
ALTER TABLE current_memory_revision OWNER TO memdot_migrate;
ALTER TABLE projection OWNER TO memdot_migrate;
ALTER TABLE context_receipt OWNER TO memdot_migrate;
ALTER TABLE context_receipt_item OWNER TO memdot_migrate;

DROP TRIGGER IF EXISTS trg_memory_item_pending_gate ON memory_item;
CREATE TRIGGER trg_memory_item_pending_gate BEFORE INSERT OR UPDATE ON memory_item
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_memory_revision_pending_gate ON memory_revision;
CREATE TRIGGER trg_memory_revision_pending_gate BEFORE INSERT OR UPDATE ON memory_revision
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_current_memory_revision_pending_gate ON current_memory_revision;
CREATE TRIGGER trg_current_memory_revision_pending_gate BEFORE INSERT OR UPDATE ON current_memory_revision
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_projection_pending_gate ON projection;
CREATE TRIGGER trg_projection_pending_gate BEFORE INSERT OR UPDATE ON projection
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_context_receipt_pending_gate ON context_receipt;
CREATE TRIGGER trg_context_receipt_pending_gate BEFORE INSERT OR UPDATE ON context_receipt
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_context_receipt_item_pending_gate ON context_receipt_item;
CREATE TRIGGER trg_context_receipt_item_pending_gate BEFORE INSERT OR UPDATE ON context_receipt_item
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();

DROP TRIGGER IF EXISTS trg_memory_item_private_relabel ON memory_item;
CREATE TRIGGER trg_memory_item_private_relabel BEFORE UPDATE ON memory_item
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_memory_revision_private_relabel ON memory_revision;
CREATE TRIGGER trg_memory_revision_private_relabel BEFORE UPDATE ON memory_revision
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_current_memory_revision_private_relabel ON current_memory_revision;
CREATE TRIGGER trg_current_memory_revision_private_relabel BEFORE UPDATE ON current_memory_revision
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_projection_private_relabel ON projection;
CREATE TRIGGER trg_projection_private_relabel BEFORE UPDATE ON projection
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();

DROP TRIGGER IF EXISTS trg_memory_revision_immutable ON memory_revision;
CREATE TRIGGER trg_memory_revision_immutable BEFORE UPDATE OR DELETE ON memory_revision
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_mutation();

DROP TRIGGER IF EXISTS trg_current_memory_revision_outbox ON current_memory_revision;
CREATE TRIGGER trg_current_memory_revision_outbox BEFORE INSERT OR UPDATE ON current_memory_revision
  FOR EACH ROW EXECUTE FUNCTION memdot_require_outbox_for_pointer();

CREATE OR REPLACE FUNCTION memdot_set_current_memory_revision(
  p_pointer_id uuid,
  p_account_id uuid,
  p_space_id uuid,
  p_memory_item_id uuid,
  p_revision_id uuid,
  p_event_id uuid,
  p_payload_sha256 text,
  p_payload jsonb
) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE existing_hash text; existing_revision uuid;
BEGIN
  IF NOT memdot_rls_ok(p_account_id) OR current_setting('app.purpose', true) NOT IN ('first_party','worker') THEN
    RAISE EXCEPTION 'pointer_authorization_denied';
  END IF;
  SELECT payload_sha256 INTO existing_hash FROM outbox_event
    WHERE account_id = p_account_id AND id = p_event_id;
  IF FOUND THEN
    SELECT revision_id INTO existing_revision FROM current_memory_revision
      WHERE account_id = p_account_id AND memory_item_id = p_memory_item_id;
    IF existing_hash = p_payload_sha256 AND existing_revision = p_revision_id THEN RETURN; END IF;
    RAISE EXCEPTION 'pointer_event_conflict';
  END IF;
  INSERT INTO outbox_event(id, account_id, event_type, payload_sha256, payload)
    VALUES (p_event_id, p_account_id, 'memory.current_revision_changed', p_payload_sha256, p_payload);
  PERFORM set_config('app.pointer_outbox_ok', '1', true);
  INSERT INTO current_memory_revision(id, account_id, space_id, memory_item_id, revision_id)
    VALUES (p_pointer_id, p_account_id, p_space_id, p_memory_item_id, p_revision_id)
  ON CONFLICT (account_id, memory_item_id) DO UPDATE SET
    space_id = EXCLUDED.space_id,
    revision_id = EXCLUDED.revision_id,
    updated_at = now();
  PERFORM set_config('app.pointer_outbox_ok', '', true);
END; $$;

ALTER FUNCTION memdot_set_current_memory_revision(uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_set_current_memory_revision(uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_set_current_memory_revision(uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb)
  TO memdot_core, memdot_test_admin, memdot_migrate;
