"""
Models package

SQLAlchemy 모델 및 Pydantic Request/Response 스키마
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# SQLAlchemy DB Models
from app.models.customer import Customer  # noqa: E402

# Pydantic Request/Response Models
from app.models.document_analysis import (  # noqa: E402
    ChunkConfig,
    DocumentUploadRequest,
    IssueExtractionRequest,
    QueryRequest,
    SummaryRequest,
)
from app.models.user import User  # noqa: E402

__all__ = [
    # Base
    "Base",
    # DB Models
    "Customer",
    "User",
    # Request/Response Models
    "ChunkConfig",
    "DocumentUploadRequest",
    "QueryRequest",
    "SummaryRequest",
    "IssueExtractionRequest",
]
