from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.main import chain, client, llm
from app.utils import error_response, success_response


class Query(BaseModel):
    prompt: str
    min_length: int = 3
    max_tokens: int = 50


router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/sync/chat")
def sync_chat(query: str):
    """동기 채팅 (LangChain)"""
    try:
        start_time = datetime.now()
        response = chain.invoke({"query": query})
        end_time = datetime.now()

        return success_response(
            data={"response": response},
            message="채팅 응답이 생성되었습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
        )
    except Exception as e:
        return error_response(
            message="채팅 응답 생성 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.get("/async/chat")
async def async_chat(query: Query):
    """비동기 채팅 (LangChain)"""
    try:
        start_time = datetime.now()
        response = await chain.ainvoke({"query": query.prompt})
        end_time = datetime.now()

        return success_response(
            data={"response": response},
            message="채팅 응답이 생성되었습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
        )
    except Exception as e:
        return error_response(
            message="채팅 응답 생성 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.get("/async/chat-stream")
async def async_chat_stream(query: str):
    """스트리밍 채팅 (OpenAI)"""

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
async def async_generate_text(query: str):
    """텍스트 생성 (OpenAI)"""
    try:
        start_time = datetime.now()

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": query}],
        )

        end_time = datetime.now()

        return success_response(
            data={
                "text": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            },
            message="텍스트가 생성되었습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
        )
    except Exception as e:
        return error_response(
            message="텍스트 생성 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.get("/complete")
async def complete_text(prompt: str):
    """텍스트 완성 (LangChain LLM)"""
    try:
        start_time = datetime.now()
        response = llm(prompt)
        end_time = datetime.now()

        return success_response(
            data={"completion": response},
            message="텍스트 완성이 완료되었습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
        )
    except Exception as e:
        return error_response(
            message="텍스트 완성 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )
