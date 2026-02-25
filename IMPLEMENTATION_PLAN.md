# 상세 구현 계획 (Implementation Plan)

> 이 문서는 각 Phase별 상세 구현 가이드이다.
> 다른 에이전트/세션에서 이 문서를 참고해 독립적으로 구현을 진행할 수 있다.
> 반드시 `PRD.md`, `AGENTS.md`, `PROJECT_STRUCTURE.md`를 함께 참조할 것.

---

## 현재 상태 (Current State)

> 최종 동기화 시점: **2026-02-25**

### 결정사항 동기화
- 운영 DB: **Supabase PostgreSQL (Session Pooler URI)**
- 이식성 원칙: Supabase 전용 기능 미사용 (SQLAlchemy + Alembic + 표준 PostgreSQL 기능만 사용)
- 임베딩 모델: OpenAI `text-embedding-3-small` (고정)
- 기본 LLM Provider: `gemini` (런타임에서 `openai`/`anthropic` 교체 가능)
- 인증: 단일 API 키 (`X-API-Key`)
- CORS: 개발용 `*`
- 중복 병합: 자동 삭제 없음, 병합은 명시 API로만 수행

### 완료된 작업
- [x] Phase 0 백엔드 핵심 완료 (설정/앱 골격/인증/헬스체크)
- [x] Phase 0 잔여 작업 (리포지토리 기준):
  - `.env.example` 파일 생성
  - `frontend/` 초기 스캐폴드(`package.json` 포함) 생성
- [x] Phase 1 핵심 구현 완료:
  - SQLAlchemy 모델 구현 (`Place/ProviderLink/Source/Note/Visit/Tag/Media/Ontology/Relation/Embedding/AuditLog/CostLog`)
  - Alembic 초기 마이그레이션 생성/적용 (`d5bd684e2818`)
  - v1 API 구현: `places`, `sources`, `notes`, `visits`, `tags`
  - 서비스 구현: `place_service`, `dedup_service`
  - 유틸 구현: `text_normalize`, `cost_tracker`
  - 테스트 구현: `test_places.py`, `test_dedup.py`
- [x] 검증 완료:
  - `uv run ruff check .` 통과
  - `uv run ruff format --check .` 통과
  - `uv run python -m pytest -q` 통과 (`9 passed`)
  - `uv run python -m alembic current` → `d5bd684e2818 (head)`
  - `uv run python - <<'PY' ... SELECT 1 ... PY` DB ping 통과

### 진행률 요약 (2026-02-25 기준)
- Phase 0: **완료 (약 95%)** — `.env.example`/`frontend` 스캐폴드 반영, 로컬 Docker 검증만 선택 잔여
- Phase 1: **완료 (약 95%)** — 코어 CRUD/중복감지/병합/테스트 완료, geocoding/URL 메타추출은 후속
- Phase 1.5: **계획 확정 (0%)** — DB 수동 입력 + 입력/조회 UI 우선 트랙
- Phase 2: **미착수 (0%)** — 임베딩/검색 코어 서비스 미구현
- Phase 3: **미착수 (0%)** — 온톨로지/LLM 코어 미구현
- Phase 4: **미착수 (0%)** — 프론트 구조 생성 완료, 입력/조회 UI 미구현
- Phase 5: **미착수 (0%)** — FastAPI 고급 API(`/search`, `/tools`, `/ontology`, `/admin`) 미구현

### 환경 정보
- Python: 3.13.3 (`backend/.venv`)
- uv: 0.6.14
- Node.js: 25.6.1 / npm: 11.9.0
- DB 연결: Supabase pooler + SSL(require) 정상
- 환경 파일: 루트 `.env.example`/`.env` 및 `backend/.env` 존재

### 현재 주의사항
- `Makefile`의 `seed`/`costs` 타겟은 대응 코드(ontology seed 스크립트, admin costs API) 구현 전까지 실패함.
- 현재도 `POST /api/v1/places` 등으로 수동 입력은 가능하지만, 대량 입력/검증/정리용 워크플로우는 별도 정리가 필요함.
- 실행 순서는 "UI 입력/조회 → 임베딩 → 온톨로지/LLM → FastAPI 확장"으로 재배치함.

---

## Phase 0: 프로젝트 셋업 — ✅ 완료

위 "현재 상태"에 기술된 내용이 Phase 0의 전체 범위이다.

### Phase 0 검증 체크리스트
- [x] `.env.example` 작성 및 루트 `.env` 초기화 플로우 정리
- [x] `backend/.env` 설정 완료
- [x] Supabase Session Pooler 연결 확인 (`SELECT 1`)
- [x] 서버 기동 확인 (`cd backend && uv run uvicorn app.main:app --reload`)
- [x] 헬스체크 확인 (`GET /health` → `{"status":"ok","db":"connected"}`)
- [x] `frontend/` 초기화 (`package.json`, `vite`, `react`, `typescript`)
- [ ] (선택) 로컬 Docker DB 기동 검증: `docker compose up -d`

---

## Phase 1: DB 스키마 + 코어 CRUD

### 목표
핵심 엔티티(Place, Source, Note, Visit, Tag, Media, ProviderLink)의 CRUD가 동작하는 상태.

### 1.1 SQLAlchemy 모델 정의

