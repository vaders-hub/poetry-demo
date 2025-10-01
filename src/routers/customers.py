from typing import Any

import orjson
from fastapi import APIRouter, HTTPException, Response

from crud.customer import (
    create_customer,
    delete_customer,
    get_customer,
    get_customers,
    update_customer,
)
from dependencies.core import DBSessionDep
from models import Customer as CustomerModel
from schemas.customer import Customer as CustomerSchema
from schemas.customer import CustomerResponseData
from utils.response_wrapper import api_response


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
async def customers(
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
async def customer(
    customer_id: int,
    db_session: DBSessionDep,
):
    customer = await get_customer(db_session, customer_id)

    return api_response(data=customer, message="customer retrieved")


@router.post(
    "/add",
    # response_model=CustomerResponseData,
)
async def add(
    customer: CustomerSchema,
    db_session: DBSessionDep,
):
    customer_model_instance = CustomerModel(**customer.model_dump())
    result = await create_customer(db_session, customer_model_instance)

    return api_response(data=result, message="customer created")


@router.put(
    "/modify",
    response_model=CustomerResponseData,
)
async def update(
    customer: CustomerSchema,
    db_session: DBSessionDep,
):
    customer_model_instance = CustomerModel(**customer.model_dump())
    result = await update_customer(db_session, customer_model_instance)

    return api_response(data=result, message="customer modified")


@router.delete(
    "/delete",
    response_model=CustomerResponseData,
)
async def remove_customer(
    customer: CustomerSchema,
    db_session: DBSessionDep,
):
    customer_model_instance = CustomerModel(**customer.model_dump())
    result = await delete_customer(db_session, customer_model_instance)

    return api_response(data=result, message="customer modified")
