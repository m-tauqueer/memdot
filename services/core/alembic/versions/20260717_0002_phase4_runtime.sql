-- Phase 4 runtime extensions (additive, compatibility-safe).

ALTER TABLE idempotency_record
  ADD COLUMN IF NOT EXISTS route TEXT,
  ADD COLUMN IF NOT EXISTS response_body JSONB,
  ADD COLUMN IF NOT EXISTS response_headers JSONB;

ALTER TABLE outbox_event
  ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS claim_token UUID,
  ADD COLUMN IF NOT EXISTS claim_expires_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS claimed_by TEXT;

ALTER TABLE durable_job DROP CONSTRAINT IF EXISTS ck_durable_job_ck_durable_job_status;
ALTER TABLE durable_job
  ADD COLUMN IF NOT EXISTS space_id UUID,
  ADD COLUMN IF NOT EXISTS correlation_id UUID,
  ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(256),
  ADD COLUMN IF NOT EXISTS payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS progress JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS error_code VARCHAR(64),
  ADD COLUMN IF NOT EXISTS error_detail_safe TEXT,
  ADD COLUMN IF NOT EXISTS auth_snapshot JSONB,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS dead_letter_at TIMESTAMPTZ;
ALTER TABLE durable_job
  ADD CONSTRAINT ck_durable_job_status CHECK (
    status IN ('pending', 'queued', 'running', 'succeeded', 'failed', 'cancelled', 'dead_letter')
  );

ALTER TABLE job_attempt
  ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS error_code VARCHAR(64),
  ADD COLUMN IF NOT EXISTS error_detail_safe TEXT;

ALTER TABLE source
  ADD COLUMN IF NOT EXISTS processing_status VARCHAR(32) NOT NULL DEFAULT 'draft',
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE source DROP CONSTRAINT IF EXISTS ck_source_processing_status;
ALTER TABLE source
  ADD CONSTRAINT ck_source_processing_status CHECK (
    processing_status IN (
      'draft', 'upload_pending', 'uploaded', 'queued', 'running',
      'partial', 'succeeded', 'failed', 'cancelled'
    )
  );

ALTER TABLE parse_run
  ADD COLUMN IF NOT EXISTS profile_hash VARCHAR(64),
  ADD COLUMN IF NOT EXISTS is_shadow BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS quality_score NUMERIC,
  ADD COLUMN IF NOT EXISTS stage_checkpoint JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS artifact_object_key TEXT,
  ADD COLUMN IF NOT EXISTS error_code VARCHAR(64),
  ADD COLUMN IF NOT EXISTS error_detail_safe TEXT,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE document_element
  ADD COLUMN IF NOT EXISTS element_index INTEGER,
  ADD COLUMN IF NOT EXISTS parent_element_id UUID,
  ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64),
  ADD COLUMN IF NOT EXISTS exact_text TEXT,
  ADD COLUMN IF NOT EXISTS normalized_text TEXT,
  ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS upload_intent (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  source_id UUID NOT NULL,
  object_key TEXT NOT NULL,
  expected_sha256 VARCHAR(64) NOT NULL,
  expected_byte_count BIGINT NOT NULL,
  content_type VARCHAR(128) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_upload_intent PRIMARY KEY (id),
  CONSTRAINT fk_upload_intent_source FOREIGN KEY(account_id, source_id)
    REFERENCES source (account_id, id),
  CONSTRAINT fk_upload_intent_source_space FOREIGN KEY(account_id, space_id, source_id)
    REFERENCES source (account_id, space_id, id),
  CONSTRAINT uq_upload_intent_1 UNIQUE (account_id, id),
  CONSTRAINT ck_upload_intent_sha_len CHECK (char_length(expected_sha256) = 64)
);

CREATE TABLE IF NOT EXISTS current_active_parse_run (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  source_id UUID NOT NULL,
  source_revision_id UUID NOT NULL,
  parse_run_id UUID NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_current_active_parse_run PRIMARY KEY (id),
  CONSTRAINT fk_current_active_parse_source FOREIGN KEY(account_id, source_id)
    REFERENCES source (account_id, id),
  CONSTRAINT fk_current_active_parse_revision FOREIGN KEY(account_id, source_revision_id)
    REFERENCES source_revision (account_id, id),
  CONSTRAINT fk_current_active_parse_run FOREIGN KEY(account_id, parse_run_id)
    REFERENCES parse_run (account_id, id),
  CONSTRAINT uq_current_active_parse_run_1 UNIQUE (account_id, source_id, source_revision_id)
);

