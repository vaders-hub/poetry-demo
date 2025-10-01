from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import User as UserDBModel
from utils import security


async def get_user_by_username(db: AsyncSession, username: str):
    stmt = select(UserDBModel).where(UserDBModel.username == username)
    result = await db.execute(stmt)

    return result.scalars().first()


async def create_user(db: AsyncSession, username: str, password: str):
    hashed_pw = security.hash_password(password)
    new_user = UserDBModel(username=username, hashed_password=hashed_pw)

    db.add(new_user)

    await db.commit()
    await db.refresh(new_user)
    return new_user
