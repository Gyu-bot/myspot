# Project Structure

```
place-db/
├── AGENTS.md                    # 코딩 에이전트 행동 규칙 및 컨벤션
├── PRD.md                       # 실행 가능한 제품 요구사항 (에이전트용)
├── PROJECT_STRUCTURE.md         # 이 파일
├── .env.example                 # 환경변수 템플릿
├── docker-compose.yml           # 로컬 개발용 (PostgreSQL + pgvector)
├── Makefile                     # 공통 명령어 (setup, migrate, seed, test, run)
│
├── backend/                     # FastAPI 서버
│   ├── pyproject.toml           # Python 의존성 (uv/poetry)
│   ├── alembic.ini              # DB 마이그레이션 설정
│   ├── alembic/
│   │   └── versions/            # 마이그레이션 파일들
│   │
│   ├── app/
│   │   ├── main.py              # FastAPI 앱 엔트리포인트
│   │   ├── config.py            # 환경변수 로드 (pydantic-settings)
│   │   ├── deps.py              # 의존성 주입 (DB 세션, 인증 등)
│   │   │
│   │   ├── auth/
│   │   │   └── api_key.py       # API Key 인증 미들웨어
│   │   │
│   │   ├── models/              # SQLAlchemy ORM 모델
│   │   │   ├── __init__.py
│   │   │   ├── place.py         # Place, ProviderLink
│   │   │   ├── source.py        # Source
│   │   │   ├── note.py          # Note
│   │   │   ├── visit.py         # Visit
│   │   │   ├── tag.py           # Tag, PlaceTag
│   │   │   ├── media.py         # Media
│   │   │   ├── ontology.py      # OntologyNode, Relation
│   │   │   └── embedding.py     # Embedding (pgvector)
│   │   │
│   │   ├── schemas/             # Pydantic request/response 스키마
│   │   │   ├── __init__.py
│   │   │   ├── place.py
│   │   │   ├── source.py
│   │   │   ├── note.py
│   │   │   ├── search.py        # SearchIntent, SearchResult
│   │   │   └── common.py        # 공통 (Pagination, ErrorResponse 등)
│   │   │
│   │   ├── api/                 # API 라우터
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── places.py    # /api/v1/places
│   │   │   │   ├── sources.py   # /api/v1/sources
│   │   │   │   ├── notes.py     # /api/v1/notes
│   │   │   │   ├── visits.py    # /api/v1/visits
│   │   │   │   ├── tags.py      # /api/v1/tags
│   │   │   │   ├── search.py    # /api/v1/search
│   │   │   │   ├── ontology.py  # /api/v1/ontology
│   │   │   │   └── tools.py     # /api/v1/tools (LLM 에이전트용)
│   │   │   └── router.py        # 라우터 통합
│   │   │
│   │   ├── services/            # 비즈니스 로직
│   │   │   ├── __init__.py
│   │   │   ├── place_service.py
│   │   │   ├── dedup_service.py          # 중복 감지/병합
│   │   │   ├── embedding_service.py      # 임베딩 생성/관리
│   │   │   ├── search_service.py         # 하이브리드 검색
│   │   │   ├── enrichment_service.py     # 외부 API 보강
│   │   │   ├── ontology_service.py       # 온톨로지 관리
│   │   │   └── llm_service.py            # LLM 추상화 (질의 파싱, 요약)
│   │   │
│   │   ├── providers/           # 외부 API 클라이언트
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # 추상 Provider 인터페이스
│   │   │   ├── naver.py         # 네이버 검색 API + 클라우드 Maps
│   │   │   ├── kakao.py         # 카카오 로컬 API
│   │   │   ├── google_places.py # Google Places API
│   │   │   └── openai_embed.py  # OpenAI 임베딩
│   │   │
│   │   ├── llm/                 # LLM Provider 추상화
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # 추상 LLM 인터페이스
│   │   │   ├── gemini_llm.py    # Gemini
│   │   │   ├── openai_llm.py    # OpenAI LLM
│   │   │   ├── anthropic_llm.py # Anthropic Claude
│   │   │   └── router.py        # Provider 선택 로직
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── geocoding.py     # 좌표 ↔ 주소 변환
│   │       ├── url_parser.py    # URL에서 장소 정보 추출
│   │       ├── text_normalize.py # 상호명/주소 정규화
│   │       └── cost_tracker.py  # API 비용 추적
│   │
│   ├── seeds/
│   │   └── ontology_seed.py     # 온톨로지 초기 데이터 (LLM 생성)
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_places.py
│       ├── test_search.py
│       ├── test_dedup.py
│       └── test_providers.py
│
├── frontend/                    # React SPA
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/                 # API 클라이언트 (fetch wrapper)
│       │   ├── client.ts
│       │   ├── places.ts
│       │   ├── search.ts
│       │   └── types.ts         # API 응답 타입 (백엔드 스키마 미러)
│       │
│       ├── components/
│       │   ├── layout/          # Header, Sidebar, Layout
│       │   ├── place/           # PlaceCard, PlaceForm, PlaceDetail
│       │   ├── search/          # SearchBar, SearchResults, FilterChips
│       │   ├── source/          # SourceList, SourceForm
│       │   ├── dedup/           # MergeSuggestion, MergeConfirm
│       │   └── common/          # Button, Input, Modal, Toast 등
│       │
│       ├── pages/
│       │   ├── HomePage.tsx
│       │   ├── SearchPage.tsx
│       │   ├── PlaceDetailPage.tsx
│       │   ├── AddPlacePage.tsx
│       │   └── DedupPage.tsx
│       │
│       ├── hooks/               # 커스텀 훅
│       │   ├── useSearch.ts
│       │   └── usePlaces.ts
│       │
│       └── styles/
│           └── globals.css      # Tailwind CSS
│
└── scripts/
    ├── setup.sh                 # 초기 셋업 스크립트
    ├── seed_ontology.py         # 온톨로지 시드 실행
    └── migrate.sh               # DB 마이그레이션
```
