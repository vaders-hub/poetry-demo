"""
Advanced Query Helper Functions

고급 쿼리 분석을 위한 헬퍼 함수 모음:
- 질문 분해 (Query Decomposition)
- 다중 검색 (Multi-Retrieval)
- 결과 통합 (Result Integration)

Author: Claude Sonnet 4.5
Created: 2026-01-16
"""

import asyncio
import warnings
from datetime import datetime
from typing import Dict, Any, List

# LlamaIndex 내부의 Pydantic validate_default 경고 억제
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=".*validate_default.*",
    module="pydantic._internal._generate_schema",
)

from llama_index.core import Settings, VectorStoreIndex

from app.utils.redis_index import load_index_from_redis
from app.utils.document_analysis import compute_confidence_score


# ============================================================================
# 파싱 함수
# ============================================================================


def parse_decomposed_queries(response_text: str) -> Dict[str, Any]:
    """
    질문 분해 응답 파싱

    Args:
        response_text: LLM 응답 텍스트

    Returns:
        분해된 질문 데이터
    """
    decomposition_data: Dict[str, Any] = {"sub_queries": [], "reasoning": ""}

    lines = response_text.split("\n")
    current_query = ""

    for line in lines:
        line = line.strip()

        # 서브 질문 시작
        if line.startswith("[서브 질문"):
            current_query = ""
            continue

        # 질문 내용
        if line.startswith("질문:"):
            current_query = line.replace("질문:", "").strip()
            if current_query:
                decomposition_data["sub_queries"].append(current_query)
            continue

        # 분해 이유
        if line.startswith("[분해 이유]"):
            continue

        if line.startswith("이유:"):
            decomposition_data["reasoning"] = line.replace("이유:", "").strip()
            continue

    return decomposition_data


# ============================================================================
# 검색 함수
# ============================================================================


async def search_tables(
    index: VectorStoreIndex, query: str, top_k: int
) -> Dict[str, Any]:
    """
    표 검색

    구조화된 데이터 (기준표, 비교표 등)를 검색합니다.
    """
    table_query = f"""
다음 질문에 대한 답변을 **표나 기준표**에서 찾아주세요:

질문: {query}

표/기준표에서만 정보를 추출해 주세요.
일반 본문이나 설명문은 제외하고, 구조화된 표 데이터만 참고해 주세요.
"""

    query_engine = index.as_query_engine(
        similarity_top_k=top_k, response_mode="tree_summarize"
    )
    response = query_engine.query(table_query)

    return {
        "search_type": "table",
        "answer": str(response),
        "confidence_score": compute_confidence_score(
            getattr(response, "source_nodes", []), top_n=3
        ),
        "source_nodes": [
            {
                "text_preview": (
                    node.node.text[:200] + "..."
                    if len(node.node.text) > 200
                    else node.node.text
                ),
                "score": round(float(node.score or 0.0), 4),
            }
            for node in getattr(response, "source_nodes", [])[:3]
        ],
    }


async def search_text(
    index: VectorStoreIndex, query: str, top_k: int
) -> Dict[str, Any]:
    """
    본문 검색

    설명문, 조항, 해설을 검색합니다.
    """
    text_query = f"""
다음 질문에 대한 답변을 **본문이나 설명문**에서 찾아주세요:

질문: {query}

조항, 해설, 설명문 등 일반 텍스트에서 정보를 추출해 주세요.
표나 기준표는 제외해 주세요.
"""

    query_engine = index.as_query_engine(
        similarity_top_k=top_k, response_mode="tree_summarize"
    )
    response = query_engine.query(text_query)

    return {
        "search_type": "text",
        "answer": str(response),
        "confidence_score": compute_confidence_score(
            getattr(response, "source_nodes", []), top_n=3
        ),
        "source_nodes": [
            {
                "text_preview": (
                    node.node.text[:200] + "..."
                    if len(node.node.text) > 200
                    else node.node.text
                ),
                "score": round(float(node.score or 0.0), 4),
            }
            for node in getattr(response, "source_nodes", [])[:3]
        ],
    }