각 모델 파일은 `PRD.md`의 SQL 스키마를 SQLAlchemy 2.0 Mapped 어노테이션으로 변환한다.

#### `backend/app/models/place.py`
```
구현 사항:
- Place 모델: PRD의 places 테이블 그대로
  - id: Mapped[UUID] PK, server_default=text("uuid_generate_v4()")
  - canonical_name: Mapped[str]
  - normalized_name: Mapped[str] — 검색용 정규화
  - address_road, address_jibun: Mapped[str | None]
  - region_depth1~3: Mapped[str | None]
  - location: Column(Geography("POINT", srid=4326)) — GeoAlchemy2 사용
  - phone: Mapped[str | None]
  - category_primary, category_secondary: Mapped[str | None]
  - parking: Mapped[bool | None]
  - reservation: Mapped[str | None] — CHECK 제약 ('available', 'required', 'unavailable', 'unknown')
  - price_range: Mapped[str | None] — CHECK 제약
  - mood: Column(ARRAY(Text)) — PostgreSQL 배열
  - companions: Column(ARRAY(Text))
  - situations: Column(ARRAY(Text))
  - is_favorite: Mapped[bool] = False
  - user_rating: Mapped[int | None] — CHECK 1~5
  - created_at, updated_at: Mapped[datetime] server_default=func.now()

  인덱스:
  - idx_places_normalized_name: GIN (gin_trgm_ops) — text_normalize 사용
  - idx_places_location: GIST
  - idx_places_category: (category_primary, category_secondary)

  관계:
  - provider_links: relationship("ProviderLink", back_populates="place", cascade="all, delete-orphan")
  - sources: relationship("Source", ...)
  - notes: relationship("Note", ...)
  - visits: relationship("Visit", ...)
  - tags: relationship("Tag", secondary=place_tags, ...)
  - media: relationship("Media", ...)

- ProviderLink 모델: PRD의 provider_links 테이블
  - provider: CHECK ('NAVER', 'KAKAO', 'GOOGLE', 'ETC')
  - UNIQUE(place_id, provider)
```

#### `backend/app/models/source.py`
```
- Source 모델: PRD의 sources 테이블
  - type: CHECK ('URL', 'TEXT', 'IMAGE', 'REVIEW_SNIPPET')
  - place 관계: ForeignKey → places(id) CASCADE
```

#### `backend/app/models/note.py`
```
- Note 모델: PRD의 notes 테이블
  - content: Mapped[str] NOT NULL
  - place 관계: ForeignKey → places(id) CASCADE
```

#### `backend/app/models/visit.py`
```
- Visit 모델: PRD의 visits 테이블
  - visited_at: Mapped[date] NOT NULL
  - rating: Mapped[int | None] CHECK 1~5
  - revisit: Mapped[bool | None]
```

#### `backend/app/models/tag.py`
```
- Tag 모델 + PlaceTag 연결 테이블
  - Tag.name: UNIQUE
  - Tag.type: CHECK ('freeform', 'system')
  - place_tags: Table (place_id, tag_id) — composite PK
```

#### `backend/app/models/media.py`
```
- Media 모델: PRD의 media 테이블
  - type: default 'image'
  - storage_url: NOT NULL
```

#### `backend/app/models/ontology.py`
```
- OntologyNode 모델: PRD의 ontology_nodes 테이블
  - namespace: CHECK ('cuisine', 'mood', 'situation', 'companion', 'feature')
  - parent_id: self-referential FK
  - UNIQUE(name, namespace)

- Relation 모델: PRD의 relations 테이블
  - 다형적 관계: from_entity_type + from_entity_id, to_entity_type + to_entity_id
  - relation_type: 'serves', 'good_for', 'fits', 'near', 'alias_of'
  - confidence: 0~1 기본값 1.0
```

#### `backend/app/models/embedding.py`
```
- Embedding 모델: PRD의 embeddings 테이블
  - vector: Column(Vector(1536)) — pgvector
  - entity_type: CHECK ('place', 'note', 'source')
  - UNIQUE(entity_type, entity_id)
  - HNSW 인덱스: vector_cosine_ops
```

#### 추가 모델 (audit_logs, cost_logs)
```
- AuditLog: PRD의 audit_logs 테이블 — action, entity_type, entity_id, detail(JSONB)
- CostLog: PRD의 cost_logs 테이블 — provider, action, tokens_in/out, cost_krw
```

#### 모델 완료 후
1. `app/models/__init__.py`에서 주석 해제하여 모든 모델 import
2. `cd backend && uv run python -m alembic revision --autogenerate -m "initial schema"`
3. 생성된 마이그레이션 파일 수동 검토 (특히 GIN 인덱스, Geography 타입, ARRAY 타입)
4. `uv run python -m alembic upgrade head`

### 1.2 Pydantic 스키마 정의

#### `backend/app/schemas/common.py`
```
- CursorPagination: cursor(str | None), limit(int, default=20, max=100)
- PaginatedResponse[T]: items: list[T], next_cursor: str | None, total: int | None
- ErrorResponse: detail: str
```

