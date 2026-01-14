from fastapi import Header, HTTPException


async def verify_token(x_api_key: str = Header(...)):
    if x_api_key != "test":
        raise HTTPException(status_code=403, detail="Invalid API Key")
