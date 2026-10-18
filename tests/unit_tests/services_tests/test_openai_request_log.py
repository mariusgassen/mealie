import asyncio
from uuid import UUID

import pytest

from mealie.schema.openai.general import OpenAIText
from mealie.services.openai import OpenAIService
from mealie.services.openai.request_log import (
    MAX_ENTRIES_PER_GROUP,
    MAX_FIELD_LENGTH,
    clear_requests,
    get_requests,
    record_request,
)
from tests.fixtures.fixture_multitenant import MultiTenant
from tests.utils.fixture_schemas import TestUser


@pytest.fixture
def group_id(unique_user: TestUser) -> UUID:
    """The unique_user group is shared by the whole module and the log is persisted, so start each test empty."""
    gid = UUID(unique_user.group_id)
    clear_requests(gid)
    return gid


def _record(group_id, label: str = "x", **kwargs) -> None:
    record_request(group_id, request_type=label, model="m", system_prompt="sys", user_message="msg", **kwargs)


def test_requests_are_newest_first_and_bounded(group_id: UUID):
    for i in range(MAX_ENTRIES_PER_GROUP + 5):
        _record(group_id, str(i))

    entries = get_requests(group_id)
    assert len(entries) == MAX_ENTRIES_PER_GROUP
    assert entries[0].request_type == str(MAX_ENTRIES_PER_GROUP + 4)


def test_requests_are_scoped_per_group_and_clearable(multitenants: MultiTenant):
    group_a, group_b = UUID(multitenants.user_one.group_id), UUID(multitenants.user_two.group_id)
    _record(group_a)

    assert len(get_requests(group_a)) == 1
    assert get_requests(group_b) == []

    clear_requests(group_a)
    assert get_requests(group_a) == []


def test_long_fields_are_truncated(group_id: UUID):
    _record(group_id, raw_response="a" * (MAX_FIELD_LENGTH + 100))

    raw = get_requests(group_id)[0].raw_response
    assert raw is not None
    assert len(raw) < MAX_FIELD_LENGTH + 100
    assert raw.endswith("(truncated)")


def test_non_uuid_group_is_ignored():
    _record(None)


def test_get_response_records_request_and_raw_response(monkeypatch: pytest.MonkeyPatch, group_id: UUID):

    async def fake_raw_response(self, prompt, content, response_schema, provider):
        self._last_raw_response = '{"text": "hi"}'
        return OpenAIText(text="hi")

    monkeypatch.setattr(OpenAIService, "_get_raw_response", fake_raw_response)

    service = OpenAIService.__new__(OpenAIService)
    service.repos = type("Repos", (), {"group_id": group_id})()  # type: ignore[assignment]
    provider = type("Provider", (), {"model": "test-model"})()

    asyncio.run(service.get_response("the prompt", "the input", response_schema=OpenAIText, provider=provider))  # type: ignore[arg-type]

    entry = get_requests(group_id)[0]
    assert entry.model == "test-model"
    assert entry.system_prompt == "the prompt"
    assert entry.user_message == "the input"
    assert entry.raw_response == '{"text": "hi"}'
    assert entry.error is None


def test_get_response_records_error(monkeypatch: pytest.MonkeyPatch, group_id: UUID):

    async def failing_raw_response(self, prompt, content, response_schema, provider):
        self._last_raw_response = "not json"
        raise ValueError("bad response")

    monkeypatch.setattr(OpenAIService, "_get_raw_response", failing_raw_response)

    service = OpenAIService.__new__(OpenAIService)
    service.repos = type("Repos", (), {"group_id": group_id})()  # type: ignore[assignment]
    provider = type("Provider", (), {"model": "test-model"})()

    with pytest.raises(Exception, match="bad response"):
        asyncio.run(service.get_response("p", "m", response_schema=OpenAIText, provider=provider))  # type: ignore[arg-type]

    entry = get_requests(group_id)[0]
    assert entry.raw_response == "not json"
    assert entry.error is not None
    assert "bad response" in entry.error


def test_requests_are_persisted_across_sessions(group_id: UUID):
    _record(group_id, "persisted", raw_response="kept")

    # get_requests opens its own session, so this reads what was committed rather than any in-process state
    entries = get_requests(group_id)
    assert [e.request_type for e in entries] == ["persisted"]
    assert entries[0].raw_response == "kept"


def test_record_request_never_raises(monkeypatch: pytest.MonkeyPatch, group_id: UUID):
    def failing_session_context():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr("mealie.services.openai.request_log.session_context", failing_session_context)

    _record(group_id)
