from typing import Optional

from fastapi import Depends, File, Form, UploadFile
from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    username: str
    password: str


def user_info_form(username: str = Form(...), password: str = Form(...)) -> UserCreate:
    return UserCreate(username=username, password=password)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
