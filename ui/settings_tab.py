from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFileDialog, QCheckBox, QMessageBox, QGroupBox)
from core.settings import SettingsManager
from core.steam_paths import SteamPathDetector
import os

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Steam Path Section
        # Install Path Group
        path_group = QGroupBox("Download Configuration")
        path_layout = QVBoxLayout()
        
        lbl = QLabel("Install Path (where images will be downloaded):")
        path_layout.addWidget(lbl)
        
        h_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(self.settings.install_path)
        h_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_path)
        h_layout.addWidget(browse_btn)
        
        path_layout.addLayout(h_layout)
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # Download Types (Checkbox Group)
        types_group = QGroupBox("Artwork Types to Download")
        types_layout = QVBoxLayout()
        
        self.type_checks = {}
        for key in ["header", "library_600x900_2x", "library_hero_2x", "logo", "capsule_231x87"]:
            chk = QCheckBox(key)
            # Default to checked 
            chk.setChecked(True) 
            types_layout.addWidget(chk)
            self.type_checks[key] = chk
            
        types_group.setLayout(types_layout)
        # Hidden for now as logic in main doesn't fully support toggling types yet
        # layout.addWidget(types_group) 

        # Save Button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()

    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Install Directory")
        if directory:
            self.path_input.setText(directory)

    def save_settings(self):
        path = self.path_input.text().strip()
        
        if path:
             # Create if doesn't exist? Or just ensure it's a valid string. 
             # We rely on worker to create it if missing, but checking here is good UX.
             pass
        
        self.settings.install_path = path or "art-downloads"
        self.settings.save_settings()
        
        QMessageBox.information(self, "Settings Saved", "Settings updated successfully.")

