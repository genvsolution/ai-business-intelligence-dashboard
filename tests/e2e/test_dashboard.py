import pytest
import os
from playwright.sync_api import Page, expect, sync_playwright, Download
import time

# --- Configuration ---
# In a real-world scenario, these configurations should be loaded from
# environment variables or a dedicated configuration file (e.g., .env, config.py)
# to avoid hardcoding sensitive information and ensure flexibility across environments.
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:5000")
TEST_USERNAME = os.getenv("E2E_TEST_USERNAME", "test_sales_manager@example.com")
TEST_PASSWORD = os.getenv("E2E_TEST_PASSWORD", "SecureP@ssw0rd123")

# --- Playwright Fixtures ---

@pytest.fixture(scope="session")
def browser():
    """
    Provides a Playwright browser instance for the entire test session.
    Launches a Chromium browser in headless mode by default for CI/CD environments.
    Set `headless=False` to observe the browser UI during local development/debugging.
    """
    with sync_playwright() as p:
        browser_instance = p.chromium.launch(headless=True)  # Set to False to watch tests run
        yield browser_instance
        browser_instance.close()

@pytest.fixture(scope="function")
def page(browser):
    """
    Provides a new Playwright page instance for each test function.
    Ensures a clean slate for every test, preventing state leakage between tests.
    """
    page_instance = browser.new_page()
    yield page_instance
    page_instance.close()

@pytest.fixture(scope="function")
def logged_in_page(page: Page):
    """
    Navigates to the login page, performs a login with predefined test credentials,
    and then navigates to the dashboard. Returns the authenticated page instance.
    This fixture simplifies tests by providing an already logged-in user context.
    """
    try:
        # Navigate to the login page
        page.goto(f"{BASE_URL}/auth/login")
        expect(page).to_have_url(f"{BASE_URL}/auth/login")
        expect(page.locator("h1")).to_have_text("Login")

        # Fill in credentials
        page.fill("input[name='email']", TEST_USERNAME)
        page.fill("input[name='password']", TEST_PASSWORD)

        # Click the login button and wait for navigation
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/dashboard") # Wait for the dashboard URL
        
        # Assert successful login and redirection to dashboard
        expect(page).to_have_url(f"{BASE_URL}/dashboard")
        expect(page.locator("h1")).to_have_text("Sales Dashboard") # Verify dashboard title
        
        yield page
        
    except Exception as e:
        # Log the error and fail the test if login fails
        print(f"Login failed for E2E test user {TEST_USERNAME}: {e}")
        page.screenshot(path="login_failure.png") # Capture screenshot for debugging
        pytest.fail(f"Failed to log in: {e}")
    finally:
        # Optional: Perform logout after each test if session cleanup is critical
        # For simplicity, closing the page usually suffices for session-based cleanup
        # if the server handles session expiry correctly.
        pass

# --- End-to-End Test Cases for Dashboard ---

def test_dashboard_loads_successfully(logged_in_page: Page):
    """
    Verifies that the sales dashboard page loads correctly after login,
    displaying essential UI elements like the navigation bar, KPI cards,
    and chart containers.
    """
    page = logged_in_page
    
    try:
        # The logged_in_page fixture already asserts the dashboard title and URL.
        # Further assertions for critical dashboard elements:

        # Verify presence of the main navigation bar
        navbar = page.locator("nav.navbar")
        expect(navbar).to_be_visible()
        expect(navbar).to_contain_text("Dashboard")
        expect(navbar).to_contain_text("Leads")
        expect(navbar).to_contain_text("Reports")
        expect(navbar).to_contain_text("AI Insights")

        # Verify presence of Key Performance Indicator (KPI) cards
        kpi_cards = page.locator(".kpi-card")
        expect(kpi_cards).to_have_count(expect.at_least(3)) # Expect at least 3 KPI cards
        expect(page.locator(".kpi-card h5:has-text('Total Revenue')")).to_be_visible()
        expect(page.locator(".kpi-card h5:has-text('Sales Volume')")).to_be_visible()
        expect(page.locator(".kpi-card h5:has-text('Conversion Rate')")).to_be_visible()

        # Verify presence of Chart.js canvas containers (where charts are rendered)
        expect(page.locator("#salesVolumeChart")).to_be_visible()
        expect(page.locator("#revenueByProductChart")).to_be_visible()
        expect(page.locator("#salesByRegionChart")).to_be_visible()
        
        print("Dashboard loaded successfully with all expected key elements visible.")

    except Exception as e:
        page.screenshot(path="dashboard_load_failure.png")
        pytest.fail(f"Dashboard failed to load or missing elements: {e}")

