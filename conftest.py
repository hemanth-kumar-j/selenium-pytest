import os
import pytest
import pytest_html
from selenium import webdriver
from pytest_metadata.plugin import metadata_key
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options


def pytest_addoption(parser):
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run tests with browser visible (non-headless mode)",
    )


def pytest_configure(config):
    config.stash[metadata_key]["Project"] = "selenium_pytest"

    # Ensure the screenshots folder exists
    os.makedirs("screenshots", exist_ok=True)


def pytest_html_report_title(report):
    report.title = "Automation Report"


@pytest.fixture(scope="session")
def driver(base_url, request):  # uses base_url from test file
    options = Options()
    # Enable headless only if --headed is NOT passed
    if not request.config.getoption("--headed"):
        options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)
    # driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(base_url)  # navigate to URL first
    yield driver
    driver.quit()


@pytest.fixture
def wait(driver):
    def _wait(timeout=10):  # default timeout is 10 seconds
        return WebDriverWait(driver, timeout)

    return _wait


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
                # Save screenshot
                screenshot_path = os.path.join("screenshots", f"{item.name}.png")
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
