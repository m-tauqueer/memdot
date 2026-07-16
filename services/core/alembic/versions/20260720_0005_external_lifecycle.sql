-- External lifecycle: Notion connector bindings, export jobs, deletion tombstones.

CREATE TABLE IF NOT EXISTS notion_connection (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  workspace_id VARCHAR(128),
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  oauth_stub JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_notion_connection PRIMARY KEY (id),
  CONSTRAINT uq_notion_connection_1 UNIQUE (account_id, id),
  CONSTRAINT ck_notion_connection_status CHECK (
    status IN ('pending', 'connected', 'revoked', 'error')
  )
);

CREATE TABLE IF NOT EXISTS notion_page_binding (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  connection_id UUID NOT NULL,
  notion_page_id VARCHAR(128) NOT NULL,
  title VARCHAR(512) NOT NULL DEFAULT '',
  direction VARCHAR(32) NOT NULL DEFAULT 'inbound_only',
  sync_state VARCHAR(32) NOT NULL DEFAULT 'idle',
  conflict_state VARCHAR(32),
  last_snapshot_sha256 VARCHAR(64),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_notion_page_binding PRIMARY KEY (id),
  CONSTRAINT fk_notion_page_binding_space FOREIGN KEY(account_id, space_id)
    REFERENCES space (account_id, id),
  CONSTRAINT fk_notion_page_binding_connection FOREIGN KEY(account_id, connection_id)
    REFERENCES notion_connection (account_id, id),
  CONSTRAINT uq_notion_page_binding_1 UNIQUE (account_id, id),
  CONSTRAINT uq_notion_page_binding_page UNIQUE (account_id, connection_id, notion_page_id),
  CONSTRAINT ck_notion_page_binding_direction CHECK (
    direction IN ('inbound_only', 'bidirectional')
  ),
  CONSTRAINT ck_notion_page_binding_sync CHECK (
    sync_state IN ('idle', 'syncing', 'paused', 'error')
  ),
  CONSTRAINT ck_notion_page_binding_conflict CHECK (
    conflict_state IS NULL OR conflict_state IN (
      'keep_notion', 'keep_memdot', 'reviewed_merge', 'unresolved'
    )
  )
);

CREATE TABLE IF NOT EXISTS deletion_tombstone (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  entity_type VARCHAR(64) NOT NULL,
  entity_id UUID NOT NULL,
  space_id UUID,
  restore_key VARCHAR(128),
  tombstoned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_deletion_tombstone PRIMARY KEY (id),
  CONSTRAINT uq_deletion_tombstone_1 UNIQUE (account_id, id),
  CONSTRAINT uq_deletion_tombstone_entity UNIQUE (account_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS export_job (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  manifest_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ,
  CONSTRAINT pk_export_job PRIMARY KEY (id),
  CONSTRAINT fk_export_job_space FOREIGN KEY(account_id, space_id)
    REFERENCES space (account_id, id),
  CONSTRAINT uq_export_job_1 UNIQUE (account_id, id),
  CONSTRAINT ck_export_job_status CHECK (
    status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled')
  )
);

DO $$
DECLARE
  tbl TEXT;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'notion_connection',
    'notion_page_binding',
    'deletion_tombstone',
    'export_job'
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
    EXECUTE format('DROP TRIGGER IF EXISTS trg_%I_pending_gate ON %I', tbl, tbl);
    EXECUTE format(
      'CREATE TRIGGER trg_%I_pending_gate BEFORE INSERT OR UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write()',
      tbl, tbl
    );
  END LOOP;
END $$;

DROP POLICY IF EXISTS tenant_external_interaction ON conversation;
CREATE POLICY tenant_external_interaction ON conversation FOR ALL
  USING (
    memdot_rls_ok(account_id)
    AND current_setting('app.purpose', true) = 'external_interaction'
    AND memdot_external_space_ok(account_id, space_id)
  )
  WITH CHECK (
    memdot_rls_ok(account_id)
    AND current_setting('app.purpose', true) = 'external_interaction'
    AND memdot_external_space_ok(account_id, space_id)
  );

DROP POLICY IF EXISTS tenant_external_interaction ON conversation_turn;
CREATE POLICY tenant_external_interaction ON conversation_turn FOR ALL
  USING (
    memdot_rls_ok(account_id)
    AND current_setting('app.purpose', true) = 'external_interaction'
    AND memdot_external_space_ok(account_id, space_id)
  )
  WITH CHECK (
    memdot_rls_ok(account_id)
    AND current_setting('app.purpose', true) = 'external_interaction'
    AND memdot_external_space_ok(account_id, space_id)
  );

DROP POLICY IF EXISTS tenant_external_write ON space;
CREATE POLICY tenant_external_write ON space FOR SELECT
  USING (
    memdot_rls_ok(account_id)
    AND current_setting('app.purpose', true) IN ('external_interaction', 'external_propose')
    AND visibility IN ('general', 'learning')
  );
