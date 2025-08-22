from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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
async def async_chat(query: str):
    def event_generator():
        with client.chat.completions.stream(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": query}],
        ) as stream:
            for event in stream:
                if event.type == "content.delta":
                    yield event.delta
            yield "[END]"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

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
