from src.models import Customer as CustomerDBModel
from src.schemas.customer import Customer as CustomerSchema
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_customers(db_session: AsyncSession):
    stmt = select(CustomerDBModel)
    result = await db_session.execute(stmt)
    customers = result.scalars().all()

    if not customers:
        raise HTTPException(status_code=404, detail="Customers not found")

    return [CustomerSchema.model_validate(c) for c in customers]

async def get_customer(db_session: AsyncSession, customer_id: str):
    stmt = select(CustomerDBModel).where(CustomerDBModel.customer_id == customer_id)
    result = await db_session.execute(stmt)

    customer = result.scalars().first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerSchema.model_validate(customer)

async def create_customer(db_session: AsyncSession, customer: CustomerSchema):
    cid = customer.customer_id
    cname = customer.name

    if not cid or not cname:
        raise HTTPException(status_code=400, detail="Customer ID and name are required")

    stmt = select(CustomerDBModel).where(CustomerDBModel.customer_id == cid)
    result = await db_session.execute(stmt)
    customer_exist = result.scalars().first()

    if not customer_exist:
        new_user = CustomerDBModel(
            customer_id=cid,
            name=cname,
            address=customer.address,
            website=customer.website,
            credit_limit=customer.credit_limit
        )
        db_session.add(new_user)
        await db_session.commit()
        await db_session.refresh(new_user)
        return CustomerSchema.model_validate(new_user)
    else:
        raise HTTPException(status_code=409, detail="Customer already exists")


async def update_customer(db_session: AsyncSession, customer: CustomerSchema):
    cid = customer.customer_id
    cname = customer.name

    if not cid or not cname:
        raise HTTPException(status_code=400, detail="Customer ID and name are required")

    stmt = select(CustomerDBModel).where(CustomerDBModel.customer_id == cid)

    result = await db_session.execute(stmt)
    customer_exist = result.scalars().first()

    if customer_exist:
        customer_exist.name = cname
        customer_exist.address = customer.address
        customer_exist.website = customer.website
        customer_exist.credit_limit = customer.credit_limit
        await db_session.commit()
        await db_session.refresh(customer_exist)
        return CustomerSchema.model_validate(customer_exist)
    else:
        raise HTTPException(status_code=404, detail="Customer does not exist")

async def delete_customer(db_session: AsyncSession, customer: CustomerSchema):
    cid = customer.customer_id

    if not cid:
        raise HTTPException(status_code=400, detail="Customer ID required")

    stmt = select(CustomerDBModel).where(CustomerDBModel.customer_id == cid)

    result = await db_session.execute(stmt)
    customer_exist = result.scalars().first()

    if customer_exist:
        await db_session.delete(customer_exist)
        await db_session.commit()
        return CustomerSchema.model_validate(customer_exist)
    else:
        raise HTTPException(status_code=404, detail="Customer does not exist")