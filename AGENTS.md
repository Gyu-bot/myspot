# AGENTS.md — 코딩 에이전트 가이드

> 이 프로젝트를 작업하는 모든 코딩 에이전트(Claude Code, Codex, Cursor, Copilot 등)는 이 문서를 먼저 읽고 따라야 한다.

---

## 프로젝트 개요

**개인 장소 DB + LLM 시맨틱 서치** — 맛집/카페/여행지를 구조화해 저장하고, LLM이 자연어로 의미 기반 검색/추천을 수행하는 개인용 장소 데이터베이스.

- 상세 요구사항: `PRD.md`
- 프로젝트 구조: `PROJECT_STRUCTURE.md`

---

## 아키텍처

```
React SPA ──▶ FastAPI (REST API) ──▶ Supabase PostgreSQL (pgvector + PostGIS)
                  │
AI Agent ────────┘
(API Key 인증)
                  │
                  ├──▶ OpenAI (임베딩: text-embedding-3-small)
                  ├──▶ LLM Provider (Claude / GPT-4o-mini / 등, 런타임 선택)
                  ├──▶ 카카오 로컬 API (Geocoding, 장소 검색)
                  ├──▶ 네이버 검색 API (지역 검색)
                  └──▶ Google Places API (place_id 조회)
```

---

## 기술 스택 및 버전

| 레이어 | 기술 | 버전/비고 |
|--------|------|-----------|
| **DB** | PostgreSQL + pgvector + PostGIS | Supabase 호스팅. 순수 PG 기능만 사용 (Supabase 전용 기능 의존 금지) |
| **백엔드** | Python 3.12+ / FastAPI | 의존성 관리: `uv` 권장 (대안: poetry) |
| **ORM** | SQLAlchemy 2.0+ (async) | asyncpg 드라이버 |
| **마이그레이션** | Alembic | 자동 생성 후 반드시 수동 검토 |
| **프론트엔드** | React 18+ / TypeScript / Vite | Tailwind CSS |
| **임베딩** | OpenAI text-embedding-3-small | 1536차원 |
| **벡터 검색** | pgvector (cosine similarity) | `vector(1536)` 타입 |
| **공간 쿼리** | PostGIS | `geography(Point, 4326)` |
| **인증** | API Key (헤더: `X-API-Key`) | MVP에서는 단일 키 |

---

## 핵심 규칙 (반드시 준수)

### 1. DB 관련

- **Supabase 전용 기능(Auth, Storage, Realtime, Edge Functions) 사용 금지** — 나중에 로컬 PostgreSQL로 마이그레이션할 수 있어야 한다. `pg_dump`로 완전한 백업/복원이 가능해야 함.
- **SQLAlchemy + asyncpg로 DB 접근** — Supabase JS 클라이언트, PostgREST 사용 금지.
- **모든 테이블에 `created_at`, `updated_at` 컬럼** — `updated_at`은 트리거 또는 앱 레벨 자동 갱신.
- **UUID를 PK로 사용** — `uuid_generate_v4()` 또는 Python `uuid.uuid4()`.
- **마이그레이션은 Alembic으로 관리** — 스키마 변경 시 반드시 마이그레이션 파일 생성. 수동 SQL 직접 실행 금지.
- **PostGIS 좌표는 `geography(Point, 4326)`** — SRID 4326 (WGS84). `ST_DWithin()` 으로 거리 필터.

### 2. 외부 API / 정책 관련

- **외부 데이터(네이버/카카오/구글) 장기 저장 금지** — ProviderLink(ID/URL)만 저장. 상세 데이터는 런타임 조회.
- **Google place_id는 저장 가능** (Google 정책 예외).
- **크롤링/스크래핑 코드 작성 금지** — 공식 API만 사용.
- **모든 외부 API 호출에 에러 핸들링** — 실패 시 graceful degradation (사용자 메모/입력은 항상 보존).
- **API 키는 환경변수** — 코드에 하드코딩 절대 금지. `.env`에 저장, `.env.example`만 커밋.

### 3. LLM 관련

- **LLM Provider는 추상화** — `app/llm/base.py`의 인터페이스를 구현. 새 Provider 추가 시 기존 코드 수정 없이 가능해야 함.
- **임베딩은 OpenAI text-embedding-3-small 고정** (MVP).
- **임베딩 생성 타이밍**: Place 생성/수정 시 1회. 임베딩 대상 텍스트 = `canonical_name + address + tags(joined) + notes(joined)`.
- **검색 시 질의 임베딩**: 사용자 질의를 동일 모델로 임베딩 → cosine similarity.
- **LLM 요약은 사용자 요청 시에만 실행** (비용 절약). 자동 실행 OFF가 기본.
- **환각 방지**: LLM 응답에는 반드시 근거(Source 링크) 포함. 근거 없으면 "추정" 표시.

