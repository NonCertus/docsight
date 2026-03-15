"""Tests for Smart Capture STT adapter and collector import hook."""

import pytest
from unittest.mock import MagicMock, patch

from app.modules.speedtest.collector import SpeedtestCollector
from app.storage import SnapshotStorage
from app.smart_capture.types import ExecutionStatus


@pytest.fixture
def storage(tmp_path):
    return SnapshotStorage(str(tmp_path / "test.db"), max_days=7)


class TestCollectorOnImport:
    def _make_collector(self):
        config = MagicMock()
        config.get = MagicMock(side_effect=lambda k, d=None: {
            "speedtest_tracker_url": "http://stt:8999",
            "speedtest_tracker_token": "test-token",
        }.get(k, d))
        config.is_speedtest_configured = MagicMock(return_value=True)
        storage = MagicMock()
        storage.db_path = ":memory:"
        web = MagicMock()
        with patch("app.modules.speedtest.collector.SpeedtestStorage"):
            collector = SpeedtestCollector(config_mgr=config, storage=storage, web=web)
        collector._storage = MagicMock()
        return collector

    def test_on_import_called_with_new_results_on_delta_sync(self):
        collector = self._make_collector()
        callback = MagicMock()
        collector.on_import = callback

        # Cache is warm (>= 50), so delta sync path is used
        collector._storage.get_latest_speedtest_id.return_value = 10
        collector._storage.get_speedtest_count.return_value = 100

        new_results = [
            {"id": 11, "timestamp": "2026-03-15T10:00:00Z", "download_mbps": 100.0,
             "upload_mbps": 20.0, "download_human": "100 Mbps", "upload_human": "20 Mbps",
             "ping_ms": 10.0, "jitter_ms": 1.0, "packet_loss_pct": 0.0},
        ]

        mock_client = MagicMock()
        mock_client.get_newer_than.return_value = new_results
        mock_client.get_latest_with_error.return_value = (new_results[:1], None)
        collector._client = mock_client
        collector._last_url = "http://stt:8999"  # prevent _ensure_client from overwriting
        collector.collect()

        callback.assert_called_once()
        imported = callback.call_args[0][0]
        assert len(imported) == 1
        assert imported[0]["id"] == 11

    def test_on_import_skipped_during_initial_backfill(self):
        collector = self._make_collector()
        callback = MagicMock()
        collector.on_import = callback

        # Cache is small (< 50), so backfill path is used
        collector._storage.get_latest_speedtest_id.return_value = 0
        collector._storage.get_speedtest_count.return_value = 0

        backfill_results = [
            {"id": i, "timestamp": f"2026-03-{i:02d}T10:00:00Z", "download_mbps": 100.0,
             "upload_mbps": 20.0, "download_human": "100 Mbps", "upload_human": "20 Mbps",
             "ping_ms": 10.0, "jitter_ms": 1.0, "packet_loss_pct": 0.0}
            for i in range(1, 20)
        ]

        mock_client = MagicMock()
        mock_client.get_results.return_value = backfill_results
        mock_client.get_latest_with_error.return_value = (backfill_results[-1:], None)
        collector._client = mock_client
        collector._last_url = "http://stt:8999"
        collector.collect()

        callback.assert_not_called()

    def test_on_import_not_called_when_no_new_results(self):
        collector = self._make_collector()
        callback = MagicMock()
        collector.on_import = callback

        collector._storage.get_latest_speedtest_id.return_value = 10
        collector._storage.get_speedtest_count.return_value = 100

        mock_client = MagicMock()
        mock_client.get_newer_than.return_value = []
        mock_client.get_latest_with_error.return_value = ([], None)
        collector._client = mock_client
        collector._last_url = "http://stt:8999"
        collector.collect()

        callback.assert_not_called()
