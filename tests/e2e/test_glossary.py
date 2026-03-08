"""E2E tests for in-app glossary tooltips."""

import pytest
from playwright.sync_api import expect


class TestGlossaryPresence:
    """Verify glossary hint icons are rendered on the dashboard."""

    def test_snr_card_has_glossary_hint(self, demo_page):
        hint = demo_page.locator('#view-dashboard .metric-card .glossary-hint').first
        expect(hint).to_be_visible()

    def test_glossary_hint_has_info_icon(self, demo_page):
        icon = demo_page.locator('#view-dashboard .glossary-hint svg').first
        expect(icon).to_be_visible()

    def test_multiple_glossary_hints_on_dashboard(self, demo_page):
        hints = demo_page.locator('#view-dashboard .glossary-hint')
        assert hints.count() >= 4, f"Expected at least 4 glossary hints, got {hints.count()}"


class TestGlossaryPopover:
    """Verify popover open/close behavior."""

    def test_popover_hidden_by_default(self, demo_page):
        popover = demo_page.locator('#view-dashboard .glossary-popover').first
        expect(popover).not_to_be_visible()

    def test_click_opens_popover(self, demo_page):
        hint = demo_page.locator('#view-dashboard .glossary-hint').first
        hint.click()
        popover = hint.locator('.glossary-popover')
        expect(popover).to_be_visible()

    def test_popover_has_text_content(self, demo_page):
        hint = demo_page.locator('#view-dashboard .glossary-hint').first
        hint.click()
        popover = hint.locator('.glossary-popover')
        text = popover.text_content()
        assert len(text) > 20, f"Popover text too short: {text}"

    def test_click_outside_closes_popover(self, demo_page):
        hint = demo_page.locator('#view-dashboard .glossary-hint').first
        hint.click()
        popover = hint.locator('.glossary-popover')
        expect(popover).to_be_visible()
        demo_page.locator('body').click(position={"x": 10, "y": 10})
        expect(popover).not_to_be_visible()

    def test_escape_closes_popover(self, demo_page):
        hint = demo_page.locator('#view-dashboard .glossary-hint').first
        hint.click()
        popover = hint.locator('.glossary-popover')
        expect(popover).to_be_visible()
        demo_page.keyboard.press("Escape")
        expect(popover).not_to_be_visible()

    def test_clicking_second_hint_closes_first(self, demo_page):
        hints = demo_page.locator('#view-dashboard .glossary-hint')
        first = hints.nth(0)
        second = hints.nth(1)
        first.click()
        expect(first.locator('.glossary-popover')).to_be_visible()
        second.click()
        expect(first.locator('.glossary-popover')).not_to_be_visible()
        expect(second.locator('.glossary-popover')).to_be_visible()


class TestGlossaryChannels:
    """Verify glossary hints in channel tables."""

    def test_ds_channel_group_has_glossary_hint(self, demo_page):
        demo_page.locator('a.nav-item[data-view="channels"]').click()
        demo_page.wait_for_timeout(500)
        hint = demo_page.locator('#view-channels .docsis-group-header .glossary-hint').first
        expect(hint).to_be_visible()

    def test_channel_glossary_popover_works(self, demo_page):
        demo_page.locator('a.nav-item[data-view="channels"]').click()
        demo_page.wait_for_timeout(500)
        hint = demo_page.locator('#view-channels .docsis-group-header .glossary-hint').first
        hint.click()
        popover = hint.locator('.glossary-popover')
        expect(popover).to_be_visible()
        text = popover.text_content()
        assert len(text) > 20


class TestGlossaryModulation:
    """Verify glossary hints on modulation KPI cards."""

    def test_modulation_kpi_has_glossary_hints(self, demo_page):
        demo_page.locator('a.nav-item[data-view="modulation"]').click()
        demo_page.wait_for_timeout(2000)
        hints = demo_page.locator('#view-modulation .glossary-hint')
        assert hints.count() >= 3, f"Expected 3 modulation glossary hints, got {hints.count()}"

    def test_health_index_popover(self, demo_page):
        demo_page.locator('a.nav-item[data-view="modulation"]').click()
        demo_page.wait_for_timeout(2000)
        hint = demo_page.locator('#view-modulation .glossary-hint').first
        hint.click()
        popover = hint.locator('.glossary-popover')
        expect(popover).to_be_visible()
