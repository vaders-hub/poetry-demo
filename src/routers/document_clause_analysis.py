"""
조항·사유·근거 분석 API Router (Redis)

정부 정책 문서의 조항, 사유, 근거, 예외 조건 등을 분석하는 전문 API
- Models는 src/models/document_analysis.py에서 import
- 헬퍼 함수는 src/utils/document_analysis.py에서 import
"""

import os
import pickle
import base64
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from src.models.document_analysis import (
    DocumentUploadRequest,
    ReasonAnalysisRequest,
    ExceptionClauseRequest,
    ClauseSearchRequest,
)
from src.utils import (
    success_response,
    error_response,
    get_redis_client,
    ping_redis,
)
from src.utils.document_analysis import (
    load_pdf_from_path,
    create_hierarchical_index,
    extract_source_references,
    format_citation,
    get_exception_keywords,
    highlight_exception_sources,
)


router = APIRouter(
    prefix="/document-clause-analysis", tags=["Document Clause Analysis (Redis)"]
)

# LlamaIndex 설정
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")


# ============================================================================
# Redis 저장/로드 헬퍼
# ============================================================================


async def load_index_from_redis(doc_id: str) -> tuple[VectorStoreIndex, Dict[str, Any]]:
    """Redis에서 인덱스 로드"""
    client = await get_redis_client()

    # Redis에서 데이터 가져오기
    data = await client.hgetall(f"doc:{doc_id}")  # type: ignore

    if not data:
        raise ValueError(f"문서 ID '{doc_id}'를 Redis에서 찾을 수 없습니다.")

    # 인덱스 복원
    index_base64 = data.get(b"index")
    metadata_json = data.get(b"metadata")

    if not index_base64:
        raise ValueError(f"문서 ID '{doc_id}'의 인덱스가 손상되었습니다.")

    index_bytes = base64.b64decode(index_base64)
    index = pickle.loads(index_bytes)

    metadata = {}
    if metadata_json:
        import json

        metadata = json.loads(metadata_json.decode("utf-8"))

    return index, metadata


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/upload-from-docs")
async def upload_document_from_docs(request: DocumentUploadRequest):
    """
    docs/ 디렉토리에서 PDF 파일 업로드 및 인덱스 생성

    Request:
    ```json
    {
        "file_name": "2024소상공인_지원정책.pdf",
        "doc_id": "policy_2024_v1"
    }
    ```

    Redis 저장:
    - 키: doc:{doc_id}
    - 필드: index (Base64 인코딩), metadata (JSON)
    """
    try:
        start_time = datetime.now()

        # PDF 파일 경로
        pdf_path = os.path.join("docs", request.file_name)

        # PDF 로드
        documents = await load_pdf_from_path(pdf_path)

        # 계층적 인덱스 생성
        index, total_chunks, child_chunks = await create_hierarchical_index(documents)

        # Redis 저장
        index_bytes = pickle.dumps(index)
        index_base64 = base64.b64encode(index_bytes).decode("utf-8")

        metadata = {
            "doc_id": request.doc_id,
            "file_name": request.file_name,
            "total_pages": len(documents),
            "total_chunks": total_chunks,
            "parent_chunks": total_chunks - child_chunks,
            "child_chunks": child_chunks,
            "created_at": datetime.now().isoformat(),
        }

        import json

        client = await get_redis_client()
        await client.hset(  # type: ignore
            f"doc:{request.doc_id}",
            mapping={
                "index": index_base64,
                "metadata": json.dumps(metadata, ensure_ascii=False),
            },
        )

        end_time = datetime.now()

        return success_response(
            data={
                "doc_id": request.doc_id,
                "file_name": request.file_name,
                "total_pages": len(documents),
                "total_chunks": total_chunks,
                "parent_chunks": total_chunks - child_chunks,
                "child_chunks": child_chunks,
            },
            message="문서가 업로드되고 인덱스가 생성되었습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            metadata={
                "index_type": "hierarchical",
                "parent_chunk_size": 2048,
                "child_chunk_size": 512,
            },
        )

    except FileNotFoundError as e:
        return error_response(
            message=f"파일을 찾을 수 없습니다: {request.file_name}",
            error=str(e),
            status_code=404,
        )
    except Exception as e:
        return error_response(
            message="문서 업로드 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


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
