from sqlalchemy import Column, String
from app.core.database import Base


class StaffEmail(Base):
    __tablename__ = "staff_emails"

    email = Column(String, primary_key=True)
