"""E2E tests for the channels view."""

import pytest


class TestChannelsView:
    """Channels view navigation and content."""

    def test_switch_to_channels_view(self, demo_page):
        demo_page.locator('.nav-item[data-view="channels"]').click()
        channels = demo_page.locator("#view-channels")
        assert channels.is_visible()

    def test_channels_view_hides_live(self, demo_page):
        demo_page.locator('.nav-item[data-view="channels"]').click()
        live = demo_page.locator("#view-live")
        assert not live.is_visible()

    def test_channels_nav_marked_active(self, demo_page):
        nav = demo_page.locator('.nav-item[data-view="channels"]')
        nav.click()
        assert "active" in nav.get_attribute("class")

    def test_channels_api_returns_data(self, live_server, page):
        resp = page.request.get(f"{live_server}/api/channels")
        assert resp.status == 200
        data = resp.json()
        assert isinstance(data, dict)
