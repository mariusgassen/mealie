from uuid import UUID

import sqlalchemy as sa

from mealie.core.root_logger import get_logger
from mealie.db.db_setup import session_context
from mealie.db.models.group.ai_request_log import AIRequestLog
from mealie.schema.group.ai_debug import AIRequestLogEntry

logger = get_logger()

MAX_ENTRIES_PER_GROUP = 20
MAX_FIELD_LENGTH = 20_000
"""
Recent requests are persisted per group, but only as a debugging aid, so each group keeps just its
newest `MAX_ENTRIES_PER_GROUP` and every field is capped at `MAX_FIELD_LENGTH` characters.
"""


def _truncate(value: str | None) -> str | None:
    if value is None or len(value) <= MAX_FIELD_LENGTH:
        return value

    return value[:MAX_FIELD_LENGTH] + "\n… (truncated)"


def record_request(
    group_id: object,
    *,
    request_type: str,
    model: str,
    system_prompt: str,
    user_message: str,
    raw_response: str | None = None,
    error: str | None = None,
) -> None:
    """Persist one request. This is a debugging aid, so a failure to log must never break the AI call itself."""
    if not isinstance(group_id, UUID):
        return

    try:
        with session_context() as session:
            session.add(
                AIRequestLog(
                    session=session,
                    group_id=group_id,
                    request_type=request_type,
                    model=model,
                    system_prompt=_truncate(system_prompt) or "",
                    user_message=_truncate(user_message) or "",
                    raw_response=_truncate(raw_response),
                    error=_truncate(error),
                )
            )
            session.flush()

            stale_ids = (
                sa.select(AIRequestLog.id)
                .where(AIRequestLog.group_id == group_id)
                .order_by(AIRequestLog.created_at.desc(), AIRequestLog.id)
                .offset(MAX_ENTRIES_PER_GROUP)
            )
            session.execute(sa.delete(AIRequestLog).where(AIRequestLog.id.in_(stale_ids)))
            session.commit()
    except Exception:
        logger.warning("Failed to record AI request log entry", exc_info=True)


def get_requests(group_id: UUID) -> list[AIRequestLogEntry]:
    """The group's recent requests, newest first."""

    with session_context() as session:
        rows = session.scalars(
            sa.select(AIRequestLog)
            .where(AIRequestLog.group_id == group_id)
            .order_by(AIRequestLog.created_at.desc(), AIRequestLog.id)
            .limit(MAX_ENTRIES_PER_GROUP)
        ).all()

        return [
            AIRequestLogEntry(
                timestamp=row.created_at,  # type: ignore[arg-type]
                request_type=row.request_type,
                model=row.model,
                system_prompt=row.system_prompt,
                user_message=row.user_message,
                raw_response=row.raw_response,
                error=row.error,
            )
            for row in rows
        ]


def clear_requests(group_id: UUID) -> None:
    with session_context() as session:
        session.execute(sa.delete(AIRequestLog).where(AIRequestLog.group_id == group_id))
        session.commit()
