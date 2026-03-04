"""E2E tests for theme (dark/light) support."""

import pytest


class TestTheme:
    """Theme attribute on <html> element."""

    def test_default_theme_is_dark(self, demo_page):
        theme = demo_page.locator("html").get_attribute("data-theme")
        assert theme == "dark"

    def test_settings_has_theme_attribute(self, settings_page):
        theme = settings_page.locator("html").get_attribute("data-theme")
        assert theme in ("dark", "light")

    def test_login_page_has_theme(self, auth_page, auth_server):
        auth_page.goto(f"{auth_server}/login")
        theme = auth_page.locator("html").get_attribute("data-theme")
        assert theme in ("dark", "light")
