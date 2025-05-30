import os
import time
import base64
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
        help="Comma-separated list of browsers: chrome,firefox,edge",
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
    parser.addoption(
        "--individual-browsers",
        action="store_true",
        help="Run all browsers one after another",
    )
    parser.addoption(
        "--parallel-browsers",
        action="store_true",
        help="Run tests in parallel across browsers",
    )

def pytest_configure(config):
    browsers = config.getoption("browser").split(",")
    remove_old = config.getoption("remove")
    if hasattr(config, "workerinput"):
        config._scope = config.workerinput.get("scope", "module")
    else:
        browsers = config.getoption("browser").split(",")
        parallel_xdist = config.getoption("numprocesses") not in [None, 0]
        individual = config.getoption("individual-browsers", False)
        parallel_browsers = config.getoption("parallel_browsers", False)

        if parallel_xdist:
            config._scope = "function"
        else:
            config._scope = "module"
        logging.info(f"[pytest_configure] Selected scope: {config._scope}")

    config.stash[metadata_key]["Project"] = "selenium_pytest"
    config.stash[metadata_key]["Browsers"] = ", ".join(browsers)
    config.stash[metadata_key]["Mode"] = (
        "Headed" if config.getoption("headed") else "Headless"
    )

    os.makedirs("screenshots", exist_ok=True)
    if remove_old:
        logging.info("Removing old screenshots...")
        for file in os.listdir("screenshots"):
            try:
                os.unlink(os.path.join("screenshots", file))
            except Exception as e:
                logging.error(f"Error deleting screenshot: {e}")

def get_scope(fixture_name=None, config=None):
    return getattr(config, "_scope", "session")

def pytest_configure_node(node):
    # This sends the scope to each xdist worker
    node.workerinput["scope"] = node.config._scope

@pytest.fixture(scope="session")
def browser_name(pytestconfig):
    return pytestconfig.getoption("browser")

def pytest_generate_tests(metafunc):
    browsers = metafunc.config.getoption("browser").split(",")
    parallel = metafunc.config.getoption("parallel_browsers")
    individual = metafunc.config.getoption("individual_browsers")
    parallel_xdist = metafunc.config.getoption("numprocesses") not in [None, 0]

    if "browser_name" in metafunc.fixturenames:
        if parallel_xdist or parallel:
            # No scope means function scope (default) — required for parallel
            metafunc.parametrize("browser_name", browsers)
        elif individual:
            metafunc.parametrize("browser_name", browsers, scope="module")
        else:
            metafunc.parametrize("browser_name", [browsers[0]], scope="module")


@pytest.fixture
def wait(driver, request):
    timeout = request.config.getoption("timeout")
    return WebDriverWait(driver, timeout)

@pytest.fixture(scope=get_scope)
def driver(request, base_url, browser_name):
    headed = request.config.getoption("headed")
    browser = browser_name.lower()

    logging.info(f"Launching {browser.capitalize()} in {'headed' if headed else 'headless'} mode for tests.")
    if browser == "chrome":
        options = ChromeOptions()
        if not headed:
            options.add_argument("--headless")
        #logging.info("Launching Chrome")
        driver = webdriver.Chrome(options=options)

    elif browser == "firefox":
        options = FirefoxOptions()
        if not headed:
            options.add_argument("--headless")
        #logging.info("Launching Firefox")
        driver = webdriver.Firefox(options=options)

    elif browser == "edge":
        options = EdgeOptions()
        if not headed:
            options.add_argument("--headless")
        #logging.info("Launching Edge")
        driver = webdriver.Edge(options=options)

    else:
        raise ValueError(f"Unsupported browser: {browser_name}")

    driver.maximize_window()
    driver.get(base_url)

    yield driver
    logging.info(f"Quitting {browser.capitalize()} browser.")
    driver.quit()

def pytest_html_report_title(report):
    report.title = "Automation Report"


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

                # Read and encode the image in base64
                with open(screenshot_path, "rb") as f:
                    encoded_image = base64.b64encode(f.read()).decode()

                # Embed screenshot into report using base64
                html_img = f'<div><img src="data:image/png;base64,{encoded_image}" alt="screenshot" style="max-width:600px; max-height:400px;" /></div>'
                extras.append(pytest_html.extras.html(html_img))

                # Optionally add the page URL
                extras.append(pytest_html.extras.url(driver.current_url))

        report.extras = extras