#### `backend/app/schemas/place.py`
```
- PlaceCreate: canonical_name(필수), address_road, lat, lng, 모든 선택 필드, tags(list[str]), notes(list[str])
- PlaceUpdate: 모든 필드 Optional
- PlaceResponse: 전체 필드 + provider_links, tags
- PlaceDetail: PlaceResponse + sources, notes, visits
- PlaceBrief: id, canonical_name, category_primary, is_favorite, user_rating — 목록용
- DuplicateCandidate: place_id, canonical_name, score, reasons(list[str])
- MergeRequest: merge_with: UUID
```

#### `backend/app/schemas/source.py`
```
- SourceCreate: place_id(선택), url, type, title, snippet, raw_text, comment
- SourceResponse: 전체 필드
```

#### `backend/app/schemas/note.py`
```
- NoteCreate: place_id, content
- NoteUpdate: content
- NoteResponse: 전체 필드
```

#### `backend/app/schemas/search.py`
```
- SearchRequest: query(str), filters(SearchFilters | None), limit(int), explain(bool)
- SearchFilters: max_distance_km, lat, lng, parking, reservation, mood[], situations[], companions[], category_primary, tags[], is_favorite, min_rating, price_range
- SearchIntent: search_text, filters — LLM 파싱 결과
- SearchResult: place(PlaceBrief), score(float), explanation(SearchExplanation | None)
- SearchExplanation: matched_keywords[], matched_ontology[], matched_sources[], distance_km, filter_match
- SearchResponse: results[], total, query_parsed(SearchIntent | None)
```

### 1.3 유틸리티

#### `backend/app/utils/text_normalize.py`
```
구현:
- normalize_place_name(name: str) -> str
  1. 소문자 변환
  2. 특수문자 제거 (한글, 영문, 숫자만 유지)
  3. 연속 공백 → 단일 공백
  4. 양쪽 공백 제거

- normalize_phone(phone: str) -> str
  1. 숫자만 추출
  2. 국제번호 접두사 제거 (+82 → 0)
```

#### `backend/app/utils/cost_tracker.py`
```
구현:
- async def log_cost(db: AsyncSession, provider: str, action: str, tokens_in: int, tokens_out: int, cost_krw: float)
  → CostLog 레코드 삽입

- async def get_monthly_cost(db: AsyncSession, year: int, month: int) -> dict
  → 월별 provider별 합산

- async def check_budget_warning(db: AsyncSession) -> bool
  → 이번 달 합산 > settings.monthly_cost_limit_krw 이면 True + 경고 로그
```

### 1.4 API 라우터

#### `backend/app/api/v1/places.py`
```
엔드포인트:
- POST /api/v1/places — PlaceCreate → PlaceResponse + duplicate_candidates[]
  1. text_normalize로 normalized_name 생성
  2. dedup_service.check_duplicates() 호출
  3. Place 생성
  4. tags가 있으면 Tag upsert + PlaceTag 연결
  5. notes가 있으면 Note 생성
  6. 임베딩 생성 (비동기, Background Task) — Phase 2에서 연결
  7. 응답 반환

- GET /api/v1/places — cursor pagination → PaginatedResponse[PlaceBrief]
  - 쿼리 파라미터: cursor, limit, category_primary, is_favorite

- GET /api/v1/places/{id} — PlaceDetail (sources, notes, visits 포함)

- PATCH /api/v1/places/{id} — PlaceUpdate → PlaceResponse
  - updated_at 자동 갱신
  - 필드 변경 시 임베딩 재생성 (Phase 2)

- DELETE /api/v1/places/{id} — 204 No Content (CASCADE로 관련 데이터 삭제)

- POST /api/v1/places/{id}/merge — MergeRequest
  - dedup_service.merge_places() 호출
  - audit_log 기록

- POST /api/v1/places/check-duplicates — {canonical_name, address_road, lat, lng, phone}
  - dedup_service.check_duplicates() → DuplicateCandidate[]
```

#### `backend/app/api/v1/sources.py`
```
- POST /api/v1/sources — SourceCreate → SourceResponse
  - URL이 있으면 url_parser로 메타 추출 시도 (Phase 1에서는 기본 구현)
- GET /api/v1/sources?place_id=... — 목록 (cursor pagination)
- DELETE /api/v1/sources/{id} — 204
```

#### `backend/app/api/v1/notes.py`
```
- POST /api/v1/notes — NoteCreate → NoteResponse
- GET /api/v1/notes?place_id=... — 목록
- PATCH /api/v1/notes/{id} — NoteUpdate → NoteResponse
- DELETE /api/v1/notes/{id} — 204
```

#### `backend/app/api/v1/visits.py`
```
- POST /api/v1/visits — VisitCreate → VisitResponse
- GET /api/v1/visits?place_id=... — 목록
```

#### `backend/app/api/v1/tags.py`
```
- POST /api/v1/tags — TagCreate → TagResponse (name + type)
- GET /api/v1/tags — 전체 태그 목록
```

#### `backend/app/api/router.py`
```
- v1_router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_api_key)])
- v1_router.include_router(places.router, ...)
- v1_router.include_router(sources.router, ...)
- ... 각 라우터 포함
- app.include_router(v1_router) — main.py에서 호출
```

### 1.5 서비스 레이어

