-- Security corrections: assessment attempts, conversation payloads, Notion/export durability.

CREATE TABLE IF NOT EXISTS assessment_attempt (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  user_id UUID NOT NULL,
  course_id UUID NOT NULL,
  assessment_item_id UUID NOT NULL,
  assessment_revision_id UUID NOT NULL,
  response_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  confidence VARCHAR(32),
  hint_revealed BOOLEAN NOT NULL DEFAULT false,
  answer_revealed BOOLEAN NOT NULL DEFAULT false,
  feedback_at TIMESTAMPTZ,
  status VARCHAR(32) NOT NULL DEFAULT 'in_progress',
  client_attempt_id VARCHAR(128),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_assessment_attempt PRIMARY KEY (id),
  CONSTRAINT fk_assessment_attempt_course FOREIGN KEY (account_id, course_id)
    REFERENCES course (account_id, id),
  CONSTRAINT uq_assessment_attempt_1 UNIQUE (account_id, id),
  CONSTRAINT uq_assessment_attempt_client UNIQUE (account_id, client_attempt_id),
  CONSTRAINT ck_assessment_attempt_status CHECK (
    status IN ('in_progress', 'submitted', 'graded', 'abandoned')
  )
);

ALTER TABLE conversation_turn
  ADD COLUMN IF NOT EXISTS payload_json JSONB,
  ADD COLUMN IF NOT EXISTS payload_ciphertext BYTEA,
  ADD COLUMN IF NOT EXISTS payload_nonce BYTEA,
  ADD COLUMN IF NOT EXISTS occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS parent_turn_id UUID,
  ADD COLUMN IF NOT EXISTS context_receipt_id UUID,
  ADD COLUMN IF NOT EXISTS client_turn_id VARCHAR(128);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'uq_conversation_turn_client'
  ) THEN
    ALTER TABLE conversation_turn
      ADD CONSTRAINT uq_conversation_turn_client
      UNIQUE (account_id, conversation_id, client_turn_id);
  END IF;
END $$;

ALTER TABLE notion_connection
  ADD COLUMN IF NOT EXISTS token_ciphertext BYTEA,
  ADD COLUMN IF NOT EXISTS token_nonce BYTEA,
  ADD COLUMN IF NOT EXISTS pagination_cursor VARCHAR(512),
  ADD COLUMN IF NOT EXISTS rate_limited_until TIMESTAMPTZ;

ALTER TABLE export_job
  ADD COLUMN IF NOT EXISTS package_object_key TEXT,
  ADD COLUMN IF NOT EXISTS package_sha256 VARCHAR(64),
  ADD COLUMN IF NOT EXISTS workflow_state VARCHAR(32) NOT NULL DEFAULT 'accepted';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_export_job_workflow'
  ) THEN
    ALTER TABLE export_job
      ADD CONSTRAINT ck_export_job_workflow CHECK (
        workflow_state IN (
          'accepted', 'packaging', 'uploaded', 'succeeded', 'failed', 'cancelled'
        )
      );
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS deletion_workflow (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  entity_type VARCHAR(64) NOT NULL,
  entity_id UUID NOT NULL,
  space_id UUID,
  state VARCHAR(32) NOT NULL DEFAULT 'accepted',
  tombstone_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_deletion_workflow PRIMARY KEY (id),
  CONSTRAINT uq_deletion_workflow_1 UNIQUE (account_id, id),
  CONSTRAINT ck_deletion_workflow_state CHECK (
    state IN (
      'accepted', 'tombstoned', 'revoking_grants', 'purging_projections',
      'completed', 'failed', 'cancelled'
    )
  )
);

DO $$
DECLARE
  tbl TEXT;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'assessment_attempt',
    'deletion_workflow'
  ]
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', tbl);
    EXECUTE format('DROP POLICY IF EXISTS tenant_first_party ON %I', tbl);
    EXECUTE format(
      'CREATE POLICY tenant_first_party ON %I FOR ALL USING (memdot_rls_ok(account_id)) WITH CHECK (memdot_rls_ok(account_id))',
      tbl
    );
    EXECUTE format('ALTER TABLE %I OWNER TO memdot_migrate', tbl);
    EXECUTE format(
      'GRANT SELECT, INSERT, UPDATE, DELETE ON %I TO memdot_core, memdot_test_admin',
      tbl
    );
  END LOOP;
END $$;

ALTER TABLE assessment_attempt OWNER TO memdot_migrate;
ALTER TABLE deletion_workflow OWNER TO memdot_migrate;
