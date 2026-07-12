from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.ticket import Ticket


def estimate_wait_minutes(db: Session, service_type: str, position: int) -> int:
    """
    Estimate wait time based on the average handling time of the last
    5 completed tickets for this service type, multiplied by how many
    people are ahead of this position.
    """
    recent_completed = (
        db.query(Ticket)
        .filter(
            Ticket.service_type == service_type,
            Ticket.status == "completed",
            Ticket.called_at.isnot(None),
        )
        .order_by(Ticket.called_at.desc())
        .limit(5)
        .all()
    )

    if not recent_completed:
        # No history yet ? fall back to a reasonable default guess
        avg_minutes_per_person = 10
    else:
        durations = [
            (t.called_at - t.joined_at).total_seconds() / 60
            for t in recent_completed
        ]
        avg_minutes_per_person = sum(durations) / len(durations)

    people_ahead = max(position - 1, 0)
    return round(avg_minutes_per_person * people_ahead)
