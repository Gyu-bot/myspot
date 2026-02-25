"""애플리케이션 설정 — pydantic-settings로 환경변수 로드."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # DB
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/placedb"

    # 인증
    api_key: str = "dev-api-key"

    # OpenAI
    openai_api_key: str = ""

    # Gemini (LLM)
    gemini_api_key: str = ""

    # Anthropic (LLM)
    anthropic_api_key: str = ""

    # 기본 LLM Provider
    default_llm_provider: str = "gemini"  # "gemini" | "openai" | "anthropic"

    # 카카오
    kakao_rest_api_key: str = ""

    # 네이버
    naver_client_id: str = ""
    naver_client_secret: str = ""
    naver_cloud_client_id: str = ""
    naver_cloud_client_secret: str = ""

    # 구글
    google_places_api_key: str = ""

    # 비용 제어
    monthly_cost_limit_krw: int = 10000


settings = Settings()
