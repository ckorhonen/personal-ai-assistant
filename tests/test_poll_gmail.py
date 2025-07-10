import asyncio
from unittest.mock import MagicMock

import pytest

import src.app as app


@pytest.mark.asyncio
async def test_poll_gmail_pushes_vip(monkeypatch):
    msgs = [{"id": "1", "historyId": "10"}]

    monkeypatch.setattr(app, "gmail_service", object())

    fetch = lambda service, last: msgs
    monkeypatch.setattr(app, "fetch_new_messages", fetch)

    classify = lambda m: "vip"
    monkeypatch.setattr(app, "classify_importance", classify)

    pushed = []

    def push_email(msg, kind):
        pushed.append((msg, kind))

    monkeypatch.setattr(app.TelegramChannel, "push_email", push_email)

    db = MagicMock()
    db.get.return_value = "0"
    monkeypatch.setattr(app, "db", db)

    async def fake_sleep(_):
        raise asyncio.CancelledError()

    monkeypatch.setattr(app.asyncio, "sleep", fake_sleep)

    await app.poll_gmail()

    assert pushed == [(msgs[0], "vip")]
    db.set.assert_called_with("last_history_id", "10")

