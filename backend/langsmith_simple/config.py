from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/langsmith_simple"
    redis_url: str = "redis://localhost:6379/0"
    port: int = 8000
    api_key: str = "local-dev-key"
    auth_enabled: bool = False

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""

    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    deployment_logs_dir: str = "/tmp/langsmith-deployments"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
