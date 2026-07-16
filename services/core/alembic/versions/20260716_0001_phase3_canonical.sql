-- FROZEN Phase 3 canonical schema. Do not use Base.metadata.create_all().
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'memdot_migrate') THEN
    CREATE ROLE memdot_migrate NOINHERIT LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'memdot_core') THEN
    CREATE ROLE memdot_core NOINHERIT LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'memdot_test_admin') THEN
    CREATE ROLE memdot_test_admin NOINHERIT LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
END $$;
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user AND rolsuper) THEN
    ALTER ROLE memdot_migrate BYPASSRLS;
    ALTER ROLE memdot_core NOBYPASSRLS;
    ALTER ROLE memdot_test_admin NOBYPASSRLS;
  END IF;
END $$;
GRANT USAGE, CREATE ON SCHEMA public TO memdot_migrate;
GRANT USAGE ON SCHEMA public TO memdot_core, memdot_test_admin;

CREATE TABLE account (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	status VARCHAR(32) NOT NULL,
	display_name VARCHAR(256),
	timezone VARCHAR(64),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_account PRIMARY KEY (id),
	CONSTRAINT uq_account_1 UNIQUE (account_id, id),
	CONSTRAINT ck_account_ck_account_status CHECK (status IN ('pending_attestation', 'active', 'disabled'))
);
CREATE TABLE audit_event (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	actor_id UUID,
	event_type VARCHAR(128) NOT NULL,
	payload JSONB NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_audit_event PRIMARY KEY (id),
	CONSTRAINT uq_audit_event_1 UNIQUE (account_id, id)
);
CREATE TABLE conflict_set (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID,
	resolution VARCHAR(32) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_conflict_set PRIMARY KEY (id),
	CONSTRAINT uq_conflict_set_1 UNIQUE (account_id, id),
	CONSTRAINT ck_conflict_set_ck_conflict_set_resolution CHECK (resolution IN ('unresolved', 'user_resolved', 'source_superseded'))
);
CREATE TABLE durable_job (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	job_type VARCHAR(128) NOT NULL,
	status VARCHAR(32) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_durable_job PRIMARY KEY (id),
	CONSTRAINT uq_durable_job_1 UNIQUE (account_id, id),
	CONSTRAINT ck_durable_job_ck_durable_job_status CHECK (status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled'))
);
CREATE TABLE idempotency_record (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	idempotency_key VARCHAR(256) NOT NULL,
	fingerprint_sha256 VARCHAR(64) NOT NULL,
	response_status INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_idempotency_record PRIMARY KEY (id),
	CONSTRAINT uq_idempotency_record_1 UNIQUE (account_id, idempotency_key)
);
CREATE TABLE oidc_login_challenge (
	id UUID NOT NULL,
	state_hash VARCHAR(128) NOT NULL,
	nonce_hash VARCHAR(128) NOT NULL,
	pkce_verifier_ciphertext TEXT NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	consumed_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_oidc_login_challenge PRIMARY KEY (id),
	CONSTRAINT uq_oidc_login_challenge_state UNIQUE (state_hash)
);
CREATE TABLE oidc_token_replay (
	id UUID NOT NULL,
	issuer TEXT NOT NULL,
	jti TEXT NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_oidc_token_replay PRIMARY KEY (id),
	CONSTRAINT uq_oidc_token_replay_1 UNIQUE (issuer, jti)
);
CREATE TABLE outbox_event (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	event_type VARCHAR(128) NOT NULL,
	payload_sha256 VARCHAR(64) NOT NULL,
	payload JSONB NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_outbox_event PRIMARY KEY (id),
	CONSTRAINT uq_outbox_event_1 UNIQUE (account_id, id)
);
CREATE TABLE projection_state (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	projection_name VARCHAR(128) NOT NULL,
	cursor TEXT,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_projection_state PRIMARY KEY (id),
	CONSTRAINT uq_projection_state_1 UNIQUE (account_id, projection_name)
);
CREATE TABLE provenance_record (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID,
	entity_type VARCHAR(64) NOT NULL,
	entity_id UUID NOT NULL,
	activity VARCHAR(128) NOT NULL,
	agent_actor_id UUID,
	source_revision_id UUID,
	recorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_provenance_record PRIMARY KEY (id),
	CONSTRAINT uq_provenance_record_1 UNIQUE (account_id, id)
);
CREATE TABLE truth_classification (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID,
	entity_type VARCHAR(64) NOT NULL,
	entity_id UUID NOT NULL,
	truth_class VARCHAR(64) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_truth_classification PRIMARY KEY (id),
	CONSTRAINT uq_truth_classification_1 UNIQUE (account_id, id),
	CONSTRAINT uq_truth_classification_2 UNIQUE (account_id, entity_type, entity_id),
	CONSTRAINT ck_truth_classification_ck_truth_classification_class CHECK (truth_class IN ('source_assertion', 'user_assertion', 'external_knowledge', 'derived_proposal', 'approved_derived', 'learner_evidence', 'system_metadata'))
);
CREATE TABLE actor (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	kind VARCHAR(32) NOT NULL,
	reference_id UUID,
	revoked_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_actor PRIMARY KEY (id),
	CONSTRAINT fk_actor_account FOREIGN KEY(account_id) REFERENCES account (id),
	CONSTRAINT uq_actor_1 UNIQUE (account_id, id),
	CONSTRAINT ck_actor_ck_actor_kind CHECK (kind IN ('user', 'external_client', 'system'))
);
CREATE TABLE conflict_member (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	conflict_set_id UUID NOT NULL,
	entity_type VARCHAR(64) NOT NULL,
	entity_id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_conflict_member PRIMARY KEY (id),
	CONSTRAINT fk_conflict_member_set FOREIGN KEY(account_id, conflict_set_id) REFERENCES conflict_set (account_id, id),
	CONSTRAINT uq_conflict_member_1 UNIQUE (account_id, id),
	CONSTRAINT uq_conflict_member_2 UNIQUE (account_id, conflict_set_id, entity_type, entity_id)
);
CREATE TABLE job_attempt (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	job_id UUID NOT NULL,
	attempt_number INTEGER NOT NULL,
	status VARCHAR(32) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_job_attempt PRIMARY KEY (id),
	CONSTRAINT fk_job_attempt_job FOREIGN KEY(account_id, job_id) REFERENCES durable_job (account_id, id),
	CONSTRAINT uq_job_attempt_1 UNIQUE (account_id, id)
);
CREATE TABLE operator_bootstrap (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	issuer TEXT NOT NULL,
	subject TEXT NOT NULL,
	singleton_key INTEGER NOT NULL,
	completed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	revoked_at TIMESTAMP WITH TIME ZONE,
	CONSTRAINT pk_operator_bootstrap PRIMARY KEY (id),
	CONSTRAINT fk_operator_bootstrap_account FOREIGN KEY(account_id) REFERENCES account (id),
	CONSTRAINT uq_operator_bootstrap_1 UNIQUE (account_id, id),
	CONSTRAINT uq_operator_bootstrap_singleton UNIQUE (singleton_key),
	CONSTRAINT ck_operator_bootstrap_ck_operator_bootstrap_singleton CHECK (singleton_key = 1)
);
CREATE TABLE space (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	name VARCHAR(256) NOT NULL,
	visibility VARCHAR(32) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_space PRIMARY KEY (id),
	CONSTRAINT fk_space_account FOREIGN KEY(account_id) REFERENCES account (id),
	CONSTRAINT uq_space_1 UNIQUE (account_id, id),
	CONSTRAINT ck_space_ck_space_visibility CHECK (visibility IN ('general', 'learning', 'private'))
);
CREATE TABLE "user" (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	email VARCHAR(320),
	display_name VARCHAR(256),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_user PRIMARY KEY (id),
	CONSTRAINT fk_user_account FOREIGN KEY(account_id) REFERENCES account (id),
	CONSTRAINT uq_user_1 UNIQUE (account_id, id)
);
CREATE TABLE account_member (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	user_id UUID NOT NULL,
	role VARCHAR(32) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_account_member PRIMARY KEY (id),
	CONSTRAINT fk_account_member_account FOREIGN KEY(account_id) REFERENCES account (id),
	CONSTRAINT fk_account_member_user FOREIGN KEY(account_id, user_id) REFERENCES "user" (account_id, id),
	CONSTRAINT uq_account_member_1 UNIQUE (account_id, id),
	CONSTRAINT uq_account_member_2 UNIQUE (account_id, user_id)
);
CREATE TABLE authored_document (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	title VARCHAR(512) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_authored_document PRIMARY KEY (id),
	CONSTRAINT fk_authored_document_space FOREIGN KEY(account_id, space_id) REFERENCES space (account_id, id),
	CONSTRAINT uq_authored_document_1 UNIQUE (account_id, id),
	CONSTRAINT uq_authored_document_space_id UNIQUE (account_id, space_id, id)
);
CREATE TABLE browser_session (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	user_id UUID NOT NULL,
	actor_id UUID NOT NULL,
	secret_hash VARCHAR(128) NOT NULL,
	csrf_token_hash VARCHAR(128) NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	idle_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	last_auth_at TIMESTAMP WITH TIME ZONE NOT NULL,
	rotated_at TIMESTAMP WITH TIME ZONE,
	revoked_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_browser_session PRIMARY KEY (id),
	CONSTRAINT fk_browser_session_account FOREIGN KEY(account_id) REFERENCES account (id),
	CONSTRAINT fk_browser_session_user FOREIGN KEY(account_id, user_id) REFERENCES "user" (account_id, id),
	CONSTRAINT fk_browser_session_actor FOREIGN KEY(account_id, actor_id) REFERENCES actor (account_id, id),
	CONSTRAINT uq_browser_session_1 UNIQUE (account_id, id)
);
CREATE TABLE conversation (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	source_client VARCHAR(64) NOT NULL,
	completeness VARCHAR(32) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_conversation PRIMARY KEY (id),
	CONSTRAINT fk_conversation_space FOREIGN KEY(account_id, space_id) REFERENCES space (account_id, id),
	CONSTRAINT uq_conversation_1 UNIQUE (account_id, id),
	CONSTRAINT uq_conversation_space_id UNIQUE (account_id, space_id, id)
);
CREATE TABLE external_client_grant (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	actor_id UUID NOT NULL,
	client_id VARCHAR(256) NOT NULL,
	scopes TEXT NOT NULL,
	revoked_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_external_client_grant PRIMARY KEY (id),
	CONSTRAINT fk_external_grant_account FOREIGN KEY(account_id) REFERENCES account (id),
	CONSTRAINT fk_external_grant_actor FOREIGN KEY(account_id, actor_id) REFERENCES actor (account_id, id),
	CONSTRAINT uq_external_client_grant_1 UNIQUE (account_id, id)
);
CREATE TABLE external_identity (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	user_id UUID NOT NULL,
	issuer TEXT NOT NULL,
	subject TEXT NOT NULL,
	provider VARCHAR(64),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_external_identity PRIMARY KEY (id),
	CONSTRAINT fk_external_identity_account FOREIGN KEY(account_id) REFERENCES account (id),
	CONSTRAINT fk_external_identity_user FOREIGN KEY(account_id, user_id) REFERENCES "user" (account_id, id),
	CONSTRAINT uq_external_identity_1 UNIQUE (issuer, subject),
	CONSTRAINT uq_external_identity_2 UNIQUE (account_id, id)
);
CREATE TABLE hosted_adult_attestation (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	user_id UUID NOT NULL,
	confirmed BOOLEAN NOT NULL,
	attested_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_hosted_adult_attestation PRIMARY KEY (id),
	CONSTRAINT fk_attestation_account FOREIGN KEY(account_id) REFERENCES account (id),
	CONSTRAINT fk_attestation_user FOREIGN KEY(account_id, user_id) REFERENCES "user" (account_id, id),
	CONSTRAINT uq_hosted_adult_attestation_1 UNIQUE (account_id, user_id),
	CONSTRAINT uq_hosted_adult_attestation_2 UNIQUE (account_id, id)
);
CREATE TABLE proposal (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	target_type VARCHAR(64) NOT NULL,
	target_id UUID NOT NULL,
	base_revision_id UUID,
	truth_class VARCHAR(64) NOT NULL,
	status VARCHAR(32) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_proposal PRIMARY KEY (id),
	CONSTRAINT fk_proposal_space FOREIGN KEY(account_id, space_id) REFERENCES space (account_id, id),
	CONSTRAINT uq_proposal_1 UNIQUE (account_id, id),
	CONSTRAINT ck_proposal_ck_proposal_status CHECK (status IN ('pending', 'approved', 'rejected', 'expired', 'conflicted')),
	CONSTRAINT ck_proposal_ck_proposal_truth_class CHECK (truth_class = 'derived_proposal')
);
CREATE TABLE source (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	title VARCHAR(512) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_source PRIMARY KEY (id),
	CONSTRAINT fk_source_space FOREIGN KEY(account_id, space_id) REFERENCES space (account_id, id),
	CONSTRAINT uq_source_1 UNIQUE (account_id, id),
	CONSTRAINT uq_source_space_id UNIQUE (account_id, space_id, id)
);
CREATE TABLE space_member (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	user_id UUID NOT NULL,
	role VARCHAR(32) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_space_member PRIMARY KEY (id),
	CONSTRAINT fk_space_member_space FOREIGN KEY(account_id, space_id) REFERENCES space (account_id, id),
	CONSTRAINT fk_space_member_user FOREIGN KEY(account_id, user_id) REFERENCES "user" (account_id, id),
	CONSTRAINT uq_space_member_1 UNIQUE (account_id, space_id, user_id),
	CONSTRAINT uq_space_member_2 UNIQUE (account_id, id)
);
CREATE TABLE conversation_turn (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	conversation_id UUID NOT NULL,
	role VARCHAR(32) NOT NULL,
	turn_index INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_conversation_turn PRIMARY KEY (id),
	CONSTRAINT fk_conversation_turn_conversation FOREIGN KEY(account_id, conversation_id) REFERENCES conversation (account_id, id),
	CONSTRAINT fk_conversation_turn_conversation_space FOREIGN KEY(account_id, space_id, conversation_id) REFERENCES conversation (account_id, space_id, id),
	CONSTRAINT uq_conversation_turn_1 UNIQUE (account_id, id)
);
CREATE TABLE document_revision (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	document_id UUID NOT NULL,
	base_revision_id UUID,
	content_sha256 VARCHAR(64) NOT NULL,
	schema_version INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_document_revision PRIMARY KEY (id),
	CONSTRAINT fk_document_revision_document FOREIGN KEY(account_id, document_id) REFERENCES authored_document (account_id, id),
	CONSTRAINT fk_document_revision_document_space FOREIGN KEY(account_id, space_id, document_id) REFERENCES authored_document (account_id, space_id, id),
	CONSTRAINT uq_document_revision_1 UNIQUE (account_id, id),
	CONSTRAINT uq_document_revision_space_id UNIQUE (account_id, space_id, id),
	CONSTRAINT uq_document_revision_pointer UNIQUE (account_id, space_id, document_id, id)
);
CREATE TABLE session_revocation (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	session_id UUID NOT NULL,
	revoked_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_session_revocation PRIMARY KEY (id),
	CONSTRAINT fk_session_revocation_session FOREIGN KEY(account_id, session_id) REFERENCES browser_session (account_id, id),
	CONSTRAINT uq_session_revocation_1 UNIQUE (account_id, id)
);
CREATE TABLE source_revision (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	source_id UUID NOT NULL,
	snapshot_sha256 VARCHAR(64) NOT NULL,
	captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
	source_native_version VARCHAR(256),
	mime_type VARCHAR(128),
	language_hints TEXT,
	byte_count BIGINT,
	page_count INTEGER,
	object_key TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_source_revision PRIMARY KEY (id),
	CONSTRAINT fk_source_revision_source FOREIGN KEY(account_id, source_id) REFERENCES source (account_id, id),
	CONSTRAINT fk_source_revision_source_space FOREIGN KEY(account_id, space_id, source_id) REFERENCES source (account_id, space_id, id),
	CONSTRAINT uq_source_revision_1 UNIQUE (account_id, id),
	CONSTRAINT uq_source_revision_2 UNIQUE (account_id, source_id, snapshot_sha256),
	CONSTRAINT uq_source_revision_space_id UNIQUE (account_id, space_id, id),
	CONSTRAINT uq_source_revision_pointer UNIQUE (account_id, space_id, source_id, id),
	CONSTRAINT ck_source_revision_ck_source_revision_sha_len CHECK (char_length(snapshot_sha256) = 64)
);
CREATE TABLE current_document_revision (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	document_id UUID NOT NULL,
	revision_id UUID NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_current_document_revision PRIMARY KEY (id),
	CONSTRAINT fk_current_document_revision_document FOREIGN KEY(account_id, document_id) REFERENCES authored_document (account_id, id),
	CONSTRAINT fk_current_document_revision_revision FOREIGN KEY(account_id, revision_id) REFERENCES document_revision (account_id, id),
	CONSTRAINT fk_current_document_revision_same_document FOREIGN KEY(account_id, space_id, document_id, revision_id) REFERENCES document_revision (account_id, space_id, document_id, id),
	CONSTRAINT uq_current_document_revision_1 UNIQUE (account_id, document_id)
);
CREATE TABLE current_source_revision (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	source_id UUID NOT NULL,
	revision_id UUID NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_current_source_revision PRIMARY KEY (id),
	CONSTRAINT fk_current_source_revision_source FOREIGN KEY(account_id, source_id) REFERENCES source (account_id, id),
	CONSTRAINT fk_current_source_revision_revision FOREIGN KEY(account_id, revision_id) REFERENCES source_revision (account_id, id),
	CONSTRAINT fk_current_source_revision_same_source FOREIGN KEY(account_id, space_id, source_id, revision_id) REFERENCES source_revision (account_id, space_id, source_id, id),
	CONSTRAINT uq_current_source_revision_1 UNIQUE (account_id, source_id)
);
CREATE TABLE parse_run (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	source_revision_id UUID NOT NULL,
	parser_profile VARCHAR(128) NOT NULL,
	status VARCHAR(32) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_parse_run PRIMARY KEY (id),
	CONSTRAINT fk_parse_run_revision FOREIGN KEY(account_id, source_revision_id) REFERENCES source_revision (account_id, id),
	CONSTRAINT fk_parse_run_revision_space FOREIGN KEY(account_id, space_id, source_revision_id) REFERENCES source_revision (account_id, space_id, id),
	CONSTRAINT uq_parse_run_1 UNIQUE (account_id, id),
	CONSTRAINT uq_parse_run_space_id UNIQUE (account_id, space_id, id),
	CONSTRAINT ck_parse_run_ck_parse_run_status CHECK (status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled'))
);
CREATE TABLE source_blob (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	source_revision_id UUID NOT NULL,
	blob_kind VARCHAR(64) NOT NULL,
	object_key TEXT NOT NULL,
	sha256 VARCHAR(64) NOT NULL,
	byte_count BIGINT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_source_blob PRIMARY KEY (id),
	CONSTRAINT fk_source_blob_revision FOREIGN KEY(account_id, source_revision_id) REFERENCES source_revision (account_id, id),
	CONSTRAINT fk_source_blob_revision_space FOREIGN KEY(account_id, space_id, source_revision_id) REFERENCES source_revision (account_id, space_id, id),
	CONSTRAINT uq_source_blob_1 UNIQUE (account_id, id)
);
CREATE TABLE document_element (
	id UUID NOT NULL,
	account_id UUID NOT NULL,
	space_id UUID NOT NULL,
	parse_run_id UUID NOT NULL,
	element_kind VARCHAR(64) NOT NULL,
	locator TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_document_element PRIMARY KEY (id),
	CONSTRAINT fk_document_element_parse_run FOREIGN KEY(account_id, parse_run_id) REFERENCES parse_run (account_id, id),
	CONSTRAINT fk_document_element_parse_run_space FOREIGN KEY(account_id, space_id, parse_run_id) REFERENCES parse_run (account_id, space_id, id),
	CONSTRAINT uq_document_element_1 UNIQUE (account_id, id)
);

CREATE TABLE IF NOT EXISTS memdot_context_secret (
  id integer PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  hmac_key bytea NOT NULL
);
INSERT INTO memdot_context_secret (id, hmac_key)
VALUES (1, gen_random_bytes(32))
ON CONFLICT (id) DO NOTHING;

CREATE OR REPLACE FUNCTION memdot_set_account_id() RETURNS trigger AS $$
BEGIN
  IF NEW.account_id IS NULL THEN NEW.account_id := NEW.id;
  ELSIF NEW.account_id IS DISTINCT FROM NEW.id THEN RAISE EXCEPTION 'account_id_must_equal_id';
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_account_set_account_id ON account;
CREATE TRIGGER trg_account_set_account_id BEFORE INSERT OR UPDATE ON account
  FOR EACH ROW EXECUTE FUNCTION memdot_set_account_id();

CREATE OR REPLACE FUNCTION memdot_enforce_source_revision_id() RETURNS trigger AS $$
BEGIN
  IF NEW.id IS DISTINCT FROM uuid_generate_v5(NEW.source_id, NEW.snapshot_sha256) THEN
    RAISE EXCEPTION 'source_revision_id_must_be_uuidv5';
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_source_revision_uuidv5 ON source_revision;
CREATE TRIGGER trg_source_revision_uuidv5 BEFORE INSERT ON source_revision
  FOR EACH ROW EXECUTE FUNCTION memdot_enforce_source_revision_id();

CREATE OR REPLACE FUNCTION memdot_deny_private_visibility_change() RETURNS trigger AS $$
BEGIN
  IF OLD.visibility = 'private' AND NEW.visibility IS DISTINCT FROM 'private' THEN
    RAISE EXCEPTION 'private_visibility_immutable';
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_space_private_visibility ON space;
CREATE TRIGGER trg_space_private_visibility BEFORE UPDATE ON space
  FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_visibility_change();

CREATE OR REPLACE FUNCTION memdot_deny_private_space_relabel() RETURNS trigger AS $$
DECLARE old_vis text; new_vis text;
BEGIN
  IF TG_OP = 'UPDATE' AND NEW.space_id IS DISTINCT FROM OLD.space_id THEN
    SELECT visibility INTO old_vis FROM space WHERE id = OLD.space_id AND account_id = OLD.account_id;
    SELECT visibility INTO new_vis FROM space WHERE id = NEW.space_id AND account_id = NEW.account_id;
    IF old_vis = 'private' AND new_vis IS DISTINCT FROM 'private' THEN
      RAISE EXCEPTION 'private_parent_space_relabel_denied';
    END IF;
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION memdot_deny_pending_product_write() RETURNS trigger AS $$
DECLARE st text;
BEGIN
  SELECT status INTO st FROM account WHERE id = NEW.account_id;
  IF st = 'pending_attestation' THEN
    RAISE EXCEPTION 'pending_attestation_product_write_denied';
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION memdot_require_outbox_for_pointer() RETURNS trigger AS $$
BEGIN
  IF current_setting('app.pointer_outbox_ok', true) IS DISTINCT FROM '1' THEN
    RAISE EXCEPTION 'pointer_mutation_requires_outbox';
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION memdot_deny_mutation() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'immutable_table_mutation_denied'; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION memdot_deny_append_only_mutation() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'append_only_table_mutation_denied'; END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION memdot_clear_tenant_context() RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  PERFORM set_config('app.account_id', '', true);
  PERFORM set_config('app.actor_id', '', true);
  PERFORM set_config('app.purpose', '', true);
  PERFORM set_config('app.context_seal', '', true);
  PERFORM set_config('app.context_issued_at', '', true);
  PERFORM set_config('app.context_nonce', '', true);
  PERFORM set_config('app.pointer_outbox_ok', '', true);
END; $$;

CREATE OR REPLACE FUNCTION memdot_begin_tenant_context(
  p_account_id uuid,
  p_actor_id uuid,
  p_purpose text,
  p_issued_at bigint,
  p_nonce text,
  p_signature text
) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  v_kind text; v_revoked timestamptz; v_ref uuid; v_member boolean; v_grant_revoked timestamptz;
  v_key bytea; v_expected text; v_runtime boolean;
BEGIN
  v_runtime := (
    CASE
      WHEN current_setting('role', true) IS NULL OR current_setting('role', true) IN ('', 'none')
        THEN session_user
      ELSE current_setting('role', true)
    END
  ) = 'memdot_core';
  IF p_purpose IN ('migration', 'admin') AND v_runtime THEN
    RAISE EXCEPTION 'purpose_not_allowed_for_runtime';
  END IF;
  IF p_purpose NOT IN ('first_party','external_read','external_propose','external_interaction','worker','migration','admin') THEN
    RAISE EXCEPTION 'invalid_purpose';
  END IF;
  IF abs(extract(epoch FROM clock_timestamp())::bigint - p_issued_at) > 60 THEN
    RAISE EXCEPTION 'tenant_context_expired';
  END IF;
  IF coalesce(p_nonce, '') = '' OR length(p_nonce) > 128 THEN
    RAISE EXCEPTION 'tenant_context_nonce_invalid';
  END IF;
  SELECT hmac_key INTO v_key FROM memdot_context_secret WHERE id = 1;
  v_expected := encode(
    hmac(
      convert_to(
        p_account_id::text || ':' || p_actor_id::text || ':' || p_purpose || ':' ||
        p_issued_at::text || ':' || p_nonce,
        'UTF8'
      ),
      v_key,
      'sha256'
    ),
    'hex'
  );
  IF p_signature IS DISTINCT FROM v_expected THEN
    RAISE EXCEPTION 'tenant_context_signature_invalid';
  END IF;
  SELECT kind, revoked_at, reference_id INTO v_kind, v_revoked, v_ref
  FROM actor WHERE id = p_actor_id AND account_id = p_account_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'invalid_actor'; END IF;
  IF v_revoked IS NOT NULL THEN RAISE EXCEPTION 'actor_revoked'; END IF;
  IF p_purpose = 'first_party' THEN
    IF v_kind <> 'user' THEN RAISE EXCEPTION 'purpose_actor_mismatch'; END IF;
    SELECT EXISTS(SELECT 1 FROM account_member am WHERE am.account_id = p_account_id AND am.user_id = v_ref) INTO v_member;
    IF NOT v_member THEN RAISE EXCEPTION 'membership_missing'; END IF;
  ELSIF p_purpose IN ('external_read','external_propose','external_interaction') THEN
    IF v_kind <> 'external_client' THEN RAISE EXCEPTION 'purpose_actor_mismatch'; END IF;
    SELECT g.revoked_at INTO v_grant_revoked FROM external_client_grant g
      WHERE g.account_id = p_account_id AND g.actor_id = p_actor_id ORDER BY g.created_at DESC LIMIT 1;
    IF NOT FOUND THEN RAISE EXCEPTION 'grant_missing'; END IF;
    IF v_grant_revoked IS NOT NULL THEN RAISE EXCEPTION 'grant_revoked'; END IF;
  ELSIF p_purpose = 'worker' THEN
    IF v_kind <> 'system' THEN RAISE EXCEPTION 'worker_requires_system_actor'; END IF;
  END IF;
  PERFORM set_config('app.account_id', p_account_id::text, true);
  PERFORM set_config('app.actor_id', p_actor_id::text, true);
  PERFORM set_config('app.purpose', p_purpose, true);
  PERFORM set_config('app.context_issued_at', p_issued_at::text, true);
  PERFORM set_config('app.context_nonce', p_nonce, true);
  PERFORM set_config('app.context_seal', p_signature, true);
END; $$;

CREATE OR REPLACE FUNCTION memdot_rls_ok(row_account_id uuid) RETURNS boolean
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public AS $$
DECLARE aid text; v_actor text; purpose text; seal text; expected text; v_key bytea; v_revoked timestamptz;
  issued_at text; nonce text;
BEGIN
  aid := current_setting('app.account_id', true);
  v_actor := current_setting('app.actor_id', true);
  purpose := current_setting('app.purpose', true);
  seal := current_setting('app.context_seal', true);
  issued_at := current_setting('app.context_issued_at', true);
  nonce := current_setting('app.context_nonce', true);
  IF coalesce(aid,'') = '' OR coalesce(seal,'') = '' OR coalesce(v_actor,'') = ''
     OR coalesce(issued_at,'') = '' OR coalesce(nonce,'') = '' THEN RETURN false; END IF;
  IF abs(extract(epoch FROM clock_timestamp())::bigint - issued_at::bigint) > 60 THEN RETURN false; END IF;
  IF row_account_id::text IS DISTINCT FROM aid THEN RETURN false; END IF;
  SELECT hmac_key INTO v_key FROM memdot_context_secret WHERE id = 1;
  expected := encode(hmac(convert_to(
    aid || ':' || v_actor || ':' || purpose || ':' || issued_at || ':' || nonce,
    'UTF8'
  ), v_key, 'sha256'), 'hex');
  IF seal IS DISTINCT FROM expected THEN RETURN false; END IF;
  SELECT a.revoked_at INTO v_revoked FROM actor a WHERE a.id = v_actor::uuid AND a.account_id = row_account_id;
  IF NOT FOUND OR v_revoked IS NOT NULL THEN RETURN false; END IF;
  IF purpose IN ('migration','admin') AND (
    CASE
      WHEN current_setting('role', true) IS NULL OR current_setting('role', true) IN ('', 'none')
        THEN session_user
      ELSE current_setting('role', true)
    END
  ) = 'memdot_core' THEN RETURN false; END IF;
  RETURN true;
END; $$;

CREATE OR REPLACE FUNCTION memdot_external_space_ok(p_account_id uuid, p_space_id uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (
    SELECT 1 FROM space s WHERE s.account_id = p_account_id AND s.id = p_space_id
      AND s.visibility IN ('general', 'learning')
  );
$$;

CREATE OR REPLACE FUNCTION memdot_auth_find_identity(p_issuer text, p_subject text)
RETURNS TABLE (id uuid, account_id uuid, user_id uuid, issuer text, subject text, provider varchar)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  RETURN QUERY SELECT ei.id, ei.account_id, ei.user_id, ei.issuer, ei.subject, ei.provider
  FROM external_identity ei WHERE ei.issuer = p_issuer AND ei.subject = p_subject;
END; $$;

CREATE OR REPLACE FUNCTION memdot_auth_load_session(p_session_id uuid, p_secret_hash text)
RETURNS TABLE (
  id uuid, account_id uuid, user_id uuid, actor_id uuid,
  secret_hash varchar, csrf_token_hash varchar,
  expires_at timestamptz, idle_expires_at timestamptz,
  last_auth_at timestamptz, rotated_at timestamptz, revoked_at timestamptz
) LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  RETURN QUERY SELECT bs.id, bs.account_id, bs.user_id, bs.actor_id, bs.secret_hash, bs.csrf_token_hash,
    bs.expires_at, bs.idle_expires_at, bs.last_auth_at, bs.rotated_at, bs.revoked_at
  FROM browser_session bs
  WHERE bs.id = p_session_id AND bs.secret_hash = p_secret_hash AND bs.revoked_at IS NULL;
END; $$;

CREATE OR REPLACE FUNCTION memdot_auth_bootstrap_exists() RETURNS boolean
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (SELECT 1 FROM operator_bootstrap WHERE singleton_key = 1 AND revoked_at IS NULL);
$$;

CREATE OR REPLACE FUNCTION memdot_auth_find_actor_for_user(p_account_id uuid, p_user_id uuid)
RETURNS TABLE (id uuid, account_id uuid, kind varchar, reference_id uuid, revoked_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  RETURN QUERY SELECT a.id, a.account_id, a.kind, a.reference_id, a.revoked_at
  FROM actor a WHERE a.account_id = p_account_id AND a.reference_id = p_user_id AND a.kind = 'user'
  LIMIT 1;
END; $$;

CREATE OR REPLACE FUNCTION memdot_oidc_create_challenge(
  p_id uuid, p_state_hash text, p_nonce_hash text,
  p_pkce_verifier_ciphertext text, p_expires_at timestamptz
) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  INSERT INTO oidc_login_challenge(
    id, state_hash, nonce_hash, pkce_verifier_ciphertext, expires_at
  ) VALUES (
    p_id, p_state_hash, p_nonce_hash, p_pkce_verifier_ciphertext, p_expires_at
  );
END; $$;

CREATE OR REPLACE FUNCTION memdot_oidc_load_challenge(p_state_hash text)
RETURNS TABLE(
  id uuid, nonce_hash varchar, pkce_verifier_ciphertext text,
  expires_at timestamptz, consumed_at timestamptz
)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT c.id, c.nonce_hash, c.pkce_verifier_ciphertext, c.expires_at, c.consumed_at
  FROM oidc_login_challenge c WHERE c.state_hash = p_state_hash;
$$;

CREATE OR REPLACE FUNCTION memdot_oidc_consume_challenge(
  p_id uuid, p_consumed_at timestamptz
) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  UPDATE oidc_login_challenge SET consumed_at = p_consumed_at
  WHERE id = p_id AND consumed_at IS NULL AND expires_at > p_consumed_at;
  RETURN FOUND;
END; $$;

CREATE OR REPLACE FUNCTION memdot_oidc_record_replay(
  p_id uuid, p_issuer text, p_jti text, p_expires_at timestamptz
) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  INSERT INTO oidc_token_replay(id, issuer, jti, expires_at)
    VALUES (p_id, p_issuer, p_jti, p_expires_at);
END; $$;

CREATE OR REPLACE FUNCTION memdot_set_current_source_revision(
  p_pointer_id uuid,
  p_account_id uuid,
  p_space_id uuid,
  p_source_id uuid,
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
    SELECT revision_id INTO existing_revision FROM current_source_revision
      WHERE account_id = p_account_id AND source_id = p_source_id;
    IF existing_hash = p_payload_sha256 AND existing_revision = p_revision_id THEN RETURN; END IF;
    RAISE EXCEPTION 'pointer_event_conflict';
  END IF;
  INSERT INTO outbox_event(id, account_id, event_type, payload_sha256, payload)
    VALUES (p_event_id, p_account_id, 'source.current_revision_changed', p_payload_sha256, p_payload);
  PERFORM set_config('app.pointer_outbox_ok', '1', true);
  INSERT INTO current_source_revision(id, account_id, space_id, source_id, revision_id)
    VALUES (p_pointer_id, p_account_id, p_space_id, p_source_id, p_revision_id)
  ON CONFLICT (account_id, source_id) DO UPDATE SET
    space_id = EXCLUDED.space_id,
    revision_id = EXCLUDED.revision_id,
    updated_at = now();
  PERFORM set_config('app.pointer_outbox_ok', '', true);
END; $$;

CREATE OR REPLACE FUNCTION memdot_set_current_document_revision(
  p_pointer_id uuid,
  p_account_id uuid,
  p_space_id uuid,
  p_document_id uuid,
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
    SELECT revision_id INTO existing_revision FROM current_document_revision
      WHERE account_id = p_account_id AND document_id = p_document_id;
    IF existing_hash = p_payload_sha256 AND existing_revision = p_revision_id THEN RETURN; END IF;
    RAISE EXCEPTION 'pointer_event_conflict';
  END IF;
  INSERT INTO outbox_event(id, account_id, event_type, payload_sha256, payload)
    VALUES (p_event_id, p_account_id, 'document.current_revision_changed', p_payload_sha256, p_payload);
  PERFORM set_config('app.pointer_outbox_ok', '1', true);
  INSERT INTO current_document_revision(id, account_id, space_id, document_id, revision_id)
    VALUES (p_pointer_id, p_account_id, p_space_id, p_document_id, p_revision_id)
  ON CONFLICT (account_id, document_id) DO UPDATE SET
    space_id = EXCLUDED.space_id,
    revision_id = EXCLUDED.revision_id,
    updated_at = now();
  PERFORM set_config('app.pointer_outbox_ok', '', true);
END; $$;

DROP TRIGGER IF EXISTS trg_authored_document_private_relabel ON authored_document;
CREATE TRIGGER trg_authored_document_private_relabel BEFORE UPDATE ON authored_document FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_conversation_private_relabel ON conversation;
CREATE TRIGGER trg_conversation_private_relabel BEFORE UPDATE ON conversation FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_conversation_turn_private_relabel ON conversation_turn;
CREATE TRIGGER trg_conversation_turn_private_relabel BEFORE UPDATE ON conversation_turn FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_current_document_revision_private_relabel ON current_document_revision;
CREATE TRIGGER trg_current_document_revision_private_relabel BEFORE UPDATE ON current_document_revision FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_current_source_revision_private_relabel ON current_source_revision;
CREATE TRIGGER trg_current_source_revision_private_relabel BEFORE UPDATE ON current_source_revision FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_document_element_private_relabel ON document_element;
CREATE TRIGGER trg_document_element_private_relabel BEFORE UPDATE ON document_element FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_document_revision_private_relabel ON document_revision;
CREATE TRIGGER trg_document_revision_private_relabel BEFORE UPDATE ON document_revision FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_parse_run_private_relabel ON parse_run;
CREATE TRIGGER trg_parse_run_private_relabel BEFORE UPDATE ON parse_run FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_proposal_private_relabel ON proposal;
CREATE TRIGGER trg_proposal_private_relabel BEFORE UPDATE ON proposal FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_source_private_relabel ON source;
CREATE TRIGGER trg_source_private_relabel BEFORE UPDATE ON source FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_source_blob_private_relabel ON source_blob;
CREATE TRIGGER trg_source_blob_private_relabel BEFORE UPDATE ON source_blob FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_source_revision_private_relabel ON source_revision;
CREATE TRIGGER trg_source_revision_private_relabel BEFORE UPDATE ON source_revision FOR EACH ROW EXECUTE FUNCTION memdot_deny_private_space_relabel();
DROP TRIGGER IF EXISTS trg_authored_document_pending_gate ON authored_document;
CREATE TRIGGER trg_authored_document_pending_gate BEFORE INSERT OR UPDATE ON authored_document FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_conflict_member_pending_gate ON conflict_member;
CREATE TRIGGER trg_conflict_member_pending_gate BEFORE INSERT OR UPDATE ON conflict_member FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_conflict_set_pending_gate ON conflict_set;
CREATE TRIGGER trg_conflict_set_pending_gate BEFORE INSERT OR UPDATE ON conflict_set FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_conversation_pending_gate ON conversation;
CREATE TRIGGER trg_conversation_pending_gate BEFORE INSERT OR UPDATE ON conversation FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_conversation_turn_pending_gate ON conversation_turn;
CREATE TRIGGER trg_conversation_turn_pending_gate BEFORE INSERT OR UPDATE ON conversation_turn FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_current_document_revision_pending_gate ON current_document_revision;
CREATE TRIGGER trg_current_document_revision_pending_gate BEFORE INSERT OR UPDATE ON current_document_revision FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_current_source_revision_pending_gate ON current_source_revision;
CREATE TRIGGER trg_current_source_revision_pending_gate BEFORE INSERT OR UPDATE ON current_source_revision FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_document_element_pending_gate ON document_element;
CREATE TRIGGER trg_document_element_pending_gate BEFORE INSERT OR UPDATE ON document_element FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_document_revision_pending_gate ON document_revision;
CREATE TRIGGER trg_document_revision_pending_gate BEFORE INSERT OR UPDATE ON document_revision FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_parse_run_pending_gate ON parse_run;
CREATE TRIGGER trg_parse_run_pending_gate BEFORE INSERT OR UPDATE ON parse_run FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_proposal_pending_gate ON proposal;
CREATE TRIGGER trg_proposal_pending_gate BEFORE INSERT OR UPDATE ON proposal FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_provenance_record_pending_gate ON provenance_record;
CREATE TRIGGER trg_provenance_record_pending_gate BEFORE INSERT OR UPDATE ON provenance_record FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_source_pending_gate ON source;
CREATE TRIGGER trg_source_pending_gate BEFORE INSERT OR UPDATE ON source FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_source_blob_pending_gate ON source_blob;
CREATE TRIGGER trg_source_blob_pending_gate BEFORE INSERT OR UPDATE ON source_blob FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_source_revision_pending_gate ON source_revision;
CREATE TRIGGER trg_source_revision_pending_gate BEFORE INSERT OR UPDATE ON source_revision FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();
DROP TRIGGER IF EXISTS trg_truth_classification_pending_gate ON truth_classification;
CREATE TRIGGER trg_truth_classification_pending_gate BEFORE INSERT OR UPDATE ON truth_classification FOR EACH ROW EXECUTE FUNCTION memdot_deny_pending_product_write();

DROP TRIGGER IF EXISTS trg_current_source_revision_outbox ON current_source_revision;
CREATE TRIGGER trg_current_source_revision_outbox BEFORE INSERT OR UPDATE ON current_source_revision
  FOR EACH ROW EXECUTE FUNCTION memdot_require_outbox_for_pointer();
DROP TRIGGER IF EXISTS trg_current_document_revision_outbox ON current_document_revision;
CREATE TRIGGER trg_current_document_revision_outbox BEFORE INSERT OR UPDATE ON current_document_revision
  FOR EACH ROW EXECUTE FUNCTION memdot_require_outbox_for_pointer();

DROP TRIGGER IF EXISTS trg_audit_event_immutable ON audit_event;
CREATE TRIGGER trg_audit_event_immutable BEFORE UPDATE OR DELETE ON audit_event FOR EACH ROW EXECUTE FUNCTION memdot_deny_mutation();
DROP TRIGGER IF EXISTS trg_conversation_turn_immutable ON conversation_turn;
CREATE TRIGGER trg_conversation_turn_immutable BEFORE UPDATE OR DELETE ON conversation_turn FOR EACH ROW EXECUTE FUNCTION memdot_deny_mutation();
DROP TRIGGER IF EXISTS trg_document_revision_immutable ON document_revision;
CREATE TRIGGER trg_document_revision_immutable BEFORE UPDATE OR DELETE ON document_revision FOR EACH ROW EXECUTE FUNCTION memdot_deny_mutation();
DROP TRIGGER IF EXISTS trg_job_attempt_immutable ON job_attempt;
CREATE TRIGGER trg_job_attempt_immutable BEFORE UPDATE OR DELETE ON job_attempt FOR EACH ROW EXECUTE FUNCTION memdot_deny_mutation();
DROP TRIGGER IF EXISTS trg_source_revision_immutable ON source_revision;
CREATE TRIGGER trg_source_revision_immutable BEFORE UPDATE OR DELETE ON source_revision FOR EACH ROW EXECUTE FUNCTION memdot_deny_mutation();
DROP TRIGGER IF EXISTS trg_audit_event_append_only ON audit_event;
CREATE TRIGGER trg_audit_event_append_only BEFORE UPDATE OR DELETE ON audit_event FOR EACH ROW EXECUTE FUNCTION memdot_deny_append_only_mutation();
DROP TRIGGER IF EXISTS trg_conversation_turn_append_only ON conversation_turn;
CREATE TRIGGER trg_conversation_turn_append_only BEFORE UPDATE OR DELETE ON conversation_turn FOR EACH ROW EXECUTE FUNCTION memdot_deny_append_only_mutation();
DROP TRIGGER IF EXISTS trg_job_attempt_append_only ON job_attempt;
CREATE TRIGGER trg_job_attempt_append_only BEFORE UPDATE OR DELETE ON job_attempt FOR EACH ROW EXECUTE FUNCTION memdot_deny_append_only_mutation();
DROP TRIGGER IF EXISTS trg_outbox_event_append_only ON outbox_event;
CREATE TRIGGER trg_outbox_event_append_only BEFORE UPDATE OR DELETE ON outbox_event FOR EACH ROW EXECUTE FUNCTION memdot_deny_append_only_mutation();
ALTER TABLE account ENABLE ROW LEVEL SECURITY;
ALTER TABLE account FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON account;

CREATE POLICY tenant_first_party ON account FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE account_member ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_member FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON account_member;

CREATE POLICY tenant_first_party ON account_member FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE actor ENABLE ROW LEVEL SECURITY;
ALTER TABLE actor FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON actor;

CREATE POLICY tenant_first_party ON actor FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE audit_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_event FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON audit_event;

CREATE POLICY tenant_first_party ON audit_event FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE authored_document ENABLE ROW LEVEL SECURITY;
ALTER TABLE authored_document FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON authored_document;

CREATE POLICY tenant_first_party ON authored_document FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON authored_document;

CREATE POLICY tenant_external_read ON authored_document FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE browser_session ENABLE ROW LEVEL SECURITY;
ALTER TABLE browser_session FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON browser_session;

CREATE POLICY tenant_first_party ON browser_session FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE conflict_member ENABLE ROW LEVEL SECURITY;
ALTER TABLE conflict_member FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON conflict_member;

CREATE POLICY tenant_first_party ON conflict_member FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE conflict_set ENABLE ROW LEVEL SECURITY;
ALTER TABLE conflict_set FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON conflict_set;

CREATE POLICY tenant_first_party ON conflict_set FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE conversation ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON conversation;

CREATE POLICY tenant_first_party ON conversation FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON conversation;

CREATE POLICY tenant_external_read ON conversation FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE conversation_turn ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_turn FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON conversation_turn;

CREATE POLICY tenant_first_party ON conversation_turn FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON conversation_turn;

CREATE POLICY tenant_external_read ON conversation_turn FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE current_document_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE current_document_revision FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON current_document_revision;

CREATE POLICY tenant_first_party ON current_document_revision FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON current_document_revision;

CREATE POLICY tenant_external_read ON current_document_revision FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE current_source_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE current_source_revision FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON current_source_revision;

CREATE POLICY tenant_first_party ON current_source_revision FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON current_source_revision;

CREATE POLICY tenant_external_read ON current_source_revision FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE document_element ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_element FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON document_element;

CREATE POLICY tenant_first_party ON document_element FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON document_element;

CREATE POLICY tenant_external_read ON document_element FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE document_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_revision FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON document_revision;

CREATE POLICY tenant_first_party ON document_revision FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON document_revision;

CREATE POLICY tenant_external_read ON document_revision FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE durable_job ENABLE ROW LEVEL SECURITY;
ALTER TABLE durable_job FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON durable_job;

CREATE POLICY tenant_first_party ON durable_job FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE external_client_grant ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_client_grant FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON external_client_grant;

CREATE POLICY tenant_first_party ON external_client_grant FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE external_identity ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_identity FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON external_identity;

CREATE POLICY tenant_first_party ON external_identity FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE hosted_adult_attestation ENABLE ROW LEVEL SECURITY;
ALTER TABLE hosted_adult_attestation FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON hosted_adult_attestation;

CREATE POLICY tenant_first_party ON hosted_adult_attestation FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE idempotency_record ENABLE ROW LEVEL SECURITY;
ALTER TABLE idempotency_record FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON idempotency_record;

CREATE POLICY tenant_first_party ON idempotency_record FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE job_attempt ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_attempt FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON job_attempt;

CREATE POLICY tenant_first_party ON job_attempt FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE operator_bootstrap ENABLE ROW LEVEL SECURITY;
ALTER TABLE operator_bootstrap FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON operator_bootstrap;

CREATE POLICY tenant_first_party ON operator_bootstrap FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE outbox_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbox_event FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON outbox_event;

CREATE POLICY tenant_first_party ON outbox_event FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE parse_run ENABLE ROW LEVEL SECURITY;
ALTER TABLE parse_run FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON parse_run;

CREATE POLICY tenant_first_party ON parse_run FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON parse_run;

CREATE POLICY tenant_external_read ON parse_run FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE projection_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE projection_state FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON projection_state;

CREATE POLICY tenant_first_party ON projection_state FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE proposal ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposal FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON proposal;

CREATE POLICY tenant_first_party ON proposal FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON proposal;

CREATE POLICY tenant_external_read ON proposal FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE provenance_record ENABLE ROW LEVEL SECURITY;
ALTER TABLE provenance_record FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON provenance_record;

CREATE POLICY tenant_first_party ON provenance_record FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE session_revocation ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_revocation FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON session_revocation;

CREATE POLICY tenant_first_party ON session_revocation FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE source ENABLE ROW LEVEL SECURITY;
ALTER TABLE source FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON source;

CREATE POLICY tenant_first_party ON source FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON source;

CREATE POLICY tenant_external_read ON source FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE source_blob ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_blob FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON source_blob;

CREATE POLICY tenant_first_party ON source_blob FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON source_blob;

CREATE POLICY tenant_external_read ON source_blob FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE source_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_revision FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON source_revision;

CREATE POLICY tenant_first_party ON source_revision FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON source_revision;

CREATE POLICY tenant_external_read ON source_revision FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND memdot_external_space_ok(account_id, space_id));

ALTER TABLE space ENABLE ROW LEVEL SECURITY;
ALTER TABLE space FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON space;

CREATE POLICY tenant_first_party ON space FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

DROP POLICY IF EXISTS tenant_external_read ON space;

CREATE POLICY tenant_external_read ON space FOR SELECT
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) = 'external_read'
    AND visibility IN ('general', 'learning'));

ALTER TABLE space_member ENABLE ROW LEVEL SECURITY;
ALTER TABLE space_member FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON space_member;

CREATE POLICY tenant_first_party ON space_member FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE truth_classification ENABLE ROW LEVEL SECURITY;
ALTER TABLE truth_classification FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON truth_classification;

CREATE POLICY tenant_first_party ON truth_classification FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "user" FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_first_party ON "user";

CREATE POLICY tenant_first_party ON "user" FOR ALL
  USING (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'))
  WITH CHECK (memdot_rls_ok(account_id) AND current_setting('app.purpose', true) IN ('first_party','worker','migration','admin'));

GRANT SELECT, INSERT, UPDATE, DELETE ON account, account_member, actor, audit_event, authored_document, browser_session, conflict_member, conflict_set, conversation, conversation_turn, current_document_revision, current_source_revision, document_element, document_revision, durable_job, external_client_grant, external_identity, hosted_adult_attestation, idempotency_record, job_attempt, operator_bootstrap, outbox_event, parse_run, projection_state, proposal, provenance_record, session_revocation, source, source_blob, source_revision, space, space_member, truth_classification, "user" TO memdot_core, memdot_test_admin;
REVOKE ALL ON oidc_login_challenge, oidc_token_replay FROM PUBLIC, memdot_core;
GRANT SELECT, INSERT, UPDATE, DELETE ON oidc_login_challenge, oidc_token_replay TO memdot_test_admin;
REVOKE INSERT, UPDATE, DELETE ON current_source_revision, current_document_revision FROM memdot_core;
REVOKE ALL ON TABLE memdot_context_secret FROM PUBLIC;
REVOKE ALL ON TABLE memdot_context_secret FROM memdot_core;
REVOKE ALL ON TABLE memdot_context_secret FROM memdot_test_admin;
ALTER TABLE account OWNER TO memdot_migrate;
ALTER TABLE audit_event OWNER TO memdot_migrate;
ALTER TABLE conflict_set OWNER TO memdot_migrate;
ALTER TABLE durable_job OWNER TO memdot_migrate;
ALTER TABLE idempotency_record OWNER TO memdot_migrate;
ALTER TABLE oidc_login_challenge OWNER TO memdot_migrate;
ALTER TABLE oidc_token_replay OWNER TO memdot_migrate;
ALTER TABLE outbox_event OWNER TO memdot_migrate;
ALTER TABLE projection_state OWNER TO memdot_migrate;
ALTER TABLE provenance_record OWNER TO memdot_migrate;
ALTER TABLE truth_classification OWNER TO memdot_migrate;
ALTER TABLE actor OWNER TO memdot_migrate;
ALTER TABLE conflict_member OWNER TO memdot_migrate;
ALTER TABLE job_attempt OWNER TO memdot_migrate;
ALTER TABLE operator_bootstrap OWNER TO memdot_migrate;
ALTER TABLE space OWNER TO memdot_migrate;
ALTER TABLE "user" OWNER TO memdot_migrate;
ALTER TABLE account_member OWNER TO memdot_migrate;
ALTER TABLE authored_document OWNER TO memdot_migrate;
ALTER TABLE browser_session OWNER TO memdot_migrate;
ALTER TABLE conversation OWNER TO memdot_migrate;
ALTER TABLE external_client_grant OWNER TO memdot_migrate;
ALTER TABLE external_identity OWNER TO memdot_migrate;
ALTER TABLE hosted_adult_attestation OWNER TO memdot_migrate;
ALTER TABLE proposal OWNER TO memdot_migrate;
ALTER TABLE source OWNER TO memdot_migrate;
ALTER TABLE space_member OWNER TO memdot_migrate;
ALTER TABLE conversation_turn OWNER TO memdot_migrate;
ALTER TABLE document_revision OWNER TO memdot_migrate;
ALTER TABLE session_revocation OWNER TO memdot_migrate;
ALTER TABLE source_revision OWNER TO memdot_migrate;
ALTER TABLE current_document_revision OWNER TO memdot_migrate;
ALTER TABLE current_source_revision OWNER TO memdot_migrate;
ALTER TABLE parse_run OWNER TO memdot_migrate;
ALTER TABLE source_blob OWNER TO memdot_migrate;
ALTER TABLE document_element OWNER TO memdot_migrate;
ALTER TABLE memdot_context_secret OWNER TO memdot_migrate;
ALTER FUNCTION memdot_clear_tenant_context() OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_clear_tenant_context() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_clear_tenant_context() TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_begin_tenant_context(uuid, uuid, text, bigint, text, text) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_begin_tenant_context(uuid, uuid, text, bigint, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_begin_tenant_context(uuid, uuid, text, bigint, text, text) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_rls_ok(uuid) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_rls_ok(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_rls_ok(uuid) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_external_space_ok(uuid, uuid) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_external_space_ok(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_external_space_ok(uuid, uuid) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_auth_find_identity(text, text) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_auth_find_identity(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_auth_find_identity(text, text) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_auth_load_session(uuid, text) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_auth_load_session(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_auth_load_session(uuid, text) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_auth_bootstrap_exists() OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_auth_bootstrap_exists() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_auth_bootstrap_exists() TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_auth_find_actor_for_user(uuid, uuid) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_auth_find_actor_for_user(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_auth_find_actor_for_user(uuid, uuid) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_oidc_create_challenge(uuid, text, text, text, timestamptz) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_oidc_create_challenge(uuid, text, text, text, timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_oidc_create_challenge(uuid, text, text, text, timestamptz) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_oidc_load_challenge(text) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_oidc_load_challenge(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_oidc_load_challenge(text) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_oidc_consume_challenge(uuid, timestamptz) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_oidc_consume_challenge(uuid, timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_oidc_consume_challenge(uuid, timestamptz) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_oidc_record_replay(uuid, text, text, timestamptz) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_oidc_record_replay(uuid, text, text, timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_oidc_record_replay(uuid, text, text, timestamptz) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_set_current_source_revision(uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_set_current_source_revision(uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_set_current_source_revision(uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb) TO memdot_core, memdot_test_admin, memdot_migrate;
ALTER FUNCTION memdot_set_current_document_revision(uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_set_current_document_revision(uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_set_current_document_revision(uuid, uuid, uuid, uuid, uuid, uuid, text, jsonb) TO memdot_core, memdot_test_admin, memdot_migrate;


-- Identity provisioning seams (SECURITY DEFINER; owned by memdot_migrate with BYPASSRLS)
CREATE OR REPLACE FUNCTION memdot_auth_provision_hosted(
  p_account_id uuid,
  p_user_id uuid,
  p_actor_id uuid,
  p_email text,
  p_issuer text,
  p_subject text,
  p_provider text
) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  INSERT INTO account (id, account_id, status) VALUES (p_account_id, p_account_id, 'pending_attestation');
  INSERT INTO "user" (id, account_id, email) VALUES (p_user_id, p_account_id, p_email);
  INSERT INTO account_member (id, account_id, user_id, role)
    VALUES (gen_random_uuid(), p_account_id, p_user_id, 'owner');
  INSERT INTO external_identity (id, account_id, user_id, issuer, subject, provider)
    VALUES (gen_random_uuid(), p_account_id, p_user_id, p_issuer, p_subject, p_provider);
  INSERT INTO actor (id, account_id, kind, reference_id)
    VALUES (p_actor_id, p_account_id, 'user', p_user_id);
END; $$;

CREATE OR REPLACE FUNCTION memdot_auth_provision_bootstrap(
  p_account_id uuid,
  p_user_id uuid,
  p_actor_id uuid,
  p_bootstrap_id uuid,
  p_email text,
  p_issuer text,
  p_subject text,
  p_provider text
) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM operator_bootstrap WHERE singleton_key = 1 AND revoked_at IS NULL) THEN
    RAISE EXCEPTION 'bootstrap_already_completed';
  END IF;
  INSERT INTO account (id, account_id, status, display_name)
    VALUES (p_account_id, p_account_id, 'active', 'Operator');
  INSERT INTO "user" (id, account_id, email, display_name)
    VALUES (p_user_id, p_account_id, p_email, 'Operator');
  INSERT INTO account_member (id, account_id, user_id, role)
    VALUES (gen_random_uuid(), p_account_id, p_user_id, 'owner');
  INSERT INTO external_identity (id, account_id, user_id, issuer, subject, provider)
    VALUES (gen_random_uuid(), p_account_id, p_user_id, p_issuer, p_subject, p_provider);
  INSERT INTO actor (id, account_id, kind, reference_id)
    VALUES (p_actor_id, p_account_id, 'user', p_user_id);
  INSERT INTO operator_bootstrap (id, account_id, issuer, subject, singleton_key)
    VALUES (p_bootstrap_id, p_account_id, p_issuer, p_subject, 1);
END; $$;

ALTER FUNCTION memdot_auth_provision_hosted(uuid, uuid, uuid, text, text, text, text) OWNER TO memdot_migrate;
ALTER FUNCTION memdot_auth_provision_bootstrap(uuid, uuid, uuid, uuid, text, text, text, text) OWNER TO memdot_migrate;
REVOKE ALL ON FUNCTION memdot_auth_provision_hosted(uuid, uuid, uuid, text, text, text, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION memdot_auth_provision_bootstrap(uuid, uuid, uuid, uuid, text, text, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION memdot_auth_provision_hosted(uuid, uuid, uuid, text, text, text, text)
  TO memdot_core, memdot_test_admin, memdot_migrate;
GRANT EXECUTE ON FUNCTION memdot_auth_provision_bootstrap(uuid, uuid, uuid, uuid, text, text, text, text)
  TO memdot_core, memdot_test_admin, memdot_migrate;
