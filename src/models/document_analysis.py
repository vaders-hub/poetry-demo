"""
Document Analysis Request/Response Models

문서 분석 API에서 사용하는 공통 Pydantic 모델
"""

from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    """문서 업로드 요청"""
    doc_id: str = Field(description="문서 ID (고유 식별자)")
    file_name: str = Field(description="파일명", default="document.pdf")


class QueryRequest(BaseModel):
    """쿼리 요청"""
    doc_id: str = Field(description="문서 ID")
    query: str = Field(description="질문")
    streaming: bool = Field(default=False, description="스트리밍 응답 여부")
    top_k: int = Field(default=5, description="검색할 청크 개수", ge=1, le=20)


class SummaryRequest(BaseModel):
    """요약 요청"""
    doc_id: str = Field(description="문서 ID")
    max_length: int = Field(default=200, description="요약 최대 길이 (자)", ge=50, le=500)


class IssueExtractionRequest(BaseModel):
    """이슈 추출 요청"""
    doc_id: str = Field(description="문서 ID")
    top_k: int = Field(default=8, description="검색할 청크 개수", ge=3, le=20)
