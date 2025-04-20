import functools
import logging
import os
from typing import Any, Callable, TypeVar

import keyboard

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Type variable for function return type
F = TypeVar('F', bound=Callable[..., Any])


def keyboard_terminable(shortcut: str = "ctrl+shift+x") -> Callable[[F], F]:
    """
    Decorator to make a test function terminable via keyboard shortcut.

    Args:
        shortcut: Keyboard shortcut to terminate the test. Default is Ctrl+Shift+X.

    Returns:
        Decorated function that can be terminated via keyboard shortcut.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # If keyboard module is not available, just run the function
            logger.warning("Keyboard termination disabled (module not installed).")

            # Function to handle keyboard event - directly exits the program

            def on_shortcut_pressed():
                logger.info(f"Termination shortcut {shortcut} pressed. Exiting program immediately.")
                # Use os.kill with SIGKILL to force immediate termination
                os._exit(0)

            keyboard.add_hotkey(shortcut, on_shortcut_pressed)
            logger.info(f"Test can be terminated with '{shortcut}' shortcut (will exit program immediately)")

            try:
                return func(*args, **kwargs)
            finally:
                # Unregister the hotkey to prevent affecting other code
                keyboard.remove_hotkey(shortcut)

        return wrapper

    return decorator
