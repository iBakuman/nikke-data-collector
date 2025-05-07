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

from PySide6.QtGui import QGuiApplication, Qt
from PySide6.QtWidgets import QApplication

from extractor.character_extractor_ui import CharacterExtractorApp

QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Floor)

if __name__ == "__main__":
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    window = CharacterExtractorApp()
    window.resize(800, 700)
    window.show()
    sys.exit(app.exec())
