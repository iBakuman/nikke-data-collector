import os
import sys
from typing import Dict, List, Tuple

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from collector.character_extractor import (CharacterExtractionParams,
                                           calculate_character_positions,
                                           generate_character_filename)
from collector.logging_config import get_logger
from components.image_input import ImageInputWidget
from components.path_selector import PathSelector

logger = get_logger(__name__)


class CharacterExtractorApp(QWidget):
    """Character extraction application with GUI for selecting characters and naming them"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Character Extractor")
        
        # Data members
        self.current_position_index = 0
        self.selected_positions = []
        self.extraction_params = CharacterExtractionParams(
            boundary_width=50,
            character_width=120,
            character_spacing=10,
            height_width_ratio=1.5
        )
        self.extracted_images = {}  # To store temporary images
        
        # Setup UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Output directory selector
        output_group = QGroupBox("Output Directory")
        output_layout = QVBoxLayout(output_group)
        self.output_path_selector = PathSelector(default_path="")
        output_layout.addWidget(self.output_path_selector)
        main_layout.addWidget(output_group)
        
        # Input image selector with clipboard support
        input_group = QGroupBox("Input Image")
        input_layout = QVBoxLayout(input_group)
        self.image_input = ImageInputWidget()
        input_layout.addWidget(self.image_input)
        main_layout.addWidget(input_group)
        
        # Character position selection
        positions_group = QGroupBox("Select Character Positions")
        positions_layout = QVBoxLayout(positions_group)
        
        # Grid for checkboxes (4×3 grid)
        checkbox_grid = QGridLayout()
        self.position_checkboxes = []
        
        for i in range(12):
            checkbox = QCheckBox(f"Position {i+1}")
            row, col = divmod(i, 3)
            checkbox_grid.addWidget(checkbox, row, col)
            self.position_checkboxes.append(checkbox)
        
        positions_layout.addLayout(checkbox_grid)
        
        # Select All button
        select_all_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all_positions)
        select_all_layout.addWidget(select_all_btn)
        
        # Clear All button
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self._clear_all_positions)
        select_all_layout.addWidget(clear_all_btn)
        
        positions_layout.addLayout(select_all_layout)
        main_layout.addWidget(positions_group)
        
        # Character preview and naming
        preview_group = QGroupBox("Character Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(200, 300)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        preview_layout.addWidget(self.image_label)
        
        # Character name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Character Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter name and press Enter")
        self.name_input.returnPressed.connect(self._save_current_and_advance)
        self.name_input.setEnabled(False)  # Disabled until extraction starts
        name_layout.addWidget(self.name_input)
        
        preview_layout.addLayout(name_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        preview_layout.addWidget(self.status_label)
        
        main_layout.addWidget(preview_group)
        
        # Run button
        self.run_button = QPushButton("Run Extraction")
        self.run_button.clicked.connect(self._start_extraction)
        main_layout.addWidget(self.run_button)
    
    def _select_all_positions(self):
        """Select all character positions"""
        for checkbox in self.position_checkboxes:
            checkbox.setChecked(True)
    
    def _clear_all_positions(self):
        """Clear all character positions"""
        for checkbox in self.position_checkboxes:
            checkbox.setChecked(False)
    
    def _start_extraction(self):
        """Start the character extraction process"""
        # Get selected positions
        self.selected_positions = []
        for i, checkbox in enumerate(self.position_checkboxes):
            if checkbox.isChecked():
                self.selected_positions.append(i + 1)
        
        if not self.selected_positions:
            QMessageBox.warning(self, "Warning", "Please select at least one character position.")
            return
        
        # Get output path
        output_path = self.output_path_selector.get_path()
        if not output_path or not os.path.isdir(output_path):
            QMessageBox.warning(self, "Warning", "Please select a valid output directory.")
            return
        
        # Get input image
        image = self.image_input.get_image()
        if image is None:
            QMessageBox.warning(self, "Warning", "Please select or paste an image first.")
            return
        
        # Extract all selected character images at once but don't save them yet
        try:
            # Calculate character positions
            positions = calculate_character_positions(
                self.extraction_params.boundary_width,
                self.extraction_params.character_width,
                self.extraction_params.character_spacing,
                12
            )
            
            # Calculate character height based on ratio
            character_height = int(self.extraction_params.character_width * 
                                 self.extraction_params.height_width_ratio)
            
            # Use image bottom as the bottom boundary
            bottom_boundary = image.height
            
            # Calculate top boundary position
            top_boundary = bottom_boundary - character_height
            
            # Store extracted images
            self.extracted_images = {}
            for position in self.selected_positions:
                start_x, end_x = positions[position - 1]
                character_image = image.crop((start_x, top_boundary, end_x, bottom_boundary))
                self.extracted_images[position] = character_image
            
            # Start the naming process with the first image
            self.current_position_index = 0
            self._show_current_character()
            
            # Enable the name input and disable the run button
            self.name_input.setEnabled(True)
            self.name_input.setFocus()
            self.run_button.setEnabled(False)
            
            # Disable UI elements during extraction
            self._set_ui_elements_enabled(False)
            
        except Exception as e:
            logger.error(f"Error extracting characters: {e}")
            QMessageBox.critical(self, "Error", f"Failed to process image: {str(e)}")
    
    def _set_ui_elements_enabled(self, enabled):
        """Enable or disable UI elements during extraction"""
        self.output_path_selector.setEnabled(enabled)
        self.image_input.setEnabled(enabled)
        
        for checkbox in self.position_checkboxes:
            checkbox.setEnabled(enabled)
    
    def _show_current_character(self):
        """Display the current character image in the preview area"""
        if self.current_position_index >= len(self.selected_positions):
            # We're done
            self.status_label.setText("All characters processed!")
            self.image_label.clear()
            self.name_input.setEnabled(False)
            self.run_button.setEnabled(True)
            self._set_ui_elements_enabled(True)
            return
        
        # Get the current position
        current_position = self.selected_positions[self.current_position_index]
        
        # Get the image
        character_image = self.extracted_images[current_position]
        
        # Display the image
        qimage = self._pil_to_qimage(character_image)
        pixmap = QPixmap.fromImage(qimage)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.width(), 
            self.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
        
        # Update status
        progress = f"{self.current_position_index + 1}/{len(self.selected_positions)}"
        self.status_label.setText(f"Naming character at position {current_position} ({progress})")
        
        # Clear the name input
        self.name_input.clear()
    
    def _save_current_and_advance(self):
        """Save the current character with the given name and advance to the next one"""
        if self.current_position_index >= len(self.selected_positions):
            return
        
        # Get the character name
        character_name = self.name_input.text().strip()
        if not character_name:
            QMessageBox.warning(self, "Warning", "Please enter a character name.")
            return
        
        # Get the current position
        current_position = self.selected_positions[self.current_position_index]
        
        # Save the image
        try:
            output_path = self.output_path_selector.get_path()
            character_image = self.extracted_images[current_position]
            
            # Generate filename using the existing function
            file_path = generate_character_filename(output_path, character_name)
            
            # Save the image
            character_image.save(file_path)
            logger.info(f"Saved character at position {current_position} as '{character_name}' to {file_path}")
            
            # Move to the next character
            self.current_position_index += 1
            self._show_current_character()
            
        except Exception as e:
            logger.error(f"Error saving character: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save image: {str(e)}")
    
    def _pil_to_qimage(self, pil_image):
        """Convert PIL Image to QImage"""
        if pil_image.mode == "RGB":
            r, g, b = pil_image.split()
            pil_image = Image.merge("RGB", (b, g, r))
        elif pil_image.mode == "RGBA":
            r, g, b, a = pil_image.split()
            pil_image = Image.merge("RGBA", (b, g, r, a))
        
        data = pil_image.tobytes("raw", pil_image.mode)
        
        if pil_image.mode == "RGBA":
            qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
        else:
            qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
            
        return qimage


def main():
    """Main entry point for the character extractor application"""
    app = QApplication(sys.argv)
    window = CharacterExtractorApp()
    window.resize(800, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 
