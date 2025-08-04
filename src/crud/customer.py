from src.models import Customer as CustomerDBModel
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.response_wrapper import api_response

async def get_customers(db_session: AsyncSession):
    try:
        stmt = select(CustomerDBModel)
        result = await db_session.execute(stmt)
        customers = result.scalars().all()

        return api_response(data=customers, message="All customers retrieved")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_customer(db_session: AsyncSession, customer_id: int):
    customer = (await db_session.scalars(select(CustomerDBModel).where(CustomerDBModel.id == customer_id))).first()
    if not customer:
        raise HTTPException(status_code=404, detail="User not found")
    return customer