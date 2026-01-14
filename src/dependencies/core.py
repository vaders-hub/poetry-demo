from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import connect

DBSessionDep = Annotated[AsyncSession, Depends(connect)]
