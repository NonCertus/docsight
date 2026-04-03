"""Tests for enriched speedtest storage schema (18 new columns)."""

import sqlite3
import pytest

from app.modules.speedtest.storage import SpeedtestStorage


ENRICHED_COLUMNS = [
    "isp", "server_host", "server_location", "server_country", "server_ip",
    "ping_low", "ping_high", "dl_latency_iqm", "dl_latency_jitter",
    "ul_latency_iqm", "ul_latency_jitter", "dl_bytes", "ul_bytes",
    "dl_elapsed_ms", "ul_elapsed_ms", "external_ip", "is_vpn", "result_url",
]


def _get_columns(db_path):
    with sqlite3.connect(db_path) as conn:
        return [r[1] for r in conn.execute("PRAGMA table_info(speedtest_results)").fetchall()]


def test_ensure_table_creates_enriched_columns(tmp_path):
    """All 18 enriched columns must exist after SpeedtestStorage init."""
    db_path = str(tmp_path / "speedtest.db")
    SpeedtestStorage(db_path)
    cols = _get_columns(db_path)
    for col in ENRICHED_COLUMNS:
        assert col in cols, f"Missing enriched column: {col}"


def test_save_upserts_enriched_fields(tmp_path):
    """Saving a result twice should update enriched fields on the second insert."""
    db_path = str(tmp_path / "speedtest.db")
    storage = SpeedtestStorage(db_path)

    base_result = {
        "id": 42,
        "timestamp": "2026-01-01T12:00:00Z",
        "download_mbps": 500.0,
        "upload_mbps": 50.0,
        "download_human": "500 Mbps",
        "upload_human": "50 Mbps",
        "ping_ms": 10.0,
        "jitter_ms": 1.0,
        "packet_loss_pct": 0.0,
        "server_id": 1,
        "server_name": "Test Server",
        # enriched fields absent on first save
    }

    # First insert - no enriched data
    storage.save_speedtest_results([base_result])

    # Verify enriched fields are NULL after first insert
    row = storage.get_speedtest_by_id(42)
    assert row is not None
    assert row["isp"] is None
    assert row["result_url"] is None
    assert row["is_vpn"] is None

    # Second insert with enriched data
    enriched_result = {
        **base_result,
        "isp": "Deutsche Telekom",
        "server_host": "speedtest.telekom.de",
        "server_location": "Frankfurt",
        "server_country": "Germany",
        "server_ip": "1.2.3.4",
        "ping_low": 8.5,
        "ping_high": 14.2,
        "dl_latency_iqm": 11.1,
        "dl_latency_jitter": 0.9,
        "ul_latency_iqm": 12.3,
        "ul_latency_jitter": 1.2,
        "dl_bytes": 654321,
        "ul_bytes": 123456,
        "dl_elapsed_ms": 9000,
        "ul_elapsed_ms": 8500,
        "external_ip": "5.6.7.8",
        "is_vpn": False,
        "result_url": "https://www.speedtest.net/result/c/abc123",
    }
    storage.save_speedtest_results([enriched_result])

    # Verify enriched fields are updated
    row = storage.get_speedtest_by_id(42)
    assert row is not None
    assert row["isp"] == "Deutsche Telekom"
    assert row["server_host"] == "speedtest.telekom.de"
    assert row["server_location"] == "Frankfurt"
    assert row["server_country"] == "Germany"
    assert row["server_ip"] == "1.2.3.4"
    assert row["ping_low"] == pytest.approx(8.5)
    assert row["ping_high"] == pytest.approx(14.2)
    assert row["dl_latency_iqm"] == pytest.approx(11.1)
    assert row["dl_latency_jitter"] == pytest.approx(0.9)
    assert row["ul_latency_iqm"] == pytest.approx(12.3)
    assert row["ul_latency_jitter"] == pytest.approx(1.2)
    assert row["dl_bytes"] == 654321
    assert row["ul_bytes"] == 123456
    assert row["dl_elapsed_ms"] == 9000
    assert row["ul_elapsed_ms"] == 8500
    assert row["external_ip"] == "5.6.7.8"
    assert row["is_vpn"] == 0  # False -> 0 in SQLite
    assert row["result_url"] == "https://www.speedtest.net/result/c/abc123"

    # Original fields must not change on upsert
    assert row["download_mbps"] == pytest.approx(500.0)
    assert row["ping_ms"] == pytest.approx(10.0)
    assert row["server_name"] == "Test Server"
