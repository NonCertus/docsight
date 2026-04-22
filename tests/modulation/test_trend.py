"""Tests for modulation trend summaries."""

from app.modules.modulation.engine import compute_trend


def _make_snapshot(timestamp, us_channels=None, ds_channels=None):
    return {
        "timestamp": timestamp,
        "us_channels": us_channels or [],
        "ds_channels": ds_channels or [],
        "summary": {},
    }


def _make_channels(modulations, docsis_version="3.0"):
    return [
        {"modulation": m, "channel_id": i, "docsis_version": docsis_version}
        for i, m in enumerate(modulations)
    ]


class TestComputeTrend:
    def test_returns_per_day_data(self):
        snaps = [
            _make_snapshot("2026-03-01T10:00:00Z", us_channels=_make_channels(["64QAM", "4QAM"])),
            _make_snapshot("2026-03-02T10:00:00Z", us_channels=_make_channels(["256QAM"])),
        ]
        trend = compute_trend(snaps, "us", "UTC")
        assert len(trend) == 2
        assert trend[0]["date"] == "2026-03-01"
        assert trend[0]["health_index"] is not None
        assert trend[0]["dominant_modulation"] is not None

    def test_empty(self):
        trend = compute_trend([], "us", "UTC")
        assert trend == []

    def test_trend_fields_present(self):
        snaps = [
            _make_snapshot("2026-03-01T10:00:00Z", us_channels=_make_channels(["64QAM"])),
        ]
        trend = compute_trend(snaps, "us", "UTC")
        assert len(trend) == 1
        entry = trend[0]
        assert "date" in entry
        assert "health_index" in entry
        assert "low_qam_pct" in entry
        assert "dominant_modulation" in entry
        assert "sample_count" in entry

    def test_trend_multi_day_order(self):
        snaps = [
            _make_snapshot("2026-03-03T10:00:00Z", us_channels=_make_channels(["64QAM"])),
            _make_snapshot("2026-03-01T10:00:00Z", us_channels=_make_channels(["4QAM"])),
            _make_snapshot("2026-03-02T10:00:00Z", us_channels=_make_channels(["256QAM"])),
        ]
        trend = compute_trend(snaps, "us", "UTC")
        dates = [t["date"] for t in trend]
        assert dates == sorted(dates)