async def extract_json_paths(
    index: VectorStoreIndex, query: str, top_k: int
) -> Dict[str, Any]:
    """
    JSON 경로 추출

    특정 필드를 JSON 경로 형태로 추출합니다.
    """
    json_query = f"""
다음 질문에 대한 답변을 **JSON 경로** 형태로 추출해 주세요:

질문: {query}

출력 형식:
{{
  "field_1": "value_1",
  "field_2": "value_2",
  ...
}}

예시:
{{
  "징계_종류": ["파면", "해임", "정직", "감봉", "견책"],
  "가장_엄격한_처분": "파면",
  "파면_특징": "퇴직급여 미지급, 5년간 재임용 제한"
}}
"""

    query_engine = index.as_query_engine(
        similarity_top_k=top_k, response_mode="tree_summarize"
    )
    response = query_engine.query(json_query)

    return {
        "search_type": "json",
        "answer": str(response),
        "confidence_score": compute_confidence_score(
            getattr(response, "source_nodes", []), top_n=3
        ),
        "source_nodes": [
            {
                "text_preview": (
                    node.node.text[:200] + "..."
                    if len(node.node.text) > 200
                    else node.node.text
                ),
                "score": round(float(node.score or 0.0), 4),
            }
            for node in getattr(response, "source_nodes", [])[:3]
        ],
    }


# ============================================================================
# 결과 통합 함수
# ============================================================================


async def integrate_results(
    query: str,
    table_results: Dict[str, Any] | None,
    text_results: Dict[str, Any] | None,
    json_results: Dict[str, Any] | None,
) -> str:
    """
    다중 검색 결과 통합

    표/본문/JSON 검색 결과를 하나의 답변으로 통합합니다.
    """
    integration_prompt = f"""
다음은 여러 검색 경로에서 얻은 정보입니다. 이를 통합하여 하나의 명확한 답변을 작성해 주세요.

원본 질문: {query}

"""

    if table_results:
        integration_prompt += f"""
[표 검색 결과]
{table_results.get('answer', 'N/A')}

"""

    if text_results:
        integration_prompt += f"""
[본문 검색 결과]
{text_results.get('answer', 'N/A')}

"""

    if json_results:
        integration_prompt += f"""
[JSON 추출 결과]
{json_results.get('answer', 'N/A')}

"""

    integration_prompt += """
위 정보들을 종합하여 다음 가이드에 따라 답변을 작성해 주세요:
1. 정보의 중복을 제거하고 일관성 있게 통합
2. 표 데이터와 본문 설명을 자연스럽게 연결
3. JSON 구조 정보를 활용하여 명확하게 정리
4. 최종 답변은 간결하고 이해하기 쉽게 작성
"""

    llm = Settings.llm
    response = await llm.acomplete(integration_prompt)

    return str(response)


async def integrate_all_results(
    original_query: str,
    sub_queries: List[str],
    sub_query_results: List[Dict[str, Any]],
) -> str:
    """
    모든 서브 질문 결과를 최종 답변으로 통합

    Args:
        original_query: 원본 질문
        sub_queries: 분해된 서브 질문 리스트
        sub_query_results: 각 서브 질문의 검색 결과

    Returns:
        최종 통합 답변
    """
    integration_prompt = f"""
다음은 원본 질문을 여러 개의 서브 질문으로 분해하고, 각 서브 질문에 대해 검색한 결과입니다.
이를 통합하여 원본 질문에 대한 명확하고 완전한 답변을 작성해 주세요.

원본 질문: {original_query}

"""

    for i, (sub_query, result) in enumerate(zip(sub_queries, sub_query_results), 1):
        integration_prompt += f"""
[서브 질문 {i}]
질문: {sub_query}

통합 답변: {result.get('integrated_answer', 'N/A')}

"""

    integration_prompt += """
위 서브 질문들의 답변을 종합하여 원본 질문에 대한 최종 답변을 작성해 주세요:
1. 모든 서브 답변을 논리적으로 연결
2. 중복 정보 제거
3. 일관성 있는 흐름으로 재구성
4. 원본 질문에 직접 답하는 형태로 작성
"""

    llm = Settings.llm
    response = await llm.acomplete(integration_prompt)

    return str(response)


