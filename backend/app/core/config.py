import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = "Orbit Station"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    database_url: str = Field(default="sqlite:///./orbit_station.db", alias="DATABASE_URL")
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    
    # OIDC Configuration
    oidc_issuer_url: str = Field(default="http://127.0.0.1:8080/realms/orbit-station", alias="OIDC_ISSUER_URL")
    oidc_client_id: str = Field(default="orbit-station-app", alias="OIDC_CLIENT_ID")
    oidc_client_secret: str = Field(default="", alias="OIDC_CLIENT_SECRET")
    oidc_audience: str = Field(default="orbit-station-app", alias="OIDC_AUDIENCE")
    
    # Optional LLM Advisory Configuration
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_provider: str = Field(default="openai-compatible", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
