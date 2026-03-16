"""Tests for community module install/uninstall API endpoints."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

from app.config import ConfigManager
from app.storage import SnapshotStorage
from app.web import app, init_config, init_storage


@pytest.fixture
def storage(tmp_path):
    return SnapshotStorage(str(tmp_path / "test.db"), max_days=7)


@pytest.fixture
def client(tmp_path, storage):
    config_mgr = ConfigManager(str(tmp_path / "config"))
    config_mgr.save({"modem_password": "test", "modem_type": "fritzbox"})
    init_config(config_mgr)
    init_storage(storage)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestModulesRegistry:
    def test_registry_returns_list(self, client):
        with patch("app.blueprints.modules_bp.get_config_manager") as mock_cfg:
            mock_cfg.return_value = MagicMock()
            mock_cfg.return_value.get = MagicMock(return_value="https://raw.githubusercontent.com/itsDNNS/docsight-modules/main/registry.json")
            resp = client.get("/api/modules/registry")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert isinstance(data, list)


class TestModulesInstall:
    def test_rejects_missing_fields(self, client):
        resp = client.post("/api/modules/install",
                           data=json.dumps({}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_rejects_path_traversal(self, client):
        resp = client.post("/api/modules/install",
                           data=json.dumps({"id": "../../../etc/passwd", "download_url": "https://api.github.com/test"}),
                           content_type="application/json")
        data = json.loads(resp.data)
        assert data["success"] is False

    def test_rejects_duplicate_builtin(self, client):
        with patch("app.blueprints.modules_bp.get_module_loader") as mock_loader:
            mock_mod = MagicMock()
            mock_mod.id = "docsight.speedtest"
            mock_loader.return_value.get_modules.return_value = [mock_mod]
            resp = client.post("/api/modules/install",
                               data=json.dumps({"id": "docsight.speedtest", "download_url": "https://api.github.com/test"}),
                               content_type="application/json")
            data = json.loads(resp.data)
            assert data["success"] is False
            assert "conflicts" in data.get("error", "").lower() or resp.status_code == 409


class TestModulesUninstall:
    def test_rejects_missing_id(self, client):
        resp = client.post("/api/modules/uninstall",
                           data=json.dumps({}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_rejects_not_installed(self, client):
        resp = client.post("/api/modules/uninstall",
                           data=json.dumps({"id": "nonexistent.module"}),
                           content_type="application/json")
        assert resp.status_code == 404

    def test_rejects_builtin_uninstall(self, client):
        with patch("app.blueprints.modules_bp._scan_installed_community_ids") as mock_scan, \
             patch("app.blueprints.modules_bp.get_module_loader") as mock_loader:
            mock_scan.return_value = {"docsight.speedtest": "docsight_speedtest"}
            mock_mod = MagicMock()
            mock_mod.id = "docsight.speedtest"
            mock_mod.builtin = True
            mock_loader.return_value.get_modules.return_value = [mock_mod]
            resp = client.post("/api/modules/uninstall",
                               data=json.dumps({"id": "docsight.speedtest"}),
                               content_type="application/json")
            assert resp.status_code == 403
