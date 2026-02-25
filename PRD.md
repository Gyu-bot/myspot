# PRD: 개인 장소 DB + LLM 시맨틱 서치

> 이 문서는 코딩 에이전트가 구현 시 참조하는 **실행 가능한 제품 요구사항**이다.
> 행동 규칙과 컨벤션은 `AGENTS.md`, 디렉토리 구조는 `PROJECT_STRUCTURE.md` 참조.

---

## 제품 한 줄 정의

개인 장소를 "근거 자료 + 메모 + 관계(온톨로지)"로 구조화해 저장하고, LLM이 자연어로 의미 기반 검색/추천/비교를 수행하는 **개인용 장소 DB**.

---

## 확정된 기술 결정

| 항목 | 결정 | 비고 |
|------|------|------|
| DB/배포 | Supabase (PostgreSQL + pgvector + PostGIS) | Supabase 전용 기능 의존 금지. `pg_dump`로 로컬 전환 가능 유지 |
| 백엔드 | FastAPI (Python 3.12+) | SQLAlchemy 2.0 async + asyncpg |
| 프론트엔드 | React SPA (TypeScript + Vite + Tailwind) | |
| 에이전트 연동 | FastAPI REST API (나중에 MCP/Skill 확장) | |
| 임베딩 | OpenAI text-embedding-3-small (1536d) | 고정 |
| LLM | Provider 교체 가능 (Gemini 기본, OpenAI/Anthropic 등) | 추상화 레이어 필수 |
| 지도 | MVP에서 제외 | V1에서 네이버 지도 추가 예정 |
| 인증 | API Key (`X-API-Key` 헤더) | 단일 키 |
| 월 비용 | ₩10,000 이하 | cost_tracker 필수 |

---

## 핵심 사용자 가치

1. **다시 찾기**: 흩어진 스크랩/메모/지도 저장을 한 곳에서 관리하고 빠르게 재검색
2. **의미 기반 검색**: "주차 편한 + 조용 + 비 오는 날" 같은 맥락 질의를 시맨틱 서치로 해결
3. **LLM 에이전트 연동**: 후보 추출 / 비교표 / 간단 동선 / 리뷰 요약(근거 포함)을 자동화

---

## Data Model (SQL 스키마)

