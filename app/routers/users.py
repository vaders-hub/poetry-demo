from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.crud.user import create_user, get_user_by_username
from app.dependencies.core import DBSessionDep
from app.schemas.user import Token, UserCreate, UserResult, user_info_form
from app.utils import (
    created_response,
    error_response,
    security,
    success_response,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
async def register(
    db_session: DBSessionDep,
    user: UserCreate = Depends(user_info_form),
):
    try:
        if len(user.password) > 72:
            return error_response(
                message="비밀번호가 너무 깁니다. 72자 이하로 설정해주세요.",
                error="PASSWORD_TOO_LONG",
                status_code=400,
            )

        db_user = await get_user_by_username(db_session, user.username)

        if db_user:
            return error_response(
                message="이미 존재하는 사용자명입니다.",
                error="USERNAME_EXISTS",
                status_code=400,
            )

        new_user = await create_user(db_session, user.username, user.password)
        user_result = UserResult.model_validate(new_user)

        return created_response(
            data=user_result,
            message="사용자가 성공적으로 등록되었습니다.",
        )
    except Exception as e:
        return error_response(
            message="사용자 등록 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )


@router.post("/login", response_model=Token)
async def login(
    db_session: DBSessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    try:
        user = await get_user_by_username(db_session, form_data.username)

        if not user or not security.verify_password(
            form_data.password, user.hashed_password
        ):
            return error_response(
                message="잘못된 사용자명 또는 비밀번호입니다.",
                error="INVALID_CREDENTIALS",
                status_code=401,
            )

        access_token = security.create_access_token({"sub": user.username})

        return success_response(
            data={"access_token": access_token, "token_type": "bearer"},
            message="로그인에 성공했습니다.",
        )
    except Exception as e:
        return error_response(
            message="로그인 중 오류가 발생했습니다.",
            error=str(e),
            status_code=500,
        )
