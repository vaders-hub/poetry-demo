import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.mysql import INTEGER

from ..db import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(
        INTEGER(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    credit_limit = Column(INTEGER(8.2), nullable=True)
