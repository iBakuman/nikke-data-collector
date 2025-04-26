import os
import sys

from PySide6.QtWidgets import QApplication

from picker import PickerApp

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    picker = PickerApp()
    if picker.wm:  # Only run if initialization was successful
        sys.exit(app.exec())
    else:
        sys.exit(1)  # Exit with error code if WM failed
