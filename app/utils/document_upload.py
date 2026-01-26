"""
Document Upload Utility

Redis 기반 문서 업로드 공통 로직
- PDF 로드
- 계층적 인덱스 생성
- Redis 저장

Usage:
    from app.utils.document_upload import upload_and_index_document

    result = await upload_and_index_document(
        doc_id="doc_001",
        file_name="sample.pdf",
        analysis_type="table",
    )
"""

import os
from datetime import datetime
from typing import Any

from app.utils.document_analysis import create_hierarchical_index, load_pdf_from_path
from app.utils.redis_index import save_index_to_redis


class DocumentUploadResult:
    """문서 업로드 결과"""

    def __init__(
        self,
        success: bool,
        doc_id: str,
        file_name: str,
        data: dict[str, Any] | None = None,
        error_message: str | None = None,
        error_code: int = 0,
    ):
        self.success = success
        self.doc_id = doc_id
        self.file_name = file_name
        self.data = data or {}
        self.error_message = error_message
        self.error_code = error_code


async def upload_and_index_document(
    doc_id: str,
    file_name: str,
    analysis_type: str = "general",
    base_dir: str = "docs",
    parent_chunk_size: int = 1024,
    child_chunk_size: int = 256,
    parent_chunk_overlap: int = 100,
    child_chunk_overlap: int = 50,
    extra_metadata: dict[str, Any] | None = None,
) -> DocumentUploadResult:
    """
    문서 업로드 및 Redis 인덱싱 공통 로직

    Args:
        doc_id: 문서 고유 ID
        file_name: PDF 파일명
        analysis_type: 분석 유형 (table, clause, report, advanced_query 등)
        base_dir: PDF 파일 기본 디렉토리 (기본: "docs")
        parent_chunk_size: 부모 청크 크기
        child_chunk_size: 자식 청크 크기
        parent_chunk_overlap: 부모 청크 오버랩
        child_chunk_overlap: 자식 청크 오버랩
        extra_metadata: 추가 메타데이터

    Returns:
        DocumentUploadResult: 업로드 결과 객체
    """
    start_time = datetime.now()

    # PDF 파일 경로
    pdf_path = os.path.join(base_dir, file_name)

    # 파일 존재 확인
    if not os.path.exists(pdf_path):
        return DocumentUploadResult(
            success=False,
            doc_id=doc_id,
            file_name=file_name,
            error_message=f"파일을 찾을 수 없습니다: {pdf_path}",
            error_code=404,
        )

    try:
        # PDF 로드
        documents = await load_pdf_from_path(pdf_path)

        # 계층적 인덱스 생성
        index, total_nodes, child_nodes = await create_hierarchical_index(
            documents=documents,
            parent_chunk_size=parent_chunk_size,
            child_chunk_size=child_chunk_size,
            parent_chunk_overlap=parent_chunk_overlap,
            child_chunk_overlap=child_chunk_overlap,
        )

        # 메타데이터 준비
        metadata = {
            "doc_id": doc_id,
            "file_name": file_name,
            "num_pages": len(documents),
            "total_nodes": total_nodes,
            "child_nodes": child_nodes,
            "parent_nodes": total_nodes - child_nodes,
            "analysis_type": analysis_type,
            "created_at": datetime.now().isoformat(),
            "chunk_config": {
                "parent_chunk_size": parent_chunk_size,
                "child_chunk_size": child_chunk_size,
                "parent_chunk_overlap": parent_chunk_overlap,
                "child_chunk_overlap": child_chunk_overlap,
            },
        }

        # 추가 메타데이터 병합
        if extra_metadata:
            metadata.update(extra_metadata)

        # Redis 저장
        await save_index_to_redis(doc_id, index, metadata)

        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        return DocumentUploadResult(
            success=True,
            doc_id=doc_id,
            file_name=file_name,
            data={
                "doc_id": doc_id,
                "file_name": file_name,
                "num_pages": len(documents),
                "total_nodes": total_nodes,
                "child_nodes": child_nodes,
                "parent_nodes": total_nodes - child_nodes,
                "analysis_type": analysis_type,
                "storage": "Redis",
                "execution_time_ms": round(execution_time_ms, 2),
            },
        )

    except Exception as e:
        return DocumentUploadResult(
            success=False,
            doc_id=doc_id,
            file_name=file_name,
            error_message=f"문서 처리 실패: {str(e)}",
            error_code=500,
        )


# 분석 유형별 기본 청크 설정
CHUNK_CONFIGS = {
    "table": {
        "parent_chunk_size": 2048,
        "child_chunk_size": 512,
        "parent_chunk_overlap": 200,
        "child_chunk_overlap": 50,
    },
    "clause": {
        "parent_chunk_size": 1024,
        "child_chunk_size": 256,
        "parent_chunk_overlap": 100,
        "child_chunk_overlap": 50,
    },
    "report": {
        "parent_chunk_size": 2048,
        "child_chunk_size": 512,
        "parent_chunk_overlap": 200,
        "child_chunk_overlap": 50,
    },
    "advanced_query": {
        "parent_chunk_size": 1024,
        "child_chunk_size": 256,
        "parent_chunk_overlap": 100,
        "child_chunk_overlap": 50,
    },
    "general": {
        "parent_chunk_size": 1024,
        "child_chunk_size": 256,
        "parent_chunk_overlap": 100,
        "child_chunk_overlap": 50,
    },
}


def get_chunk_config(analysis_type: str) -> dict[str, int]:
    """
    분석 유형에 맞는 청크 설정 반환

    Args:
        analysis_type: 분석 유형

    Returns:
        청크 설정 딕셔너리
    """
    return CHUNK_CONFIGS.get(analysis_type, CHUNK_CONFIGS["general"])
