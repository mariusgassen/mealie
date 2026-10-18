import asyncio
from uuid import uuid4

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


def _record(group_id, label: str = "x", **kwargs) -> None:
    record_request(group_id, request_type=label, model="m", system_prompt="sys", user_message="msg", **kwargs)


def test_requests_are_newest_first_and_bounded():
    group_id = uuid4()
    for i in range(MAX_ENTRIES_PER_GROUP + 5):
        _record(group_id, str(i))

    entries = get_requests(group_id)
    assert len(entries) == MAX_ENTRIES_PER_GROUP
    assert entries[0].request_type == str(MAX_ENTRIES_PER_GROUP + 4)


def test_requests_are_scoped_per_group_and_clearable():
    group_a, group_b = uuid4(), uuid4()
    _record(group_a)

    assert len(get_requests(group_a)) == 1
    assert get_requests(group_b) == []

    clear_requests(group_a)
    assert get_requests(group_a) == []


def test_long_fields_are_truncated():
    group_id = uuid4()
    _record(group_id, raw_response="a" * (MAX_FIELD_LENGTH + 100))

    raw = get_requests(group_id)[0].raw_response
    assert raw is not None
    assert len(raw) < MAX_FIELD_LENGTH + 100
    assert raw.endswith("(truncated)")


def test_non_uuid_group_is_ignored():
    _record(None)


def test_get_response_records_request_and_raw_response(monkeypatch: pytest.MonkeyPatch):
    group_id = uuid4()

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


def test_get_response_records_error(monkeypatch: pytest.MonkeyPatch):
    group_id = uuid4()

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
