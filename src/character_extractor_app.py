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

from PySide6.QtWidgets import QApplication

from ui.character_extractor_ui import CharacterExtractorApp


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    window = CharacterExtractorApp()
    window.resize(800, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
