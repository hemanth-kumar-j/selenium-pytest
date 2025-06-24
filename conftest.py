import os
import sys
import glob
import time
import json
import base64
import pytest
import logging
import subprocess
import pytest_html
from bs4 import BeautifulSoup
from pytest_html_merger.main import merge_html_files

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


def update_browsers_in_html_report(report_path: str, browsers: list[str]):
    """
    Modifies an existing merged HTML report by updating the 'Browsers' entry
    within the JSON data stored in the 'data-jsonblob' attribute.
    """
    if not os.path.exists(report_path):
        logging.error(
            f"Report file not found at '{report_path}'. Cannot update browsers."
        )
        return  # Do not raise, just log and exit if file is missing

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        data_container_div = soup.find("div", id="data-container")

        if data_container_div and "data-jsonblob" in data_container_div.attrs:
            json_blob_str = data_container_div["data-jsonblob"]

            report_data = json.loads(json_blob_str)

            if "environment" in report_data:
                original_browsers = report_data["environment"].get(
                    "Browsers", "Not found"
                )
                updated_browsers_str = ", ".join(browsers)
                report_data["environment"]["Browsers"] = updated_browsers_str
            else:
                logging.warning(
                    "No 'environment' key found in data-jsonblob. Cannot update browsers."
                )

            updated_json_blob_str = json.dumps(
                report_data, indent=None, separators=(",", ":")
            )

            data_container_div["data-jsonblob"] = updated_json_blob_str

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(str(soup))
            logging.info(f"Successfully modified HTML report at '{report_path}'.")

        else:
            logging.error(
                f"Could not find div with id='data-container' or 'data-jsonblob' attribute in '{report_path}'."
            )
            logging.warning(
                "Please ensure the HTML structure matches the expected pytest-html report format."
            )

    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from 'data-jsonblob' attribute: {e}")
        # Note: json_blob_str might not be defined if 'data-jsonblob' was not found.
        # Ensure it's defined before attempting to slice it.
        error_json_preview = (
            json_blob_str[:500] if "json_blob_str" in locals() else "N/A"
        )
        logging.error(
            f"The content of 'data-jsonblob' might be malformed: {error_json_preview}..."
        )
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while modifying the HTML report: {e}"
        )
        logging.error(f"Error details: {e.__class__.__name__}: {e}")


def merge_parallel_browser_reports(config, browsers: list[str]):
    report_files = sorted(glob.glob("reports/report_*.html"))

    if not report_files:
        raise RuntimeError("No report files found to merge.")

    output_file = "reports/report.html"
    title = "Parallel Browsers Report"

    merge_html_files("reports", output_file, title)
    print(f"Merged reports to {output_file}")

    # Update the browsers in the merged report's JSON blob
    update_browsers_in_html_report(output_file, browsers)


def run_parallel_browsers_via_subprocess(config):
    browser_opt = next((arg for arg in sys.argv if arg.startswith("--browser=")), None)
    if not browser_opt:
        print(
            "No --browser option provided. Exiting. Add '--browser=browser names' and try again."
        )
        sys.exit(1)

    browsers = browser_opt.split("=")[1].split(",")
    extra_args = [
        arg
        for arg in sys.argv[1:]
        if not arg.startswith("--browser") and arg != "--parallel-browsers"
    ]

    base_cmd = [sys.executable, "-m", "pytest"]
    processes = []

    os.makedirs("reports", exist_ok=True)

    for f in glob.glob("reports/report_*.html"):
        os.remove(f)
        logging.info(f"Removed old {f}...")

    for browser in browsers:
        html_report = f"reports/report_{browser}.html"
        cmd = (
            base_cmd
            + [f"--browser={browser}", f"--html={html_report}", "--self-contained-html"]
            + extra_args
        )
        env = os.environ.copy()
        env["IS_SUBPROCESS"] = "1"  # Prevent recursion
        print(f"\n[Launching] {' '.join(cmd)}")
        processes.append(subprocess.Popen(cmd, env=env))

    for p in processes:
        p.wait()

    merge_parallel_browser_reports(config, browsers)


def pytest_cmdline_main(config):
    if config.getoption("parallel_browsers"):
        if config.getoption("numprocesses") not in [None, 0]:
            print(
                '"--parallel-browsers" cannot be used with "-n". Please remove "-n" and try again.'
            )
            sys.exit(1)
        run_parallel_browsers_via_subprocess(config)
        return 0  # Exit parent run after launching subprocesses


def pytest_configure(config):
    browsers = config.getoption("browser").split(",")
    individual = config.getoption("individual_browsers")
    subprocess = os.environ.get("IS_SUBPROCESS")
    remove_old = config.getoption("remove")
    # In subprocess workers launched by xdist (-n), config will have workerinput
    if hasattr(config, "workerinput"):
        # These are passed from the main process via pytest_configure_node
        execution_mode = config.workerinput.get("execution_mode", "sequence-tests")
        config._scope = config.workerinput.get("scope", "module")
    else:
        # This is the main pytest process (not a worker)
        parallel_xdist = config.getoption("numprocesses") not in [None, 0]
        execution_mode = "parallel-tests" if parallel_xdist else "sequence-tests"
        config._scope = "function" if parallel_xdist else "module"
        config._execution_mode = execution_mode  # This will be passed to workers
        logging.info(f"[pytest_configure] Selected scope: {config._scope}")

    # Add info to HTML report
    config.stash[metadata_key]["Project"] = "selenium_pytest"
    config.stash[metadata_key]["Test Execution Mode"] = execution_mode
    config.stash[metadata_key]["Browsers"] = ", ".join(browsers)
    config.stash[metadata_key]["Display Mode"] = (
        "headed" if config.getoption("headed") else "headless"
    )
    if individual or subprocess:
        config.stash[metadata_key]["Browser Execution Mode"] = (
            "individual-browsers" if individual else "parallel-browsers"
        )

    # Ensure the screenshots folder exists
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
    # Pass values from main process to xdist worker subprocess
    node.workerinput["scope"] = node.config._scope
    node.workerinput["execution_mode"] = getattr(
        node.config, "_execution_mode", "sequence-tests"
    )


@pytest.fixture(scope="session")
def browser_name(pytestconfig):
    return pytestconfig.getoption("browser")


def pytest_generate_tests(metafunc):
    browsers = metafunc.config.getoption("browser").split(",")
    individual = metafunc.config.getoption("individual_browsers")
    parallel_xdist = metafunc.config.getoption("numprocesses") not in [None, 0]

    if "browser_name" in metafunc.fixturenames:
        if parallel_xdist:
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

    logging.info(
        f"Launching {browser.capitalize()} in {'headed' if headed else 'headless'} mode for tests."
    )
    if browser == "chrome":
        options = ChromeOptions()
        if not headed:
            options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

    elif browser == "firefox":
        options = FirefoxOptions()
        if not headed:
            options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)

    elif browser == "edge":
        options = EdgeOptions()
        if not headed:
            options.add_argument("--headless")
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
