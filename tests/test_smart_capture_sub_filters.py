"""Tests for Smart Capture per-trigger sub-filter functions."""

import pytest
from unittest.mock import MagicMock

from app.smart_capture.sub_filters import (
    modulation_sub_filter,
    snr_sub_filter,
    error_spike_sub_filter,
    health_sub_filter,
    packet_loss_sub_filter,
)


def _config(**overrides):
    defaults = {
        "sc_trigger_modulation_direction": "both",
        "sc_trigger_modulation_min_qam": "",
        "sc_trigger_error_spike_min_delta": 0,
        "sc_trigger_health_level": "any_degradation",
        "sc_trigger_packet_loss_min_pct": "5.0",
    }
    defaults.update(overrides)
    mock = MagicMock()
    mock.get = lambda key, default=None: defaults.get(key, default)
    return mock


class TestModulationSubFilter:
    def _event(self, changes):
        return {"event_type": "modulation_change", "severity": "warning",
                "details": {"direction": "downgrade", "changes": changes}}

    def test_no_filter_passes(self):
        config = _config()
        event = self._event([{"channel": 1, "direction": "DS", "prev_rank": 7, "current_rank": 5}])
        assert modulation_sub_filter(config, event) is True

    def test_direction_ds_only(self):
        config = _config(sc_trigger_modulation_direction="DS")
        event = self._event([
            {"channel": 1, "direction": "US", "prev_rank": 5, "current_rank": 3},
        ])
        assert modulation_sub_filter(config, event) is False

    def test_direction_ds_passes_ds_change(self):
        config = _config(sc_trigger_modulation_direction="DS")
        event = self._event([
            {"channel": 1, "direction": "DS", "prev_rank": 7, "current_rank": 5},
        ])
        assert modulation_sub_filter(config, event) is True

    def test_direction_us_only(self):
        config = _config(sc_trigger_modulation_direction="US")
        event = self._event([
            {"channel": 1, "direction": "DS", "prev_rank": 7, "current_rank": 5},
        ])
        assert modulation_sub_filter(config, event) is False

    def test_min_qam_threshold(self):
        """Only trigger when current rank is below 256QAM (rank 7)."""
        config = _config(sc_trigger_modulation_min_qam="256QAM")
        # 64QAM (rank 5) is below 256QAM (rank 7) → qualifies
        event = self._event([{"channel": 1, "direction": "DS", "prev_rank": 7, "current_rank": 5}])
        assert modulation_sub_filter(config, event) is True

    def test_min_qam_above_threshold(self):
        """Don't trigger when current rank is at or above threshold."""
        config = _config(sc_trigger_modulation_min_qam="64QAM")
        # 256QAM (rank 7) is above 64QAM (rank 5) → does not qualify
        event = self._event([{"channel": 1, "direction": "DS", "prev_rank": 9, "current_rank": 7}])
        assert modulation_sub_filter(config, event) is False

    def test_qualifying_subset_any_match(self):
        """If ANY change qualifies, the filter passes."""
        config = _config(sc_trigger_modulation_direction="DS")
        event = self._event([
            {"channel": 1, "direction": "US", "prev_rank": 5, "current_rank": 3},  # not DS
            {"channel": 2, "direction": "DS", "prev_rank": 7, "current_rank": 5},  # DS → qualifies
        ])
        assert modulation_sub_filter(config, event) is True

    def test_empty_changes_passes(self):
        config = _config()
        event = self._event([])
        assert modulation_sub_filter(config, event) is True


class TestSnrSubFilter:
    def test_always_passes(self):
        config = _config()
        event = {"event_type": "snr_change", "severity": "warning", "details": {}}
        assert snr_sub_filter(config, event) is True


class TestErrorSpikeSubFilter:
    def test_zero_min_delta_passes_all(self):
        config = _config(sc_trigger_error_spike_min_delta=0)
        event = {"event_type": "error_spike", "details": {"delta": 100}}
        assert error_spike_sub_filter(config, event) is True

    def test_min_delta_filters(self):
        config = _config(sc_trigger_error_spike_min_delta=5000)
        event = {"event_type": "error_spike", "details": {"delta": 2000}}
        assert error_spike_sub_filter(config, event) is False

    def test_min_delta_passes(self):
        config = _config(sc_trigger_error_spike_min_delta=1000)
        event = {"event_type": "error_spike", "details": {"delta": 5000}}
        assert error_spike_sub_filter(config, event) is True


class TestHealthSubFilter:
    def test_any_degradation_passes_all(self):
        config = _config(sc_trigger_health_level="any_degradation")
        event = {"event_type": "health_change", "details": {"current": "marginal"}}
        assert health_sub_filter(config, event) is True

    def test_critical_only_blocks_marginal(self):
        config = _config(sc_trigger_health_level="critical_only")
        event = {"event_type": "health_change", "details": {"current": "marginal"}}
        assert health_sub_filter(config, event) is False

    def test_critical_only_passes_critical(self):
        config = _config(sc_trigger_health_level="critical_only")
        event = {"event_type": "health_change", "details": {"current": "critical"}}
        assert health_sub_filter(config, event) is True


class TestPacketLossSubFilter:
    def test_above_threshold_passes(self):
        config = _config(sc_trigger_packet_loss_min_pct="5.0")
        event = {"event_type": "cm_packet_loss_warning",
                 "details": {"packet_loss_pct": 8.5, "target_id": 1}}
        assert packet_loss_sub_filter(config, event) is True

    def test_below_threshold_fails(self):
        config = _config(sc_trigger_packet_loss_min_pct="10.0")
        event = {"event_type": "cm_packet_loss_warning",
                 "details": {"packet_loss_pct": 5.0, "target_id": 1}}
        assert packet_loss_sub_filter(config, event) is False

    def test_equal_threshold_passes(self):
        config = _config(sc_trigger_packet_loss_min_pct="5.0")
        event = {"event_type": "cm_packet_loss_warning",
                 "details": {"packet_loss_pct": 5.0, "target_id": 1}}
        assert packet_loss_sub_filter(config, event) is True
