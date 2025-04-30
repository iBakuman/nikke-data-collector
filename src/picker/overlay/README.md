# Overlay and Page Configuration Integration

This module provides a powerful system for capturing UI elements in games or applications and configuring them for automated workflows. It combines two key components:

1. **Overlay System** - For visually capturing elements using strategies
2. **Page Configuration** - For organizing elements into pages and defining interactions

## Architecture

The system follows these design patterns:

- **Strategy Pattern**: Different capture strategies for different element types
- **State Machine**: Managing the capture process through discrete steps
- **Observer Pattern**: Components communicate through signals/events
- **Composite Pattern**: Visual elements form a rendering hierarchy

## Components

### Overlay System

- **OverlayWidget**: Transparent widget that captures mouse events and displays visual feedback
- **VisualElements**: Visual primitives (points, rectangles, text) rendered on the overlay
- **CaptureStrategies**: Workflows for capturing different element types
- **OverlayManager**: Coordinates between strategies and the overlay

### Page Configuration

- **PageConfigManager**: Manages page definitions and element associations
- **ElementTypeRegistry**: Registry of supported element types and handlers
- **PageDetector**: Detects the current page based on defined identifiers
- **PageConfigDialog**: UI for configuring pages, elements, and transitions

## Usage Examples

Two example applications demonstrate how to use the integrated system:

### 1. Basic Integration Example (`integration_example.py`)

A simple UI showing how to:
- Capture UI elements using the overlay
- Save elements to the page configuration
- Define pages, identifiers, and transitions

Run with:
```bash
python -m src.picker.integration_example
```

### 2. Game Automation Example (`game_automation_example.py`)

A more complete UI showing a practical workflow:
- Capture elements using overlay system
- Configure pages and transitions
- Execute automated workflows
- Preview the captured screen
- Log interactions and events

Run with:
```bash
python -m src.picker.game_automation_example
```

## Workflow Guide

### 1. Element Capture

1. Click "Capture Pixel Color" or "Capture Image Element"
2. Follow on-screen instructions to select the element
3. Confirm the capture with "Done"

### 2. Page Configuration

1. Create pages for each distinct game state
2. Add captured elements to pages
3. Designate elements as:
   - **Page Identifiers**: Used to detect the current page
   - **Interactive Elements**: Elements that can be clicked
4. Define transitions between pages

### 3. Automation

1. Create workflows as sequences of element interactions
2. Execute workflows to automate repetitive tasks
3. Monitor the state through the preview and log

## Extending the System

### Adding New Element Types

1. Create a new entity class for the element
2. Register a handler in the ElementTypeRegistry
3. Create a capture strategy for the new element type
4. Register the strategy with the OverlayManager

### Adding New Capture Strategies

1. Create a new class inheriting from CaptureStrategy
2. Implement the required methods:
   - start_capture()
   - handle_press(), handle_move(), handle_release()
   - get_instructions()
3. Register the strategy with the OverlayManager

## Dependencies

- PySide6 for UI
- PIL/Pillow for image processing
- (Optional) pyautogui for actual mouse/keyboard automation 
