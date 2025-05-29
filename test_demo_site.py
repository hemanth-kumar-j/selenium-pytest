import pytest
import logging
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from drag_utils import html5_drag_and_drop
from conftest import get_scope


# Set the URL here
@pytest.fixture(scope="session")
def base_url():
    return "https://seleniumbase.io/demo_page"


@pytest.fixture(scope=get_scope, autouse=True)
def wait_for_element(request, driver):
    wait_scope = getattr(request.config, "_wait_scope", "module")
    if wait_scope != "module":
        return

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tbodyId")))
    logging.info("Demo Page Is Visible")


def test_hover_dropdown(driver, wait):

    def select_dropdown_links(link_text):
        actions = ActionChains(driver)
        dropdown = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='Hover Dropdown']"))
        )
        actions.move_to_element(dropdown).perform()
        dropdown_link = wait.until(
            EC.visibility_of_element_located((By.LINK_TEXT, f"{link_text}"))
        )
        actions.move_to_element(dropdown_link).perform()
        dropdown_link.click()
        wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "h3"), f"{link_text} Selected"
            )
        )

    select_dropdown_links("Link One")
    select_dropdown_links("Link Two")
    select_dropdown_links("Link Three")


def verify_text_input(driver, element_id, input_text):
    text_input = driver.find_element(By.ID, element_id)
    text_input.clear()
    text_input.send_keys(input_text)
    text_value = text_input.get_attribute("value")
    assert input_text == text_value, "Text field does not contain expected text"


def test_text_input_field(driver):
    verify_text_input(driver, "myTextInput", "This is a sample text")


def test_textarea(driver):
    verify_text_input(driver, "myTextarea", "This is a sample text for the text area.")


def test_prefilled_text_field(driver):
    prefilled_text = driver.find_element(By.ID, "myTextInput2").text
    verify_text_input(driver, "myTextInput2", "Hello World!")
    assert "Hello World!" != prefilled_text, "Pre-filled Text Didn't Changed"


def test_placeholder(driver):
    before_text = driver.find_element(By.ID, "placeholderText").get_attribute(
        "placeholder"
    )
    verify_text_input(driver, "placeholderText", "HELLO WORLD")
    assert "HELLO WORLD" != before_text, "Placeholder Text Didn't Changed"


def test_button_color_change(driver):
    button = driver.find_element(By.ID, "myButton")
    before_color = button.value_of_css_property("color")
    button.click()
    after_color = button.value_of_css_property("color")
    assert (
        after_color != before_color
    ), "Button color didnot changed or Button is not clicked"


def test_read_only_text(driver):
    text_field = driver.find_element(By.ID, "readOnlyText").get_attribute("readonly")
    assert text_field is not None, "Text field is not read-only"


def test_paragraph_with_text(driver):
    paragraph_text = driver.find_element(By.ID, "pText").text.strip()
    assert len(paragraph_text) > 0, "Paragraph is empty"


def test_svg_animation(driver, wait):
    rect = driver.find_element(By.ID, "svgRect")
    rect.click()
    wait.until(lambda d: rect.value_of_css_property("opacity") == "1")
    wait.until(lambda d: rect.get_attribute("width") == "154")
    final_opacity = rect.value_of_css_property("opacity")
    final_width = rect.get_attribute("width")
    assert "1" == final_opacity, "Opacity animation did not complete"
    assert "154" == final_width, "Width animation did not complete"


def test_slider_and_progress_bar(driver):
    slider_input = 80

    def move_slider():
        slider = driver.find_element(By.ID, "mySlider")
        before_slider_value = slider.get_attribute("value")
        slider_width = slider.size["width"]
        slider_step = slider_width / 100  # Calculate pixel per percent
        slider_value = slider_step * slider_input
        slider_half = slider_width / 2
        x = slider_value - slider_half
        ActionChains(driver).click_and_hold(slider).move_by_offset(
            x, 0
        ).release().perform()
        after_slider_value = slider.get_attribute("value")
        assert after_slider_value != before_slider_value, "Slider did not move"

    def check_progress_bar():
        progress_label_text = driver.find_element(By.ID, "progressLabel").text
        progress_bar_value = driver.find_element(By.ID, "progressBar").get_attribute(
            "value"
        )
        assert (
            f"({slider_input}%)" in progress_label_text
        ), "Progress label did not update correctly"
        assert (
            str(slider_input) == progress_bar_value
        ), "Progress bar did not update correctly"

    move_slider()
    check_progress_bar()


