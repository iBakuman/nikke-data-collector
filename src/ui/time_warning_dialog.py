#!/usr/bin/env python
"""
Dialog to warn users about long-running tasks
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QLabel,
                               QVBoxLayout)


class TimeWarningDialog(QDialog):
    """
    Dialog to warn users about long-running tasks with an option
    to not show the warning again.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Time Warning")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # Set window icon if parent has an icon
        if parent and parent.windowIcon():
            self.setWindowIcon(parent.windowIcon())
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Warning message
        warning_text = (
            "The '64 Players' and 'Round of 64 → 32' tasks may take a long time to complete.\n\n"
            "If you need to regain control of your computer, press Ctrl+Shift+Alt+Q."
        )
        
        warning_label = QLabel(warning_text)
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # "Don't show again" checkbox
        self.dont_show_again = QCheckBox("Don't show this warning again")
        layout.addWidget(self.dont_show_again)
        
        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def should_not_show_again(self):
        """Return True if the user checked 'Don't show again'"""
        return self.dont_show_again.isChecked() 
