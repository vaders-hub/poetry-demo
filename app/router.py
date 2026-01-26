from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.configs.llama_index import init_llama_index_settings
from app.db import sessionmanager
from app.routers import (
    customers,
    document_advanced_query,
    document_analysis,
    document_analysis_redis,
    document_clause_analysis,
    document_report_generation,
    document_table_analysis,
    document_upload,
    lcel_examples,
    llamaindex_examples,
    llm,
    mcp,
    rag,
    users,
)


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


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint for Docker and load balancer."""
    return {"status": "healthy"}
