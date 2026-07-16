-- Learning curriculum, sealed assessments, learner events, and FSRS projections.

CREATE TABLE IF NOT EXISTS course (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  title VARCHAR(512) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_course PRIMARY KEY (id),
  CONSTRAINT fk_course_space FOREIGN KEY(account_id, space_id) REFERENCES space (account_id, id),
  CONSTRAINT uq_course_1 UNIQUE (account_id, id),
  CONSTRAINT uq_course_space_id UNIQUE (account_id, space_id, id)
);

CREATE TABLE IF NOT EXISTS curriculum_node (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  course_id UUID NOT NULL,
  kind VARCHAR(32) NOT NULL,
  title VARCHAR(512) NOT NULL,
  confirmation VARCHAR(32) NOT NULL DEFAULT 'suggested',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_curriculum_node PRIMARY KEY (id),
  CONSTRAINT fk_curriculum_node_course FOREIGN KEY(account_id, course_id)
    REFERENCES course (account_id, id),
  CONSTRAINT fk_curriculum_node_course_space FOREIGN KEY(account_id, space_id, course_id)
    REFERENCES course (account_id, space_id, id),
  CONSTRAINT uq_curriculum_node_1 UNIQUE (account_id, id),
  CONSTRAINT ck_curriculum_node_kind CHECK (
    kind IN ('unit', 'objective', 'concept', 'source_unit')
  ),
  CONSTRAINT ck_curriculum_node_confirmation CHECK (
    confirmation IN ('suggested', 'confirmed')
  )
);

CREATE TABLE IF NOT EXISTS curriculum_edge (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  course_id UUID NOT NULL,
  from_node_id UUID NOT NULL,
  to_node_id UUID NOT NULL,
  edge_kind VARCHAR(32) NOT NULL DEFAULT 'prerequisite',
  confirmation VARCHAR(32) NOT NULL DEFAULT 'suggested',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_curriculum_edge PRIMARY KEY (id),
  CONSTRAINT fk_curriculum_edge_course FOREIGN KEY(account_id, course_id)
    REFERENCES course (account_id, id),
  CONSTRAINT fk_curriculum_edge_from FOREIGN KEY(account_id, from_node_id)
    REFERENCES curriculum_node (account_id, id),
  CONSTRAINT fk_curriculum_edge_to FOREIGN KEY(account_id, to_node_id)
    REFERENCES curriculum_node (account_id, id),
  CONSTRAINT uq_curriculum_edge_1 UNIQUE (account_id, id),
  CONSTRAINT uq_curriculum_edge_pair UNIQUE (account_id, course_id, from_node_id, to_node_id, edge_kind),
  CONSTRAINT ck_curriculum_edge_kind CHECK (edge_kind IN ('prerequisite', 'covers')),
  CONSTRAINT ck_curriculum_edge_confirmation CHECK (
    confirmation IN ('suggested', 'confirmed')
  ),
  CONSTRAINT ck_curriculum_edge_no_self CHECK (from_node_id <> to_node_id)
);

CREATE TABLE IF NOT EXISTS assessment_item (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  course_id UUID NOT NULL,
  concept_node_id UUID,
  title VARCHAR(512) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_assessment_item PRIMARY KEY (id),
  CONSTRAINT fk_assessment_item_course FOREIGN KEY(account_id, course_id)
    REFERENCES course (account_id, id),
  CONSTRAINT uq_assessment_item_1 UNIQUE (account_id, id),
  CONSTRAINT uq_assessment_item_space_id UNIQUE (account_id, space_id, id)
);

CREATE TABLE IF NOT EXISTS assessment_revision (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  assessment_item_id UUID NOT NULL,
  item_type VARCHAR(32) NOT NULL,
  prompt TEXT NOT NULL,
  sealed_answer JSONB NOT NULL,
  sealed_rubric JSONB NOT NULL DEFAULT '{}'::jsonb,
  source_locators JSONB NOT NULL DEFAULT '[]'::jsonb,
  difficulty REAL,
  guessing_chance REAL,
  state VARCHAR(32) NOT NULL DEFAULT 'draft',
  content_sha256 VARCHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_assessment_revision PRIMARY KEY (id),
  CONSTRAINT fk_assessment_revision_item FOREIGN KEY(account_id, assessment_item_id)
    REFERENCES assessment_item (account_id, id),
  CONSTRAINT uq_assessment_revision_1 UNIQUE (account_id, id),
  CONSTRAINT ck_assessment_revision_type CHECK (
    item_type IN ('mcq', 'short_answer', 'written')
  ),
  CONSTRAINT ck_assessment_revision_state CHECK (
    state IN ('draft', 'provisional', 'human_verified', 'retired')
  ),
  CONSTRAINT ck_assessment_revision_sha_len CHECK (char_length(content_sha256) = 64)
);

