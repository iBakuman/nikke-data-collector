#!/usr/bin/env python
"""
Main entry point for NIKKE Arena application.
"""
import locale
import os
import signal
import sys
import time
from typing import Union

import keyboard
from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QMainWindow,
                               QMessageBox, QPushButton, QTextEdit,
                               QVBoxLayout)

from about import AboutWindow
from admin_helper import is_admin
from config_manager import ConfigManager
from nikke_arena import CharacterDAO
from nikke_arena.character_matcher import CharacterMatcher
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
from nikke_arena.window_manager import WindowManager, WindowNotFoundException
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
    def __init__(self, config_manager: ConfigManager):
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
        self.config_manager = config_manager

        # Apply saved configuration
        self._apply_saved_config()

        # Connect UI signals
        self.ui.startBtn.clicked.connect(self._on_confirm)
        self.path_selector.pathChanged.connect(self._on_path_changed)
        self.ui.languageComboBox.currentIndexChanged.connect(self._on_language_changed)

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

        # Set language selection based on config
        saved_language = self.config_manager.get("app_language", "")
        if saved_language.startswith("zh"):
            self.ui.languageComboBox.setCurrentIndex(1)  # Chinese
        else:
            self.ui.languageComboBox.setCurrentIndex(0)  # English

    def _on_path_changed(self, path):
        """Save the selected path when it changes"""
        self.config_manager.set("last_save_dir", path)
        self.config_manager.save_config()

    def _on_language_changed(self,index):
        """Handle language change from dropdown"""
        # Map index to language code
        if index == 1:  # Chinese
            language_code = "zh_CN"
        else:  # Default to English
            language_code = "en_US"
        self.config_manager.set("app_language", language_code)
        self.config_manager.save_config()
        # Show notification that restart is required
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        # Use translation for current language
        if language_code.startswith('zh'):
            msg.setWindowTitle("需要重启")
            msg.setText("语言设置已更改。请重启应用程序以应用新的语言设置。")
        else:
            msg.setWindowTitle("Restart Required")
            msg.setText(
                "Language setting has been changed. Please restart the application to apply the new language setting.")
        msg.exec()

    @staticmethod
    def _copy_to_clipboard(text):
        """Copy text to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def show_message(self, title, message, icon: Union[QMessageBox.Icon, int] = QMessageBox.Icon.Information, enable_copy=False):
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
            copy_btn = QPushButton(self.tr("Copy to Clipboard"), dialog)
            copy_btn.clicked.connect(lambda: self._copy_to_clipboard(message))
            button_layout.addWidget(copy_btn)

            # OK button
            ok_btn = QPushButton(self.tr("OK"), dialog)
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
            self.show_message(self.tr("Error"), self.tr("No Task Selected"), QMessageBox.Icon.Critical)

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
            self.show_message(self.tr("Error"), self.tr("Save path is empty. Please select a directory to save data."),
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
                self.show_message(self.tr("Error"), self.tr("Delay min is greater than or equal to delay max"),
                                  QMessageBox.Icon.Critical)
                return
            self.config_manager.set("delay.min", delay_min)
            self.config_manager.set("delay.max", delay_max)
            self.config_manager.save_config()

            # Initialize window manager - this might throw an exception if NIKKE isn't running
            try:
                self.window_manager = WindowManager(process_name="nikke.exe")
                self.window_capturer = WindowCapturer(self.window_manager)
            except WindowNotFoundException:
                self.show_message(self.tr("Error"), self.tr("NIKKE is not running. Please start the game first."),
                                  QMessageBox.Icon.Critical)
                return
            except Exception as e:
                # Re-raise if it's a different error
                raise

            delay_manager = DelayManager(min_delay=delay_min, max_delay=delay_max)
            mouse_controller = MouseController(self.window_manager, delay_manager=delay_manager)

            # Get cache directory
            cache_dir = ConfigManager.get_cache_dir()
            logger.info(f"Using cache directory: {cache_dir}")

            if collection_type == 'players':
                character_dao =CharacterDAO()
                # Initialize character matcher with platform-specific cache dir
                character_matcher = CharacterMatcher(cache_dir=cache_dir, character_dao=character_dao)
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
                success_msg = f"{success_msg}\n{self.tr('Execution time')}: {time_str}"
            else:
                success_msg = f"{self.tr('Data collection completed successfully')}\n{self.tr('Execution time')}: {time_str}"

            # Log execution time
            logger.info(f"Task completed in {time_str}")

            # Show results
            self.show_message(self.tr("Success"), success_msg)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.info(f"Error during processing: {e}")
            logger.info(f"Error details:\n{error_details}")

            self.show_message(self.tr("Error"), self.tr("Error: {0}").format(str(e)), QMessageBox.Icon.Critical)
        finally:
            # Re-enable UI elements
            self.ui.startBtn.setEnabled(True)
            self.ui.startBtn.setText(self.tr("Link Start"))
            self.path_selector.setEnabled(True)

    def _execute_crawl_players(self):
        """Execute group data collection"""
        self._execute_data_collection(
            collection_type='players',
            success_msg=self.tr("Group data collection completed successfully")
        )

    def _execute_crawl_64_32(self):
        """Execute 64->32 tournament data collection"""
        self._execute_data_collection(
            collection_type='promotion',
            stage=TournamentStage.STAGE_64_32,
            success_msg=self.tr("64->32 tournament data collection completed successfully")
        )

    def _execute_crawl_32_16(self):
        """Execute 32->16 tournament data collection"""
        self._execute_data_collection(
            collection_type='promotion',
            stage=TournamentStage.STAGE_32_16,
            success_msg=self.tr("32->16 tournament data collection completed successfully")
        )

    def _execute_crawl_16_8(self):
        """Execute 16->8 tournament data collection"""
        self._execute_data_collection(
            collection_type='promotion',
            stage=TournamentStage.STAGE_16_8,
            success_msg=self.tr("16->8 tournament data collection completed successfully")
        )

    def _execute_crawl_8_4(self):
        """Execute 8->4 tournament data collection"""
        self._execute_data_collection(
            collection_type='championship',
            stage=TournamentStage.STAGE_8_4,
            success_msg=self.tr("8->4 tournament data collection completed successfully")
        )

    def _execute_crawl_4_2(self):
        """Execute 4->2 tournament data collection"""
        self._execute_data_collection(
            collection_type='championship',
            stage=TournamentStage.STAGE_4_2,
            success_msg=self.tr("4->2 tournament data collection completed successfully")
        )

    def _execute_crawl_2_1(self):
        """Execute 2->1 tournament data collection"""
        self._execute_data_collection(
            collection_type='championship',
            stage=TournamentStage.STAGE_2_1,
            success_msg=self.tr("2->1 tournament data collection completed successfully")
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
        # Store app instance for easy access from other parts of the program
        self.app.parent_app = self
        set_app_theme(self.app)

        # Load translations based on system locale or saved preference
        self.config_manager = ConfigManager()
        self.translator = QTranslator()

        # Get language preference from config, or use system locale as default
        saved_language = self.config_manager.get("app_language", "")
        if saved_language:
            current_locale = QLocale(saved_language)
        else:
            # Use system locale
            current_locale = QLocale.system()

        # Get language name (e.g., "zh_CN", "en_US")
        lang_name = current_locale.name()
        logger.info(f"Setting application language to: {lang_name}")

        # Check if translation file exists and load it
        try:
            # Import the translation file loading function from ui.asset
            from ui.asset import get_translation_file
            # Try loading the translation file for the current locale
            translation_path = get_translation_file(lang_name)
            # Try loading the translation file
            ok = self.translator.load(translation_path)
            logger.info(f"Load translation file for {lang_name}")
            self.app.installTranslator(self.translator)
            if not ok:
                logger.warning(f"Failed to load translation file for {lang_name}, using english")
        except Exception as e:
            logger.error(f"Error loading translation: {e}")

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
        self.window = MainWindow(self.config_manager)


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
        return self.app.exec()


if __name__ == "__main__":
    app = App()
    sys.exit(app.run())
