"""
Models package

SQLAlchemy 모델 및 Pydantic Request/Response 스키마
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# SQLAlchemy DB Models
from src.models.customer import Customer
from src.models.user import User

# Pydantic Request/Response Models
from src.models.document_analysis import (
    DocumentUploadRequest,
    QueryRequest,
    SummaryRequest,
    IssueExtractionRequest,
)

__all__ = [
    # Base
    "Base",
    # DB Models
    "Customer",
    "User",
    # Request/Response Models
    "DocumentUploadRequest",
    "QueryRequest",
    "SummaryRequest",
    "IssueExtractionRequest",
]
