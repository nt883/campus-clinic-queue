import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TicketBase(BaseModel):
    student_id: str
    service_type: str


class TicketCreate(TicketBase):
    pass


class TicketResponse(TicketBase):
    id: uuid.UUID
    status: str
    joined_at: datetime
    called_at: Optional[datetime] = None
    position: Optional[int] = None  # computed, not stored

    class Config:
        from_attributes = True


class QueueUpdateMessage(BaseModel):
    type: str = "queue_update"
    queue: list[TicketResponse]
    estimated_wait_minutes: Optional[int] = None
