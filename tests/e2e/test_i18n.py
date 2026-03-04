"""E2E tests for internationalization (language switching)."""

import pytest


class TestLanguageSwitching:
    """Language can be switched via ?lang= query parameter."""

    def test_default_language_is_english(self, demo_page):
        lang = demo_page.locator("html").get_attribute("lang")
        assert lang == "en"

    def test_switch_to_german(self, page, live_server):
        page.goto(f"{live_server}/?lang=de")
        page.wait_for_load_state("networkidle")
        lang = page.locator("html").get_attribute("lang")
        assert lang == "de"

    def test_switch_to_french(self, page, live_server):
        page.goto(f"{live_server}/?lang=fr")
        page.wait_for_load_state("networkidle")
        lang = page.locator("html").get_attribute("lang")
        assert lang == "fr"

    def test_switch_to_spanish(self, page, live_server):
        page.goto(f"{live_server}/?lang=es")
        page.wait_for_load_state("networkidle")
        lang = page.locator("html").get_attribute("lang")
        assert lang == "es"

    def test_settings_respects_lang_param(self, page, live_server):
        page.goto(f"{live_server}/settings?lang=de")
        page.wait_for_load_state("networkidle")
        lang = page.locator("html").get_attribute("lang")
        assert lang == "de"
