from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from crud.user import create_user, get_user_by_username
from dependencies.core import DBSessionDep
from schemas.user import Token, UserCreate, UserLogin
from utils import security

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
async def register(
    user: UserCreate,
    db_session: DBSessionDep,
):
    db_user = await get_user_by_username(db_session, user.username)

    if db_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = await create_user(db_session, user.username, user.password)
    access_token = security.create_access_token({"sub": new_user.username})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    db_session: DBSessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await get_user_by_username(db_session, form_data.username)

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = security.create_access_token({"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}