### 4. 비용 관련

- **월 ₩10,000 이하 유지가 목표**.
- **cost_tracker.py로 외부 API 호출 횟수/토큰 사용량 기록** — 일별/월별 집계 가능하게.
- **불필요한 LLM 호출 금지** — 룰 기반으로 해결 가능하면 LLM 호출하지 않음.
- **임베딩 재생성 최소화** — 텍스트 변경이 없으면 재생성 스킵.
- **외부 API 결과 단기 캐시** — TTL 기반 인메모리 캐시 (정책상 장기 저장은 안 되지만 동일 세션 내 중복 호출은 방지).

### 5. 코드 스타일

- **Python**: Ruff (lint + format). Type hints 필수. docstring은 Google style.
- **TypeScript**: ESLint + Prettier. 모든 API 응답에 타입 정의.
- **네이밍**: Python은 snake_case, TypeScript는 camelCase. DB 컬럼은 snake_case.
- **에러 응답**: FastAPI의 HTTPException 사용. `{ "detail": "에러 메시지" }` 형태.
- **테스트**: pytest (backend), Vitest (frontend). 새 서비스/엔드포인트마다 테스트 필수.
- **커밋 메시지**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:` 등).
- **한국어 주석 허용** — 비즈니스 로직 설명은 한국어 OK. 코드/변수명은 영어.

### 6. API 설계

- **RESTful**: `GET /api/v1/places`, `POST /api/v1/places`, `GET /api/v1/places/{id}` 등.
- **버전 프리픽스**: `/api/v1/`
- **Pagination**: cursor 기반 (`?cursor=xxx&limit=20`). offset 기반 사용 금지.
- **검색 엔드포인트**: `POST /api/v1/search` (body에 질의 + 필터).
- **에이전트 전용 Tool 엔드포인트**: `POST /api/v1/tools/{tool_name}` — PRD의 Tool 스키마 참조.
- **인증**: 모든 엔드포인트에 `X-API-Key` 헤더 필수. `app/auth/api_key.py`에서 검증.

---

## 작업 순서 (Phase별)

에이전트는 아래 순서로 작업한다. 각 Phase는 이전 Phase가 완료된 후 시작.

### Phase 0: 프로젝트 셋업
**목표**: 프로젝트 뼈대, 의존성, DB 연결 확인

1. `backend/pyproject.toml` 생성 — 의존성: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pgvector, geoalchemy2, pydantic-settings, httpx, openai
2. `frontend/package.json` 생성 — 의존성: react, react-dom, react-router-dom, @tanstack/react-query, tailwindcss, vite, typescript
3. `.env.example` 생성 — 필요한 환경변수 목록
4. `docker-compose.yml` — 로컬 개발용 PostgreSQL + pgvector + PostGIS (Supabase 다운 시 대비)
5. `backend/app/config.py` — pydantic-settings로 환경변수 로드
6. `backend/app/main.py` — FastAPI 앱 생성, CORS 설정, health check 엔드포인트
7. DB 연결 테스트 (`/health` → DB ping)

### Phase 1: DB 스키마 + 코어 CRUD
**목표**: 핵심 엔티티 CRUD가 동작하는 상태

1. SQLAlchemy 모델 정의 (`app/models/` 전체)
2. Alembic 초기 마이그레이션 생성 + 실행
3. Pydantic 스키마 정의 (`app/schemas/` 전체)
4. Place CRUD API (`POST/GET/PATCH/DELETE /api/v1/places`)
5. ProviderLink 연결 로직
6. Source CRUD API
7. Note CRUD API
8. Tag CRUD API (자유 태그 + 시스템 태그)
9. Visit CRUD API
10. 중복 감지 서비스 (`dedup_service.py`) — 좌표 50m + 전화번호 + 문자열 유사도
11. Geocoding 연동 (`providers/kakao.py`) — 주소 → 좌표, 좌표 → 주소

### Phase 2: 임베딩 + 검색
**목표**: 자연어 검색이 동작하는 상태

1. OpenAI 임베딩 클라이언트 (`providers/openai_embed.py`)
2. 임베딩 생성 파이프라인 (`embedding_service.py`) — Place 저장/수정 시 자동 생성
3. pgvector 인덱스 설정 (IVFFlat 또는 HNSW)
4. 하이브리드 검색 (`search_service.py`):
   - 벡터 검색 (pgvector cosine similarity)
   - 키워드 검색 (pg_trgm)
   - PostGIS 거리 필터
   - 태그/속성 필터
   - 스코어 통합 + 랭킹
5. LLM 질의 파싱 (`llm_service.py`) — 자연어 → SearchIntent + Filters JSON
6. 검색 API (`POST /api/v1/search`)
7. 결과 설명 생성 — 매칭 근거 하이라이트

### Phase 3: 온톨로지 + LLM 도구
**목표**: 온톨로지 확장 검색 + 에이전트 연동 가능

1. OntologyNode/Relation 모델 + CRUD
2. 온톨로지 시드 데이터 생성 (`seeds/ontology_seed.py`) — LLM으로 한국 맛집/카페 도메인 트리 생성
3. 온톨로지 확장 검색 — "파스타" → "이탈리안" → "양식" 확장
4. LLM Provider 추상화 (`llm/base.py`, `llm/openai_llm.py`, `llm/anthropic_llm.py`)
5. LLM 라우터 (`llm/router.py`) — 설정/요청별 Provider 선택
6. Tool 엔드포인트 (`api/v1/tools.py`):
   - `search_places` — 검색
   - `get_place_detail` — 상세 조회
   - `create_place` — 장소 생성
   - `attach_source` — 근거 자료 첨부
   - `build_comparison_table` — 후보 비교표
   - `draft_itinerary` — 간단 동선 초안
7. API Key 인증 미들웨어 (`auth/api_key.py`)

### Phase 4: 웹 UI
**목표**: 브라우저에서 장소 등록/검색/조회 가능

1. React 프로젝트 구조 + Tailwind 설정
2. API 클라이언트 (`api/client.ts`) — fetch wrapper + API Key 헤더
3. 장소 등록 페이지 (`AddPlacePage.tsx`) — 이름/주소/메모/태그 입력 폼
4. 검색 페이지 (`SearchPage.tsx`) — 검색바 + 필터 칩 + 결과 카드 리스트
5. 장소 상세 페이지 (`PlaceDetailPage.tsx`) — Source/Note/Visit 타임라인
6. 중복 병합 페이지 (`DedupPage.tsx`) — 병합 제안 + 확인/거부
7. 홈 페이지 (`HomePage.tsx`) — 최근 저장 + 빠른 검색

---

## 파일별 책임 (서비스 레이어)

| 파일 | 책임 | 의존 |
|------|------|------|
| `place_service.py` | Place CRUD, ProviderLink 관리 | models, dedup_service |
| `dedup_service.py` | 중복 감지 (좌표+전화+문자열), 병합 제안/실행 | models, geocoding |
| `embedding_service.py` | 임베딩 생성/재생성/삭제 | openai_embed provider |
| `search_service.py` | 하이브리드 검색, 필터, 랭킹, 결과 설명 | embedding_service, ontology_service |
| `enrichment_service.py` | 외부 API로 장소 정보 런타임 조회 (저장 안 함) | naver, kakao, google_places providers |
| `ontology_service.py` | 온톨로지 CRUD, 트리 탐색, 확장 검색 | models |
| `llm_service.py` | 질의 파싱, 요약 생성, 비교표, 동선 | llm router |

---

## 환경변수

```env
# DB
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# 인증
API_KEY=your-api-key-here