ALTER TABLE upload_intent ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_intent FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON upload_intent;
CREATE POLICY tenant_first_party ON upload_intent FOR ALL
  USING (memdot_rls_ok(account_id)) WITH CHECK (memdot_rls_ok(account_id));

ALTER TABLE current_active_parse_run ENABLE ROW LEVEL SECURITY;
ALTER TABLE current_active_parse_run FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON current_active_parse_run;
CREATE POLICY tenant_first_party ON current_active_parse_run FOR ALL
  USING (memdot_rls_ok(account_id)) WITH CHECK (memdot_rls_ok(account_id));
DROP POLICY IF EXISTS tenant_external_read ON current_active_parse_run;
CREATE POLICY tenant_external_read ON current_active_parse_run FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

GRANT SELECT, INSERT, UPDATE, DELETE ON upload_intent, current_active_parse_run
  TO memdot_core, memdot_test_admin;
REVOKE INSERT, UPDATE, DELETE ON current_active_parse_run FROM memdot_core;

ALTER TABLE upload_intent OWNER TO memdot_migrate;
ALTER TABLE current_active_parse_run OWNER TO memdot_migrate;

DROP TRIGGER IF EXISTS trg_upload_intent_pending_gate ON upload_intent;
CREATE TRIGGER trg_upload_intent_pending_gate BEFORE INSERT OR UPDATE ON upload_intent
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_current_active_parse_pending_gate ON current_active_parse_run;
CREATE TRIGGER trg_current_active_parse_pending_gate BEFORE INSERT OR UPDATE ON current_active_parse_run
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_current_active_parse_outbox ON current_active_parse_run;
CREATE TRIGGER trg_current_active_parse_outbox BEFORE INSERT OR UPDATE ON current_active_parse_run
  FOR EACH ROW EXECUTE FUNCTION memdot_require_outbox_for_pointer();

CREATE OR REPLACE FUNCTION memdot_claim_outbox_events(
  p_worker_id text,
  p_batch_size integer,
  p_lease_seconds integer
) RETURNS SETOF outbox_event
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  v_now timestamptz := now();
  v_token uuid := gen_random_uuid();
  v_expires timestamptz := v_now + make_interval(secs => p_lease_seconds);
BEGIN
  RETURN QUERY
  WITH candidates AS (
    SELECT oe.id, oe.account_id
    FROM outbox_event oe
    WHERE oe.published_at IS NULL
      AND (oe.claim_expires_at IS NULL OR oe.claim_expires_at < v_now)
    ORDER BY oe.created_at ASC
    LIMIT p_batch_size
    FOR UPDATE SKIP LOCKED
  ),
  claimed AS (
    UPDATE outbox_event oe
    SET claim_token = v_token,
        claim_expires_at = v_expires,
        claimed_by = p_worker_id
    FROM candidates c
    WHERE oe.account_id = c.account_id AND oe.id = c.id
    RETURNING oe.*
  )
  SELECT * FROM claimed;
END; $$;

CREATE OR REPLACE FUNCTION memdot_ack_outbox_event(
  p_account_id uuid,
  p_event_id uuid,
  p_claim_token uuid
) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  updated integer;
BEGIN
  UPDATE outbox_event
  SET published_at = now(),
      claim_token = NULL,
      claim_expires_at = NULL,
      claimed_by = NULL
  WHERE account_id = p_account_id
    AND id = p_event_id
    AND claim_token = p_claim_token
    AND published_at IS NULL;
  GET DIAGNOSTICS updated = ROW_COUNT;
  RETURN updated = 1;
END; $$;

