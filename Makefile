.PHONY: bootstrap format format-check lint typecheck test contracts docs-validate build containers container-smoke check clean workspace-list

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
	docker build -f apps/web/Dockerfile -t memdot-web:phase1 .
	docker build -f apps/mcp/Dockerfile -t memdot-mcp:phase1 .
	docker build -f services/core/Dockerfile -t memdot-core:phase1 .
	docker build -f services/workers/Dockerfile -t memdot-workers:phase1 .
	docker build -f services/model-router/Dockerfile -t memdot-model-router:phase1 .
	./scripts/docker_nonroot_check.sh memdot-web:phase1
	./scripts/docker_nonroot_check.sh memdot-mcp:phase1
	./scripts/docker_nonroot_check.sh memdot-core:phase1
	./scripts/docker_nonroot_check.sh memdot-workers:phase1
	./scripts/docker_nonroot_check.sh memdot-model-router:phase1

container-smoke:
	./scripts/docker_health_smoke.sh

check: format-check lint typecheck test contracts docs-validate build
	./scripts/check_focused_tests.sh
	./scripts/secret_scan.sh
	./scripts/validate_compose_placeholder.sh
	./scripts/check_whitespace.sh
	@echo "Phase 1 local CI-equivalent suite passed."

clean:
	pnpm -r --if-present run clean || true
	rm -rf node_modules apps/*/node_modules packages/*/node_modules .next coverage .ruff_cache .pytest_cache .mypy_cache .import_linter_cache
	find . -type d -name __pycache__ -not -path './.git/*' -exec rm -rf {} + 2>/dev/null || true

workspace-list:
	@echo "=== pnpm workspaces ==="
	pnpm -r list --depth -1
	@echo "=== uv workspace members ==="
	uv tree
