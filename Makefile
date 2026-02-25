.PHONY: setup backend frontend migrate seed test lint

# --- 초기 셋업 ---
setup:
	cp -n .env.example .env || true
	cd backend && uv sync --all-extras
	cd frontend && npm install

# --- 백엔드 ---
backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# --- 프론트엔드 ---
frontend:
	cd frontend && npm run dev

# --- DB 마이그레이션 ---
migrate:
	cd backend && uv run alembic upgrade head

migrate-new:
	@read -p "Migration message: " msg; \
	cd backend && uv run alembic revision --autogenerate -m "$$msg"

# --- 온톨로지 시드 ---
seed:
	cd backend && uv run python -m seeds.ontology_seed

# --- 테스트 ---
test:
	cd backend && uv run pytest -v
	cd frontend && npm run test

test-backend:
	cd backend && uv run pytest -v

test-frontend:
	cd frontend && npm run test

# --- 린트 ---
lint:
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint

lint-fix:
	cd backend && uv run ruff check --fix . && uv run ruff format .
	cd frontend && npm run lint --fix

# --- 로컬 DB (Docker) ---
db-up:
	docker compose up -d

db-down:
	docker compose down

# --- 비용 확인 ---
costs:
	@echo "이번 달 API 비용 조회..."
	curl -s -H "X-API-Key: $$(grep API_KEY .env | cut -d= -f2)" \
		http://localhost:8000/api/v1/admin/costs?period=monthly | python -m json.tool
