def html5_drag_and_drop(driver, source_element, target_element):
    js_code = """
    function triggerDragAndDrop(source, target) {
        const dataTransfer = new DataTransfer();

        source.dispatchEvent(new DragEvent('dragstart', { dataTransfer }));
        target.dispatchEvent(new DragEvent('dragover', { dataTransfer }));
        target.dispatchEvent(new DragEvent('drop', { dataTransfer }));
        source.dispatchEvent(new DragEvent('dragend', { dataTransfer }));
    }
    triggerDragAndDrop(arguments[0], arguments[1]);
    """
    driver.execute_script(js_code, source_element, target_element)
