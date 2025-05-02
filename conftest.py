import os
import time
import pytest
import logging
import pytest_html

from selenium import webdriver
from pytest_metadata.plugin import metadata_key
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        help="Browser type: chrome, or firefox",
    )
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run tests with browser visible (non-headless mode)",
    )
    parser.addoption(
        "--timeout",
        action="store",
        default=10,
        type=int,
        help="WebDriverWait timeout in seconds (default: 10)",
    )
    parser.addoption(
        "--remove",
        action="store_true",
        default=False,
        help="Remove old screenshots before running tests",
    )


def pytest_configure(config):
    browser = config.getoption("--browser").lower()
    headed = config.getoption("--headed")
    should_remove = config.getoption("--remove")

    # Validate browser type
    if browser not in ["chrome", "firefox", "edge"]:
        pytest.exit(f"Unsupported browser: {browser}. Supported browsers: chrome (default), firefox, edge", returncode=1)

    config.stash[metadata_key]["Project"] = "selenium_pytest"
    config.stash[metadata_key]["Browser"] = browser
    if not headed:
        config.stash[metadata_key]["Mode"] = "headless"

    # Ensure the screenshots folder exists
    os.makedirs("screenshots", exist_ok=True)

    if should_remove:
        logging.info("Removing old screenshots...")
        for filename in os.listdir("screenshots"):
            file_path = os.path.join("screenshots", filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logging.error(f"Error deleting file {file_path}: {e}")


def pytest_html_report_title(report):
    report.title = "Automation Report"


@pytest.fixture(scope="session")
def driver(base_url, request):  # uses base_url from test file
    browser = request.config.getoption("--browser").lower()
    headed = request.config.getoption("--headed")

    if browser == "firefox":
        logging.info("Launching Firefox")
        options = FirefoxOptions()
        if not headed:
            options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
    elif browser == "edge":
        print("Launching Edge")
        options = EdgeOptions()
        if not headed:
            options.add_argument("--headless")
        driver = webdriver.Edge(options=options)
    else:
        logging.info("Launching Chrome")
        options = ChromeOptions()
        if not headed:
            options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.get(base_url)  # navigate to URL first
    yield driver
    driver.quit()


@pytest.fixture
def wait(driver, request):
    timeout = request.config.getoption("--timeout")
    return WebDriverWait(driver, timeout)


# This hook adds screenshots and driver URL to the HTML report on test failure
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Execute other hooks to get the report object
    outcome = yield
    report = outcome.get_result()
    extras = getattr(report, "extras", [])

    if report.when == "call" or report.when == "setup":
        xfail = hasattr(report, "wasxfail")
        if (report.skipped and xfail) or (report.failed and not xfail):
            driver = item.funcargs.get("driver", None)
            if driver:
                # Timestamped screenshot filename
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                screenshot_name = f"{item.name}_{timestamp}.png"
                screenshot_path = os.path.join("screenshots", screenshot_name)
                driver.save_screenshot(screenshot_path)

                # Relative path from HTML report (in reports/) to screenshot
                relative_path = f"../{screenshot_path}"

                # Add extras
                extras.append(pytest_html.extras.url(driver.current_url))
                extras.append(pytest_html.extras.image(relative_path))
                extras.append(
                    pytest_html.extras.html(
                        "<div>Test failed — Screenshot attached.</div>"
                    )
                )

        report.extras = extras
