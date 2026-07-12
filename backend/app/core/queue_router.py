import uuid
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.connection_manager import manager
from app.core.wait_estimator import estimate_wait_minutes
from app.models.ticket import Ticket

router = APIRouter()


def serialize_queue(db: Session, service_type: str):
    """Build the current waiting queue for a service type, with computed positions and wait times."""
    waiting_tickets = (
        db.query(Ticket)
        .filter(Ticket.service_type == service_type, Ticket.status == "waiting")
        .order_by(Ticket.joined_at.asc())
        .all()
    )

    queue = []
    for i, ticket in enumerate(waiting_tickets):
        position = i + 1
        queue.append({
            "ticket_id": str(ticket.id),
            "student_id": ticket.student_id,
            "service_type": ticket.service_type,
            "position": position,
            "joined_at": ticket.joined_at.isoformat(),
            "estimated_wait_minutes": estimate_wait_minutes(db, service_type, position),
        })
    return queue


async def broadcast_queue_update(db: Session, queue_id: str):
    queue = serialize_queue(db, queue_id)
    await manager.broadcast(queue_id, {
        "type": "queue_update",
        "queue": queue,
    })


@router.websocket("/ws/queue/{queue_id}")
async def queue_socket(websocket: WebSocket, queue_id: str):
    await manager.connect(queue_id, websocket)
    db = SessionLocal()
    try:
        # Send current state only to the newly-connected client, not everyone
        queue = serialize_queue(db, queue_id)
        await manager.send_personal(websocket, {
            "type": "queue_update",
            "queue": queue,
        })

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "join_queue":
                ticket = Ticket(
                    id=uuid.uuid4(),
                    student_id=data["student_id"],
                    service_type=queue_id,
                    status="waiting",
                    joined_at=datetime.utcnow(),
                )
                db.add(ticket)
                db.commit()
                await broadcast_queue_update(db, queue_id)

            elif msg_type == "leave_queue":
                ticket = (
                    db.query(Ticket)
                    .filter(Ticket.student_id == data["student_id"], Ticket.status == "waiting")
                    .first()
                )
                if ticket:
                    db.delete(ticket)
                    db.commit()
                await broadcast_queue_update(db, queue_id)

            elif msg_type == "call_next":
                next_ticket = (
                    db.query(Ticket)
                    .filter(Ticket.service_type == queue_id, Ticket.status == "waiting")
                    .order_by(Ticket.joined_at.asc())
                    .first()
                )
                if next_ticket:
                    next_ticket.status = "called"
                    next_ticket.called_at = datetime.utcnow()
                    db.commit()
                    await manager.broadcast(queue_id, {
                        "type": "your_turn",
                        "ticket_id": str(next_ticket.id),
                    })
                    await broadcast_queue_update(db, queue_id)
                else:
                    await manager.send_personal(websocket, {
                        "type": "error",
                        "message": "No one waiting in this queue",
                    })

            elif msg_type == "mark_complete":
                ticket = db.query(Ticket).filter(Ticket.id == data["ticket_id"]).first()
                if ticket:
                    ticket.status = "completed"
                    if not ticket.called_at:
                        ticket.called_at = datetime.utcnow()
                    db.commit()
                    await broadcast_queue_update(db, queue_id)
                else:
                    await manager.send_personal(websocket, {
                        "type": "error",
                        "message": "Ticket not found",
                    })

            elif msg_type == "mark_no_show":
                ticket = db.query(Ticket).filter(Ticket.id == data["ticket_id"]).first()
                if ticket:
                    ticket.status = "no_show"
                    db.commit()
                    await broadcast_queue_update(db, queue_id)
                else:
                    await manager.send_personal(websocket, {
                        "type": "error",
                        "message": "Ticket not found",
                    })

            else:
                await manager.send_personal(websocket, {
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        manager.disconnect(queue_id, websocket)
    finally:
        db.close()