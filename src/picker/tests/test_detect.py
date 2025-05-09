def test_detect():
    """Example demonstrating how to use the page configuration with automation."""
    # Load configuration
    config_dir = Path("data") / "configs"
    config_path = config_dir / "pages.json"

    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Run the picker first to create a configuration.")
        return

    config_manager = PageConfigManager(config_path)

    # Create page detector
    page_detector = PageDetector(config_manager)

    # Create window capturer for screenshots
    capturer = WindowCapturer()
    capturer.set_window_name("NIKKE")  # Set to your game window name

    # Simulate getting a screenshot
    screenshot_result = capturer.capture_window()
    if not screenshot_result:
        logger.error("Failed to capture window")
        return

    screenshot = screenshot_result.to_pil()

    # Detect current page
    detection_result = page_detector.detect_page(screenshot)

    if detection_result.is_detected:
        logger.info(f"Current page: {detection_result.page_id} "
                    f"(confidence: {detection_result.confidence:.2f})")
        logger.info(f"Elements found: {detection_result.elements_found}")

        # Get all pages in configuration
        available_pages = list(config_manager.config.pages.keys())

        if available_pages:
            # Example: Find path to another page
            target_page = available_pages[0]
            if target_page != detection_result.page_id:
                path = page_detector.find_path(detection_result.page_id, target_page)

                if path:
                    logger.info(f"Path to {target_page}: {' -> '.join(path)}")


                    # Example: Navigate to target page
                    def click_handler(element):
                        # In a real application, this would perform the click
                        logger.info(f"Clicking on {element.name}")


                    def screenshot_getter():
                        # In a real application, this would get a fresh screenshot
                        result = capturer.capture_window()
                        return result.to_pil() if result else screenshot


                    # Navigate along the path
                    for i in range(len(path) - 1):
                        from_page = path[i]
                        to_page = path[i + 1]

                        logger.info(f"Navigating from {from_page} to {to_page}")

                        success = page_detector.navigate_to_page(
                            from_page, to_page, click_handler, screenshot_getter
                        )

                        if not success:
                            logger.error(f"Failed to navigate to {to_page}")
                            break
                else:
                    logger.info(f"No path found to {target_page}")
    else:
        logger.info("No page detected")
