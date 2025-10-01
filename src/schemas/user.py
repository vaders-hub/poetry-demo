from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("password")
    def password_max_72_bytes(cls, v: str) -> str:
        """
        bcrypt는 최대 72바이트 제한이 있으므로,
        입력 비밀번호가 이를 초과하면 ValueError 발생
        """
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 bytes")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