#### `backend/app/services/place_service.py`
```
- async def create_place(db, data: PlaceCreate) -> Place
  1. normalized_name 생성
  2. Geocoding (주소 있으면 → 좌표, 좌표만 있으면 → 주소) — Phase 1에서는 선택적
  3. Place 레코드 생성
  4. ProviderLink, Tag, Note 연결
  5. return Place

- async def get_place(db, id) -> Place | None
- async def list_places(db, cursor, limit, filters) -> (list[Place], next_cursor)
- async def update_place(db, id, data: PlaceUpdate) -> Place
- async def delete_place(db, id) -> None
```

#### `backend/app/services/dedup_service.py`
```
- async def check_duplicates(db, name, address, lat, lng, phone) -> list[DuplicateCandidate]
  스코어링 (PRD 기준):
  1. Provider ID 매칭 (0.95)
  2. 좌표 50m 이내: ST_DWithin(location, ST_MakePoint(lng, lat)::geography, 50) → weight 0.3
  3. 전화번호 exact match (정규화 후) → weight 0.4
  4. 상호명 유사도: similarity(normalized_name, target) >= 0.6 → weight 0.3
  5. 합산 >= 0.7 → 후보

- async def merge_places(db, keep_id, merge_id) -> Place
  1. merge_id의 ProviderLink, Source, Note, Visit, Tag, Media → keep_id로 이전
  2. merge_id Place 삭제
  3. AuditLog 기록
  4. return kept Place
```

### 1.6 테스트

#### `backend/tests/test_places.py`
```
- test_create_place — 최소 필드(canonical_name)로 생성
- test_create_place_with_tags — 태그 포함 생성
- test_get_place — 생성 후 조회
- test_list_places — 여러 개 생성 후 목록 조회 (cursor pagination)
- test_update_place — 필드 수정
- test_delete_place — 삭제 후 404
```

#### `backend/tests/test_dedup.py`
```
- test_duplicate_by_name — 유사 이름 감지
- test_duplicate_by_phone — 동일 전화번호 감지
- test_merge_places — 병합 후 데이터 통합 확인
```

### Phase 1 완료 조건
- [x] 모든 모델이 DB에 반영됨 (`alembic upgrade head` 성공)
- [x] Place CRUD 전체 동작
- [x] Source, Note, Visit, Tag CRUD 동작
- [x] 중복 감지 → 유사 이름/전화번호 후보 반환
- [x] 병합 API 동작
- [x] pytest 전체 통과

### Phase 1 구현 메모 (실제 상태)
- 구현된 라우터:
  - `POST/GET/PATCH/DELETE /api/v1/places`
  - `POST /api/v1/places/check-duplicates`
  - `POST /api/v1/places/{id}/merge`
  - `POST/GET/DELETE /api/v1/sources`
  - `POST/GET/PATCH/DELETE /api/v1/notes`
  - `POST/GET /api/v1/visits`
  - `POST/GET /api/v1/tags`
- dedup 규칙은 PRD 가중치 기반 + 강한 단일 시그널(전화번호 exact / 고유사도 이름) 감지를 보강함.
- `normalize_place_name()`은 공백 제거까지 수행하도록 구현됨 (문자열 유사도 안정화 목적).
- 테스트 실행 시 생성되는 샘플 데이터는 정리 스크립트로 제거해 DB 잔여 데이터 없음을 확인함.
- Phase 1 범위 중 다음은 **다음 스프린트 후보**:
  - 카카오 geocoding 실제 연동
  - `POST /sources`에서 URL 메타 추출(url_parser) 기본 구현
  - ProviderLink 자동 연결 고도화

### 다음 착수 계획 (업데이트: 2026-02-25, UI 선행 트랙)
1. Phase 1.5 입력/조회 UI + DB 수동 입력 운영 (최우선, 3~5일)
2. Phase 2 임베딩 파이프라인 (1~2일)
3. Phase 3 온톨로지 + LLM 코어 (2~3일)
4. Phase 5 FastAPI 확장(검색/툴/온톨로지 API) (2~3일)
5. Phase 4B 검색/추천 UI 확장 (2~3일)

---

## Phase 1.5: DB 수동 입력 + 입력/조회 UI 우선 트랙 (신규)

### 목표
검색/임베딩 구현 전에 사용자가 장소 데이터를 미리 안정적으로 입력/조회/정리할 수 있는 경로를 먼저 완성한다.

### 1.5.1 수동 입력 경로 확정 (API 우선)
- 기존 CRUD API를 수동 입력 표준으로 확정:
  - `POST /api/v1/places`
  - `POST /api/v1/notes`
  - `POST /api/v1/sources`
  - `POST /api/v1/visits`
  - `POST /api/v1/tags`
- `docs/manual_data_entry.md` 작성:
  - 필드별 필수/선택 입력 규칙
  - 추천 입력 순서 (Place → Tag/Note → Source → Visit)
  - 중복 감지/병합 절차 (`check-duplicates`, `/{id}/merge`)
  - 실패 시 재시도 규칙

### 1.5.2 대량 입력(사전 적재) 도구
- `backend/scripts/import_places.py` 추가 (CSV/JSONL → API or DB 세션 입력)
- 요구사항:
  - dry-run 모드
  - idempotent upsert 기준 (`canonical_name + phone + lat/lng` 보조키)
  - 행 단위 에러 리포트(`failed_rows.csv`)
  - 외부 API 호출 없이 사용자 입력만 저장 (정책 준수)