def test_chart_interactivity_date_filter(logged_in_page: Page):
    """
    Tests the functionality of filtering charts by a date range.
    It simulates selecting a new date range and verifies that a KPI value updates,
    indicating the charts have re-rendered with new data.
    """
    page = logged_in_page

    try:
        # Locate the date range picker element. This selector assumes a common ID.
        # Adjust selector based on actual HTML implementation (e.g., `input[name="date_range"]`, `#dateFilterSelect`).
        date_range_selector = page.locator("#dateRangeFilter")
        expect(date_range_selector).to_be_visible()

        # Get the initial value of a KPI (e.g., Total Revenue) before applying the filter.
        # This acts as a baseline to detect changes.
        initial_revenue_locator = page.locator(".kpi-card h5:has-text('Total Revenue') + p")
        expect(initial_revenue_locator).to_be_visible()
        initial_revenue_text = initial_revenue_locator.inner_text()
        print(f"Initial Total Revenue: {initial_revenue_text}")

        # Simulate selecting a new date range.
        # This example assumes a dropdown select element. For a date picker component,
        # interaction would involve clicking the input, then selecting dates from a calendar UI.
        # For this test, we select a predefined option like "Last 30 Days".
        date_range_selector.select_option(value="last_30_days")
        
        # Wait for the application to process the filter and update the charts.
        # A more robust wait would be `page.wait_for_response` for the data API call,
        # or `expect(locator).not_to_have_text` if a loading spinner is present.
        page.wait_for_timeout(2000) # Arbitrary wait; adjust based on application performance

        # Get the updated KPI value.
        updated_revenue_text = initial_revenue_locator.inner_text()
        print(f"Updated Total Revenue (Last 30 Days): {updated_revenue_text}")

        # Assert that the KPI value has changed, indicating the filter was applied and data updated.
        # This assertion assumes that applying "Last 30 Days" will indeed change the revenue figure.
        expect(updated_revenue_text).not_to_equal(initial_revenue_text)
        print("Date range filter applied successfully and dashboard KPIs updated.")

    except Exception as e:
        page.screenshot(path="date_filter_failure.png")
        pytest.fail(f"Date filter functionality failed: {e}")

def test_chart_interactivity_product_filter(logged_in_page: Page):
    """
    Tests the functionality of filtering charts by product category.
    It simulates selecting a product category and verifies that a KPI value updates.
    """
    page = logged_in_page

    try:
        # Locate the product category filter (e.g., a dropdown select).
        product_filter_select = page.locator("#productCategoryFilter")
        expect(product_filter_select).to_be_visible()

        # Get the initial value of a KPI (e.g., Sales Volume) before applying the filter.
        initial_sales_volume_locator = page.locator(".kpi-card h5:has-text('Sales Volume') + p")
        expect(initial_sales_volume_locator).to_be_visible()
        initial_sales_volume_text = initial_sales_volume_locator.inner_text()
        print(f"Initial Sales Volume: {initial_sales_volume_text}")

        # Select a specific product category (e.g., "Electronics").
        # This assumes "Electronics" is an available option in the dropdown.
        product_filter_select.select_option(value="Electronics")
        
        # Wait for charts to re-render with filtered data.
        page.wait_for_timeout(2000)

        # Get the updated KPI value.
        updated_sales_volume_text = initial_sales_volume_locator.inner_text()
        print(f"Updated Sales Volume (Electronics filter): {updated_sales_volume_text}")

        # Assert that the KPI value has changed.
        expect(updated_sales_volume_text).not_to_equal(initial_sales_volume_text)
        print("Product category filter applied successfully and dashboard KPIs updated.")

    except Exception as e:
        page.screenshot(path="product_filter_failure.png")
        pytest.fail(f"Product filter functionality failed: {e}")

def test_drill_down_functionality(logged_in_page: Page):
    """
    Tests drill-down functionality from a chart element.
    This test assumes there's a clickable element (e.g., a button or a specific chart region)
    that navigates to a detailed report page or opens a modal.
    Note: Interacting directly with Chart.js canvas elements can be brittle.
    A more robust approach often involves clicking on an associated HTML element
    (like a legend item, a "View Details" button, or an overlay).
    """
    page = logged_in_page

    try:
        # Locate a "View Details" button associated with a chart, if available.
        # This is the most reliable way to test drill-down.
        view_details_button = page.locator("#salesByRegionChartContainer button:has-text('View Details')").first
        
        if view_details_button.is_visible():
            print("Found 'View Details' button for Sales by Region chart. Initiating drill-down.")
            view_details_button.click()
            
            # Expect to navigate to a new page (e.g., a region-specific report).
            # Adjust the expected URL and title based on your application's routing.
            page.wait_for_url(f"{BASE_URL}/reports/region_details/**") # Wildcard for dynamic region ID
            expect(page).to_have_url(f"{BASE_URL}/reports/region_details/north_america") # Example specific URL
            expect(page.locator("h1")).to_have_text("Sales by Region Details")
            print("Drill-down to region details successful via 'View Details' button.")
        else:
            # Fallback: If no explicit button, attempt to click on the chart canvas.
            # This is less reliable as it depends on precise coordinates and Chart.js event handling.
            print("No 'View Details' button found. Attempting to click on Sales by Region chart canvas.")
            sales_by_region_chart = page.locator("#salesByRegionChart")
            expect(sales_by_region_chart).to_be_visible()

            # Click near the center of the chart canvas. This is a heuristic.
            # A real application might have specific interactive areas.
            sales_by_region_chart.click(position={"x": 100, "y": 100})
            page.wait_for_timeout(2000) # Wait for potential navigation or modal opening

            # Check if navigation occurred or a modal appeared.
            if page.url != f"{BASE_URL}/dashboard":
                expect(page).to_have_url(f"{BASE_URL}/reports/region_details/north_america") # Example
                expect(page.locator("h1")).to_have_text("Sales by Region Details")
                print("Drill-down to region details successful via chart canvas click (heuristic).")
            elif page.locator(".modal-dialog").is_visible():
                expect(page.locator(".modal-dialog h5:has-text('Region Details')")).to_be_visible()
                print("Drill-down opened a modal with region details.")
            else:
                pytest.fail("Drill-down functionality did not trigger expected navigation or modal.")

    except Exception as e:
        page.screenshot(path="drill_down_failure.png")
        pytest.fail(f"Drill-down functionality failed: {e}")

def test_data_export_functionality(logged_in_page: Page):
    """
    Tests the data export functionality (e.g., CSV, PNG) for a chart or table.
    Verifies that a file download is initiated successfully.
    """
    page = logged_in_page

    try:
        # Locate an export button. This selector assumes a button with "Export CSV" text.
