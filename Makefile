.PHONY: bootstrap format format-check lint typecheck test contracts docs-validate build containers container-smoke check clean workspace-list \
	compose-config compose-up compose-down compose-ps compose-logs selfhost-smoke migrate-domain check-rls phase3-gates phase4-gates phase5-gates phase6-gates phase7-gates phase8-gates

COMPOSE_DIR := infra/compose
COMPOSE_ENV := $(COMPOSE_DIR)/.env
COMPOSE_FILES := -f $(COMPOSE_DIR)/compose.yaml -f $(COMPOSE_DIR)/compose.dev.yaml
COMPOSE := docker compose --env-file $(COMPOSE_ENV) $(COMPOSE_FILES)
MEMDOT_HTTP_PORT ?= 8080
MEMDOT_HTTPS_PORT ?= 8443

bootstrap:
	pnpm install --frozen-lockfile
	uv python install 3.12
	uv sync --all-packages --group dev --frozen --python 3.12

format:
	pnpm exec prettier --write .
	uv run ruff format .
	uv run ruff check --fix .

format-check:
	pnpm exec prettier --check .
	uv run ruff format --check .
	uv run ruff check .

lint:
	pnpm -r --if-present run lint
	pnpm exec dependency-cruiser --config dependency-cruiser.cjs apps packages
	uv run ruff check .
	uv run lint-imports

typecheck:
	pnpm -r --if-present run typecheck
	uv run pyright

test:
	pnpm -r --if-present run test
	uv run pytest

contracts:
	uv run python scripts/generate_openapi.py
	pnpm --filter @memdot/contracts run generate
	uv run python scripts/validate_schemas.py
	pnpm --filter @memdot/contracts run check

docs-validate:
	uv run python scripts/validate_docs.py
	node --import ./scripts/mermaid-preload.mjs scripts/validate_mermaid.mjs

build:
	pnpm -r --if-present run build
	uv run python -c "import memdot_core, memdot_workers, memdot_model_router, memdot_domain, memdot_provider_adapters"

containers:
	docker build -f apps/web/Dockerfile -t memdot-web:local -t memdot-web:phase1 .
	docker build -f apps/mcp/Dockerfile -t memdot-mcp:local -t memdot-mcp:phase1 .
	docker build -f services/core/Dockerfile -t memdot-core:local -t memdot-core:phase1 .
	docker build -f services/workers/Dockerfile -t memdot-workers:local -t memdot-workers:phase1 .
	docker build -f services/model-router/Dockerfile -t memdot-model-router:local -t memdot-model-router:phase1 .
	./scripts/docker_nonroot_check.sh memdot-web:local
	./scripts/docker_nonroot_check.sh memdot-mcp:local
	./scripts/docker_nonroot_check.sh memdot-core:local
	./scripts/docker_nonroot_check.sh memdot-workers:local
	./scripts/docker_nonroot_check.sh memdot-model-router:local

container-smoke:
	./scripts/docker_health_smoke.sh

compose-config:
	./scripts/validate_compose_placeholder.sh

compose-up:
	bash infra/compose/scripts/materialize_local_secrets.sh
	MEMDOT_HTTP_PORT=$(MEMDOT_HTTP_PORT) MEMDOT_HTTPS_PORT=$(MEMDOT_HTTPS_PORT) \
		$(COMPOSE) up -d --build --force-recreate --remove-orphans

compose-down:
	MEMDOT_HTTP_PORT=$(MEMDOT_HTTP_PORT) MEMDOT_HTTPS_PORT=$(MEMDOT_HTTPS_PORT) \
		$(COMPOSE) down

compose-ps:
	MEMDOT_HTTP_PORT=$(MEMDOT_HTTP_PORT) MEMDOT_HTTPS_PORT=$(MEMDOT_HTTPS_PORT) \
		$(COMPOSE) ps

compose-logs:
	MEMDOT_HTTP_PORT=$(MEMDOT_HTTP_PORT) MEMDOT_HTTPS_PORT=$(MEMDOT_HTTPS_PORT) \
		$(COMPOSE) logs --tail=200

selfhost-smoke:
	MEMDOT_HTTP_PORT=$(MEMDOT_HTTP_PORT) MEMDOT_HTTPS_PORT=$(MEMDOT_HTTPS_PORT) \
		bash infra/compose/scripts/selfhost_smoke.sh

migrate-domain:
	bash scripts/migrate_domain.sh

check-rls:
	bash scripts/check_rls_registry.sh

phase3-gates: migrate-domain check-rls
	uv run pytest services/core/tests tests/security -q

phase4-gates: migrate-domain check-rls
	uv run pytest services/core/tests services/workers/tests tests/security tests/contracts -q
	uv run python scripts/generate_openapi.py
	pnpm --filter @memdot/contracts run generate
	uv run python scripts/generate_openapi.py
	pnpm --filter @memdot/contracts run generate
	uv run python scripts/validate_schemas.py
	pnpm --filter @memdot/contracts run check

phase5-gates: migrate-domain check-rls
	uv run pytest \
		packages/domain-python/tests/test_memdot_document.py \
		packages/domain-python/tests/test_retrieval_fusion.py \
		packages/domain-python/tests/test_context_compiler.py \
		services/core/tests/test_wave5_documents.py \
		services/model-router/tests/test_model_router_policy.py \
		-q
	uv run python scripts/generate_openapi.py
	pnpm --filter @memdot/contracts run generate
	uv run python scripts/validate_schemas.py
	pnpm --filter @memdot/contracts run check

phase6-gates: migrate-domain check-rls
	uv run pytest \
		packages/domain-python/tests/test_learning_domain.py \
		packages/domain-python/tests/test_memdot_document.py \
		packages/domain-python/tests/test_retrieval_fusion.py \
		packages/domain-python/tests/test_context_compiler.py \
		-q
	uv run python scripts/generate_openapi.py
	pnpm --filter @memdot/contracts run generate
	uv run python scripts/validate_schemas.py
	pnpm --filter @memdot/contracts run check

phase7-gates: migrate-domain check-rls
	uv run pytest \
		packages/domain-python/tests/test_mcp_domain.py \
		packages/domain-python/tests/test_telemetry_allowlist.py \
		services/core/tests/test_external_lifecycle.py \
		services/core/tests/test_overload_policy.py \
		tests/benchmark/run_benchmarks.py \
		-q
	uv run python tests/benchmark/run_benchmarks.py

phase8-gates: phase7-gates typecheck docs-validate
	uv run pytest \
		packages/domain-python/tests/test_mcp_domain.py \
		packages/domain-python/tests/test_telemetry_allowlist.py \
		services/core/tests/test_external_lifecycle.py \
		services/core/tests/test_overload_policy.py \
		-q
	uv run python scripts/generate_openapi.py
	pnpm --filter @memdot/contracts run generate
	uv run python scripts/validate_schemas.py
	pnpm --filter @memdot/contracts run check

check: format-check lint typecheck test contracts docs-validate build
	./scripts/check_focused_tests.sh
	./scripts/secret_scan.sh
	./scripts/validate_compose_placeholder.sh
	./scripts/check_whitespace.sh
	@echo "Local CI-equivalent suite passed."

clean:
	pnpm -r --if-present run clean || true
	rm -rf node_modules apps/*/node_modules packages/*/node_modules .next coverage .ruff_cache .pytest_cache .mypy_cache .import_linter_cache
	find . -type d -name __pycache__ -not -path './.git/*' -exec rm -rf {} + 2>/dev/null || true

workspace-list:
	@echo "=== pnpm workspaces ==="
	pnpm -r list --depth -1
	@echo "=== uv workspace members ==="
	uv tree