### 1.5.3 입력 품질/정리 루프
- 입력 직후 자동 점검:
  - 이름 정규화 누락 필드 점검
  - 전화번호 정규화 점검
  - 좌표/주소 누락 점검 리포트
- 중복 정리 배치:
  - `check-duplicates` 결과를 모아 검토용 목록 생성
  - 병합은 항상 수동 승인 후 `merge` 호출

### 1.5.4 입력/조회 UI 선행 구현 (필수)
- Phase 4 본개발 전, 최소 UI를 먼저 고정:
  - `AddPlacePage`: 장소 + 태그 + 메모 입력, 중복 후보 즉시 확인
  - `RecentPlacesPage`: 최근 입력 목록 조회(최신순, cursor 기반 더보기)
  - `PlaceDetailLitePage`: 기본 정보/태그/메모/방문 이력 조회
  - `DedupReviewPage`(선택): 후보 병합 승인/거부
- 구현 범위는 "입력/조회 검증"에 필요한 최소 화면만 포함하고, 검색 UI는 제외

### 1.5 완료 조건
- [ ] 수동 입력 가이드 문서(`docs/manual_data_entry.md`) 작성 완료
- [ ] 단건 입력: Place/Note/Source/Visit/Tag 입력 절차 검증 완료
- [ ] 대량 입력 스크립트 1종(CSV 또는 JSONL) 동작 검증 완료
- [ ] 중복 검토/병합 운영 절차 문서화 완료
- [ ] 입력/조회 최소 UI(`AddPlacePage`, `RecentPlacesPage`, `PlaceDetailLitePage`) 동작 확인
- [ ] 실제 사전 데이터 N건 입력 후 샘플 검수 완료 (N은 운영자가 결정)

---

## Phase 2: 임베딩 + 검색

### 목표
임베딩 파이프라인과 검색 코어 로직(서비스 레이어)을 완성하는 상태.

### 2.1 OpenAI 임베딩 클라이언트

#### `backend/app/providers/openai_embed.py`
```
구현:
- class OpenAIEmbedProvider:
    model = "text-embedding-3-small"
    dimensions = 1536

    async def embed(self, text: str) -> list[float]
      - openai.AsyncClient 사용
      - cost_tracker.log_cost() 호출
      - 반환: 1536차원 벡터

    async def embed_batch(self, texts: list[str]) -> list[list[float]]
      - 배치 임베딩 (한 번에 최대 100개)

    def build_embed_text(self, place: Place, notes: list[Note], tags: list[Tag]) -> str
      - "{canonical_name} {address_road} {' '.join(tags)} {' '.join(note.content for note in notes)}"
      - 최대 8000자 truncate
```

### 2.2 임베딩 서비스

#### `backend/app/services/embedding_service.py`
```
구현:
- async def create_or_update_embedding(db, entity_type, entity_id, text: str)
  1. text의 hash 계산 (SHA-256)
  2. 기존 Embedding 조회
  3. text_hash가 같으면 스킵 (불필요한 재생성 방지)
  4. OpenAI embed 호출
  5. Embedding upsert (UNIQUE 제약 활용)

- async def create_place_embedding(db, place_id)
  1. Place + Notes + Tags 로드
  2. embed_text 생성
  3. create_or_update_embedding() 호출

- async def delete_embedding(db, entity_type, entity_id)

- async def embed_query(text: str) -> list[float]
  - 검색 질의용 임베딩 (DB 저장 안 함)
```

### 2.3 하이브리드 검색 서비스

#### `backend/app/services/search_service.py`
```
핵심 파이프라인:

async def hybrid_search(db, request: SearchRequest) -> SearchResponse:

  1. Query Understanding (Phase 2 기본: 룰 기반, Phase 3에서 LLM 추가)
     - query에서 필터 키워드 추출 (간단한 규칙)
     - 명시적 filters와 병합

  2. Vector Search
     - embed_query(request.query)
     - SQL: SELECT e.entity_id, 1 - (e.vector <=> :query_vector) AS sim
            FROM embeddings e
            WHERE e.entity_type = 'place'
            ORDER BY e.vector <=> :query_vector
            LIMIT 200

  3. Keyword Search (보조)
     - SQL: SELECT p.id, similarity(p.normalized_name, :query) AS sim
            FROM places p
            WHERE similarity(p.normalized_name, :query) > 0.3
            UNION
            SELECT n.place_id, similarity(n.content, :query) AS sim
            FROM notes n
            WHERE similarity(n.content, :query) > 0.3

  4. Filter
     - PostGIS 거리: ST_DWithin(p.location, ST_MakePoint(:lng, :lat)::geography, :max_dist_m)
     - 속성 필터: parking, mood (ANY overlap), situations, companions, category_primary
     - 태그 필터: place_tags JOIN
     - is_favorite, min_rating

  5. Rank (PRD 공식)
     score = 0.5 * vector_sim
           + 0.2 * keyword_sim
           + 0.15 * freshness   -- (1 / (1 + days_since_update/365))
           + 0.1 * favorite     -- (1.0 if is_favorite else 0.0)
           + 0.05 * visit_freq  -- min(visit_count / 10, 1.0)

  6. Explain (explain=true)
     - 매칭된 키워드, 온톨로지 노드, Source snippet
     - 거리, 필터 매칭 여부

구현 전략:
  - 벡터 검색 + 필터를 하나의 CTE 쿼리로 합치지 말고, 2단계로 분리
  - 1단계: 벡터 Top-200 후보 ID 추출
  - 2단계: 후보 ID에 대해 필터 + 키워드 + 메타 정보 조회 → Python에서 랭킹
  - 이유: pgvector 쿼리와 PostGIS/ARRAY 필터를 합치면 인덱스 비효율
```

