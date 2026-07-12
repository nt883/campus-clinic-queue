import os
import httpx
from fastapi import Header, HTTPException
from sqlalchemy.orm import Session
from app.models.staff_email import StaffEmail

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")


async def verify_supabase_token(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
            },
        )
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return response.json()


def get_role_for_email(db: Session, email: str) -> str:
    is_staff = db.query(StaffEmail).filter(StaffEmail.email == email).first()
    return "staff" if is_staff else "student"


async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ")
    user_data = await verify_supabase_token(token)
    return user_data
