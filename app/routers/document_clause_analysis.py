"""
조항·사유·근거 분석 API Router (Redis)

정부 정책 문서의 조항, 사유, 근거, 예외 조건 등을 분석하는 전문 API
- Models는 src/models/document_analysis.py에서 import
- 헬퍼 함수는 src/utils/document_analysis.py에서 import
- Redis 유틸리티는 src/utils/redis_index.py에서 import
"""

from datetime import datetime

from fastapi import APIRouter

from app.models.document_analysis import (
    ClauseSearchRequest,
    ExceptionClauseRequest,
    ReasonAnalysisRequest,
)
from app.utils import (
    error_response,
    load_index_from_redis,
    ping_redis,
    success_response,
)
from app.utils.document_analysis import (
    compute_confidence_score,
    extract_source_references,
    format_citation,
    get_exception_keywords,
    highlight_exception_sources,
)

router = APIRouter(
    prefix="/document-clause-analysis", tags=["Document Clause Analysis (Redis)"]
)


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/analyze-reason")
async def analyze_decision_reason(request: ReasonAnalysisRequest):
    """
    조치·판단의 구체적 사유 및 근거 분석

    특정 조치나 판단에 대한 구체적인 사유와 근거를 분석하고,
    관련 문단의 출처를 제공합니다.

    Request:
    ```json
    {
        "doc_id": "policy_2024",
        "decision_or_action": "소상공인 지원금 확대",
        "top_k": 10
    }
    ```

    Response:
    - analysis: 사유 및 근거 분석 결과
    - source_references: 참조 소스 정보 (참조 번호, 점수, 텍스트, 메타데이터)
    - citations: 인용 형식 리스트 ("[참조 1: 문단 45]")
    """
    try:
        start_time = datetime.now()

        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        # 쿼리 엔진 생성
        query_engine = index.as_query_engine(
            similarity_top_k=request.top_k, response_mode="tree_summarize"
        )

        # 사유 분석 프롬프트
        query = f"""
            다음 조치 또는 판단에 대한 구체적인 사유와 근거를 분석해주세요:

            **조치/판단**: {request.decision_or_action}

            아래 형식으로 답변해주세요:

            ## 1. 주요 사유
            - [사유 1]
            - [사유 2]
            ...

            ## 2. 근거 및 배경
            - [근거 1]
            - [근거 2]
            ...

            ## 3. 관련 조항 또는 정책
            - [조항/정책 1]
            - [조항/정책 2]
            ...

            각 항목에는 문서의 구체적인 내용을 인용하여 근거를 명확히 해주세요.
            """

        # 쿼리 실행
        response = query_engine.query(query)

        # 소스 참조 추출
        source_references = extract_source_references(response.source_nodes, top_n=5)

        # 인용 형식 생성
        citations = [format_citation(ref) for ref in source_references]

        end_time = datetime.now()

        return success_response(
            data={
                "doc_id": request.doc_id,
                "decision_or_action": request.decision_or_action,
                "analysis": str(response),
                "source_references": source_references,
                "citations": citations,
                "total_sources_found": len(response.source_nodes),
                "confidence_score": compute_confidence_score(response.source_nodes),
            },
            message="사유 및 근거 분석이 완료되었습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            metadata={
                "analysis_type": "reason_analysis",
                "top_k_used": request.top_k,
            },
        )

    except ValueError as e:
        return error_response(
            message="문서를 찾을 수 없습니다.",
            error=str(e),
            status_code=404,
        )
    except Exception as e:
        return error_response(
            message="사유 분석 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.post("/find-exceptions")
async def find_exception_clauses(request: ExceptionClauseRequest):
    """
    예외 조항 및 단서 조항 검색

    특정 상황에 대한 예외 조항, 단서 조항, 특례 규정을 검색합니다.
    "다만", "단서", "예외적으로", "제외", "이 경우", "특례", "불구하고" 등의
    키워드를 포함한 조항을 우선적으로 찾습니다.

    Request:
    ```json
    {
        "doc_id": "policy_2024",
        "situation": "경영난으로 인한 폐업",
        "top_k": 10
    }
    ```

    Response:
    - exception_analysis: 예외 조항 분석 결과
    - highlighted_sources: 예외 키워드가 포함된 소스 (found_exception_keywords 포함)
    - all_source_references: 전체 소스 참조
    - exception_clauses_found: 발견된 예외 조항 개수
    """
    try:
        start_time = datetime.now()

        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        # 쿼리 엔진 생성
        query_engine = index.as_query_engine(
            similarity_top_k=request.top_k, response_mode="tree_summarize"
        )

        # 예외 키워드
        exception_keywords = get_exception_keywords()

        # 예외 조항 검색 프롬프트
        query = f"""
다음 상황에 대해 적용 가능한 예외 조항, 단서 조항, 특례 규정을 찾아주세요:

**상황**: {request.situation}

문서에서 다음과 같은 표현을 포함한 조항을 우선적으로 찾아주세요:
- "다만", "단서", "예외적으로", "제외하고", "이 경우"
- "특례", "특별한 경우", "별도로 정하는"
- "~을 제외하고는", "~에도 불구하고"

발견된 예외 조항을 아래 형식으로 정리해주세요:

## 발견된 예외 조항

### 1. [예외 조항 제목]
[예외 조항 내용 전문 또는 요약]

### 2. [예외 조항 제목]
[예외 조항 내용 전문 또는 요약]
...

각 조항에 대해 어떤 예외나 특례가 적용되는지 명확히 설명해주세요.
"""

        # 쿼리 실행
        response = query_engine.query(query)

        # 소스 참조 추출
        source_references = extract_source_references(response.source_nodes, top_n=7)

        # 예외 키워드가 포함된 소스만 하이라이팅
        highlighted_sources = highlight_exception_sources(
            source_references, exception_keywords
        )

        end_time = datetime.now()

        return success_response(
            data={
                "doc_id": request.doc_id,
                "situation": request.situation,
                "exception_analysis": str(response),
                "highlighted_sources": highlighted_sources,
                "all_source_references": source_references,
                "exception_clauses_found": len(highlighted_sources),
                "confidence_score": compute_confidence_score(response.source_nodes),
            },
            message="예외 조항 검색이 완료되었습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            metadata={
                "analysis_type": "exception_clause_search",
                "exception_keywords_searched": exception_keywords,
            },
        )

    except ValueError as e:
        return error_response(
            message="문서를 찾을 수 없습니다.",
            error=str(e),
            status_code=404,
        )
    except Exception as e:
        return error_response(
            message="예외 조항 검색 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.post("/search-clause")
async def search_specific_clause(request: ClauseSearchRequest):
    """
    특정 조항 검색

    조항 번호나 키워드로 특정 조항을 검색합니다.
    예: "제1조", "제12조", "부칙", "별표", "시행령" 등

    Request:
    ```json
    {
        "doc_id": "policy_2024",
        "clause_keyword": "제1조",
        "top_k": 5
    }
    ```

    Response:
    - search_results: 검색 결과
    - source_references: 참조 소스 정보
    - total_matches: 매칭된 총 개수
    """
    try:
        start_time = datetime.now()

        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        # 쿼리 엔진 생성
        query_engine = index.as_query_engine(
            similarity_top_k=request.top_k, response_mode="compact"
        )

        # 조항 검색 프롬프트
        query = f"""
문서에서 "{request.clause_keyword}"에 해당하는 조항을 찾아주세요.

해당 조항의 전문(全文)을 정확하게 인용해주세요.
조항 번호, 제목, 내용을 모두 포함해서 답변해주세요.
"""

        # 쿼리 실행
        response = query_engine.query(query)

        # 소스 참조 추출
        source_references = extract_source_references(
            response.source_nodes, top_n=request.top_k
        )

        end_time = datetime.now()

        return success_response(
            data={
                "doc_id": request.doc_id,
                "clause_keyword": request.clause_keyword,
                "search_results": str(response),
                "source_references": source_references,
                "total_matches": len(response.source_nodes),
                "confidence_score": compute_confidence_score(response.source_nodes),
            },
            message="조항 검색이 완료되었습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            metadata={
                "analysis_type": "clause_search",
                "top_k_used": request.top_k,
            },
        )

    except ValueError as e:
        return error_response(
            message="문서를 찾을 수 없습니다.",
            error=str(e),
            status_code=404,
        )
    except Exception as e:
        return error_response(
            message="조항 검색 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.get("/health")
async def health_check():
    """
    조항 분석 API Health Check

    Redis 연결 상태 확인
    """
    redis_connected = await ping_redis()

    return success_response(
        data={
            "status": "healthy" if redis_connected else "degraded",
            "redis_connected": redis_connected,
        },
        message=(
            "조항 분석 API가 정상 작동 중입니다."
            if redis_connected
            else "Redis 연결 오류"
        ),
    )
