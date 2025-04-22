#!/usr/bin/env python
"""
Main entry point for NIKKE Arena application.
"""
import locale
import os
import signal
import sys
import time

import keyboard
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QMainWindow,
                               QMessageBox, QPushButton, QTextEdit,
                               QVBoxLayout)

from about import AboutWindow
from admin_helper import is_admin
from config_manager import ConfigManager
from nikke_arena.character_matcher import CharacterImageMatcher
from nikke_arena.delay_manager import DelayManager
from nikke_arena.image_detector import ImageDetector
from nikke_arena.lineup_processor import LineupProcessor
from nikke_arena.logging_config import configure_logging
from nikke_arena.models import TournamentStage
from nikke_arena.mouse_control import MouseController
from nikke_arena.profile_collector import ProfileCollector
from nikke_arena.resources import logo_path
from nikke_arena.tournament_64_player_collector import \
    Tournament64PlayerCollector
from nikke_arena.tournament_championship_collector import \
    ChampionshipTournamentCollector
from nikke_arena.tournament_promotion_collector import PromotionDataCollector
from nikke_arena.window_capturer import WindowCapturer
from nikke_arena.window_manager import WindowManager
from theme import set_app_theme
from ui.main import Ui_MainWindow
from ui.path_selector import PathSelector
from ui.time_warning_dialog import TimeWarningDialog