CREATE OR REPLACE FUNCTION memdot_set_current_active_parse_run(
  p_pointer_id uuid,
  p_account_id uuid,
  p_space_id uuid,
  p_source_id uuid,
  p_source_revision_id uuid,
  p_parse_run_id uuid,
  p_event_id uuid,
  p_payload_sha256 text,
  p_payload jsonb
) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  existing_hash text;
BEGIN
  SELECT payload_sha256 INTO existing_hash FROM outbox_event
    WHERE account_id = p_account_id AND id = p_event_id;
  IF existing_hash IS NOT NULL AND existing_hash <> p_payload_sha256 THEN
    RAISE EXCEPTION 'outbox_payload_hash_mismatch';
  END IF;
  IF existing_hash IS NULL THEN
    INSERT INTO outbox_event(id, account_id, event_type, payload_sha256, payload)
      VALUES (p_event_id, p_account_id, 'source.active_parse_changed', p_payload_sha256, p_payload);
  END IF;
  PERFORM set_config('app.pointer_outbox_ok', '1', true);
  INSERT INTO current_active_parse_run(
    id, account_id, space_id, source_id, source_revision_id, parse_run_id
  ) VALUES (
    p_pointer_id, p_account_id, p_space_id, p_source_id, p_source_revision_id, p_parse_run_id
  )
  ON CONFLICT (account_id, source_id, source_revision_id) DO UPDATE SET
    parse_run_id = EXCLUDED.parse_run_id,
    updated_at = now();
  PERFORM set_config('app.pointer_outbox_ok', '', true);
END; $$;

ALTER FUNCTION memdot_claim_outbox_events(text, integer, integer) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_claim_outbox_events(text, integer, integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_claim_outbox_events(text, integer, integer)
  TO memdot_core, memdot_test_admin, memdot_migrate;

ALTER FUNCTION memdot_ack_outbox_event(uuid, uuid, uuid) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_ack_outbox_event(uuid, uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_ack_outbox_event(uuid, uuid, uuid)
  TO memdot_core, memdot_test_admin, memdot_migrate;

ALTER FUNCTION memdot_set_current_active_parse_run(uuid, uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb)
  OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_set_current_active_parse_run(uuid, uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb)
  FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_set_current_active_parse_run(uuid, uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb)
  TO memdot_core, memdot_test_admin, memdot_migrate;

-- Outbox dispatch metadata may be updated; payload and identity fields remain immutable.
CREATE OR REPLACE FUNCTION memdot_allow_outbox_dispatch_update() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'append_only_table_mutation_denied';
  END IF;
  IF OLD.account_id IS DISTINCT FROM NEW.account_id
     OR OLD.event_type IS DISTINCT FROM NEW.event_type
     OR OLD.payload_sha256 IS DISTINCT FROM NEW.payload_sha256
     OR OLD.payload IS DISTINCT FROM NEW.payload
     OR OLD.created_at IS DISTINCT FROM NEW.created_at
  THEN
    RAISE EXCEPTION 'outbox_immutable_fields_mutation_denied';
  END IF;
  RETURN NEW;
END; $$;

DROP TRIGGER IF EXISTS trg_outbox_event_append_only ON outbox_event;
CREATE TRIGGER trg_outbox_event_dispatch_update
  BEFORE UPDATE ON outbox_event
  FOR EACH ROW EXECUTE FUNCTION memdot_allow_outbox_dispatch_update();
CREATE TRIGGER trg_outbox_event_append_only_delete
  BEFORE DELETE ON outbox_event
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_append_only_mutation();

-- Job attempts remain append-only for identity/history but allow progress completion fields.
CREATE OR REPLACE FUNCTION memdot_allow_job_attempt_progress_update() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'append_only_table_mutation_denied';
  END IF;
  IF OLD.account_id IS DISTINCT FROM NEW.account_id
     OR OLD.job_id IS DISTINCT FROM NEW.job_id
     OR OLD.attempt_number IS DISTINCT FROM NEW.attempt_number
     OR OLD.created_at IS DISTINCT FROM NEW.created_at
  THEN
    RAISE EXCEPTION 'job_attempt_immutable_fields_mutation_denied';
  END IF;
  RETURN NEW;
END; $$;

-- Phase 3 installed both immutable and append-only guards. Replace both;
-- otherwise the earlier immutable trigger fires first and makes completion
-- impossible even though this migration permits progress fields.
DROP TRIGGER IF EXISTS trg_job_attempt_immutable ON job_attempt;
DROP TRIGGER IF EXISTS trg_job_attempt_append_only ON job_attempt;
CREATE TRIGGER trg_job_attempt_progress_update
  BEFORE UPDATE ON job_attempt
  FOR EACH ROW EXECUTE FUNCTION memdot_allow_job_attempt_progress_update();
CREATE TRIGGER trg_job_attempt_append_only_delete
  BEFORE DELETE ON job_attempt
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_append_only_mutation();
