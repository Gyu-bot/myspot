"""FastAPI 앱 엔트리포인트."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import v1_router
from app.deps import engine

app = FastAPI(title="Place DB", version="0.1.0", description="개인 장소 DB + LLM 시맨틱 서치")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP: 전체 허용. 프로덕션에서는 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """헬스체크 — DB 연결 확인 포함."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "degraded", "db": str(e)}


app.include_router(v1_router)
