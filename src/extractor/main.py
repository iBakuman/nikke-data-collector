#!/usr/bin/env python
"""
Character Extractor Application

This script launches the Character Extractor UI that allows users to:
1. Select or paste an input image containing character sprites
2. Choose which character positions to extract
3. Name each extracted character
4. Save characters to the specified output directory
"""
import sys

import qdarktheme
from PySide6.QtGui import QGuiApplication, Qt
from PySide6.QtWidgets import QApplication

from collector.ui_def import STANDARD_WINDOW_WIDTH
from collector.window_manager import WindowManager
from extractor.app_config import AppConfigManager
from extractor.main_window import MainWindow

QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Floor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme('dark')
    config_manager = AppConfigManager()
    window_manager = WindowManager("nikke.exe")
    window_manager.resize_to_standard(STANDARD_WINDOW_WIDTH)
    window = MainWindow(config_manager)
    window.resize(600, 700)
    window.show()
    sys.exit(app.exec())