### 2.4 검색 API (Phase 5로 이관)

#### `backend/app/api/v1/search.py`
```
- POST /api/v1/search — SearchRequest → SearchResponse
  1. search_service.hybrid_search() 호출
  2. 응답 반환
```
위 엔드포인트 구현/노출은 "FastAPI 확장 마무리(Phase 5)"에서 진행한다.

### 2.5 Place 생성/수정 시 임베딩 연동

```
place_service.create_place()와 update_place()에서:
  - BackgroundTasks를 사용하여 비동기로 임베딩 생성
  - 임베딩 실패 시 Place는 저장, 로그만 남김
```

### Phase 2 테스트

#### `backend/tests/test_search.py`
```
- test_vector_search — 임베딩 생성 후 유사 질의 검색
- test_keyword_search — 이름/노트 키워드 매칭
- test_filter_search — 속성 필터 적용
- test_combined_search — 벡터 + 키워드 + 필터 통합
- test_search_explain — explain=true 응답 구조
```

### Phase 2 완료 조건
- [ ] 장소 생성 시 임베딩 자동 생성
- [ ] 벡터 유사도 + 키워드 매칭 + 필터 조합
- [ ] 결과 랭킹 정상
- [ ] 검색 서비스 단위 테스트 통과 (`search_service` 레벨)
- [ ] pytest 전체 통과

---

## Phase 3: 온톨로지 + LLM 코어

### 목표
온톨로지/LLM 내부 로직을 완성하고, API 노출 없이 코어 동작을 검증한다.

### 3.1 온톨로지 서비스

#### `backend/app/services/ontology_service.py`
```
- async def get_tree(db, namespace: str | None) -> list[OntologyNode]
  - namespace가 None이면 전체, 아니면 해당 namespace만
  - 트리 구조로 반환 (parent-child)

- async def expand_search_terms(db, term: str) -> list[tuple[str, float]]
  1. ontology_nodes에서 term과 일치하는 노드 찾기
  2. parent 노드 → 가중치 0.5
  3. sibling 노드 → 가중치 0.5
  4. 1단계만 확장 (비용/노이즈 방지)
  5. 반환: [(확장된 term, weight), ...]

  예: "파스타" → [("이탈리안", 0.5), ("피자", 0.5), ("리조또", 0.5)]
```

### 3.2 온톨로지 시드

#### `backend/seeds/ontology_seed.py`
```
- LLM에게 PRD의 프롬프트로 트리 생성 요청
- JSON 파싱 후 DB에 OntologyNode bulk insert
- parent 참조는 name+namespace로 resolve
- 실행: uv run python -m seeds.ontology_seed
- 또는: 미리 생성된 JSON 파일을 seeds/ontology_data.json에 저장해두고 로드

권장: LLM 호출 비용을 아끼기 위해, 한 번 생성한 결과를 JSON 파일로 저장하고 이후에는 파일에서 로드
```

### 3.3 LLM Provider 추상화

#### `backend/app/llm/base.py`
```
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

#### `backend/app/llm/gemini_llm.py`
```
class GeminiLLM(BaseLLM):
    model = "gemini-2.5-flash"

    async def chat(self, messages, **kwargs):
      - Gemini API 호출
      - cost_tracker.log_cost() 호출

    async def parse_search_intent(self, query):
      - PRD의 질의 파싱 시스템 프롬프트 사용
      - JSON 응답 파싱 → SearchIntent 반환
      - JSON 파싱 실패 시 fallback: 전체를 search_text로

    async def summarize(self, texts, context):
      - 근거 텍스트 + 컨텍스트로 요약 생성

    async def build_comparison(self, places):
      - 장소 데이터 → Markdown 비교표 생성
```

#### `backend/app/llm/openai_llm.py`
```
class OpenAILLM(BaseLLM):
    model = "gpt-4o-mini"
    - OpenAI Chat API 호출
```

#### `backend/app/llm/anthropic_llm.py`
```
class AnthropicLLM(BaseLLM):
    model = "claude-sonnet-4-20250514"
    - Anthropic Messages API 호출
```

#### `backend/app/llm/router.py`
```
class LLMRouter:
    def get_provider(self, provider: str | None = None) -> BaseLLM:
      - provider 지정 없으면 settings.default_llm_provider 사용
      - "gemini" → GeminiLLM()
      - "openai" → OpenAILLM()
      - "anthropic" → AnthropicLLM()
```

### 3.4 검색에 LLM 질의 파싱 통합

```
search_service.hybrid_search()의 Step 1을 LLM으로 교체:
  - llm_service.parse_search_intent(query) → SearchIntent
  - SearchIntent.search_text → 벡터 검색에 사용
  - SearchIntent.filters → 명시적 filters와 병합
  - LLM 호출 실패 시 fallback: 기존 룰 기반
