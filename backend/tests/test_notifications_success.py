# Tests for successful notifications (notifications/dispatcher.py)
import pytest
import asyncio
from backend.app.notifications.dispatcher import EnterpriseNotificationDispatcher

class DummyResponseSuccess:
    def __init__(self):
        self.status_code = 200

class DummyAsyncClientSuccess:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
    async def post(self, url, json):
        # Simulate successful delivery for any URL that contains "success"
        if "success" in url:
            return DummyResponseSuccess()
        return DummyResponseSuccess()

@pytest.fixture(autouse=True)
def patch_httpx_success(monkeypatch):
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClientSuccess)

@pytest.mark.asyncio
async def test_send_slack_alert_success():
    result = await EnterpriseNotificationDispatcher.send_slack_alert(
        webhook_url="https://example.com/success",
        title="OK",
        message="All good",
        severity="info",
        fields={"key": "value"},
    )
    assert result is True

@pytest.mark.asyncio
async def test_send_generic_webhook_success():
    result = await EnterpriseNotificationDispatcher.send_generic_webhook(
        webhook_url="https://example.com/success",
        event_type="event",
        payload={"data": 123},
    )
    assert result is True

