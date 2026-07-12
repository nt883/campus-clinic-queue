from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import engine, Base, get_db
from app.models.ticket import Ticket
from app.models.staff_email import StaffEmail
from app.core.queue_router import router as queue_router
from app.core.auth import get_current_user, get_role_for_email

app = FastAPI(title="Campus Clinic Queue Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def health_check_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "database connected"}


@app.get("/me")
async def get_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    email = user.get("email")
    role = get_role_for_email(db, email)
    return {"email": email, "role": role}


app.include_router(queue_router)