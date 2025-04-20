#!/usr/bin/env python
"""
Administrator privilege helper for NIKKE Arena.
This utility checks for admin rights and can restart the application with elevated privileges.
"""
import ctypes
import locale
import os
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QMessageBox,
                               QPushButton, QVBoxLayout, QWidget)


def is_admin():
    """
    Check if the program is running with administrator privileges

    Returns:
        bool: True if running as administrator, False otherwise
    """
    try:
        # Windows-specific check for admin rights
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        # If non-Windows or error in check, return False
        return False


def restart_as_admin():
    """
    Restart the current program with administrator privileges

    Returns:
        bool: True if restart was initiated, False on error
    """
    try:
        # Get the path of the current executable
        if getattr(sys, 'frozen', False):
            # We're running in a bundle (PyInstaller or similar)
            executable = sys.executable
        else:
            # We're running in a normal Python environment
            executable = sys.argv[0]

        # Use ShellExecute to elevate privileges
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, executable, None, 1
        )
        return True
    except Exception as e:
        print(f"Error restarting as admin: {e}")
        return False


def get_system_language():
    """
    Get the system language using non-deprecated methods
    
    Returns:
        bool: True if the system language is Chinese, False otherwise
    """
    try:
        # Set locale to system default
        locale.setlocale(locale.LC_ALL, '')
        # Get current locale
        system_lang = locale.getlocale()[0]
        # Check if it's Chinese
        return system_lang and system_lang.startswith(('zh_', 'zh-'))
    except Exception as e:
        print(f"Error detecting system language: {e}")
        return False


class AdminHelperWindow(QMainWindow):
    """Helper window to check and request admin privileges"""

    def __init__(self):
        super().__init__()

        # Check system language
        self.is_chinese = get_system_language()

        # Set up the window
        if self.is_chinese:
            self.setWindowTitle("管理员权限检查")
        else:
            self.setWindowTitle("Admin Rights Check")

        self.setMinimumSize(400, 200)

        # Create central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Info label
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Action button
        self.action_button = QPushButton()
        self.action_button.setMinimumHeight(40)
        self.action_button.clicked.connect(self.on_action_button_clicked)
        layout.addWidget(self.action_button)

        # Exit button
        if self.is_chinese:
            exit_text = "退出"
        else:
            exit_text = "Exit"

        exit_button = QPushButton(exit_text)
        exit_button.clicked.connect(self.close)
        layout.addWidget(exit_button)

        # Set the central widget
        self.setCentralWidget(central_widget)

        # Check admin status and update UI
        self.update_ui()

    def update_ui(self):
        """Update UI based on admin status"""
        has_admin = is_admin()

        if self.is_chinese:
            if has_admin:
                self.status_label.setText("✅ 已以管理员身份运行")
                self.info_label.setText("程序已经拥有管理员权限，可以正常运行NIKKE Arena。")
                self.action_button.setText("启动NIKKE Arena")
            else:
                self.status_label.setText("❌ 没有管理员权限")
                self.info_label.setText("NIKKE Arena需要管理员权限才能正常运行。\n"
                                        "点击下方按钮以管理员身份重启应用。")
                self.action_button.setText("以管理员身份重启")
        else:
            if has_admin:
                self.status_label.setText("✅ Running as Administrator")
                self.info_label.setText(
                    "The application has administrator privileges and can run NIKKE Arena normally.")
                self.action_button.setText("Launch NIKKE Arena")
            else:
                self.status_label.setText("❌ No Administrator Rights")
                self.info_label.setText("NIKKE Arena requires administrator privileges to function properly.\n"
                                        "Click the button below to restart with elevated privileges.")
                self.action_button.setText("Restart as Administrator")

    def on_action_button_clicked(self):
        """Handle action button click"""
        if is_admin():
            # Already have admin rights, launch the main application
            self.launch_main_app()
        else:
            # Need to restart with admin rights
            if restart_as_admin():
                # If restart initiated, close this application
                self.close()
            else:
                # Show error if restart failed
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Critical)

                if self.is_chinese:
                    msg.setWindowTitle("错误")
                    msg.setText("无法以管理员身份重启应用程序。")
                    msg.setInformativeText("请手动右键点击应用程序并选择'以管理员身份运行'。")
                else:
                    msg.setWindowTitle("Error")
                    msg.setText("Failed to restart application with administrator privileges.")
                    msg.setInformativeText(
                        "Please manually right-click the application and select 'Run as administrator'.")

                msg.exec()

    def launch_main_app(self):
        """Launch the main application"""
        try:
            # Determine the path to main.py
            if getattr(sys, 'frozen', False):
                # We're running in a bundle
                main_dir = os.path.dirname(sys.executable)
            else:
                # We're running in a normal Python environment
                main_dir = os.path.dirname(os.path.abspath(__file__))

            main_script = os.path.join(main_dir, "main.py")

            # Start the main application
            subprocess.Popen([sys.executable, main_script])

            # Close this helper
            self.close()

        except Exception as e:
            # Show error if launch failed
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)

            if self.is_chinese:
                msg.setWindowTitle("错误")
                msg.setText(f"启动主应用程序时出错: {e}")
            else:
                msg.setWindowTitle("Error")
                msg.setText(f"Error launching main application: {e}")

            msg.exec()


def main():
    """Main entry point for the admin helper"""
    app = QApplication(sys.argv)
    window = AdminHelperWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
