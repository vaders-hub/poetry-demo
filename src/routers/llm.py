from fastapi import APIRouter, Query
from src.main import llm, chain

router = APIRouter(prefix="/llm", tags=["llm"])

@router.get("/sync/chat")
def sync_chat(query: str = Query(None, min_length=3, max_length=50)):
    response = chain.invoke({"query": query})
    return response

@router.get("/async/chat")
async def async_chat(query: str = Query(None, min_length=3, max_length=50)):
    response = await chain.ainvoke({"query": query})
    return response

@router.get("/complete")
async def complete_text(prompt: str):
    return llm(prompt)
