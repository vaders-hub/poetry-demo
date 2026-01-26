import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = {"extend_existing": True}

    customer_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(nullable=True)
    website: Mapped[str] = mapped_column(nullable=True)
    credit_limit: Mapped[int] = mapped_column(nullable=True)
