from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import connect

DBSessionDep = Annotated[AsyncSession, Depends(connect)]
