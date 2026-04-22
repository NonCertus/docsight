"""Tests for analyzer threshold configuration and OFDMA handling."""

import pytest
from unittest.mock import patch
from app import analyzer

_TEST_THRESHOLDS = {
    "downstream_power": {
        "_default": "256QAM",
        "256QAM": {"good": [-4, 13], "warning": [-6, 18], "critical": [-8, 20]},
    },
    "upstream_power": {
        "_default": "sc_qam",
        "sc_qam": {"good": [41, 47], "warning": [37, 51], "critical": [35, 53]},
        "ofdma": {"good": [44, 47], "warning": [40, 48], "critical": [38, 50]},
    },
    "snr": {
        "_default": "256QAM",
        "256QAM": {"good_min": 33, "warning_min": 31, "critical_min": 30},
    },
    "upstream_modulation": {"critical_max_qam": 4, "warning_max_qam": 16},
    "errors": {"uncorrectable_pct": {"warning": 1.0, "critical": 3.0}},
}
from app.analyzer import analyze, _parse_float, _parse_qam_order, _resolve_modulation, _channel_bitrate_mbps, _metric_healths


# -- Helper to build FritzBox-style channel data --

def _make_ds30(channel_id=1, power=3.0, mse="-35.0", corr=0, uncorr=0):
    return {
        "channelID": channel_id,
        "frequency": "602 MHz",
        "powerLevel": str(power),
        "modulation": "256QAM",
        "mse": str(mse),
        "corrErrors": corr,
        "nonCorrErrors": uncorr,
    }


def _make_ds31(channel_id=100, power=5.0, mer="38.0", corr=0, uncorr=0):
    return {
        "channelID": channel_id,
        "frequency": "159 MHz",
        "powerLevel": str(power),
        "modulation": "4096QAM",
        "mer": str(mer),
        "corrErrors": corr,
        "nonCorrErrors": uncorr,
    }


def _make_us30(channel_id=1, power=42.0, modulation="64QAM"):
    return {
        "channelID": channel_id,
        "frequency": "37 MHz",
        "powerLevel": str(power),
        "modulation": modulation,
        "multiplex": "ATDMA",
    }


def _make_data(ds30=None, ds31=None, us30=None, us31=None):
    return {
        "channelDs": {
            "docsis30": ds30 or [],
            "docsis31": ds31 or [],
        },
        "channelUs": {
            "docsis30": us30 or [],
            "docsis31": us31 or [],
        },
    }


# -- parse_float --

class TestSetThresholds:
    """Test dynamic threshold loading."""

    def setup_method(self):
        self._orig = analyzer._thresholds.copy()
        analyzer.set_thresholds(_TEST_THRESHOLDS)

    def teardown_method(self):
        analyzer._thresholds = self._orig

    def test_set_thresholds_updates_global(self):
        assert "downstream_power" in analyzer._thresholds
        assert analyzer._thresholds["downstream_power"]["256QAM"]["good"] == [-4, 13]

    def test_ds_power_getter_reads_array(self):
        t = analyzer._get_ds_power_thresholds("256QAM")
        assert t["good_min"] == -4
        assert t["good_max"] == 13
        assert t["crit_min"] == -8
        assert t["crit_max"] == 20

    def test_us_power_getter_sc_qam(self):
        t = analyzer._get_us_power_thresholds("sc_qam")
        assert t["good_min"] == 41
        assert t["good_max"] == 47

    def test_us_power_getter_ofdma(self):
        t = analyzer._get_us_power_thresholds("ofdma")
        assert t["good_min"] == 44
        assert t["good_max"] == 47

    def test_snr_getter_reads_new_keys(self):
        t = analyzer._get_snr_thresholds("256QAM")
        assert t["good_min"] == 33
        assert t["crit_min"] == 30

    def test_error_threshold_percent(self):
        t = analyzer._get_uncorr_thresholds()
        assert t["warning"] == 1.0
        assert t["critical"] == 3.0

    def test_fallback_when_empty(self):
        analyzer._thresholds = {}
        t = analyzer._get_ds_power_thresholds("256QAM")
        assert t["good_min"] == -4.0  # fallback value (Vodafone pNTP spec v1.06)


