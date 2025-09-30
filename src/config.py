import os

from pydantic_settings import BaseSettings

username = "ot"
password = "oracle"
host = "localhost"
port = "1521"
service_name = "freepdb1"


class Settings(BaseSettings):
    database_url: str = (
        "oracle+oracledb://ot:oracle@localhost:1521/?service_name=freepdb1"
    )
    echo_sql: bool = True
    test: bool = False
    project_name: str = "My FastAPI project"
    oauth_token_secret: str = "my_dev_secret"
    log_level: str = "DEBUG"


setting = Settings()  # type: ignore

# Database Credentials