# OpenAI
OPENAI_API_KEY=sk-...

# LLM (선택적 — 사용할 Provider만)
ANTHROPIC_API_KEY=sk-ant-...
# 기본 LLM Provider: openai | anthropic
DEFAULT_LLM_PROVIDER=openai

# 네이버
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
NAVER_CLOUD_CLIENT_ID=...
NAVER_CLOUD_CLIENT_SECRET=...

# 카카오
KAKAO_REST_API_KEY=...

# 구글
GOOGLE_PLACES_API_KEY=...

# 비용 제어
MONTHLY_COST_LIMIT_KRW=10000
```

---

## 테스트 가이드

- **단위 테스트**: 서비스 레이어 중심. 외부 API는 mock.
- **통합 테스트**: DB 포함 (테스트용 PostgreSQL).
- **테스트 DB**: `docker-compose.yml`의 로컬 PostgreSQL 사용 또는 Supabase 별도 프로젝트.
- **실행**: `cd backend && pytest`
- **커버리지 목표**: 서비스 레이어 80% 이상.

---

## 자주 하는 실수 (에이전트 주의사항)

1. ❌ Supabase JS 클라이언트 (`@supabase/supabase-js`) 사용 — 반드시 SQLAlchemy
2. ❌ 외부 API 결과를 DB에 장기 저장 — ProviderLink(ID/URL)만 저장
3. ❌ 임베딩을 매 검색마다 재생성 — 저장 시 1회만, 검색 시는 질의만 임베딩
4. ❌ LLM 자동 요약을 기본 ON — 반드시 기본 OFF, 사용자 요청 시에만
5. ❌ `.env` 파일 커밋 — `.gitignore`에 포함 확인
6. ❌ 마이그레이션 없이 DB 스키마 수동 변경
7. ❌ offset 기반 pagination — cursor 기반으로
8. ❌ 크롤링/스크래핑 코드 — 공식 API만
