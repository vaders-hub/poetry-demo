from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.main import client, llm, chain

class Query(BaseModel):
    prompt: str
    min_length: int = 3
    max_tokens: int = 50

router = APIRouter(prefix="/llm", tags=["llm"])

@router.get("/sync/chat")
def sync_chat(query: str):
    response = chain.invoke({"query": query})
    return response

@router.get("/async/chat")
async def async_chat(query: Query):
    response = await chain.ainvoke({"query": query.prompt})
    return response

@router.get("/async/chat-stream")
async def async_chat(query: Query):
    answer = llm.stream("대한민국의 아름다운 관광지 10곳과 주소를 알려주세요!")
    for token in answer:
        response = token.content
    return response

@router.get("/async/generate-text")
async def async_chat(query: str):
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=query,
        )
        return {"text": response.output_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/complete")
async def complete_text(prompt: str):
    return llm(prompt)
