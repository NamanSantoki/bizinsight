# Tests for EnterpriseNotificationDispatcher (notifications/dispatcher.py)
import pytest
from backend.app.notifications.dispatcher import EnterpriseNotificationDispatcher

@pytest.mark.asyncio
async def test_send_slack_alert_no_url_returns_false():
    result = await EnterpriseNotificationDispatcher.send_slack_alert(
        webhook_url="",
        title="Test",
        message="msg",
    )
    assert result is False

@pytest.mark.asyncio
async def test_send_generic_webhook_no_url_returns_false():
    result = await EnterpriseNotificationDispatcher.send_generic_webhook(
        webhook_url="",
        event_type="test",
        payload={"key": "value"},
    )
    assert result is False

