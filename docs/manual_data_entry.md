# Manual Data Entry Guide

이 문서는 DB를 먼저 채우기 위한 수동 입력/검수 운영 절차를 정리한다.

## 1) 사전 준비

1. 서버 실행
```bash
cd backend
uv run uvicorn app.main:app --reload
```

2. 환경변수 확인
- API URL: `http://127.0.0.1:8000`
- API Key: `.env`의 `API_KEY`

3. 프론트 실행(입력/조회 UI)
```bash
cd frontend
npm run dev
```

## 2) 권장 입력 순서

1. Place 생성 (`POST /api/v1/places`)
2. 중복 후보 검토 (`POST /api/v1/places/check-duplicates`)
3. 필요 시 병합 (`POST /api/v1/places/{id}/merge`)
4. 근거 자료 추가 (`POST /api/v1/sources`)
5. 추가 메모 (`POST /api/v1/notes`)
6. 방문 기록 (`POST /api/v1/visits`)

## 3) 필드 운영 기준

필수:
- `canonical_name`

권장:
- `address_road` 또는 `lat`/`lng`
- `category_primary`
- `tags[]`, `notes[]`

입력 품질 체크:
- 전화번호는 가능한 실제 표기(서비스에서 정규화)
- 좌표 입력 시 `lat`/`lng` 쌍으로 입력
- 태그는 너무 세분화하지 말고 재사용 가능한 단어로 통일

## 4) 주요 API 예시

환경변수 설정:
```bash
export API_URL=http://127.0.0.1:8000
export API_KEY=your-api-key
```

장소 생성:
```bash
curl -s -X POST "$API_URL/api/v1/places" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "canonical_name": "합정 모모카페",
    "address_road": "서울 마포구 양화로 00",
    "phone": "02-123-4567",
    "category_primary": "카페",
    "tags": ["조용함", "데이트"],
    "notes": ["주말엔 웨이팅 가능", "2층 좌석 간격 넓음"]
  }'
```

중복 확인:
```bash
curl -s -X POST "$API_URL/api/v1/places/check-duplicates" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "canonical_name": "합정모모카페",
    "phone": "021234567"
  }'
```

장소 목록 조회:
```bash
curl -s "$API_URL/api/v1/places?limit=20" \
  -H "X-API-Key: $API_KEY"
```

장소 상세 조회:
```bash
curl -s "$API_URL/api/v1/places/{PLACE_ID}" \
  -H "X-API-Key: $API_KEY"
```

병합:
```bash
curl -s -X POST "$API_URL/api/v1/places/{KEEP_ID}/merge" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"merge_with": "{MERGE_ID}"}'
```

메모 추가:
```bash
curl -s -X POST "$API_URL/api/v1/notes" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": "{PLACE_ID}",
    "content": "평일 오전이 상대적으로 한산"
  }'
```

근거 자료 추가:
```bash
curl -s -X POST "$API_URL/api/v1/sources" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": "{PLACE_ID}",
    "type": "URL",
    "url": "https://example.com/post/123",
    "title": "방문 후기"
  }'
```

방문 기록 추가:
```bash
curl -s -X POST "$API_URL/api/v1/visits" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": "{PLACE_ID}",
    "visited_at": "2026-02-25",
    "rating": 5,
    "memo": "재방문 의사 높음"
  }'
```

## 5) UI로 입력/검수하는 방법

1. `/places/add`에서 장소 기본 정보 입력
2. `중복 확인` 버튼으로 후보 점검
3. `저장` 후 상세 페이지로 이동
4. `/places/recent`에서 최근 입력 목록 점검
5. 상세 화면의 `정보 수정`으로 `/places/{id}/edit` 진입 후 기존 정보 수정
6. 상세 화면에서 기존 메모 `수정` 또는 `메모 추가` 실행
7. 메모/근거/방문 기록 반영 여부 최종 확인

## 6) 일일 운영 체크리스트

1. 신규 입력 건수 확인
2. 중복 후보 확인 및 병합 처리
3. 주소/좌표 누락 건 확인
4. 카테고리/태그 표기 통일
5. 랜덤 샘플 5건 상세 검수
