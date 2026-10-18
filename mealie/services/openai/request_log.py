from collections import deque
from datetime import UTC, datetime
from uuid import UUID

from mealie.schema.group.ai_debug import AIRequestLogEntry

MAX_ENTRIES_PER_GROUP = 20
MAX_FIELD_LENGTH = 20_000

_entries: dict[UUID, deque[AIRequestLogEntry]] = {}
"""
Recent requests per group, kept in memory only: it is a debugging aid, so it is bounded, not
persisted, and lost on restart (and not shared between workers).
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
    if not isinstance(group_id, UUID):
        return

    entry = AIRequestLogEntry(
        timestamp=datetime.now(UTC),
        request_type=request_type,
        model=model,
        system_prompt=_truncate(system_prompt) or "",
        user_message=_truncate(user_message) or "",
        raw_response=_truncate(raw_response),
        error=_truncate(error),
    )
    _entries.setdefault(group_id, deque(maxlen=MAX_ENTRIES_PER_GROUP)).append(entry)


def get_requests(group_id: UUID) -> list[AIRequestLogEntry]:
    """The group's recent requests, newest first."""

    return list(reversed(_entries.get(group_id, ())))


def clear_requests(group_id: UUID) -> None:
    _entries.pop(group_id, None)
