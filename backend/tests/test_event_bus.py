import pytest
from backend.app.events.event_bus import (
    DistributedEventBus,
    EventMessage,
    EnterpriseEventType,
    event_bus
)

def test_event_message_creation_and_dict():
    msg = EventMessage(
        event_type=EnterpriseEventType.DATASET_UPLOADED,
        payload={"dataset_id": 1, "records": 100},
        tenant_id="tenant_alpha",
        producer="test_runner",
        correlation_id="corr_12345"
    )
    d = msg.to_dict()
    assert d["event_type"] == EnterpriseEventType.DATASET_UPLOADED
    assert d["payload"]["records"] == 100
    assert d["tenant_id"] == "tenant_alpha"
    assert d["producer"] == "test_runner"
    assert d["correlation_id"] == "corr_12345"
    assert "timestamp" in d
    assert d["event_id"].startswith("evt_")

def test_distributed_event_bus_publish_subscribe():
    bus = DistributedEventBus()
    received = []

    def handler(msg: EventMessage):
        received.append(msg)

    bus.subscribe(EnterpriseEventType.QUALITY_CHECK_COMPLETED, handler)

    published = bus.publish(
        event_type=EnterpriseEventType.QUALITY_CHECK_COMPLETED,
        payload={"score": 99.5, "gate": "PASSED"}
    )

    assert len(received) == 1
    assert received[0].event_id == published.event_id
    assert received[0].payload["score"] == 99.5

def test_distributed_event_bus_handler_exception():
    bus = DistributedEventBus()

    def faulty_handler(msg: EventMessage):
        raise RuntimeError("Handler failure")

    bus.subscribe(EnterpriseEventType.MODEL_DRIFT_DETECTED, faulty_handler)
    # Should not raise exception
    msg = bus.publish(EnterpriseEventType.MODEL_DRIFT_DETECTED, {"drift_pct": 5.0})
    assert msg.event_type == EnterpriseEventType.MODEL_DRIFT_DETECTED

def test_distributed_event_bus_webhooks():
    bus = DistributedEventBus()
    hook = bus.register_webhook(
        url="https://hooks.slack.com/services/T00/B00/X00",
        subscribed_events=[EnterpriseEventType.INCIDENT_RAISED],
        tenant_id="enterprise_corp"
    )

    assert hook["active"] is True
    assert hook["deliveries_count"] == 0

    webhooks = bus.list_webhooks(tenant_id="enterprise_corp")
    assert len(webhooks) == 1
    assert webhooks[0]["url"] == "https://hooks.slack.com/services/T00/B00/X00"

    # Publish matching event
    bus.publish(
        event_type=EnterpriseEventType.INCIDENT_RAISED,
        payload={"severity": "P1", "service": "data-pipeline"},
        tenant_id="enterprise_corp"
    )
    assert hook["deliveries_count"] == 1

def test_distributed_event_bus_list_recent():
    bus = DistributedEventBus()
    events = bus.list_recent_events(limit=5)
    assert len(events) <= 5

    # Filter by tenant
    tenant_events = bus.list_recent_events(tenant_id="non_existent_tenant")
    assert len(tenant_events) == 0

def test_global_singleton_event_bus():
    assert event_bus is not None
    recent = event_bus.list_recent_events(limit=10)
    assert len(recent) > 0

