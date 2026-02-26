from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DB
    database_url: str = Field(..., alias="DATABASE_URL")

    # OpenAI
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small")
    chat_model: str = Field(default="gpt-4o-mini")

    # App
    app_env: str = Field(default="dev", alias="APP_ENV")
    cors_allow_origins: str = Field(default="*")

    # Files
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")

    # Retrieval
    top_k: int = Field(default=8)

    @property
    def cors_origins_list(self) -> list[str]:
        v = self.cors_allow_origins.strip()
        if v == "*":
            return ["*"]
        return [x.strip() for x in v.split(",") if x.strip()]


settings = Settings()