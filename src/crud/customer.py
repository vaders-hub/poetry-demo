from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Customer as CustomerDBModel


async def get_customers(db_session: AsyncSession):
    stmt = select(CustomerDBModel)
    result = await db_session.execute(stmt)
    customers = result.scalars().all()

    if not customers:
        raise HTTPException(status_code=404, detail="Customers not found")

    return customers


async def get_customer(db_session: AsyncSession, customer_id: int):
    stmt = select(CustomerDBModel).where(CustomerDBModel.customer_id == customer_id)
    result = await db_session.execute(stmt)
    customer = result.scalars().first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


async def create_customer(db_session: AsyncSession, customer: CustomerDBModel):
    cid = customer.customer_id
    cname = customer.name

    if not cid or cname:
        raise HTTPException(status_code=500, detail="Customer ID required")

    stmt = select(CustomerDBModel).where(CustomerDBModel.customer_id == cid)
    result = await db_session.execute(stmt)
    customer_exist = result.scalars().first()

    if not customer_exist:
        new_user = CustomerDBModel(customer_id=cid)
        db_session.add(new_user)
        await db_session.commit()
    else:
        raise HTTPException(status_code=500, detail="Customer already exists")

    return customer


async def update_customer(db_session: AsyncSession, customer: CustomerDBModel):
    cid = customer.customer_id
    cname = customer.name

    if not cid or cname:
        raise HTTPException(status_code=500, detail="Customer ID required")

    stmt = select(CustomerDBModel).where(CustomerDBModel.customer_id == cid)

    result = await db_session.execute(stmt)
    customer_exist = result.scalars().first()

    if customer_exist:
        merge_user = CustomerDBModel(customer_id=cid)
        await db_session.merge(merge_user)
        await db_session.commit()
    else:
        raise HTTPException(status_code=404, detail="Customer not exists")

    return customer


async def delete_customer(db_session: AsyncSession, customer: CustomerDBModel):
    cid = customer.customer_id

    if not cid:
        raise HTTPException(status_code=500, detail="Customer ID required")

    stmt = select(CustomerDBModel).where(CustomerDBModel.customer_id == cid)

    result = await db_session.execute(stmt)
    customer_exist = result.scalars().first()

    if customer_exist:
        delete_user = CustomerDBModel(customer_id=cid)
        await db_session.delete(delete_user)
        await db_session.commit()
    else:
        raise HTTPException(status_code=404, detail="Customer not exists")

    return customer
