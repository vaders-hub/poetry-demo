"""
Redis 기반 문서 분석 API Router

LlamaIndex 인덱스를 Redis에 저장하여 영구 보존 및 분산 환경 지원
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json
import pickle
import base64
from datetime import datetime

from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from src.models import (
    DocumentUploadRequest,
    QueryRequest,
    SummaryRequest,
    IssueExtractionRequest,
)
from src.utils import (
    load_pdf_from_path,
    create_hierarchical_index,
    stream_response,
    success_response,
    created_response,
    error_response,
    get_redis_client,
    close_redis_client,
    ping_redis,
)


router = APIRouter(
    prefix="/document-analysis-redis", tags=["Document Analysis (Redis)"]
)

# LlamaIndex 설정
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")


# ============================================================================
# Redis 저장/로드 헬퍼
# ============================================================================


async def save_index_to_redis(
    doc_id: str, index: VectorStoreIndex, metadata: Dict[str, Any]
):
    """
    인덱스를 Redis에 저장

    인덱스 자체는 pickle로 직렬화하여 저장
    메타데이터는 JSON으로 별도 저장
    """
    client = await get_redis_client()

    # 인덱스 직렬화 (pickle)
    index_bytes = pickle.dumps(index)
    index_b64 = base64.b64encode(index_bytes).decode("utf-8")

    # Redis에 저장
    _ = await client.hset(  # type: ignore
        f"doc:{doc_id}", mapping={"index": index_b64, "metadata": json.dumps(metadata)}
    )

    # TTL 설정 (선택사항, 24시간)
    await client.expire(f"doc:{doc_id}", 86400)


async def load_index_from_redis(doc_id: str) -> tuple[VectorStoreIndex, Dict[str, Any]]:
    """Redis에서 인덱스 로드"""
    client = await get_redis_client()

    # Redis에서 가져오기
    data = await client.hgetall(f"doc:{doc_id}")  # type: ignore

    if not data or b"index" not in data:
        raise ValueError(f"문서 ID '{doc_id}'를 찾을 수 없습니다.")

    # 인덱스 역직렬화
    index_b64 = data[b"index"].decode("utf-8")
    index_bytes = base64.b64decode(index_b64)
    index = pickle.loads(index_bytes)

    # 메타데이터 파싱
    metadata = json.loads(data[b"metadata"].decode("utf-8"))

    return index, metadata


async def check_document_exists(doc_id: str) -> bool:
    """문서가 Redis에 존재하는지 확인"""
    client = await get_redis_client()
    exists = await client.exists(f"doc:{doc_id}")
    return exists > 0


async def list_all_documents() -> list[Dict[str, Any]]:
    """Redis의 모든 문서 목록 조회"""
    client = await get_redis_client()

    # 모든 doc:* 키 찾기
    keys = []
    cursor = 0
    while True:
        cursor, batch = await client.scan(cursor, match="doc:*", count=100)
        keys.extend(batch)
        if cursor == 0:
            break

    documents = []
    for key in keys:
        doc_id = key.decode("utf-8").replace("doc:", "")
        metadata_bytes = await client.hget(key, "metadata")  # type: ignore
        if metadata_bytes:
            metadata = json.loads(metadata_bytes.decode("utf-8"))  # type: ignore
            documents.append({"doc_id": doc_id, **metadata})

    return documents


async def delete_document_from_redis(doc_id: str):
    """Redis에서 문서 삭제"""
    client = await get_redis_client()
    await client.delete(f"doc:{doc_id}")


# ============================================================================
# Helper Functions
# ============================================================================


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/upload-from-docs")
async def upload_pdf_from_docs(request: DocumentUploadRequest):
    """
    docs 폴더의 PDF 파일 업로드 및 Redis에 인덱싱

    인덱스를 Redis에 저장하여 서버 재시작 후에도 유지됩니다.
    """
    try:
        start_time = datetime.now()

        # docs 폴더에서 파일 찾기
        pdf_path = f"docs/{request.file_name}"

        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=404, detail=f"파일을 찾을 수 없습니다: {pdf_path}"
            )

        # PDF 로드
        documents = await load_pdf_from_path(pdf_path)

        # 계층적 인덱스 생성
        index, total_nodes, child_nodes = await create_hierarchical_index(documents)

        # 메타데이터 준비
        metadata = {
            "file_name": request.file_name,
            "num_pages": len(documents),
            "total_nodes": total_nodes,
            "child_nodes": child_nodes,
            "created_at": datetime.now().isoformat(),
        }

        # Redis에 저장
        await save_index_to_redis(request.doc_id, index, metadata)

        end_time = datetime.now()

        return created_response(
            data={
                "doc_id": request.doc_id,
                "storage": "Redis",
                **metadata,
            },
            message="PDF 파일이 Redis에 성공적으로 저장되었습니다.",
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
    """문서 목적 및 핵심 내용 요약 (Redis에서 로드)"""
    try:
        start_time = datetime.now()

        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

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
                "storage": "Redis",
                "summary": str(response),
                "summary_length": len(str(response)),
                "source_nodes_count": len(response.source_nodes),
            },
            message="문서의 목적과 핵심 내용을 요약했습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
        )

    except ValueError as e:
        return error_response(
            message=str(e),
            error="NOT_FOUND",
            status_code=404,
        )
    except Exception as e:
        return error_response(
            message="문서 요약 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.post("/summary-streaming")
async def get_document_summary_streaming(request: SummaryRequest):
    """문서 요약 (스트리밍, Redis에서 로드)"""
    try:
        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        query_engine = index.as_query_engine(streaming=True, similarity_top_k=5)

        query = f"""
        이 문서의 목적과 핵심 내용을 한 문단({request.max_length}자 이내)으로 요약해 주세요.
        """

        streaming_response = query_engine.query(query)

        return StreamingResponse(
            stream_response(streaming_response.response_gen),  # type: ignore[attr-defined]
            media_type="text/event-stream",
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-issues")
async def extract_issues(request: IssueExtractionRequest):
    """주요 이슈 추출 (Redis에서 로드)"""
    try:
        start_time = datetime.now()

        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        query_engine = index.as_query_engine(
            similarity_top_k=request.top_k, response_mode="tree_summarize"
        )

        query = """
        이 정부 정책 문서에서 다음 내용을 추출해주세요:
        1. 기존에 존재하던 문제점이나 개선이 필요한 사항
        2. 2024년 대비 2025년에 달라지는 내용 (변경사항)
        3. 새롭게 신설되거나 확대되는 지원 사업
        """

        response = query_engine.query(query)

        source_nodes_info = [
            {
                "score": node.score,
                "text_preview": getattr(node.node, "text", "")[:200] + "..." if len(getattr(node.node, "text", "")) > 200 else getattr(node.node, "text", ""),  # type: ignore[attr-defined]
            }
            for node in sorted(
                response.source_nodes, key=lambda x: x.score or 0.0, reverse=True
            )[:5]
        ]

        end_time = datetime.now()

        return success_response(
            data={
                "doc_id": request.doc_id,
                "storage": "Redis",
                "issues": str(response),
                "source_nodes": source_nodes_info,
                "total_source_nodes": len(response.source_nodes),
            },
            message="문서에서 주요 이슈를 추출했습니다.",
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
        )

    except ValueError as e:
        return error_response(
            message=str(e),
            error="NOT_FOUND",
            status_code=404,
        )
    except Exception as e:
        return error_response(
            message="이슈 추출 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.post("/query")
async def query_document(request: QueryRequest):
    """자유 질의응답 (Redis에서 로드)"""
    try:
        start_time = datetime.now()

        # Redis에서 인덱스 로드
        index, metadata = await load_index_from_redis(request.doc_id)

        if request.streaming:
            query_engine = index.as_query_engine(
                streaming=True, similarity_top_k=request.top_k
            )
            streaming_response = query_engine.query(request.query)

            return StreamingResponse(
                stream_response(streaming_response.response_gen),  # type: ignore[attr-defined]
                media_type="text/event-stream",
            )
        else:
            query_engine = index.as_query_engine(similarity_top_k=request.top_k)
            response = query_engine.query(request.query)

            end_time = datetime.now()

            return success_response(
                data={
                    "doc_id": request.doc_id,
                    "storage": "Redis",
                    "query": request.query,
                    "response": str(response),
                    "source_nodes": [
                        {
                            "score": node.score,
                            "text_preview": getattr(node.node, "text", "")[:200] + "...",  # type: ignore
                        }
                        for node in response.source_nodes
                    ],
                },
                message="질의응답이 완료되었습니다.",
                execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            )

    except ValueError as e:
        return error_response(
            message=str(e),
            error="NOT_FOUND",
            status_code=404,
        )
    except Exception as e:
        return error_response(
            message="질의응답 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.get("/list-documents")
async def list_indexed_documents():
    """Redis에 저장된 모든 문서 목록 조회"""
    try:
        documents = await list_all_documents()

        return success_response(
            data=documents,
            message="문서 목록 조회 성공",
            metadata={
                "storage": "Redis",
                "total_documents": len(documents),
            }
        )
    except Exception as e:
        return error_response(
            message="문서 목록 조회 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.delete("/delete-document/{doc_id}")
async def delete_document(doc_id: str):
    """Redis에서 문서 삭제"""
    try:
        # 문서 존재 확인
        exists = await check_document_exists(doc_id)
        if not exists:
            return error_response(
                message=f"문서 ID '{doc_id}'를 찾을 수 없습니다.",
                error="NOT_FOUND",
                status_code=404,
            )

        # 삭제
        await delete_document_from_redis(doc_id)

        # 남은 문서 수 확인
        remaining_docs = await list_all_documents()

        return success_response(
            data={"doc_id": doc_id, "deleted": True},
            message=f"문서 '{doc_id}'가 삭제되었습니다.",
            metadata={
                "storage": "Redis",
                "remaining_documents": len(remaining_docs),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="문서 삭제 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.get("/redis-info")
async def get_redis_info():
    """Redis 연결 정보 및 통계"""
    try:
        client = await get_redis_client()

        # Redis INFO 명령어로 통계 가져오기
        info = await client.info()

        return success_response(
            data={
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_keys": await client.dbsize(),
            },
            message="Redis 연결 정보 조회 성공",
        )
    except Exception as e:
        return error_response(
            message="Redis 연결 정보 조회 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )
