#!/usr/bin/env python
"""
About window for the NIKKE Data Collector application.
"""
import os

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QLabel, QTextBrowser,
                               QVBoxLayout)

from nikke_arena.resources import RESOURCE_DIR


class AboutWindow(QDialog):
    """
    Dialog window that shows information about the application,
    including version, credits, and license information.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set window title and properties
        self.setWindowTitle("About NIKKE Data Collector")
        self.setMinimumSize(QSize(600, 400))
        self.setMaximumSize(QSize(600, 400))
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # Create layout
        layout = QVBoxLayout(self)

        # Try to add logo if it exists
        try:
            logo_path = os.path.join(RESOURCE_DIR, "logo.png")
            if os.path.exists(logo_path):
                logo_label = QLabel(self)
                logo_pixmap = QPixmap(logo_path)
                logo_label.setPixmap(logo_pixmap.scaledToWidth(128, Qt.TransformationMode.SmoothTransformation))
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(logo_label)
        except Exception:
            # Continue without logo if it can't be loaded
            pass

        # Add title and version
        title_label = QLabel("NIKKE Data Collector", self)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        version_label = QLabel("Version 1.0.0", self)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        # Add description
        description = QTextBrowser(self)
        description.setOpenExternalLinks(True)
        description.setHtml("""
        <p style='text-align:center'>
            A tool for collecting and analyzing data from NIKKE Arena tournaments.
        </p>
        <p style='text-align:center'>
            <a href='https://github.com/iBakuman/nikke-data-collector' style='color:#20a8f0'>GitHub Repository</a>
        </p>
        <p style='text-align:center'>
            <b>Acknowledgements:</b><br>
            Uses PySide6 for the user interface<br>
            Uses OpenCV for image recognition<br>
            Special thanks to contributors and testers
        </p>
        <p style='text-align:center'>
            <b>Copyright Information:</b><br>
            © 2023-2024 NIKKE Data Collector Contributors<br>
            Licensed under the MIT License<br>
            This is open source software - see the repository for full license details
        </p>
        <p style='text-align:center'>
            <b>Legal Notice:</b><br>
            This tool is not affiliated with Shift Up or the official NIKKE game.<br>
            NIKKE and all related properties are trademarks of their respective owners.
        </p>
        <p style='text-align:center'>
            <b>Disclaimer:</b><br>
            This software is for personal learning and research purposes only and not for commercial use.<br>
            Users must comply with relevant laws and game service terms while using this software.<br>
            The developers are not responsible for any account issues or losses that may result from using this software.<br>
            By using this software, you acknowledge that you have read and agreed to the above statement.
        </p>
        """)
        description.setMinimumHeight(150)
        layout.addWidget(description)

        # Add OK button
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttonBox.accepted.connect(self.accept)
        layout.addWidget(buttonBox)

        # Set the layout
        self.setLayout(layout)
