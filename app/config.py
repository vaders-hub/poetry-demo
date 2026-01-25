import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Database configuration
    db_username: str = os.getenv("DB_USERNAME", "ot")
    db_password: str = os.getenv("DB_PASSWORD", "oracle")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: str = os.getenv("DB_PORT", "1521")
    db_service_name: str = os.getenv("DB_SERVICE_NAME", "freepdb1")

    @property
    def database_url(self) -> str:
        return f"oracle+oracledb://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/?service_name={self.db_service_name}"

    # Application settings
    echo_sql: bool = True
    test: bool = False
    project_name: str = "My FastAPI project"
    oauth_token_secret: str = os.getenv("OAUTH_TOKEN_SECRET", "my_dev_secret")
    log_level: str = "DEBUG"

    # LLM configuration
    temperature: int = 0
    model_name: str = "gpt-4o-mini"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")

setting = Settings() # type: ignore

if not setting.openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
