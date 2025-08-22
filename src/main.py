import sys
import logging

import uvicorn
from uvicorn.config import LOGGING_CONFIG

from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import LLMChain

from src.config import setting

log_config = uvicorn.config.LOGGING_CONFIG
LOGGING_CONFIG["formatters"]["access"]["fmt"] = "%(asctime)s - Uvicorn.Access - %(levelname)s - %(message)s"
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - Uvicorn.Default - %(levelname)s - %(message)s"

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG if setting.log_level == "DEBUG" else logging.INFO,
    # handlers=[logging.StreamHandler()]
)

client = OpenAI()
llm = ChatOpenAI(
    temperature=setting.temperature,
    model_name=setting.model_name
)

template = "아래 질문에 대한 답변을 해주세요. \n{query}"
prompt = PromptTemplate.from_template(template=template)
chain = prompt | llm | StrOutputParser()

def start():
    try:
        uvicorn.run("src.router:app", host="0.0.0.0", port=8001, reload=True, log_config=LOGGING_CONFIG)
    except uvicorn.Error as error:
        logging.critical(f"An unhandled uvicorn error occurred: {error}")

if __name__ == "__main__":
    start()
