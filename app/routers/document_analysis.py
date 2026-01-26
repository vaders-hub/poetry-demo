"""
실무형 문서 분석 API Router

PDF 문서를 LlamaIndex로 인덱싱하고 실무 질문에 답변하는 FastAPI 엔드포인트
"""

import os
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models import (
    DocumentUploadRequest,
    IssueExtractionRequest,
    QueryRequest,
    SummaryRequest,
)
from app.utils import (
    compute_confidence_score,
    create_hierarchical_index,
    created_response,
    error_response,
    load_pdf_from_path,
    stream_response,
    success_response,
)

router = APIRouter(prefix="/document-analysis", tags=["Document Analysis"])

# 인덱스 저장소 (실제 환경에서는 Redis 등 사용)
_index_storage = {}


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/upload-from-docs")
async def upload_pdf_from_docs(request: DocumentUploadRequest):
    """
    docs 폴더의 PDF 파일 업로드 및 인덱싱

    미리 docs 폴더에 배치된 PDF 파일을 인덱싱합니다.
    """
    try:
        start_time = datetime.now()

        # docs 폴더에서 파일 찾기
        pdf_path = f"docs/{request.file_name}"

        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=404,
                detail=f"파일을 찾을 수 없습니다: {pdf_path}. docs 폴더에 파일을 배치했는지 확인하세요.",
            )

        # PDF 로드
        documents = await load_pdf_from_path(pdf_path)

        # 계층적 인덱스 생성
        index, total_nodes, child_nodes = await create_hierarchical_index(documents)

        # 인덱스 저장
        _index_storage[request.doc_id] = {
            "index": index,
            "file_name": request.file_name,
            "num_pages": len(documents),
            "total_nodes": total_nodes,
            "child_nodes": child_nodes,
            "created_at": datetime.now().isoformat(),
        }

        end_time = datetime.now()

        return created_response(
            data={
                "doc_id": request.doc_id,
                "file_name": request.file_name,
                "num_pages": len(documents),
                "total_nodes": total_nodes,
                "child_nodes": child_nodes,
            },
            message="PDF 파일이 성공적으로 인덱싱되었습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
        )

    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="문서 업로드 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.post("/summary")
async def get_document_summary(request: SummaryRequest):
    """
    문서 목적 및 핵심 내용 요약

    문서의 목적과 핵심 내용을 한 문단으로 요약합니다.
    """
    try:
        if request.doc_id not in _index_storage:
            return error_response(
                message=f"문서 ID '{request.doc_id}'를 찾을 수 없습니다.",
                error="NOT_FOUND",
                status_code=404,
            )

        start_time = datetime.now()

        storage = _index_storage[request.doc_id]
        index = storage["index"]

        query_engine = index.as_query_engine(
            similarity_top_k=5, response_mode="compact"
        )

        query = f"""
        이 문서의 목적과 핵심 내용을 한 문단({request.max_length}자 이내)으로 요약해 주세요.
        정부의 정책 방향, 주요 지원 내용, 예산 규모 등을 포함해주세요.
        """

        response = query_engine.query(query)

        end_time = datetime.now()

        return success_response(
            data={
                "doc_id": request.doc_id,
                "summary": str(response),
                "summary_length": len(str(response)),
                "source_nodes_count": len(response.source_nodes),
                "confidence_score": compute_confidence_score(response.source_nodes),
            },
            message="문서의 목적과 핵심 내용을 요약했습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
        )

    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="문서 요약 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.post("/summary-streaming")
async def get_document_summary_streaming(request: SummaryRequest):
    """
    문서 목적 및 핵심 내용 요약 (스트리밍)

    실시간 스트리밍 방식으로 요약을 제공합니다.
    """
    try:
        if request.doc_id not in _index_storage:
            raise HTTPException(
                status_code=404,
                detail=f"문서 ID '{request.doc_id}'를 찾을 수 없습니다.",
            )

        storage = _index_storage[request.doc_id]
        index = storage["index"]

        query_engine = index.as_query_engine(streaming=True, similarity_top_k=5)

        query = f"""
        이 문서의 목적과 핵심 내용을 한 문단({request.max_length}자 이내)으로 요약해 주세요.
        정부의 정책 방향, 주요 지원 내용, 예산 규모 등을 포함해주세요.
        """

        streaming_response = query_engine.query(query)

        return StreamingResponse(
            stream_response(streaming_response.response_gen),
            media_type="text/event-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/extract-issues")
