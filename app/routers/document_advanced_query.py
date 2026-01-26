"""
Advanced Query Analysis Router

고급 쿼리 분석 기능:
1. 질문 분해 (Query Decomposition)
2. 다중 검색 (Multi-Retrieval): 표/본문/JSON 경로 분리
3. 병렬 검색 및 결과 통합

Author: Claude Sonnet 4.5
Created: 2026-01-16
"""

from datetime import datetime

from fastapi import APIRouter

from app.models.document_analysis import AdvancedQueryRequest
from app.utils import (
    decompose_query_internal,
    error_response,
    integrate_all_results,
    multi_retrieval_internal,
    ping_redis,
    success_response,
)

router = APIRouter(
    prefix="/document-advanced-query",
    tags=["Document Advanced Query Analysis"],
)


# ============================================================================
# 질문 분해 엔드포인트
# ============================================================================


@router.post("/decompose-query")
async def decompose_query(request: AdvancedQueryRequest):
    """
    질문 분해 (Query Decomposition)

    복잡한 질문을 여러 개의 단순한 서브 질문으로 분해합니다.

    예시:
    - 원본 질문: "징계 종류와 각각의 처벌 수위를 비교하고, 가장 엄격한 처분은 무엇인가요?"
    - 분해 결과:
      1. 징계 종류에는 어떤 것들이 있나요?
      2. 각 징계의 처벌 수위는 어떻게 되나요?
      3. 가장 엄격한 처분은 무엇인가요?

    Returns:
        - sub_queries: 분해된 서브 질문 리스트
        - reasoning: 분해 이유
    """
    try:
        data = await decompose_query_internal(request.doc_id, request.query)
        return success_response(
            data=data,
            message=f"질문이 {data['num_sub_queries']}개의 서브 질문으로 분해되었습니다.",
        )

    except Exception as e:
        return error_response(f"질문 분해 실패: {str(e)}", 500)


# ============================================================================
# 다중 검색 엔드포인트 (표/본문/JSON 경로 분리)
# ============================================================================


@router.post("/multi-retrieval")
async def multi_retrieval(request: AdvancedQueryRequest):
    """
    다중 검색 (Multi-Retrieval)

    표/본문/JSON 경로를 분리하여 병렬 검색하고 결과를 통합합니다.

    검색 전략:
    1. 표 검색: 구조화된 데이터 (기준표, 비교표 등)
    2. 본문 검색: 설명문, 조항, 해설
    3. JSON 추출: 특정 필드 직접 추출

    Returns:
        - table_results: 표 검색 결과
        - text_results: 본문 검색 결과
        - json_results: JSON 추출 결과
        - integrated_answer: 통합 답변
    """
    try:
        data = await multi_retrieval_internal(
            doc_id=request.doc_id,
            query=request.query,
            use_table_search=request.use_table_search,
            use_text_search=request.use_text_search,
            use_json_extraction=request.use_json_extraction,
            top_k=request.top_k,
        )
        return success_response(
            data=data,
            message="다중 검색이 완료되었습니다.",
        )

    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"다중 검색 실패: {str(e)}", 500)


# ============================================================================
# 통합 엔드포인트 (질문 분해 + 다중 검색)
# ============================================================================


@router.post("/advanced-query")
async def advanced_query(request: AdvancedQueryRequest):
    """
    고급 쿼리 분석 (질문 분해 + 다중 검색)

    1단계: 질문 분해
    2단계: 각 서브 질문에 대해 다중 검색
    3단계: 모든 결과 통합

    Returns:
        - decomposition: 질문 분해 결과
        - sub_query_results: 각 서브 질문의 검색 결과
        - final_answer: 최종 통합 답변
    """
    try:
        # 1단계: 질문 분해
        decomposition_data = await decompose_query_internal(
            doc_id=request.doc_id,
            query=request.query,
        )

        # 2단계: 각 서브 질문에 대해 다중 검색
        sub_queries = decomposition_data.get("sub_queries", [])
        sub_query_results = []

        for sub_query in sub_queries:
            sub_result = await multi_retrieval_internal(
                doc_id=request.doc_id,
                query=sub_query,
                use_table_search=request.use_table_search,
                use_text_search=request.use_text_search,
                use_json_extraction=request.use_json_extraction,
                top_k=request.top_k,
            )
            sub_query_results.append(sub_result)

        # 3단계: 최종 답변 통합
        final_answer = await integrate_all_results(
            original_query=request.query,
            sub_queries=sub_queries,
            sub_query_results=sub_query_results,
        )

        return success_response(
            data={
                "doc_id": request.doc_id,
                "original_query": request.query,
                "decomposition": {
                    "sub_queries": sub_queries,
                    "num_sub_queries": len(sub_queries),
                    "reasoning": decomposition_data.get("reasoning", ""),
                },
                "sub_query_results": sub_query_results,
                "final_answer": final_answer,
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                },
            },
            message="고급 쿼리 분석이 완료되었습니다.",
        )

    except Exception as e:
        return error_response(f"고급 쿼리 분석 실패: {str(e)}", 500)


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def health_check():
    """
    Health Check

    Returns:
        서비스 상태
    """
    redis_status = await ping_redis()

    return success_response(
        data={
            "status": "healthy",
            "redis_connected": redis_status,
            "service": "document_advanced_query",
            "features": [
                "query_decomposition",
                "multi_retrieval",
                "table_search",
                "text_search",
                "json_extraction",
                "integrated_search",
            ],
        },
        message="고급 쿼리 분석 API가 정상 작동 중입니다.",
    )
