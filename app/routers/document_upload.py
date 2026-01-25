"""
공통 문서 업로드 API Router

모든 Redis 기반 문서 분석 라우터에서 공유하는 업로드 엔드포인트
- 문서 업로드 및 Redis 인덱싱
- 문서 목록 조회
- 문서 삭제
- 문서 존재 확인
"""

from fastapi import APIRouter, HTTPException

from app.models import DocumentUploadRequest
from app.utils import (
    success_response,
    created_response,
    error_response,
    ping_redis,
    check_document_exists,
    delete_document_from_redis,
    list_all_documents,
    upload_and_index_document,
)


router = APIRouter(
    prefix="/documents",
    tags=["Document Upload (Redis)"],
)


# ============================================================================
# 문서 업로드
# ============================================================================


@router.post("/upload")
async def upload_document(request: DocumentUploadRequest):
    """
    PDF 문서 업로드 및 Redis 인덱싱

    docs/ 폴더의 PDF 파일을 읽어 계층적 인덱스를 생성하고 Redis에 저장합니다.
    저장된 문서는 모든 document-* 라우터에서 공유됩니다.

    Request:
    ```json
    {
        "doc_id": "policy_2024",
        "file_name": "2024소상공인_지원정책.pdf",
        "chunk_config": {
            "parent_chunk_size": 2048,
            "child_chunk_size": 512,
            "parent_chunk_overlap": 200,
            "child_chunk_overlap": 50
        }
    }
    ```

    chunk_config는 선택 사항이며, 지정하지 않으면 위 기본값이 사용됩니다.
    """
    # 청크 설정 추출
    chunk_config = request.chunk_config

    # 공통 업로드 유틸리티 사용
    result = await upload_and_index_document(
        doc_id=request.doc_id,
        file_name=request.file_name,
        analysis_type="shared",
        parent_chunk_size=chunk_config.parent_chunk_size,
        child_chunk_size=chunk_config.child_chunk_size,
        parent_chunk_overlap=chunk_config.parent_chunk_overlap,
        child_chunk_overlap=chunk_config.child_chunk_overlap,
    )

    if not result.success:
        if result.error_code == 404:
            raise HTTPException(status_code=404, detail=result.error_message)
        return error_response(
            result.error_message or "알 수 없는 오류", result.error_code
        )

    return created_response(
        data=result.data,
        message="문서가 성공적으로 업로드되고 인덱싱되었습니다.",
        execution_time_ms=result.data.get("execution_time_ms"),
    )


# ============================================================================
# 문서 관리
# ============================================================================


@router.get("/list")
async def get_document_list():
    """
    저장된 모든 문서 목록 조회

    Returns:
        - documents: 문서 목록 (doc_id, file_name, created_at 등)
        - total_count: 총 문서 수
    """
    try:
        documents = await list_all_documents()

        return success_response(
            data={
                "documents": documents,
                "total_count": len(documents),
            },
            message=f"총 {len(documents)}개의 문서가 있습니다.",
        )

    except Exception as e:
        return error_response(f"문서 목록 조회 실패: {str(e)}", 500)


@router.get("/{doc_id}/exists")
async def check_document(doc_id: str):
    """
    문서 존재 여부 확인

    Args:
        doc_id: 문서 ID

    Returns:
        - exists: 존재 여부 (true/false)
    """
    try:
        exists = await check_document_exists(doc_id)

        return success_response(
            data={
                "doc_id": doc_id,
                "exists": exists,
            },
            message="문서가 존재합니다." if exists else "문서가 존재하지 않습니다.",
        )

    except Exception as e:
        return error_response(f"문서 확인 실패: {str(e)}", 500)


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    문서 삭제

    Args:
        doc_id: 삭제할 문서 ID

    Returns:
        - deleted: 삭제 성공 여부
    """
    try:
        # 문서 존재 확인
        exists = await check_document_exists(doc_id)
        if not exists:
            raise HTTPException(
                status_code=404,
                detail=f"문서 ID '{doc_id}'를 찾을 수 없습니다.",
            )

        deleted = await delete_document_from_redis(doc_id)

        return success_response(
            data={
                "doc_id": doc_id,
                "deleted": deleted,
            },
            message="문서가 성공적으로 삭제되었습니다.",
        )

    except HTTPException:
        raise
    except Exception as e:
        return error_response(f"문서 삭제 실패: {str(e)}", 500)


# ============================================================================
# 상태 확인
# ============================================================================


@router.get("/health")
async def health_check():
    """
    Redis 연결 상태 확인

    Returns:
        - status: 상태 (healthy/unhealthy)
        - redis_connected: Redis 연결 여부
    """
    redis_status = await ping_redis()

    return success_response(
        data={
            "status": "healthy" if redis_status else "unhealthy",
            "redis_connected": redis_status,
            "service": "document_upload",
        },
        message=(
            "문서 업로드 서비스가 정상 작동 중입니다."
            if redis_status
            else "Redis 연결에 문제가 있습니다."
        ),
    )