### 확장 활성화 (마이그레이션 최초 1회)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";        -- pgvector
CREATE EXTENSION IF NOT EXISTS "postgis";       -- PostGIS
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- 트라이그램 (키워드 유사도 검색)
```

### 1) Place (Canonical Place)

```sql
CREATE TABLE places (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_name  TEXT NOT NULL,
    normalized_name TEXT NOT NULL,              -- 검색용 정규화 (소문자, 공백 제거 등)
    address_road    TEXT,
    address_jibun   TEXT,
    region_depth1   TEXT,                       -- 시/도
    region_depth2   TEXT,                       -- 시/군/구
    region_depth3   TEXT,                       -- 읍/면/동
    location        geography(Point, 4326),     -- PostGIS: lng, lat 순서
    phone           TEXT,
    category_primary   TEXT,                    -- 예: "음식점", "카페"
    category_secondary TEXT,                    -- 예: "이탈리안", "브런치"
    -- 사용자 직접 입력 필드
    parking         BOOLEAN,
    reservation     TEXT CHECK (reservation IN ('available', 'required', 'unavailable', 'unknown')),
    price_range     TEXT CHECK (price_range IN ('cheap', 'moderate', 'expensive', 'very_expensive', 'unknown')),
    mood            TEXT[],                     -- ["quiet", "romantic", "casual" ...]
    companions      TEXT[],                     -- ["date", "family", "solo", "friends" ...]
    situations      TEXT[],                     -- ["rainy", "night", "weekend", "anniversary" ...]
    is_favorite     BOOLEAN DEFAULT FALSE,
    user_rating     SMALLINT CHECK (user_rating BETWEEN 1 AND 5),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 검색 인덱스
CREATE INDEX idx_places_normalized_name ON places USING gin (normalized_name gin_trgm_ops);
CREATE INDEX idx_places_location ON places USING gist (location);
CREATE INDEX idx_places_category ON places (category_primary, category_secondary);
```

### 2) ProviderLink

```sql
CREATE TABLE provider_links (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    place_id          UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    provider          TEXT NOT NULL CHECK (provider IN ('NAVER', 'KAKAO', 'GOOGLE', 'ETC')),
    provider_place_id TEXT,                     -- Google place_id (저장 가능), 카카오 id 등
    provider_url      TEXT,                     -- 네이버 플레이스 URL 등
    last_verified_at  TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (place_id, provider)
);
```

### 3) Source (스크랩/근거 자료)

```sql
CREATE TABLE sources (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    place_id    UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    type        TEXT NOT NULL CHECK (type IN ('URL', 'TEXT', 'IMAGE', 'REVIEW_SNIPPET')),
    url         TEXT,
    title       TEXT,
    snippet     TEXT,                           -- 짧은 요약 또는 사용자 코멘트
    raw_text    TEXT,                           -- 카톡 추천 문구, 메모 원문 등
    captured_at TIMESTAMPTZ DEFAULT now(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 4) Note

```sql
CREATE TABLE notes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    place_id    UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 5) Visit

```sql
CREATE TABLE visits (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    place_id    UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    visited_at  DATE NOT NULL,
    rating      SMALLINT CHECK (rating BETWEEN 1 AND 5),
    with_whom   TEXT,                           -- "연인", "가족", "친구A" 등
    situation   TEXT,                           -- "기념일", "비 오는 날" 등
    memo        TEXT,
    revisit     BOOLEAN,                        -- 재방문 의사
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6) Media

```sql
CREATE TABLE media (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    place_id    UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    type        TEXT NOT NULL DEFAULT 'image',
    storage_url TEXT NOT NULL,                  -- 로컬 경로 또는 S3 URL
    caption     TEXT,
    captured_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 7) Tag

```sql
CREATE TABLE tags (
    id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name    TEXT NOT NULL UNIQUE,
    type    TEXT NOT NULL DEFAULT 'freeform' CHECK (type IN ('freeform', 'system'))
);

CREATE TABLE place_tags (
    place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    tag_id   UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (place_id, tag_id)
);
```

### 8) OntologyNode

```sql
CREATE TABLE ontology_nodes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    namespace   TEXT NOT NULL CHECK (namespace IN ('cuisine', 'mood', 'situation', 'companion', 'feature')),
    parent_id   UUID REFERENCES ontology_nodes(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, namespace)
);

CREATE INDEX idx_ontology_parent ON ontology_nodes (parent_id);
CREATE INDEX idx_ontology_namespace ON ontology_nodes (namespace);
```

### 9) Relation

```sql
CREATE TABLE relations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_entity_type    TEXT NOT NULL,          -- 'place', 'ontology_node'
    from_entity_id      UUID NOT NULL,
    to_entity_type      TEXT NOT NULL,
    to_entity_id        UUID NOT NULL,
    relation_type       TEXT NOT NULL,          -- 'serves', 'good_for', 'fits', 'near', 'alias_of'
    confidence          REAL DEFAULT 1.0 CHECK (confidence BETWEEN 0 AND 1),
    evidence_source_id  UUID REFERENCES sources(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_relations_from ON relations (from_entity_type, from_entity_id);
CREATE INDEX idx_relations_to ON relations (to_entity_type, to_entity_id);
```

### 10) Embedding

```sql
CREATE TABLE embeddings (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('place', 'note', 'source')),
    entity_id   UUID NOT NULL,
    vector      vector(1536) NOT NULL,          -- OpenAI text-embedding-3-small
    model       TEXT NOT NULL DEFAULT 'text-embedding-3-small',
    text_hash   TEXT,                           -- 원본 텍스트 해시 (변경 감지용)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_type, entity_id)
);

-- HNSW 인덱스 (검색 성능)
CREATE INDEX idx_embeddings_vector ON embeddings USING hnsw (vector vector_cosine_ops);
```

### 11) 감사 로그

```sql
CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action      TEXT NOT NULL,                  -- 'merge', 'delete', 'export', 'bulk_update'
    entity_type TEXT,
    entity_id   UUID,
    detail      JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 12) 비용 추적

