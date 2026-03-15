"""E2E tests for the settings page."""

import pytest
from playwright.sync_api import expect


class TestSettingsLoad:
    """Settings page loads correctly."""

    def test_page_title(self, settings_page):
        assert "DOCSight" in settings_page.title()
        assert "Settings" in settings_page.title() or "Einstellungen" in settings_page.title()

    def test_sidebar_visible(self, settings_page):
        sidebar = settings_page.locator("#settings-sidebar")
        assert sidebar.is_visible()

    def test_connection_tab_active(self, settings_page):
        btn = settings_page.locator('button[data-section="connection"]')
        assert "active" in btn.get_attribute("class")


class TestSettingsTabSwitching:
    """Clicking sidebar tabs shows the correct panel."""

    @pytest.mark.parametrize("section", [
        "general",
        "security",
        "appearance",
        "notifications",
        "extensions",
    ])
    def test_switch_to_section(self, settings_page, section):
        btn = settings_page.locator(f'button[data-section="{section}"]')
        btn.click()
        panel = settings_page.locator(f'#panel-{section}, [id="panel-{section}"]')
        assert panel.is_visible()

    def test_switch_back_to_connection(self, settings_page):
        settings_page.locator('button[data-section="general"]').click()
        settings_page.locator('button[data-section="connection"]').click()
        panel = settings_page.locator("#panel-connection")
        assert panel.is_visible()


class TestSettingsFormElements:
    """Form elements exist on settings panels."""

    def test_connection_has_modem_type_select(self, settings_page):
        select = settings_page.locator('select[name="modem_type"], #modem_type, #modem-type')
        assert select.count() > 0

    def test_security_has_password_field(self, settings_page):
        settings_page.locator('button[data-section="security"]').click()
        pw = settings_page.locator('input[type="password"]')
        assert pw.count() > 0

    def test_back_to_dashboard_link(self, settings_page):
        link = settings_page.locator('a[href="/"]')
        assert link.count() > 0


class TestSpeedtestModule:
    """Speedtest module settings interactions."""

    def test_speedtest_section_shows_test_button(self, settings_page):
        settings_page.locator('button[data-section="mod-docsight_speedtest"]').click()

        button = settings_page.get_by_role("button", name="Test Connection")
        assert button.is_visible()

    def test_speedtest_test_connection_success(self, settings_page):
        settings_page.route(
            "**/api/test-speedtest",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body="""
                {
                  "success": true,
                  "results": 1,
                  "latest": {
                    "download": "120.50 Mbps",
                    "upload": "24.10 Mbps",
                    "ping": "11.4 ms"
                  }
                }
                """,
            ),
        )

        settings_page.locator('button[data-section="mod-docsight_speedtest"]').click()
        settings_page.get_by_role("button", name="Test Connection").click()

        result = settings_page.locator("#speedtest-test")
        expect(result).to_be_visible()
        expect(result).to_contain_text("Connected")
        expect(result).to_contain_text("120.50 Mbps")
        expect(result).to_contain_text("24.10 Mbps")
        expect(result).to_contain_text("11.4 ms")

    def test_speedtest_test_connection_error(self, settings_page):
        settings_page.route(
            "**/api/test-speedtest",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body='{"success": false, "error": "HTTP 401"}',
            ),
        )

        settings_page.locator('button[data-section="mod-docsight_speedtest"]').click()
        settings_page.get_by_role("button", name="Test Connection").click()

        result = settings_page.locator("#speedtest-test")
        expect(result).to_be_visible()
        expect(result).to_contain_text("Error")
        expect(result).to_contain_text("HTTP 401")


class TestBackupModule:
    """Backup module settings interactions."""

    def test_backup_section_loads_existing_backups(self, settings_page):
        settings_page.route(
            "**/api/backup/list",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body="""
                [
                  {
                    "filename": "docsight_backup_2026-03-14_120000.tar.gz",
                    "size": 3145728,
                    "modified": "2026-03-14T12:00:00"
                  }
                ]
                """,
            ),
        )

        settings_page.locator('button[data-section="mod-docsight_backup"]').click()

        backup_list = settings_page.locator("#backup-list")
        assert backup_list.locator("code").first.text_content() == "docsight_backup_2026-03-14_120000.tar.gz"
        assert backup_list.get_by_text("3.0 MB").count() > 0
