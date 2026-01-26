"""
LlamaIndex Configuration

LlamaIndex 전역 설정을 중앙에서 관리합니다.
애플리케이션 시작 시 한 번만 초기화됩니다.

Usage:
    from app.configs.llama_index import init_llama_index_settings

    # FastAPI lifespan 또는 애플리케이션 시작 시 호출
    init_llama_index_settings()
"""

import os
import warnings

# LlamaIndex 내부의 Pydantic validate_default 경고 억제
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=".*validate_default.*",
    module="pydantic._internal._generate_schema",
)

from llama_index.core import Settings  # noqa: E402
from llama_index.embeddings.openai import OpenAIEmbedding  # noqa: E402
from llama_index.llms.openai import OpenAI  # noqa: E402

# 기본 설정값
DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_LLM_TEMPERATURE = 0.1
DEFAULT_EMBED_MODEL = "text-embedding-3-small"

_initialized = False


def init_llama_index_settings(
    llm_model: str | None = None,
    llm_temperature: float | None = None,
    embed_model: str | None = None,
) -> None:
    """
    LlamaIndex 전역 설정 초기화

    환경 변수 또는 파라미터로 설정을 커스터마이즈할 수 있습니다.

    환경 변수:
        - LLAMA_INDEX_LLM_MODEL: LLM 모델명 (기본: gpt-4o-mini)
        - LLAMA_INDEX_LLM_TEMPERATURE: LLM temperature (기본: 0.1)
        - LLAMA_INDEX_EMBED_MODEL: 임베딩 모델명 (기본: text-embedding-3-small)

    Args:
        llm_model: LLM 모델명 (선택)
        llm_temperature: LLM temperature (선택)
        embed_model: 임베딩 모델명 (선택)
    """
    global _initialized

    if _initialized:
        return

    # 환경 변수 또는 파라미터 또는 기본값 사용
    model = llm_model or os.getenv("LLAMA_INDEX_LLM_MODEL", DEFAULT_LLM_MODEL)
    temperature = llm_temperature or float(
        os.getenv("LLAMA_INDEX_LLM_TEMPERATURE", str(DEFAULT_LLM_TEMPERATURE))
    )
    embedding = embed_model or os.getenv("LLAMA_INDEX_EMBED_MODEL", DEFAULT_EMBED_MODEL)

    # LlamaIndex 전역 설정
    Settings.llm = OpenAI(model=model, temperature=temperature)
    Settings.embed_model = OpenAIEmbedding(model=embedding)

    _initialized = True


def get_llama_index_settings() -> dict:
    """
    현재 LlamaIndex 설정 반환 (디버깅/상태 확인용)

    Returns:
        현재 설정 딕셔너리
    """
    return {
        "initialized": _initialized,
        "llm_model": getattr(Settings.llm, "model", None) if Settings.llm else None,
        "llm_temperature": (
            getattr(Settings.llm, "temperature", None) if Settings.llm else None
        ),
        "embed_model": (
            getattr(Settings.embed_model, "model_name", None)
            if Settings.embed_model
            else None
        ),
    }
