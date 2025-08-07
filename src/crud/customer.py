from src.models import Customer as CustomerDBModel
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_customers(db_session: AsyncSession):
    stmt = select(CustomerDBModel)
    result = await db_session.execute(stmt)
    customers = result.scalars().all()

    if not customers:
        raise HTTPException(status_code=404, detail="Users not found")
    return customers

async def get_customer(db_session: AsyncSession, customer_id: int):
    stmt = select(CustomerDBModel).where(CustomerDBModel.customer_id == customer_id)
    result = await db_session.execute(stmt)

    customer = result.scalars(stmt).first()

    if not customer:
        raise HTTPException(status_code=404, detail="User not found")
    return customer