CREATE TABLE IF NOT EXISTS current_assessment_revision (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  assessment_item_id UUID NOT NULL,
  revision_id UUID NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_current_assessment_revision PRIMARY KEY (id),
  CONSTRAINT fk_current_assessment_item FOREIGN KEY(account_id, assessment_item_id)
    REFERENCES assessment_item (account_id, id),
  CONSTRAINT fk_current_assessment_revision FOREIGN KEY(account_id, revision_id)
    REFERENCES assessment_revision (account_id, id),
  CONSTRAINT uq_current_assessment_revision_1 UNIQUE (account_id, assessment_item_id)
);

CREATE TABLE IF NOT EXISTS learner_event (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  course_id UUID NOT NULL,
  user_id UUID NOT NULL,
  concept_node_id UUID,
  assessment_item_id UUID,
  assessment_revision_id UUID,
  attempt_id UUID,
  client_event_id VARCHAR(128),
  event_type VARCHAR(64) NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload_schema_version INTEGER NOT NULL DEFAULT 1,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  eligibility VARCHAR(32) NOT NULL,
  exclusion_reason VARCHAR(128),
  CONSTRAINT pk_learner_event PRIMARY KEY (id),
  CONSTRAINT fk_learner_event_course FOREIGN KEY(account_id, course_id)
    REFERENCES course (account_id, id),
  CONSTRAINT uq_learner_event_1 UNIQUE (account_id, id),
  CONSTRAINT uq_learner_event_client UNIQUE (account_id, client_event_id),
  CONSTRAINT ck_learner_event_eligibility CHECK (
    eligibility IN ('eligible', 'ineligible')
  )
);

CREATE TABLE IF NOT EXISTS review_item (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  course_id UUID NOT NULL,
  user_id UUID NOT NULL,
  assessment_item_id UUID NOT NULL,
  assessment_revision_id UUID NOT NULL,
  fsrs_state JSONB NOT NULL DEFAULT '{}'::jsonb,
  due_at TIMESTAMPTZ,
  priority INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_review_item PRIMARY KEY (id),
  CONSTRAINT fk_review_item_course FOREIGN KEY(account_id, course_id)
    REFERENCES course (account_id, id),
  CONSTRAINT uq_review_item_1 UNIQUE (account_id, id),
  CONSTRAINT uq_review_item_user_item UNIQUE (account_id, user_id, assessment_item_id)
);

CREATE TABLE IF NOT EXISTS learner_projection (
  id UUID NOT NULL,
  account_id UUID NOT NULL,
  space_id UUID NOT NULL,
  course_id UUID NOT NULL,
  user_id UUID NOT NULL,
  concept_node_id UUID NOT NULL,
  evidence_state VARCHAR(32) NOT NULL DEFAULT 'unassessed',
  recall_state VARCHAR(32) NOT NULL DEFAULT 'current',
  confidence VARCHAR(32),
  coverage REAL NOT NULL DEFAULT 0,
  projection_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT pk_learner_projection PRIMARY KEY (id),
  CONSTRAINT fk_learner_projection_course FOREIGN KEY(account_id, course_id)
    REFERENCES course (account_id, id),
  CONSTRAINT uq_learner_projection_1 UNIQUE (account_id, id),
  CONSTRAINT uq_learner_projection_user_concept UNIQUE (account_id, user_id, concept_node_id),
  CONSTRAINT ck_learner_projection_evidence CHECK (
    evidence_state IN ('unassessed', 'practicing', 'demonstrated', 'delayed_demonstrated')
  ),
  CONSTRAINT ck_learner_projection_recall CHECK (
    recall_state IN ('current', 'due', 'lapsed')
  )
);

DO $$
DECLARE
  tbl TEXT;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'course',
    'curriculum_node',
    'curriculum_edge',
    'assessment_item',
    'assessment_revision',
    'current_assessment_revision',
    'learner_event',
    'review_item',
    'learner_projection'
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

REVOKE INSERT, UPDATE, DELETE ON current_assessment_revision FROM memdot_core;
DROP TRIGGER IF EXISTS trg_current_assessment_outbox ON current_assessment_revision;
CREATE TRIGGER trg_current_assessment_outbox BEFORE INSERT OR UPDATE ON current_assessment_revision
  FOR EACH ROW EXECUTE FUNCTION memdot_require_outbox_for_pointer();