```

### 3.5 검색에 온톨로지 확장 통합

```
search_service.hybrid_search()에서:
  - 검색 텍스트에서 키워드 추출 → ontology_service.expand_search_terms()
  - 확장된 키워드를 가중치 0.5로 벡터 검색에 추가
  - 또는 확장된 키워드로 추가 벡터 검색 수행 후 결과 병합
```

### 3.6 Tool 엔드포인트 (Phase 5로 이관)

#### `backend/app/api/v1/tools.py`
```
POST /api/v1/tools/{tool_name}

각 tool별 입력/출력:

1. search_places:
   입력: { "query": str, "filters": {...}, "limit": int }
   처리: search_service.hybrid_search() 호출
   출력: SearchResponse

2. get_place_detail:
   입력: { "place_id": UUID }
   처리: place_service.get_place() + sources + notes + visits
   출력: PlaceDetail

3. create_place:
   입력: PlaceCreate 필드들
   처리: place_service.create_place()
   출력: PlaceResponse

4. attach_source:
   입력: { "place_id": UUID, "url": str, "type": str, "snippet": str }
   처리: Source 생성
   출력: SourceResponse

5. build_comparison_table:
   입력: { "place_ids": list[UUID], "columns": list[str] }
   처리: 장소들 조회 → LLM으로 Markdown 비교표 생성
   출력: { "markdown": str }

6. draft_itinerary:
   입력: { "place_ids": list[UUID], "start_location": { "lat": float, "lng": float } }
   처리: 장소 좌표 기반 순서 최적화 + 이동시간 추정 (LLM)
   출력: { "markdown": str, "places_ordered": list[PlaceBrief] }
```

### 3.7 온톨로지 API (Phase 5로 이관)

#### `backend/app/api/v1/ontology.py`
```
- GET /api/v1/ontology — 전체 온톨로지 트리
- GET /api/v1/ontology/{namespace} — namespace별 트리
```
위 API 노출은 "FastAPI 확장 마무리(Phase 5)"에서 진행한다.

### Phase 3 완료 조건
- [ ] 온톨로지 시드 데이터 DB에 로드됨
- [ ] "파스타" 검색 시 이탈리안/피자 등 확장 결과 포함
- [ ] LLM 질의 파싱: "비 오는 날 조용한 데이트 코스" → 구조화된 필터
- [ ] LLM Provider 교체 가능 (config만 변경)
- [ ] LLM 코어 함수(parse/summarize/comparison/itinerary) 단위 테스트 통과
- [ ] pytest 전체 통과

---

## Phase 4: 웹 UI

### 전제 조건
- Node.js 설치: `nvm install --lts && nvm use --lts`
- 또는 직접 설치
- 실행 순서:
  - Phase 4A(입력/조회 UI) 먼저 진행
  - Phase 4B(검색/추천 UI)는 Phase 5 이후 진행

### 4.1 프론트엔드 프로젝트 초기화

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install react-router-dom @tanstack/react-query
npm install -D tailwindcss @tailwindcss/vite
```

### 4.2 API 클라이언트

#### `frontend/src/api/client.ts`
```
- fetchAPI(path, options) — fetch wrapper
  - base URL: import.meta.env.VITE_API_URL || "http://localhost:8000"
  - 헤더: X-API-Key, Content-Type
  - 에러 처리

- VITE_API_KEY 환경변수로 API 키 주입 (개발용)
```

#### `frontend/src/api/types.ts`
```
- Place, PlaceBrief, PlaceDetail — 백엔드 스키마 미러
- Source, Note, Visit, Tag
- SearchRequest, SearchResponse, SearchResult
- PaginatedResponse<T>
```

#### `frontend/src/api/places.ts`, `search.ts`
```
- getPlaces(cursor?, limit?) → PaginatedResponse<PlaceBrief>
- getPlace(id) → PlaceDetail
- createPlace(data) → Place
- updatePlace(id, data) → Place
- deletePlace(id) → void
- searchPlaces(request) → SearchResponse
```

### 4.3 페이지

#### Phase 4A (선행): 입력/조회 UI
#### `HomePage.tsx`
```
- 최근 저장된 장소 카드 리스트 (최신 10개)
- 빠른 입력 버튼 → AddPlacePage로 이동
- 즐겨찾기 장소 섹션
```

#### `RecentPlacesPage.tsx`
```
- 최근 입력 데이터 목록 조회(최신순, cursor pagination)
- 필터: 즐겨찾기/카테고리(최소)
- 상세 페이지로 이동
```

#### `PlaceDetailPage.tsx` (`PlaceDetailLitePage`로 시작 가능)
```
- 장소 기본 정보 (이름, 주소, 카테고리, 태그)
- 탭 구조: 메모 | 근거자료 | 방문기록
- 수정/삭제 버튼
- 즐겨찾기 토글
```

#### `AddPlacePage.tsx`
```
- 폼: 이름(필수), 주소, 카테고리, 분위기(멀티셀렉트), 태그, 메모
- 중복 감지 결과 표시 (생성 시 응답에 포함)
- 저장 후 PlaceDetailPage로 이동
```

#### `DedupPage.tsx`
```
- 병합 제안 목록
- 각 제안: 두 장소 나란히 비교
- 병합/무시 버튼
```

