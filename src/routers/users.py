from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def read_users():
    return {"message": "Read all users"}

@router.get("/{user_id}")
async def read_user(user_id: int):
    return {"message": f"Read user {user_id}"}