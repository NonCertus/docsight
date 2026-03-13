"""E2E tests for the settings page."""

import pytest


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
