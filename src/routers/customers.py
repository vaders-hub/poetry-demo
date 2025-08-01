from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.models.customer import Customer
from src.schemas.customer_schema import CustomerSchema
from src.db import connect
from src.utils.response_wrapper import api_response

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/")
def get_customers(db: Session = Depends(connect)):
    try:
        customers = db.query(Customer).all()
        return api_response(data=customers, message="All customers retrieved")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
