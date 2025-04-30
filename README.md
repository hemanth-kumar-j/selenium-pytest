# Selenium Pytest Automation

A simple Selenium test suite using Pytest to automate UI testing on the SeleniumBase demo page.

---

## Project Structure

- `test_demo_site.py` — Main test cases
- `conftest.py` — Fixtures and setup for WebDriver
- `screenshots/` — Saved screenshots from failed tests
- `log.html` — Test execution report (generated automatically)

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

### 4. Run tests with HTML report
```bash
pytest --html=log.html --self-contained-html
```

### 5. Check report
Open `log.html` in your browser.

---

## Notes

- Failing tests will save screenshots in the `screenshots/` folder.
- Code is auto-formatted using `black`.

---
