from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # 사용자에게 정적 파일을 제공

from app.db import sessionmanager
from app.configs.llama_index import init_llama_index_settings

from app.routers import customers
from app.routers import users
from app.routers import llm
from app.routers import rag
from app.routers import mcp
from app.routers import lcel_examples
from app.routers import llamaindex_examples
from app.routers import document_analysis
from app.routers import document_upload
from app.routers import document_analysis_redis
from app.routers import document_clause_analysis
from app.routers import document_table_analysis
from app.routers import document_report_generation
from app.routers import document_advanced_query


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    # Initialize LlamaIndex settings on startup
    init_llama_index_settings()

    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)

origins = ["http://localhost:3000", "localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(users.router)
app.include_router(llm.router)
app.include_router(rag.router)
app.include_router(mcp.router)
app.include_router(lcel_examples.router)
app.include_router(llamaindex_examples.router)
app.include_router(document_analysis.router)
app.include_router(document_upload.router)  # 공통 문서 업로드 라우터
app.include_router(document_analysis_redis.router)
app.include_router(document_clause_analysis.router)
app.include_router(document_table_analysis.router)
app.include_router(document_report_generation.router)
app.include_router(document_advanced_query.router)

# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your todo list."}
