from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.database import engine, Base
from app.models.ticket import Ticket
from app.core.queue_router import router as queue_router

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


app.include_router(queue_router)