```sql
CREATE TABLE cost_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider    TEXT NOT NULL,                  -- 'openai_embedding', 'gemini_llm', 'openai_llm', 'anthropic_llm', 'naver', 'kakao', 'google'
    action      TEXT NOT NULL,                  -- 'embed', 'chat', 'search', 'geocode'
    tokens_in   INTEGER,
    tokens_out  INTEGER,
    cost_krw    REAL,                           -- 추정 비용 (원)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_cost_logs_date ON cost_logs (created_at);
CREATE INDEX idx_cost_logs_provider ON cost_logs (provider);
```

---

## Functional Requirements

### FR-1: 데이터 입력

#### FR-1.1: 수동 입력
- **엔드포인트**: `POST /api/v1/places`
- **필수 필드**: `canonical_name`
- **권장 필드**: `address_road` 또는 (`lat`, `lng`)
- **선택 필드**: 모든 나머지 Place 필드 + tags[] + notes[]
- **처리 로직**:
  1. 주소가 있으면 → Geocoding (카카오 로컬 API)으로 좌표 생성
  2. 좌표만 있으면 → Reverse Geocoding으로 주소 생성
  3. `normalized_name` 자동 생성 (소문자, 공백/특수문자 제거)
  4. 중복 후보 탐색 (FR-1.3) → 중복 있으면 응답에 `duplicate_candidates[]` 포함
  5. Place 생성 + 임베딩 생성 (비동기)
- **응답**: Place 상세 + duplicate_candidates (있으면)

#### FR-1.2: URL 스크랩 입력
- **엔드포인트**: `POST /api/v1/sources`
- **입력**: `{ "url": "...", "comment": "..." }`
- **처리 로직**:
  1. URL 도메인 분류 (네이버지도 / 카카오맵 / 구글지도 / 블로그 / 기타)
  2. 가능하면 ProviderLink 추출 (place_id, 장소 URL)
  3. OG 태그/메타 파싱 (title, description, image URL)
  4. 기존 Place 매칭 → 없으면 Place 자동 생성 (사용자 확인 필요 플래그)
  5. Source 레코드 생성
- **실패 시**: URL + 사용자 코멘트만 Source로 저장

#### FR-1.3: 중복 감지 및 병합
- **트리거**: Place 생성 시 자동, 또는 `POST /api/v1/places/check-duplicates`
- **스코어링 로직** (가중합, 0∼1):
  1. **Provider ID 매칭** (weight: 0.95) — 동일 provider_place_id
  2. **좌표 근접** (weight: 0.3) — 50m 이내 (`ST_DWithin(location, point, 50)`)
  3. **전화번호** (weight: 0.4) — exact match (정규화 후)
  4. **상호명 유사도** (weight: 0.3) — pg_trgm `similarity()` ≥ 0.6
- **기준**: 합산 스코어 ≥ 0.7 → 중복 후보로 제안
- **병합 API**: `POST /api/v1/places/{id}/merge` — body: `{ "merge_with": "uuid" }`
- **병합 시**: Canonical Place 유지, alias/providerlink/source/note/visit 통합, audit_log 기록

### FR-2: 검색

#### FR-2.1: 하이브리드 검색
- **엔드포인트**: `POST /api/v1/search`
- **입력 스키마**:
```json
{
  "query": "비 오는 날 조용한 실내 데이트",
  "filters": {
    "max_distance_km": 10,
    "lat": 35.87,
    "lng": 128.60,
    "parking": true,
    "reservation": "preferred",
    "mood": ["quiet"],
    "situations": ["rainy"],
    "companions": ["date"],
    "category_primary": "음식점",
    "tags": ["재방문각"],
    "is_favorite": true,
    "min_rating": 4
  },
  "limit": 10,
  "explain": true
}
```
- **처리 파이프라인**:
  1. **Query Understanding**: LLM(또는 룰 기반)으로 자연어 → `query`(검색 텍스트) + `filters`(구조화) 분리
  2. **Candidate Retrieval**:
     - 벡터 검색: 질의 임베딩 → pgvector cosine similarity (Top 200)
     - 키워드 검색: pg_trgm on normalized_name, notes.content
  3. **Filter**: PostGIS 거리, 속성 필터 (parking, mood, situations 등)
  4. **Rank**: `score = 0.5*vector_sim + 0.2*keyword_sim + 0.15*freshness + 0.1*favorite + 0.05*visit_count`
  5. **Explain** (explain=true): 매칭 태그/온톨로지 노드 + 관련 Note/Source 근거

