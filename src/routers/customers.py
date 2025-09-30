from typing import Any

import orjson
from fastapi import APIRouter, HTTPException, Response

from src.crud.customer import (
    create_customer,
    delete_customer,
    get_customer,
    get_customers,
    update_customer,
)
from src.dependencies.core import DBSessionDep
from src.schemas.customer import Customer, CustomerResponseData
from src.utils.response_wrapper import api_response


class CustomORJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


router = APIRouter(
    prefix="/customer",
    tags=["customers"],
    responses={404: {"description": "Not found"}},
)


@router.get("/list", response_model=CustomerResponseData)
async def customer_list(
    db_session: DBSessionDep,
):
    try:
        customers = await get_customers(db_session)
        return api_response(data=customers, message="customer retrieved")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{customer_id}",
    response_model=CustomerResponseData,
)
async def customer_single(
    customer_id: int,
    db_session: DBSessionDep,
):
    customer = await get_customer(db_session, customer_id)
    return api_response(data=customer, message="customer retrieved")


@router.post(
    "/add",
    response_model=CustomerResponseData,
)
async def add_customer(
    customer: Customer,
    db_session: DBSessionDep,
):
    customer = await create_customer(db_session, customer)
    return api_response(data=customer, message="customer created")


@router.put(
    "/modify",
    response_model=CustomerResponseData,
)
async def update_customer(
    customer: Customer,
    db_session: DBSessionDep,
):
    customer = await update_customer(db_session, customer)
    return api_response(data=customer, message="customer modified")


@router.delete(
    "/delete",
    response_model=CustomerResponseData,
)
async def remove_customer(
    customer: Customer,
    db_session: DBSessionDep,
):
    customer = await delete_customer(db_session, customer)
    return api_response(data=customer, message="customer modified")