# Initialize logging with platform-specific log directory
log_dir = ConfigManager.get_log_dir()
log_file = os.path.join(log_dir, "nikke_data_collector.log")
logger = configure_logging(log_file=log_file, include_file_info=True)
logger.info("Starting NIKKE Arena application")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.path_selector = PathSelector()
        self.ui.appLayout.insertWidget(0, self.path_selector)

        # Set application icon if available
        try:
            from pathlib import Path

            from nikke_arena.resources import RESOURCE_DIR
            icon_path = Path(RESOURCE_DIR) / "icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception as e:
            logger.error(f"Failed to set application icon: {e}")

        # Initialize config manager
        self.config_manager = ConfigManager()

        # Apply saved configuration
        self._apply_saved_config()

        # Initialize core components
        self.window_manager = WindowManager(process_name="nikke.exe")
        self.window_capturer = WindowCapturer(self.window_manager)

        # Connect UI signals
        self.ui.startBtn.clicked.connect(self._on_confirm)
        self.path_selector.pathChanged.connect(self._on_path_changed)

        # Set up About menu
        self._setup_about_menu()

        # Clear focus from all widgets
        self.setFocus()

    def _apply_saved_config(self):
        """Apply saved configuration to UI elements"""
        # Set delay values from config
        min_delay = self.config_manager.get("delay.min", 0.5)
        max_delay = self.config_manager.get("delay.max", 2.0)
        self.ui.delayMinSpin.setValue(min_delay)
        self.ui.delayMaxSpin.setValue(max_delay)

        # Set last save directory if it exists
        last_save_dir = self.config_manager.get("last_save_dir", "")
        if last_save_dir and os.path.exists(last_save_dir):
            self.path_selector.set_path(last_save_dir)

    def _on_path_changed(self, path):
        """Save the selected path when it changes"""
        self.config_manager.set("last_save_dir", path)
        self.config_manager.save_config()

    @staticmethod
    def _copy_to_clipboard(text):
        """Copy text to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def show_message(self, title, message, icon=QMessageBox.Icon.Information, enable_copy=False):
        if not enable_copy:
            # Standard message box for normal messages
            msg = QMessageBox(self)
            msg.setWindowTitle(self.tr(title))
            msg.setText(self.tr(message))
            msg.setIcon(icon)
            # Set window flag to make the message box stay on top
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

            # Set window icon if application has an icon
            if self.windowIcon():
                msg.setWindowIcon(self.windowIcon())

            msg.exec()
        else:
            # Custom dialog with copy button for copyable content
            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr(title))
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            dialog.setMinimumWidth(400)

            # Set window icon if application has an icon
            if self.windowIcon():
                dialog.setWindowIcon(self.windowIcon())

            # Create layout
            layout = QVBoxLayout(dialog)

            # Add text display area
            text_edit = QTextEdit(dialog)
            text_edit.setPlainText(message)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)

            # Add buttons
            button_layout = QHBoxLayout()

            # Copy button
            copy_btn = QPushButton("Copy to Clipboard", dialog)
            copy_btn.clicked.connect(lambda: self._copy_to_clipboard(message))
            button_layout.addWidget(copy_btn)

            # OK button
            ok_btn = QPushButton("OK", dialog)
            ok_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(ok_btn)

            layout.addLayout(button_layout)

            # Show dialog
            dialog.exec()

    def _on_confirm(self):
        if self.ui.crawl_players_btn.isChecked():
            self._execute_crawl_players()
        elif self.ui.crawl_64_32_btn.isChecked():
            self._execute_crawl_64_32()
        elif self.ui.crawl_32_16_btn.isChecked():
            self._execute_crawl_32_16()
        elif self.ui.crawl_16_8_btn.isChecked():
            self._execute_crawl_16_8()
        elif self.ui.crawl_8_4_btn.isChecked():
            self._execute_crawl_8_4()
        elif self.ui.crawl_4_2_btn.isChecked():
            self._execute_crawl_4_2()
        elif self.ui.crawl_2_1_btn.isChecked():
            self._execute_crawl_2_1()
        else:
            self.show_message("Error", "No Task Selected", QMessageBox.Icon.Critical)

    def _execute_data_collection(self, collection_type, stage=None, success_msg=None):
        """
        Common helper method for all data collection tasks.

        Args:
            collection_type: Type of collection task ('group', 'promotion', 'championship')
            stage: Tournament stage enum (required for promotion and championship)
            success_msg: Success message to show on completion
        """
        # Check if save path is empty
        storage_path = self.path_selector.get_path()
        if not storage_path:
            self.show_message("Error", "Save path is empty. Please select a directory to save data.",
                              QMessageBox.Icon.Critical)
            return

        # Show warning for long-running tasks if needed
        if collection_type == 'players' or (collection_type == 'promotion' and stage == TournamentStage.STAGE_64_32):
            # Check if user has opted not to show the warning
            show_warning = self.config_manager.get("show_time_warning", True)

            if show_warning:
                warning_dialog = TimeWarningDialog(self)
                result = warning_dialog.exec()

                # If user clicked cancel, abort the operation
                if result != QDialog.DialogCode.Accepted:
                    return

                # Save user preference if they checked "Don't show again"
                if warning_dialog.should_not_show_again():
                    self.config_manager.set("show_time_warning", False)
                    self.config_manager.save_config()

        # Disable UI elements during processing
        self.ui.startBtn.setEnabled(False)
        self.ui.startBtn.setText(self.tr("Processing..."))
        self.path_selector.setEnabled(False)

        # Record start time
        start_time = time.time()

        try:
            # Get delay settings and save to config
            delay_min = self.ui.delayMinSpin.value()
            delay_max = self.ui.delayMaxSpin.value()
            if delay_min >= delay_max:
                self.show_message("Error", "Delay min is greater than or equal to delay max", QMessageBox.Icon.Critical)
                return
            self.config_manager.set("delay.min", delay_min)
            self.config_manager.set("delay.max", delay_max)
            self.config_manager.save_config()

            delay_manager = DelayManager(min_delay=delay_min, max_delay=delay_max)
            mouse_controller = MouseController(self.window_manager, delay_manager=delay_manager)

            # Get cache directory
            cache_dir = ConfigManager.get_cache_dir()
            logger.info(f"Using cache directory: {cache_dir}")

            if collection_type == 'players':
                # Initialize character matcher with platform-specific cache dir
                character_matcher = CharacterImageMatcher(cache_dir=cache_dir)

                profile_collector = ProfileCollector(controller=mouse_controller, capturer=self.window_capturer)
                lineup_processor = LineupProcessor(
                    controller=mouse_controller,
                    capturer=self.window_capturer,
                    matcher=character_matcher,
                    profile_collector=profile_collector
                )

                collector = Tournament64PlayerCollector(
                    controller=mouse_controller,
                    lineup_processor=lineup_processor,
                    save_dir=storage_path,
                )

                logger.info(f"Starting collection of all players. Results will be saved to: {storage_path}")
                collector.collect_all_groups()
            else:
                image_detector = ImageDetector(
                    self.window_capturer,
                    self.window_manager,
                )

                if collection_type == 'promotion':
                    # Initialize promotion tournament collector
                    collector = PromotionDataCollector(
                        capturer=self.window_capturer,
                        controller=mouse_controller,
                        detector=image_detector,
                        save_dir=storage_path
                    )
                    collector.collect_stage(stage=stage)
                elif collection_type == 'championship':
                    # Initialize championship tournament collector
                    collector = ChampionshipTournamentCollector(
                        capturer=self.window_capturer,
                        controller=mouse_controller,
                        detector=image_detector,
                        save_dir=storage_path
                    )

                    # Collect data for this stage
                    collector.collect_stage(stage=stage)

            # Calculate execution time
            end_time = time.time()
            execution_time = end_time - start_time

            # Format execution time
            hours, remainder = divmod(execution_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = ""
            if hours > 0:
                time_str += f"{int(hours)} hours "
            if minutes > 0:
                time_str += f"{int(minutes)} minutes "
            time_str += f"{int(seconds)} seconds"

            # Add execution time to success message
            if success_msg:
                success_msg = f"{success_msg}\nExecution time: {time_str}"
            else:
                success_msg = f"Data collection completed successfully\nExecution time: {time_str}"

            # Log execution time
            logger.info(f"Task completed in {time_str}")

            # Show results
            self.show_message("Success", success_msg)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.info(f"Error during processing: {e}")
            logger.info(f"Error details:\n{error_details}")

            self.show_message("Error", "Error: {0}".format(str(e)), QMessageBox.Icon.Critical)
        finally:
            # Re-enable UI elements
            self.ui.startBtn.setEnabled(True)
            self.ui.startBtn.setText(self.tr("Link Start"))
            self.path_selector.setEnabled(True)

    def _execute_crawl_players(self):
        """Execute group data collection"""
        self._execute_data_collection(
            collection_type='players',
            success_msg="Group data collection completed successfully"
        )

    def _execute_crawl_64_32(self):
        """Execute 64->32 tournament data collection"""
        self._execute_data_collection(
            collection_type='promotion',
            stage=TournamentStage.STAGE_64_32,
            success_msg="64->32 tournament data collection completed successfully"
        )

    def _execute_crawl_32_16(self):
        """Execute 32->16 tournament data collection"""
        self._execute_data_collection(
            collection_type='promotion',
            stage=TournamentStage.STAGE_32_16,
            success_msg="32->16 tournament data collection completed successfully"
        )

    def _execute_crawl_16_8(self):
        """Execute 16->8 tournament data collection"""
        self._execute_data_collection(
            collection_type='promotion',
            stage=TournamentStage.STAGE_16_8,
            success_msg="16->8 tournament data collection completed successfully"
        )

    def _execute_crawl_8_4(self):
        """Execute 8->4 tournament data collection"""
        self._execute_data_collection(
            collection_type='championship',
            stage=TournamentStage.STAGE_8_4,
            success_msg="8->4 tournament data collection completed successfully"
        )

    def _execute_crawl_4_2(self):
        """Execute 4->2 tournament data collection"""
        self._execute_data_collection(
            collection_type='championship',
            stage=TournamentStage.STAGE_4_2,
            success_msg="4->2 tournament data collection completed successfully"
        )

    def _execute_crawl_2_1(self):
        """Execute 2->1 tournament data collection"""
        self._execute_data_collection(
            collection_type='championship',
            stage=TournamentStage.STAGE_2_1,
            success_msg="2->1 tournament data collection completed successfully"
        )

    def _setup_about_menu(self):
        """Set up About menu with action to show About dialog"""
        self.ui.actionAbout.triggered.connect(self._show_about_dialog)

    def _show_about_dialog(self):
        """Show the About dialog"""
        about_dialog = AboutWindow(self)
        about_dialog.exec()


class App:
    def __init__(self):
        """Initialize the main application"""
        # Create application
        self.app = QApplication([])
        set_app_theme(self.app)

        icon_path = logo_path
        if icon_path.exists():
            self.app.setWindowIcon(QIcon(str(icon_path)))

        # Verify admin rights before continuing
        if not is_admin():
            # Check if system language is Chinese
            # Use non-deprecated method to detect locale
            locale.setlocale(locale.LC_ALL, '')
            system_lang = locale.getlocale()[0]
            is_chinese = system_lang and system_lang.startswith(('zh_', 'zh-'))
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            if is_chinese:
                msg.setWindowTitle("需要管理员权限")
                msg.setText("此应用程序需要管理员权限才能正常运行。")
                msg.setInformativeText("请右键点击应用程序并选择'以管理员身份运行'。")
            else:
                msg.setWindowTitle("Administrator Rights Required")
                msg.setText("This application requires administrator privileges to function properly.")
                msg.setInformativeText("Please right-click on the application and select 'Run as administrator'.")
            msg.exec()
            sys.exit(1)
        keyboard.add_hotkey('ctrl+shift+alt+q', self._force_quit)
        logger.info("Global force quit shortcut registered: Ctrl+Shift+Alt+Q")
        self.window = MainWindow()

    @staticmethod
    def _force_quit():
        """Force quit the application immediately using signal termination"""
        logger.info("Force quit triggered")
        # Send SIGINT to the current process - more reliable than normal quit
        os.kill(os.getpid(), signal.SIGINT)

    def run(self) -> int:
        """Run the application"""
        self.window.show()

        # Clear focus from all controls after showing window
        self.window.setFocus()

        # self.window.show_message("Resources Directory", str(RESOURCE_DIR), enable_copy=True)
        return self.app.exec()


if __name__ == "__main__":
    app = App()
    sys.exit(app.run())
