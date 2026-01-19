"""
Document Analysis Request/Response Models

문서 분석 API에서 사용하는 공통 Pydantic 모델
"""

from pydantic import BaseModel, Field


class ChunkConfig(BaseModel):
    """청크 설정"""

    parent_chunk_size: int = Field(
        default=2048,
        description="부모 청크 크기 (문자 수)",
        ge=256,
        le=8192,
    )
    child_chunk_size: int = Field(
        default=512,
        description="자식 청크 크기 (문자 수)",
        ge=64,
        le=2048,
    )
    parent_chunk_overlap: int = Field(
        default=200,
        description="부모 청크 오버랩 (문자 수)",
        ge=0,
        le=500,
    )
    child_chunk_overlap: int = Field(
        default=50,
        description="자식 청크 오버랩 (문자 수)",
        ge=0,
        le=200,
    )


class DocumentUploadRequest(BaseModel):
    """문서 업로드 요청"""

    doc_id: str = Field(description="문서 ID (고유 식별자)")
    file_name: str = Field(description="파일명", default="document.pdf")
    chunk_config: ChunkConfig = Field(
        default_factory=ChunkConfig,
        description="청크 설정 (선택, 기본값 사용 가능)",
    )


class QueryRequest(BaseModel):
    """쿼리 요청"""

    doc_id: str = Field(description="문서 ID")
    query: str = Field(description="질문")
    streaming: bool = Field(default=False, description="스트리밍 응답 여부")
    top_k: int = Field(default=5, description="검색할 청크 개수", ge=1, le=20)


class SummaryRequest(BaseModel):
    """요약 요청"""

    doc_id: str = Field(description="문서 ID")
    max_length: int = Field(
        default=200, description="요약 최대 길이 (자)", ge=50, le=500
    )


class IssueExtractionRequest(BaseModel):
    """이슈 추출 요청"""

    doc_id: str = Field(description="문서 ID")
    top_k: int = Field(default=8, description="검색할 청크 개수", ge=3, le=20)


# ==================== Clause Analysis Models ====================


class ReasonAnalysisRequest(BaseModel):
    """사유 및 근거 분석 요청"""

    doc_id: str = Field(description="문서 ID")
    decision_or_action: str = Field(
        description="분석할 조치 또는 판단 (예: '소상공인 지원금 확대')"
    )
    top_k: int = Field(default=10, description="검색할 청크 개수", ge=3, le=20)


class ExceptionClauseRequest(BaseModel):
    """예외 조항 검색 요청"""

    doc_id: str = Field(description="문서 ID")
    situation: str = Field(description="상황 설명 (예: '경영난으로 인한 폐업')")
    top_k: int = Field(default=10, description="검색할 청크 개수", ge=3, le=20)


class ClauseSearchRequest(BaseModel):
    """특정 조항 검색 요청"""

    doc_id: str = Field(description="문서 ID")
    clause_keyword: str = Field(description="조항 키워드 (예: '제1조', '부칙')")
    top_k: int = Field(default=5, description="검색할 청크 개수", ge=1, le=15)


# ==================== Table Analysis Models ====================


class TableImportanceRequest(BaseModel):
    """표 중요도 분석 요청"""

    doc_id: str = Field(description="문서 ID")
    table_context: str = Field(
        description="표 관련 맥락 (예: '징계 기준표', '처분 사유별 기준')", default=""
    )
    top_n: int = Field(default=3, description="추출할 중요 기준 개수", ge=1, le=10)
    top_k: int = Field(default=15, description="검색할 청크 개수", ge=5, le=30)


class TableComparisonRequest(BaseModel):
    """표 조건 비교 요청"""

    doc_id: str = Field(description="문서 ID")
    comparison_aspect: str = Field(
        description="비교 관점 (예: '엄격함', '처벌 강도', '적용 범위')",
        default="엄격함",
    )
    table_context: str = Field(
        description="표 관련 맥락 (예: '징계 기준표', '처분 사유별 기준')", default=""
    )
    top_k: int = Field(default=15, description="검색할 청크 개수", ge=5, le=30)


# ==================== Report Generation Models ====================


class ReportSummaryRequest(BaseModel):
    """보고서 초안 생성 요청"""

    doc_id: str = Field(description="문서 ID")
    max_length: int = Field(
        default=500, description="요약 최대 길이 (자)", ge=200, le=1000
    )
    top_k: int = Field(default=20, description="검색할 청크 개수", ge=10, le=40)


class ChecklistRequest(BaseModel):
    """체크리스트 생성 요청"""

    doc_id: str = Field(description="문서 ID")
    checklist_type: str = Field(
        default="procedure",
        description="체크리스트 유형 (procedure: 절차, compliance: 준수사항, review: 검토사항)",
    )
    top_k: int = Field(default=20, description="검색할 청크 개수", ge=10, le=40)


class AmbiguousTextRequest(BaseModel):
    """모호한 표현 분석 요청"""

    doc_id: str = Field(description="문서 ID")
    top_k: int = Field(default=20, description="검색할 청크 개수", ge=10, le=40)


class FAQGenerationRequest(BaseModel):
    """FAQ 생성 요청"""

    doc_id: str = Field(description="문서 ID")
    num_questions: int = Field(default=5, description="생성할 FAQ 개수", ge=3, le=10)
    top_k: int = Field(default=20, description="검색할 청크 개수", ge=10, le=40)


class AdvancedQueryRequest(BaseModel):
    """고급 쿼리 요청 (질문 분해 + 다중 검색)"""

    doc_id: str = Field(description="문서 ID")
    query: str = Field(description="사용자 질문")
    use_table_search: bool = Field(default=True, description="표 검색 활성화")
    use_text_search: bool = Field(default=True, description="본문 검색 활성화")
    use_json_extraction: bool = Field(
        default=False, description="JSON 경로 추출 활성화"
    )
    top_k: int = Field(default=20, description="검색할 청크 개수", ge=10, le=40)