def test_dropdown_and_meter(driver):
    dropdown_value = 75

    def select_dropdown_and_check_value():
        dropdown = Select(driver.find_element(By.ID, "mySelect"))
        dropdown.select_by_visible_text(f"Set to {dropdown_value}%")
        selected_dropdown = dropdown.first_selected_option.text
        assert (
            selected_dropdown == f"Set to {dropdown_value}%"
        ), "Did not select correct dropdown value"

    def check_meter():
        meter_label = driver.find_element(By.ID, "meterLabel")
        assert (
            f"({dropdown_value}%)" in meter_label.text
        ), "Meter label did not update correctly"
        meter_bar = driver.find_element(By.ID, "meterBar")
        meter_value = (
            float(meter_bar.get_attribute("value")) * 100
        )  # Convert to percentage
        assert (
            dropdown_value == meter_value
        ), "Meter bar value does not match dropdown selection"

    select_dropdown_and_check_value()
    check_meter()


def test_iframe_image(driver):
    iframe = driver.find_element(By.ID, "myFrame1")
    driver.switch_to.frame(iframe)
    image_src = driver.find_element(By.TAG_NAME, "img").get_attribute("src")
    assert image_src.startswith(
        "data:image/gif;base64,"
    ), "Image is not loaded correctly"
    driver.switch_to.default_content()


def test_iframe_text(driver):
    iframe = driver.find_element(By.ID, "myFrame2")
    driver.switch_to.frame(iframe)
    iframe_text = driver.find_element(By.TAG_NAME, "h4").text
    assert (
        iframe_text == "iFrame Text"
    ), f"Expected 'iFrame Text' but found '{iframe_text}'"
    driver.switch_to.default_content()


def test_radio_buttons(driver):
    radio_button_1 = driver.find_element(By.ID, "radioButton1")
    radio_button_2 = driver.find_element(By.ID, "radioButton2")
    radio_button_2.click()
    assert radio_button_2.is_selected(), "Radio Button 2 is not selected"
    assert not radio_button_1.is_selected(), "Radio Button 1 should not be selected"


'''def test_checkbox_and_drag_n_drop(driver):

    def check_checkbox():
        checkbox = driver.find_element(By.ID, "checkBox1")
        if not checkbox.is_selected():
            checkbox.click()
        assert checkbox.is_selected(), "Checkbox is not selected!"

    def check_drag_n_drop():
        source = driver.find_element(By.ID, "logo")
        target = driver.find_element(By.ID, "drop2")
        html5_drag_and_drop(driver, source, target)
        new_parent = source.find_element(By.XPATH, "..")
        assert new_parent == target, "Drag and Drop failed! Image is not inside Drop B."

    check_checkbox()
    check_drag_n_drop()


def test_checkboxes(driver):
    checkboxes = driver.find_elements(
        By.XPATH, '//td[contains(text(),"CheckBoxes")]/input[@type="checkbox"]'
    )
    for checkbox in checkboxes:
        checkbox.send_keys(Keys.SPACE)
    checked_count = sum(1 for checkbox in checkboxes if checkbox.is_selected())
    expected_checked_count = 3
    assert (
        checked_count == expected_checked_count
    ), f"Checkbox count mismatch: {checked_count} checked (Expected: {expected_checked_count})"


def test_pre_check_box(driver):
    checkbox = driver.find_element(By.ID, "checkBox5")
    if checkbox.is_selected():
        checkbox.click()
    assert not checkbox.is_selected(), "Checkbox should be unchecked!"


def test_checkbox_in_iframe(driver):
    iframe = driver.find_element(By.ID, "myFrame3")
    driver.switch_to.frame(iframe)
    checkbox = driver.find_element(By.ID, "checkBox6")
    if not checkbox.is_selected():
        checkbox.click()
    assert checkbox.is_selected(), "Checkbox is not selected!"
    driver.switch_to.default_content()


def test_url_link(driver):

    def url_link(locator, url):
        link = driver.find_element(By.ID, locator)
        link_url = link.get_attribute("href")
        expected_url = url
        assert (
            link_url == expected_url
        ), f"URL mismatch! Expected: {expected_url}, Found: {link_url}"
        link.click()
        sleep(2)
        assert driver.current_url.startswith(
            expected_url
        ), f"Navigation failed: Expected '{expected_url}', but got '{driver.current_url}'"
        driver.back()

    url_link("myLink1", "https://seleniumbase.com/")
    url_link("myLink3", "https://seleniumbase.io/")


def test_link_with_text(driver):

    def text_url(text, url):
        link_element = driver.find_element(By.LINK_TEXT, text)
        actual_text = link_element.text.strip()
        actual_url = link_element.get_attribute("href")
        expected_text = text
        expected_url = url
        assert (
            actual_text == expected_text
        ), f"Text Mismatch: Expected '{expected_text}', but got '{actual_text}'"
        assert (
            actual_url == expected_url
        ), f"URL Mismatch: Expected '{expected_url}', but got '{actual_url}'"
        link_element.click()
        sleep(2)
        assert driver.current_url.startswith(
            expected_url
        ), f"Navigation failed: Expected '{expected_url}', but got '{driver.current_url}'"
        driver.back()

    text_url("SeleniumBase on GitHub", "https://github.com/seleniumbase/SeleniumBase")
    text_url("SeleniumBase Demo Page", "https://seleniumbase.io/demo_page/")'''
