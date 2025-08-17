import os
from pydantic_settings import BaseSettings
from langchain.chains import LLMChain
from dotenv import load_dotenv

username = "ot"
password = "oracle"
host = "localhost"
port = "1521"
service_name = "freepdb1"

class Settings(BaseSettings):
    database_url: str = "oracle+oracledb://ot:oracle@localhost:1521/?service_name=freepdb1"
    echo_sql: bool = True
    test: bool = False
    project_name: str = "My FastAPI project"
    oauth_token_secret: str = "my_dev_secret"
    log_level: str = "DEBUG"
    temperature: int = 0
    model_name: str = "gpt-4o-mini"

load_dotenv()
setting = Settings() # type: ignore

# Database Credentials
