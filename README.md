# Selenium Pytest Automation

A simple Selenium test suite using Pytest to automate UI testing on the SeleniumBase demo page.

---

## Project Structure

- `test_demo_site.py` — Main test cases
- `conftest.py` — Fixtures and setup for WebDriver
- `screenshots/` — Saved screenshots from failed tests
- `reports/report.html` — Test execution report (generated automatically)

---

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/hemanth-kumar-j/selenium-pytest.git
cd selenium_pytest
```

### 2. Install Rye (if not already installed)
Visit [https://rye-up.com](https://rye-up.com) for installation instructions.

### 3. Setup Environment
```bash
rye sync
```

### 4. Run tests (headless by default)
```bash
pytest
```

### 5. Run tests with browser visible (headed mode)
```bash
pytest --headed
```

### 6. Check report
Open `reports/report.html` in your browser.

---

## Notes

- Failing tests will save screenshots in the `screenshots/` folder.
- Code is auto-formatted using `black`.

---
