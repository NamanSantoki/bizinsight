# Tests for Notification Dispatcher Slack alert with webhook (notifications/dispatcher.py)
import pytest
import asyncio
from backend.app.notifications.dispatcher import EnterpriseNotificationDispatcher

class DummyResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code

class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
    async def post(self, url, json):
        # Simulate a successful post when a known URL is provided
        if url == "https://example.com/webhook":
            return DummyResponse(200)
        return DummyResponse(400)

@pytest.fixture(autouse=True)
def patch_httpx(monkeypatch):
    # Patch httpx.AsyncClient globally for the duration of the test session
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

@pytest.mark.asyncio
async def test_send_slack_alert_success():
    result = await EnterpriseNotificationDispatcher.send_slack_alert(
        webhook_url="https://example.com/webhook",
        title="Alert",
        message="Test message",
        severity="critical",
        fields={"env": "test"},
    )
    assert result is True

@pytest.mark.asyncio
async def test_send_slack_alert_failure_invalid_url():
    result = await EnterpriseNotificationDispatcher.send_slack_alert(
        webhook_url="https://invalid-url",
        title="Alert",
        message="Test",
    )
    assert result is False