- **응답 스키마**:
```json
{
  "results": [
    {
      "place": { /* Place 객체 */ },
      "score": 0.87,
      "explanation": {
        "matched_keywords": ["조용", "데이트"],
        "matched_ontology": ["mood:quiet", "companion:date"],
        "matched_sources": [{ "id": "...", "snippet": "조용한 분위기..." }],
        "distance_km": 3.2,
        "filter_match": { "parking": true, "mood": true }
      }
    }
  ],
  "total": 8,
  "query_parsed": {
    "intent": "search_place",
    "extracted_filters": { "mood": ["quiet"], "situations": ["rainy"] }
  }
}
```

#### FR-2.2: 온톨로지 확장 검색
- "파스타" 검색 시 → 온톨로지에서 "파스타" → parent "이탈리안" → sibling "피자" 등으로 확장
- 확장은 **1단계(parent + siblings)** 까지만 (비용/노이즈 방지)
- 확장된 키워드는 가중치를 낮춰서 (0.5x) 검색에 포함

### FR-3: LLM 연동

#### FR-3.1: LLM Provider 추상화
```python
# app/llm/base.py
class BaseLLM(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str: ...

    @abstractmethod
    async def parse_search_intent(self, query: str) -> SearchIntent: ...

    @abstractmethod
    async def summarize(self, texts: list[str], context: str) -> str: ...

    @abstractmethod
    async def build_comparison(self, places: list[dict]) -> str: ...
```

- MVP 기본 구현: `GeminiLLM` (`app/llm/gemini_llm.py`)
- 런타임 교체 구현: `OpenAILLM`, `AnthropicLLM`를 `LLMRouter`에서 선택 가능하게 유지
- 임베딩은 LLM provider와 분리하여 OpenAI 임베딩 클라이언트 사용

#### FR-3.2: 질의 파싱 프롬프트
LLM에게 보내는 시스템 프롬프트:
```
너는 장소 검색 질의를 구조화하는 파서야.
사용자의 자연어 질의를 아래 JSON으로 변환해.

{
  "search_text": "벡터 검색에 사용할 핵심 텍스트",
  "filters": {
    "max_distance_km": number | null,
    "parking": boolean | null,
    "reservation": "available" | "required" | null,
    "mood": string[] | null,
    "situations": string[] | null,
    "companions": string[] | null,
    "category_primary": string | null,
    "price_range": string | null,
    "min_rating": number | null
  }
}

모르는 필드는 null로 둬. 추측하지 마.
```

#### FR-3.3: Tool 엔드포인트 (에이전트용)
- **엔드포인트**: `POST /api/v1/tools/{tool_name}`
- **인증**: API Key
- **지원 도구**:

| tool_name | 설명 | 입력 | 출력 |
|-----------|------|------|------|
| `search_places` | 조건 기반 장소 검색 | query + filters + limit | Place 리스트 + explanation |
| `get_place_detail` | 장소 상세 조회 | place_id | Place + sources + notes + visits |
| `create_place` | 장소 생성 | place 필드들 | 생성된 Place |
| `attach_source` | 근거 자료 첨부 | place_id + source 데이터 | Source |
| `build_comparison_table` | 후보 비교표 | place_ids[] + columns[] | Markdown 비교표 |
| `draft_itinerary` | 간단 동선 초안 | place_ids[] + start_location | 순서 + 이동시간 추정 |

### FR-4: 보강 (Enrichment)

#### 원칙: 외부 데이터 저장 금지. 런타임 조회만.

- `GET /api/v1/places/{id}/enrich` — 요청 시점에 외부 API 조회, 응답에 포함 (DB 저장 안 함)
- 카카오 로컬 API로 기본 정보 (주소 확인, 카테고리)
- Google Places API로 운영시간/리뷰 수 등 (place_id가 있을 때만)
- **캐시**: 인메모리 TTL 캐시 (1시간). 동일 세션 중복 호출 방지용.

### FR-5: 내보내기

