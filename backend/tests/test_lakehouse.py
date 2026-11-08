import pytest
from backend.app.lakehouse.parquet_lake import (
    TechnicalLakehouseEngine,
    LakehouseSnapshot,
    lakehouse_engine
)

def test_lakehouse_snapshot_to_dict():
    snap = LakehouseSnapshot(
        snapshot_id="snap_test_01",
        table_name="orders",
        layer="Bronze",
        operation="APPEND",
        records_count=1000,
        schema={"id": "int64"},
        timestamp="2026-11-08 12:00:00 UTC",
        commit_hash="abc1234",
        data_summary={"format": "Parquet"}
    )
    d = snap.to_dict()
    assert d["snapshot_id"] == "snap_test_01"
    assert d["table_name"] == "orders"
    assert d["layer"] == "Bronze"
    assert d["records_count"] == 1000

def test_technical_lakehouse_list_snapshots():
    engine = TechnicalLakehouseEngine()
    snapshots = engine.list_snapshots("sales_orders")
    assert len(snapshots) >= 3
    assert any(s["layer"] == "Gold" for s in snapshots)

    empty = engine.list_snapshots("unknown_table")
    assert empty == []

def test_technical_lakehouse_time_travel():
    engine = TechnicalLakehouseEngine()
    
    # Query specific snapshot ID
    res = engine.time_travel_query("sales_orders", "snap_001_bronze")
    assert res["status"] == "success"
    assert res["resolved_snapshot"]["snapshot_id"] == "snap_001_bronze"
    assert res["storage_layer"] == "Bronze"

    # Fallback to closest snapshot for non-exact match
    fallback_res = engine.time_travel_query("sales_orders", "2026-11-01 00:00:00 UTC")
    assert fallback_res["status"] == "success"
    assert "resolved_snapshot" in fallback_res

    # Query unknown table
    err_res = engine.time_travel_query("missing_table", "snap_001")
    assert "error" in err_res

def test_technical_lakehouse_evolve_schema():
    engine = TechnicalLakehouseEngine()
    evolved = engine.evolve_schema("sales_orders", "discount_code", "string")
    assert evolved["operation"] == "SCHEMA_EVOLVE"
    assert "discount_code" in evolved["schema"]

    # Unknown table
    err = engine.evolve_schema("unknown_table", "col1", "int")
    assert "error" in err

def test_global_lakehouse_singleton():
    assert lakehouse_engine is not None
    snaps = lakehouse_engine.list_snapshots("sales_orders")
    assert len(snaps) > 0

