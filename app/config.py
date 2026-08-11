from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Wealth & Asset Consolidation API"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = "sqlite:///./wealth_360.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
