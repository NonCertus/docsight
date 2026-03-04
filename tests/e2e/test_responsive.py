"""E2E tests for responsive / mobile layout."""

import pytest


@pytest.fixture()
def mobile_page(page, live_server):
    """Page with a mobile viewport (375x667, iPhone SE)."""
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(live_server)
    page.wait_for_load_state("networkidle")
    return page


class TestMobileLayout:
    """Mobile viewport behavior."""

    def test_hamburger_visible_on_mobile(self, mobile_page):
        hamburger = mobile_page.locator("#hamburger")
        assert hamburger.is_visible()

    def test_sidebar_hidden_on_mobile(self, mobile_page):
        sidebar = mobile_page.locator("nav.sidebar")
        # Sidebar is positioned off-screen (x < 0) on mobile
        box = sidebar.bounding_box()
        assert box is None or box["x"] + box["width"] <= 0

    def test_bottom_nav_visible_on_mobile(self, mobile_page):
        bottom_nav = mobile_page.locator("nav.bottom-nav")
        assert bottom_nav.is_visible()

    def test_bottom_nav_has_tabs(self, mobile_page):
        tabs = mobile_page.locator(".bottom-nav-item")
        assert tabs.count() >= 4
