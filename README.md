# Selenium Pytest Automation

A simple Selenium test suite using Pytest to automate UI testing on the SeleniumBase demo page.

## Project Structure

- `test_demo_site.py` — Main test cases
- `conftest.py` — Fixtures and setup for WebDriver
- `screenshots/` — Saved screenshots from failed tests
- `log.html` — Test execution report (generated automatically)

## How to Run

1. **Install dependencies**:
```bash
pip install -r requirements.lock
```

2. **Run tests with HTML report**:
```bash
pytest --html=log.html --self-contained-html
```

3. **Check report**:
Open `log.html` in your browser.

## Notes

- Failing tests will save screenshots in the `screenshots/` folder.
- Code is auto-formatted using `black`.
