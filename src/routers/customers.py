from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.dependencies.core import DBSessionDep
from src.crud.customer import get_customer, get_customers
from src.schemas.customer import Customer

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    responses={404: {"description": "Not found"}},
)

@router.get(
    "/",
    response_model=List[Customer],
)
async def get_customers(
    db_session: DBSessionDep,
):
    customers = await get_customers(db_session)
    return customers

@router.get(
    "/{customer_id}",
    response_model=Customer,
)
async def get_customer(
    customer_id: int,
    db_session: DBSessionDep,
):
    customer = await get_customer(db_session, customer_id)
    return customer