- `GET /api/v1/export?format=json|csv` — Place + Note + Source + Visit + Tag 전체 내보내기
- JSON은 전체 구조, CSV는 Place 기본 필드 + 태그(쉼표 구분)

---

## Non-Functional Requirements

### 성능
- 검색 응답 P95 ≤ 1.5초
- Place CRUD 응답 P95 ≤ 500ms
- 벡터 검색 Top-200 후 필터/랭킹

### 보안
- API Key 인증 (모든 엔드포인트)
- API 키는 환경변수. 코드/클라이언트 노출 금지.
- 개인 메모/방문 기록은 DB 레벨 암호화 (Supabase 기본 제공)

### 비용 제어
- cost_logs 테이블에 모든 외부 호출 기록
- `GET /api/v1/admin/costs?period=monthly` — 월별 비용 집계
- 월 비용 ₩10,000 초과 시 경고 로그

### 신뢰성
- 외부 API 실패 시: 사용자 메모/입력은 항상 보존. "외부 조회 실패" 플래그.
- 임베딩 생성 실패 시: Place는 저장하되, 임베딩은 재시도 큐에 등록.

---

## 온톨로지 시드 데이터 (LLM 생성)

아래 namespace별로 LLM에게 한국 맛집/카페 도메인에 맞는 트리를 생성시킨다.

### 생성 프롬프트 (seed 스크립트용)
```
한국 맛집/카페/여행지 도메인에 맞는 온톨로지 트리를 JSON으로 생성해줘.
각 namespace별 2∼3단계 깊이, 총 노드 수 50∼100개.

namespace:
1. cuisine — 음식 종류 계층 (한식 > 찌개 > 김치찌개, 양식 > 이탈리안 > 파스타 등)
2. mood — 분위기 (조용, 캐주얼, 로맨틱, 힙한, 뷰맛집 등)
3. situation — 상황 (비 오는 날, 야간, 주말, 아이 동반, 기념일 등)
4. companion — 동행 (혼밥, 데이트, 가족, 친구, 회식 등)
5. feature — 시설/특징 (주차, 예약, 테라스, 반려동물, 단체석, 개인룸 등)

JSON 형식:
[
  { "name": "한식", "namespace": "cuisine", "parent": null },
  { "name": "찌개", "namespace": "cuisine", "parent": "한식" },
  ...
]
```

---

## API 엔드포인트 전체 목록

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| POST | `/api/v1/places` | 장소 생성 |
| GET | `/api/v1/places` | 장소 목록 (cursor pagination) |
| GET | `/api/v1/places/{id}` | 장소 상세 |
| PATCH | `/api/v1/places/{id}` | 장소 수정 |
| DELETE | `/api/v1/places/{id}` | 장소 삭제 |
| POST | `/api/v1/places/{id}/merge` | 장소 병합 |
| POST | `/api/v1/places/check-duplicates` | 중복 체크 |
| GET | `/api/v1/places/{id}/enrich` | 외부 보강 (런타임) |
| POST | `/api/v1/sources` | 근거 자료 생성 |
| GET | `/api/v1/sources?place_id=...` | 근거 자료 목록 |
| DELETE | `/api/v1/sources/{id}` | 근거 자료 삭제 |
| POST | `/api/v1/notes` | 메모 생성 |
| GET | `/api/v1/notes?place_id=...` | 메모 목록 |
| PATCH | `/api/v1/notes/{id}` | 메모 수정 |
| DELETE | `/api/v1/notes/{id}` | 메모 삭제 |
| POST | `/api/v1/visits` | 방문 기록 생성 |
| GET | `/api/v1/visits?place_id=...` | 방문 기록 목록 |
| POST | `/api/v1/tags` | 태그 생성 |
| GET | `/api/v1/tags` | 태그 목록 |
| POST | `/api/v1/search` | 하이브리드 검색 |
| GET | `/api/v1/ontology` | 온톨로지 트리 |
| GET | `/api/v1/ontology/{namespace}` | 네임스페이스별 트리 |
| POST | `/api/v1/tools/{tool_name}` | 에이전트 Tool 호출 |
| GET | `/api/v1/export` | 전체 데이터 내보내기 |
| GET | `/api/v1/admin/costs` | 비용 집계 |
