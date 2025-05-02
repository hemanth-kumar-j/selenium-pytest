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

### 3. Set Up the Environment
```bash
rye sync
```

### 4. Run Tests (Headless Chrome by Default)
```bash
pytest
```

### 5. Run Tests with Browser UI (Headed Mode)
```bash
pytest --headed
```

### 6. Run Tests with Other Browsers
```bash
pytest --browser=firefox
pytest --browser=edge
```

### 7. View Test Report
Open `reports/report.html` in your browser.

---

## Notes

- Failing tests will save screenshots in the `screenshots/` folder.
- Code is auto-formatted using `black`.

---
