
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFileDialog, QCheckBox, QMessageBox, QGroupBox)
from PySide6.QtCore import Signal
from core.settings import SettingsManager
from core.steam_paths import SteamPathDetector
import os

class SettingsTab(QWidget):
    show_logs_requested = Signal()

    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Steam Path Section
        steam_group = QGroupBox("Steam Installation")
        steam_layout = QVBoxLayout()
        
        lbl_steam = QLabel("Steam Location (Optional override):")
        steam_layout.addWidget(lbl_steam)
        
        steam_h_layout = QHBoxLayout()
        self.steam_path_input = QLineEdit()
        self.steam_path_input.setText(self.settings.steam_path)
        steam_h_layout.addWidget(self.steam_path_input)
        
        steam_browse_btn = QPushButton("Browse")
        steam_browse_btn.clicked.connect(self.browse_steam_path)
        steam_h_layout.addWidget(steam_browse_btn)
        
        steam_layout.addLayout(steam_h_layout)
        steam_group.setLayout(steam_layout)
        layout.addWidget(steam_group)

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
        
        # Show Logs Button
        logs_btn = QPushButton("Show Application Logs")
        logs_btn.clicked.connect(self.show_logs_requested.emit)
        layout.addWidget(logs_btn)
        
        layout.addStretch()

    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Install Directory")
        if directory:
            self.path_input.setText(directory)

    def browse_steam_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Steam Directory")
        if directory:
            self.steam_path_input.setText(directory)

    def save_settings(self):
        path = self.path_input.text().strip()
        steam_path = self.steam_path_input.text().strip()
        
        self.settings.install_path = path or "art-downloads"
        self.settings.steam_path = steam_path
        self.settings.save_settings()
        
        QMessageBox.information(self, "Settings Saved", "Settings updated successfully.")