#### Phase 4B (후행): 검색/추천 UI
#### `SearchPage.tsx`
```
- 검색 바 (자연어 입력)
- 필터 칩: 카테고리, 분위기, 상황, 동행, 주차 등
- 결과 카드 리스트: 장소명, 카테고리, 점수, 매칭 이유
- 무한 스크롤 또는 "더보기"
```

### 4.4 컴포넌트

```
components/
├── layout/
│   ├── Header.tsx — 로고, 네비게이션
│   ├── Sidebar.tsx — (선택) 카테고리 필터
│   └── Layout.tsx — Header + main content wrapper
│
├── place/
│   ├── PlaceCard.tsx — 목록용 카드 (이름, 카테고리, 별점, 즐겨찾기)
│   ├── PlaceForm.tsx — 장소 입력/수정 폼
│   └── PlaceDetail.tsx — 상세 정보 표시
│
├── search/
│   ├── SearchBar.tsx — 자연어 입력 + 검색 버튼
│   ├── SearchResults.tsx — 결과 카드 리스트
│   └── FilterChips.tsx — 필터 토글 칩
│
├── source/
│   ├── SourceList.tsx — 근거 자료 목록
│   └── SourceForm.tsx — 근거 자료 추가 폼
│
└── common/
    ├── Button.tsx
    ├── Input.tsx
    ├── Modal.tsx
    └── Toast.tsx
```

### Phase 4 완료 조건
- [ ] Phase 4A: 장소 등록/수정/삭제 동작
- [ ] Phase 4A: 장소 목록/상세 조회(메모/근거/방문 포함)
- [ ] Phase 4A: 중복 병합 UI 동작
- [ ] Phase 4B: 자연어 검색 + 필터 동작
- [ ] 반응형 레이아웃 (모바일 대응)

---

## Phase 5: FastAPI 확장 마무리 (마지막 단계)

### 목표
기존 CRUD FastAPI는 유지하고, 고급 기능용 API를 마지막에 일괄 노출한다.

### 5.1 검색 API 노출
- `POST /api/v1/search`
- `search_service.hybrid_search()`와 연결
- explain 옵션/필터 스키마 응답 안정화

### 5.2 온톨로지/Tool API 노출
- `GET /api/v1/ontology`
- `GET /api/v1/ontology/{namespace}`
- `POST /api/v1/tools/{tool_name}` 6종

### 5.3 운영성 API 정리
- 비용/운영 확인용 admin endpoint 정리 (예: `/api/v1/admin/costs`)
- `Makefile`의 `costs` 타겟과 실제 엔드포인트 동기화

### Phase 5 완료 조건
- [ ] 검색 API(`/api/v1/search`) 동작
- [ ] 온톨로지 API 동작
- [ ] Tool API 6종 동작
- [ ] admin costs API 동작 및 `make costs` 검증
- [ ] FastAPI 확장 구간 테스트 통과

---

## Phase별 의존 관계

```
Phase 0 (셋업) ✅ 완료
    ↓
Phase 1 (DB + CRUD) ✅ 완료
    ↓
Phase 1.5 (입력/조회 UI + DB 수동 입력) ⏳ 다음 우선순위
    ↓
Phase 2 (임베딩 코어) ⏳ Phase 1.5 이후
    ↓
Phase 3 (온톨로지 + LLM 코어) ⏳ Phase 2 이후
    ↓
Phase 5 (FastAPI 확장 마무리) ⏳ Phase 3 이후
    ↓
Phase 4B (검색/추천 UI 확장) ⏳ Phase 5 이후
```

**참고**: 기존 CRUD FastAPI는 이미 동작 중이며, 마지막 단계는 "고급 API 확장" 범위다.

---

## 에이전트를 위한 작업 컨텍스트

### 실행 전 체크리스트 (모든 Phase)
1. `.env` 파일 존재 확인 (`cp .env.example .env`)
2. Supabase pooler `DATABASE_URL`/`ssl=require` 확인 + `backend/.env` 동기화
3. `cd backend && uv run python -m alembic upgrade head` — 마이그레이션 적용
4. `cd backend && uv run uvicorn app.main:app --reload` — 서버 실행
5. `curl http://127.0.0.1:8000/health` — 연결 상태 확인
6. (선택) 로컬 이식성 점검 시 `docker compose up -d`로 동일 마이그레이션 재적용

### 코딩 컨벤션 요약
- Python: Ruff lint/format, type hints 필수, Google-style docstring
- DB 접근: SQLAlchemy async only (Supabase JS 금지)
- 인증: `Depends(verify_api_key)` — 모든 v1 라우터에 적용
- Pagination: cursor 기반 (offset 금지)
- 외부 API: 결과 장기 저장 금지, ProviderLink(ID/URL)만 저장
- 임베딩: 저장 시 1회, 검색 시 질의만 임베딩
- 비용: cost_tracker로 모든 외부 호출 기록
- 테스트: 새 서비스/엔드포인트마다 필수

### 주요 파일 경로 참조
```
backend/app/config.py          — 환경변수 설정
backend/app/deps.py            — DB 세션 의존성
backend/app/main.py            — FastAPI 앱
backend/app/auth/api_key.py    — 인증
backend/app/models/__init__.py — Base + 모델 import
backend/alembic/env.py         — 마이그레이션 환경
```
