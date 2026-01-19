"""
표·항목 기반 분석 API Router (Redis)

정부 문서의 표, 기준표, 비교표 등을 분석하는 전문 API
- Models는 src/models/document_analysis.py에서 import
- Redis 유틸리티는 src/utils/redis_index.py에서 import
"""

from datetime import datetime

from fastapi import APIRouter

from src.models.document_analysis import (
    TableImportanceRequest,
    TableComparisonRequest,
)
from src.utils import (
    success_response,
    error_response,
    ping_redis,
    load_index_from_redis,
    compute_confidence_score,
)


router = APIRouter(
    prefix="/document-table-analysis", tags=["Document Table Analysis (Redis)"]
)


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/analyze-table-importance")
async def analyze_table_importance(request: TableImportanceRequest):
    """
    표에서 가장 중요한 기준 N개 추출

    예시:
    - "징계 기준표에서 가장 중요한 기준 3가지"
    - "처분 사유별 기준표에서 핵심 항목"

    Returns:
    - important_criteria: 중요한 기준 리스트 (순위, 기준명, 설명)
    - reasoning: LLM의 선정 근거
    - source_references: 참조 소스
    """
    try:
        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        # 쿼리 엔진 생성 (표 중요도 분석에 최적화)
        query_engine = index.as_query_engine(
            similarity_top_k=request.top_k,
            response_mode="tree_summarize",  # 계층적 요약으로 표 전체 파악
        )

        # 표 맥락 포함 쿼리 생성
        table_context_phrase = (
            f"'{request.table_context}'의 " if request.table_context else ""
        )

        query = f"""
문서에 있는 {table_context_phrase}표에서 가장 중요한 기준 {request.top_n}가지를 찾아주세요.

각 기준에 대해 다음 정보를 제공해주세요:
1. 순위 (1위, 2위, 3위...)
2. 기준명
3. 중요한 이유 (구체적으로)
4. 해당 기준이 표에서 어떻게 표현되어 있는지

출력 형식:
[1위] 기준명: ...
중요한 이유: ...
표 내용: ...

[2위] 기준명: ...
(이하 동일)
"""

        # 쿼리 실행
        response = query_engine.query(query)

        # 소스 참조 추출
        source_nodes = getattr(response, "source_nodes", [])
        references = []

        for idx, node in enumerate(
            source_nodes[: request.top_n * 2], 1
        ):  # 기준당 2개 소스
            node_text = getattr(node.node, "text", "")
            node_metadata = getattr(node.node, "metadata", {})

            references.append(
                {
                    "reference_number": idx,
                    "score": round(float(node.score or 0.0), 4),
                    "text_preview": (
                        node_text[:500] + "..." if len(node_text) > 500 else node_text
                    ),
                    "metadata": {
                        "page": node_metadata.get("page_label", "Unknown"),
                        "chunk_index": node_metadata.get("chunk_index", 0),
                    },
                }
            )

        return success_response(
            data={
                "doc_id": request.doc_id,
                "table_context": request.table_context or "전체 표",
                "top_n": request.top_n,
                "analysis_result": str(response),
                "source_references": references,
                "confidence_score": compute_confidence_score(source_nodes),
                "metadata": {
                    "total_nodes_searched": len(source_nodes),
                    "file_name": metadata.get("file_name", "Unknown"),
                    "analyzed_at": datetime.now().isoformat(),
                },
            },
            message=f"표 중요도 분석 완료 (상위 {request.top_n}개)",
        )

    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"표 중요도 분석 실패: {str(e)}", 500)


@router.post("/compare-table-criteria")
async def compare_table_criteria(request: TableComparisonRequest):
    """
    표의 조건들을 비교하여 가장 엄격한/관대한 기준 도출

    예시:
    - "징계 기준표에서 가장 엄격한 조건은?"
    - "처분 사유별로 비교했을 때 가장 강한 처벌은?"

    Returns:
    - comparison_result: 비교 결과 (가장 엄격한 기준, 이유)
    - criteria_list: 비교된 조건 리스트
    - source_references: 참조 소스
    """
    try:
        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        # 쿼리 엔진 생성 (표 비교에 최적화)
        query_engine = index.as_query_engine(
            similarity_top_k=request.top_k,
            response_mode="compact",  # 비교를 위한 효율적 모드
        )

        # 표 맥락 포함 쿼리 생성
        table_context_phrase = (
            f"'{request.table_context}'의 " if request.table_context else ""
        )

        query = f"""
문서에 있는 {table_context_phrase}표에 나온 조건들을 '{request.comparison_aspect}' 관점에서 비교해주세요.

다음 정보를 제공해주세요:
1. 가장 {request.comparison_aspect} 기준은 무엇인가요?
2. 그 기준이 가장 {request.comparison_aspect} 이유는 무엇인가요?
3. 다른 기준들과 비교했을 때 구체적인 차이점은?
4. 표에서 해당 조건이 어떻게 표현되어 있는지

출력 형식:
[가장 {request.comparison_aspect} 기준]
기준명: ...
이유: ...
표 내용: ...

[다른 기준들과의 비교]
- 기준 A: ...
- 기준 B: ...
(상대적 {request.comparison_aspect} 정도 설명)
"""

        # 쿼리 실행
        response = query_engine.query(query)

        # 소스 참조 추출
        source_nodes = getattr(response, "source_nodes", [])
        references = []

        for idx, node in enumerate(source_nodes[:10], 1):  # 상위 10개 소스
            node_text = getattr(node.node, "text", "")
            node_metadata = getattr(node.node, "metadata", {})

            references.append(
                {
                    "reference_number": idx,
                    "score": round(float(node.score or 0.0), 4),
                    "text_preview": (
                        node_text[:500] + "..." if len(node_text) > 500 else node_text
                    ),
                    "metadata": {
                        "page": node_metadata.get("page_label", "Unknown"),
                        "chunk_index": node_metadata.get("chunk_index", 0),
                    },
                }
            )

        return success_response(
            data={
                "doc_id": request.doc_id,
                "table_context": request.table_context or "전체 표",
                "comparison_aspect": request.comparison_aspect,
                "comparison_result": str(response),
                "source_references": references,
                "confidence_score": compute_confidence_score(source_nodes),
                "metadata": {
                    "total_nodes_searched": len(source_nodes),
                    "file_name": metadata.get("file_name", "Unknown"),
                    "analyzed_at": datetime.now().isoformat(),
                },
            },
            message=f"표 조건 비교 완료 ('{request.comparison_aspect}' 관점)",
        )

    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"표 조건 비교 실패: {str(e)}", 500)


@router.get("/health")
async def health_check():
    """
    표 분석 API Health Check
    """
    redis_connected = await ping_redis()

    return success_response(
        data={
            "status": "healthy",
            "redis_connected": redis_connected,
            "service": "document_table_analysis",
            "features": [
                "table_importance_analysis",
                "table_criteria_comparison",
            ],
            "timestamp": datetime.now().isoformat(),
        },
        message="표 분석 API가 정상 작동 중입니다.",
    )
