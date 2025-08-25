import os
from pydantic_settings import BaseSettings
from langchain.chains import LLMChain
from dotenv import load_dotenv

username = "ot"
password = "oracle"
host = "localhost"
port = "1521"
service_name = "freepdb1"

load_dotenv()

class Settings(BaseSettings):
    database_url: str = "oracle+oracledb://ot:oracle@localhost:1521/?service_name=freepdb1"
    echo_sql: bool = True
    test: bool = False
    project_name: str = "My FastAPI project"
    oauth_token_secret: str = "my_dev_secret"
    log_level: str = "DEBUG"
    temperature: int = 0
    model_name: str = "gpt-4o-mini"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")

setting = Settings() # type: ignore

if not setting.openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
