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

    def test_mobile_header_visible(self, mobile_page):
        header = mobile_page.locator(".mobile-header")
        assert header.is_visible()

    def test_hamburger_opens_sidebar(self, mobile_page):
        mobile_page.locator("#hamburger").click()
        mobile_page.wait_for_timeout(300)
        sidebar = mobile_page.locator("nav.sidebar")
        box = sidebar.bounding_box()
        assert box is not None and box["x"] >= 0

    def test_primary_nav_items_in_sidebar(self, mobile_page):
        mobile_page.locator("#hamburger").click()
        mobile_page.wait_for_timeout(300)
        nav_items = mobile_page.locator(
            '.nav-section[data-nav-section="monitoring"] .nav-item'
        )
        assert nav_items.count() >= 4

    def test_analysis_section_collapsible(self, mobile_page):
        mobile_page.locator("#hamburger").click()
        mobile_page.wait_for_timeout(300)
        analysis = mobile_page.locator(
            '.nav-section[data-nav-section="analysis"]'
        )
        if analysis.count() > 0:
            toggle = analysis.locator(".nav-group-toggle")
            toggle.click()
            mobile_page.wait_for_timeout(200)
            items = analysis.locator(".nav-section-items .nav-item")
            assert items.count() >= 1