class TestOFDMAUpstream:
    """Test OFDMA upstream channel assessment."""

    def setup_method(self):
        self._orig = analyzer._thresholds.copy()
        analyzer.set_thresholds(_TEST_THRESHOLDS)

    def teardown_method(self):
        analyzer._thresholds = self._orig

    def test_ofdma_channel_good(self):
        ch = {"powerLevel": "45.0", "modulation": "OFDMA", "type": "OFDMA"}
        health, detail = analyzer._assess_us_channel(ch)
        assert health == "good"

    def test_ofdma_channel_tolerated(self):
        """OFDMA power 40.5 is tolerated (between warn_min 40.1 and good_min 44.1)."""
        ch = {"powerLevel": "40.5", "modulation": "OFDMA", "type": "OFDMA"}
        health, detail = analyzer._assess_us_channel(ch)
        assert health == "tolerated"

    def test_ofdma_channel_critical_low(self):
        ch = {"powerLevel": "37.0", "modulation": "OFDMA", "type": "OFDMA"}
        health, detail = analyzer._assess_us_channel(ch)
        assert health == "critical"

    def test_sc_qam_still_uses_sc_qam_thresholds(self):
        ch = {"powerLevel": "42.0", "modulation": "64QAM", "type": "ATDMA"}
        health, detail = analyzer._assess_us_channel(ch)
        assert health == "good"

    def test_analyze_preserves_ofdma_profile_modulation(self):
        data = _make_data(
            us31=[{
                "channelID": 5,
                "frequency": "18.000 - 44.000",
                "powerLevel": "40.0",
                "modulation": "OFDMA",
                "profile_modulation": "128QAM",
                "type": "OFDMA",
                "multiplex": "OFDMA",
            }]
        )

        result = analyze(data)
        channel = result["us_channels"][0]
        assert channel["modulation"] == "OFDMA"
        assert channel["profile_modulation"] == "128QAM"
        assert channel["power_health"] in ("warning", "critical", "tolerated")


class TestPercentErrors:
    """Test percent-based error thresholds."""

    def setup_method(self):
        self._orig = analyzer._thresholds.copy()
        analyzer.set_thresholds(_TEST_THRESHOLDS)

    def teardown_method(self):
        analyzer._thresholds = self._orig

    def test_no_errors_healthy(self):
        data = _make_data(ds30=[_make_ds30(1, corr=1000, uncorr=0)])
        result = analyze(data)
        assert "uncorr_errors_high" not in result["summary"]["health_issues"]
        assert "uncorr_errors_critical" not in result["summary"]["health_issues"]

    def test_warning_threshold(self):
        # 1% uncorrectable => warning
        data = _make_data(ds30=[_make_ds30(1, corr=9900, uncorr=100)])
        result = analyze(data)
        assert "uncorr_errors_high" in result["summary"]["health_issues"]

    def test_critical_threshold(self):
        # 5% uncorrectable => critical
        data = _make_data(ds30=[_make_ds30(1, corr=9500, uncorr=500)])
        result = analyze(data)
        assert "uncorr_errors_critical" in result["summary"]["health_issues"]

    def test_zero_codewords_no_error(self):
        data = _make_data(ds30=[_make_ds30(1, corr=0, uncorr=0)])
        result = analyze(data)
        assert "uncorr_errors_high" not in result["summary"]["health_issues"]
        assert "uncorr_errors_critical" not in result["summary"]["health_issues"]

    def test_below_min_codewords_suppressed(self):
        # 50% uncorrectable but only 6 total codewords — below min_codewords threshold
        data = _make_data(ds30=[_make_ds30(1, corr=3, uncorr=3)])
        result = analyze(data)
        assert result["summary"]["ds_uncorr_pct"] == 0.0
        assert "uncorr_errors_high" not in result["summary"]["health_issues"]
        assert "uncorr_errors_critical" not in result["summary"]["health_issues"]

