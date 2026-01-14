import sys
import logging

import uvicorn
from uvicorn.config import LOGGING_CONFIG

from openai import OpenAI

import faiss

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS

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

# Global variables for lazy initialization
client = None
llm = None
chain = None
embeddings = None
vector_store = None


def get_client():
    """Get or create OpenAI client."""
    global client
    if client is None:
        client = OpenAI()
    return client


def get_llm():
    """Get or create ChatOpenAI instance."""
    global llm
    if llm is None:
        llm = ChatOpenAI(
            temperature=setting.temperature,
            model_name=setting.model_name
        )
    return llm


def get_chain():
    """Get or create LangChain chain."""
    global chain
    if chain is None:
        template = "아래 질문에 대한 답변을 해주세요. \n{query}"
        prompt = PromptTemplate.from_template(template=template)
        chain = prompt | get_llm() | StrOutputParser()
    return chain


def get_embeddings():
    """Get or create OpenAI embeddings."""
    global embeddings
    if embeddings is None:
        embeddings = OpenAIEmbeddings(openai_api_key=setting.openai_api_key)
    return embeddings


def get_vector_store():
    """Get or create FAISS vector store."""
    global vector_store
    if vector_store is None:
        emb = get_embeddings()
        # Use a default dimension (1536 for text-embedding-ada-002)
        # This avoids the initial API call
        embedding_dim = 1536
        index = faiss.IndexFlatL2(embedding_dim)

        vector_store = FAISS(
            embedding_function=emb,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
    return vector_store


# Initialize client and llm eagerly (they don't make API calls)
client = OpenAI()
llm = ChatOpenAI(
    temperature=setting.temperature,
    model_name=setting.model_name
)

template = "아래 질문에 대한 답변을 해주세요. \n{query}"
prompt = PromptTemplate.from_template(template=template)
chain = prompt | llm | StrOutputParser()

# Embeddings and vector store are lazy-loaded
embeddings = None
vector_store = None


def start():
    try:
        uvicorn.run("src.router:app", host="0.0.0.0", port=8001, reload=True, log_config=LOGGING_CONFIG)
    except uvicorn.Error as error:
        logging.critical(f"An unhandled uvicorn error occurred: {error}")

if __name__ == "__main__":
    start()