async def extract_issues(request: IssueExtractionRequest):
    """
    문제로 지적된 주요 사안 추출

    문서에서 문제점, 개선사항, 변경내용 등을 추출합니다.
    """
    try:
        if request.doc_id not in _index_storage:
            return error_response(
                message=f"문서 ID '{request.doc_id}'를 찾을 수 없습니다.",
                error="NOT_FOUND",
                status_code=404,
            )

        start_time = datetime.now()

        storage = _index_storage[request.doc_id]
        index = storage["index"]

        query_engine = index.as_query_engine(
            similarity_top_k=request.top_k, response_mode="tree_summarize"
        )

        query = """
        이 정부 정책 문서에서 다음 내용을 추출해주세요:
        1. 기존에 존재하던 문제점이나 개선이 필요한 사항
        2. 2024년 대비 2025년에 달라지는 내용 (변경사항)
        3. 새롭게 신설되거나 확대되는 지원 사업

        각 항목을 명확하게 구분하여 정리해주세요.
        """

        response = query_engine.query(query)

        # 참조된 소스 노드 정보
        source_nodes_info = [
            {
                "score": node.score,
                "text_preview": (
                    node.node.text[:200] + "..."
                    if len(node.node.text) > 200
                    else node.node.text
                ),
                "metadata": node.node.metadata,
            }
            for node in sorted(
                response.source_nodes, key=lambda x: x.score, reverse=True
            )[:5]
        ]

        end_time = datetime.now()

        return success_response(
            data={
                "doc_id": request.doc_id,
                "issues": str(response),
                "source_nodes": source_nodes_info,
                "total_source_nodes": len(response.source_nodes),
                "confidence_score": compute_confidence_score(response.source_nodes),
            },
            message="문서에서 주요 이슈를 추출했습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
        )

    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="이슈 추출 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.post("/query")
async def query_document(request: QueryRequest):
    """
    자유 질의응답

    인덱싱된 문서에 대해 자유롭게 질문할 수 있습니다.
    """
    try:
        if request.doc_id not in _index_storage:
            return error_response(
                message=f"문서 ID '{request.doc_id}'를 찾을 수 없습니다.",
                error="NOT_FOUND",
                status_code=404,
            )

        start_time = datetime.now()

        storage = _index_storage[request.doc_id]
        index = storage["index"]

        if request.streaming:
            query_engine = index.as_query_engine(
                streaming=True, similarity_top_k=request.top_k
            )
            streaming_response = query_engine.query(request.query)

            return StreamingResponse(
                stream_response(streaming_response.response_gen),
                media_type="text/event-stream",
            )
        else:
            query_engine = index.as_query_engine(similarity_top_k=request.top_k)
            response = query_engine.query(request.query)

            end_time = datetime.now()

            return success_response(
                data={
                    "doc_id": request.doc_id,
                    "query": request.query,
                    "response": str(response),
                    "source_nodes": [
                        {
                            "score": node.score,
                            "text_preview": (
                                node.node.text[:200] + "..."
                                if len(node.node.text) > 200
                                else node.node.text
                            ),
                        }
                        for node in response.source_nodes
                    ],
                    "confidence_score": compute_confidence_score(response.source_nodes),
                },
                message="질의응답이 완료되었습니다.",
                execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            )

    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="질의응답 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.get("/list-documents")
async def list_indexed_documents():
    """
    인덱싱된 문서 목록 조회
    """
    documents = []
    for doc_id, storage in _index_storage.items():
        documents.append(
            {
                "doc_id": doc_id,
                "file_name": storage["file_name"],
                "num_pages": storage["num_pages"],
                "total_nodes": storage["total_nodes"],
                "child_nodes": storage["child_nodes"],
                "created_at": storage["created_at"],
            }
        )

    return success_response(
        data=documents,
        message="문서 목록 조회 성공",
        metadata={
            "total_documents": len(documents),
        },
    )


@router.delete("/delete-document/{doc_id}")
async def delete_document(doc_id: str):
    """
    인덱싱된 문서 삭제
    """
    if doc_id not in _index_storage:
        return error_response(
            message=f"문서 ID '{doc_id}'를 찾을 수 없습니다.",
            error="NOT_FOUND",
            status_code=404,
        )

    del _index_storage[doc_id]

    return success_response(
        data={"doc_id": doc_id, "deleted": True},
        message=f"문서 '{doc_id}'가 삭제되었습니다.",
        metadata={
            "remaining_documents": len(_index_storage),
        },
    )