# ============================================================================
# 메인 헬퍼 함수
# ============================================================================


async def decompose_query_internal(doc_id: str, query: str) -> Dict[str, Any]:
    """
    질문 분해 내부 로직

    복잡한 질문을 여러 개의 단순한 서브 질문으로 분해합니다.

    Args:
        doc_id: 문서 ID
        query: 원본 질문

    Returns:
        분해된 질문 데이터 딕셔너리
    """
    # 질문 분해 프롬프트
    decomposition_prompt = f"""
다음 질문을 여러 개의 단순한 서브 질문으로 분해해 주세요.

원본 질문: {query}

분해 가이드:
1. 복잡한 질문은 2-5개의 단순한 질문으로 분해
2. 각 서브 질문은 독립적으로 답변 가능해야 함
3. 서브 질문들을 모두 답변하면 원본 질문의 답변이 가능해야 함
4. 질문 순서는 논리적 흐름을 유지

다음 형식으로 작성해 주세요:

[서브 질문 1]
질문: ...

[서브 질문 2]
질문: ...

[서브 질문 3]
질문: ...

[분해 이유]
이유: 왜 이렇게 분해했는지 설명
"""

    # LLM 호출
    llm = Settings.llm
    response = await llm.acomplete(decomposition_prompt)
    response_text = str(response)

    # 응답 파싱
    decomposition_data = parse_decomposed_queries(response_text)

    return {
        "doc_id": doc_id,
        "original_query": query,
        "sub_queries": decomposition_data.get("sub_queries", []),
        "num_sub_queries": len(decomposition_data.get("sub_queries", [])),
        "reasoning": decomposition_data.get("reasoning", ""),
        "full_text": response_text,
    }


async def multi_retrieval_internal(
    doc_id: str,
    query: str,
    use_table_search: bool = True,
    use_text_search: bool = True,
    use_json_extraction: bool = False,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    다중 검색 내부 로직

    표/본문/JSON 경로를 분리하여 병렬 검색하고 결과를 통합합니다.

    Args:
        doc_id: 문서 ID
        query: 검색 질문
        use_table_search: 표 검색 사용 여부
        use_text_search: 본문 검색 사용 여부
        use_json_extraction: JSON 추출 사용 여부
        top_k: 검색 결과 수

    Returns:
        다중 검색 결과 딕셔너리
    """
    # Redis에서 인덱스 로드
    index, metadata = await load_index_from_redis(doc_id)

    # 병렬 검색 태스크 생성
    tasks = []

    if use_table_search:
        tasks.append(search_tables(index, query, top_k))
    else:
        tasks.append(asyncio.sleep(0))  # Dummy task

    if use_text_search:
        tasks.append(search_text(index, query, top_k))
    else:
        tasks.append(asyncio.sleep(0))  # Dummy task

    if use_json_extraction:
        tasks.append(extract_json_paths(index, query, top_k))
    else:
        tasks.append(asyncio.sleep(0))  # Dummy task

    # 병렬 실행
    results = await asyncio.gather(*tasks)

    # 결과 언팩
    table_results = results[0] if use_table_search else None
    text_results = results[1] if use_text_search else None
    json_results = results[2] if use_json_extraction else None

    # 결과 통합
    integrated_answer = await integrate_results(
        query=query,
        table_results=table_results,
        text_results=text_results,
        json_results=json_results,
    )

    return {
        "doc_id": doc_id,
        "query": query,
        "search_strategies": {
            "table_search": use_table_search,
            "text_search": use_text_search,
            "json_extraction": use_json_extraction,
        },
        "table_results": table_results,
        "text_results": text_results,
        "json_results": json_results,
        "integrated_answer": integrated_answer,
        "metadata": {
            "file_name": metadata.get("file_name", "Unknown"),
            "searched_at": datetime.now().isoformat(),
        },
    }
