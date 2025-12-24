from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QScrollArea, QGridLayout, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices
from pathlib import Path
import os

from core.settings import SettingsManager
from core.steamdb import SteamDBFetcher



class DownloadWorker(QThread):
    item_finished = Signal(dict, str, str) # results dict, message, saved_path
    progress = Signal(int, int) # current, total
    finished_batch = Signal(str) # overall message

    def __init__(self, app_ids: list, parent=None):
        super().__init__(parent)
        self.app_ids = app_ids
        self.last_path = ""

    def run(self):
        total = len(self.app_ids)
        success_count = 0
        
        # Get install path from settings
        settings = SettingsManager()
        install_root = Path(settings.install_path)
        
        for i, app_id in enumerate(self.app_ids):
            # Report progress start of item
            self.progress.emit(i, total)
            
            # 1. Fetch Game Name
            game_name = SteamDBFetcher.get_game_name(app_id)
            
            # Sanitize folder name
            safe_name = "".join([c for c in game_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            folder_name = f"{safe_name} ({app_id})"
            
            # Create base directory
            base_dir = install_root / folder_name
            try:
                base_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                self.item_finished.emit({}, f"Error creating folder for {app_id}: {e}", "")
                continue

            # 2. Fetch all artwork types
            results = SteamDBFetcher.fetch_all_artwork(app_id)
            if not any(results.values()):
                self.item_finished.emit({}, f"No artwork found for {game_name}.", "")
                continue

            # 3. Save Images Locally
            local_saved = 0
            
            # Mapping for local filenames
            local_mapping = {
                "header": "header.jpg",
                "library_600x900_2x": "library_600x900_2x.jpg",
                "library_hero_2x": "library_hero_2x.jpg",
                "logo": "logo.png",
                "capsule_231x87": "capsule_231x87.jpg"
            }
            for key, data in results.items():
                if not data: continue
                
                # Local Save
                if key in local_mapping:
                    target = base_dir / local_mapping[key]
                    if SteamDBFetcher.save_image(data, str(target)):
                        local_saved += 1
                                    
            if local_saved > 0:
                success_count += 1
                msg = f"Downloaded {local_saved} images for '{game_name}'."
                self.last_path = str(base_dir.resolve())
                self.item_finished.emit(results, msg, self.last_path)
            else:
                self.item_finished.emit({}, f"Failed to save images for {game_name}.", "")

        # Final progress update
        self.progress.emit(total, total)
        self.finished_batch.emit(f"Batch completed. Successfully downloaded {success_count}/{total} games.")

from ui.search_dialog import SearchDialog

class DownloaderTab(QWidget):
    def __init__(self):
        super().__init__()
        self.last_saved_path = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Input
        input_layout = QHBoxLayout()
        self.appid_input = QLineEdit()
        self.appid_input.setPlaceholderText("Enter Steam AppID(s) or Game Name")
        input_layout.addWidget(self.appid_input)
        
        self.fetch_btn = QPushButton("Fetch & Install")
        self.fetch_btn.clicked.connect(self.start_download)
        input_layout.addWidget(self.fetch_btn)
        
        layout.addLayout(input_layout)



        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Action Buttons
        action_layout = QHBoxLayout()
        self.open_folder_btn = QPushButton("Open Destination Folder")
        self.open_folder_btn.clicked.connect(self.open_destination)
        action_layout.addWidget(self.open_folder_btn)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)

        self.status_label = QLabel("Idle")
        layout.addWidget(self.status_label)

        # Scroll Area for Previews
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)

        # Keep track of grid position
        self.grid_row = 0
        self.grid_col = 0

    def start_download(self):
        user_input = self.appid_input.text().strip()
        if not user_input:
            return

        # Check for batch input (space separated digits)
        parts = user_input.split()
        is_batch = len(parts) > 1 and all(p.isdigit() for p in parts)
        
        target_ids = []

        if is_batch:
            target_ids = parts
        else:
            # Single item logic (ID or Search)
            if user_input.isdigit():
                target_ids = [user_input]
            else:
                # Search mode
                dialog = SearchDialog(user_input, self)
                if dialog.exec():
                    target_ids = [dialog.selected_appid]
                    self.appid_input.setText(dialog.selected_appid)
                else:
                    return

        self.fetch_btn.setEnabled(False)
        self.status_label.setText("Starting download...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Clear previous previews
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        self.grid_row = 0
        self.grid_col = 0
        
        self.worker = DownloadWorker(target_ids)
        self.worker.item_finished.connect(self.on_item_finished)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_batch.connect(self.on_batch_finished)
        self.worker.start()

    def on_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_batch_finished(self, message):
        self.fetch_btn.setEnabled(True)
        self.status_label.setText(message)
        # self.progress_bar.setVisible(False) # Keep visible to show completion

    def on_item_finished(self, results, message, saved_path):
        self.status_label.setText(message)
        if saved_path:
            self.last_saved_path = saved_path

        # Display previews
        for key, data in results.items():
            if data:
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                
                # Scale down if huge
                if pixmap.width() > 300:
                    pixmap = pixmap.scaledToWidth(300, Qt.SmoothTransformation)

                container = QWidget()
                vbox = QVBoxLayout(container)
                
                img_lbl = QLabel()
                img_lbl.setPixmap(pixmap)
                img_lbl.setAlignment(Qt.AlignCenter)
                vbox.addWidget(img_lbl)
                
                txt_lbl = QLabel(key)
                txt_lbl.setAlignment(Qt.AlignCenter)
                vbox.addWidget(txt_lbl)
                
                self.grid_layout.addWidget(container, self.grid_row, self.grid_col)
                self.grid_col += 1
                if self.grid_col > 1: # 2 columns
                    self.grid_col = 0
                    self.grid_row += 1

    def open_destination(self):
        path_to_open = ""
        if self.last_saved_path and os.path.exists(self.last_saved_path):
            path_to_open = self.last_saved_path
        else:
            # Fallback to configured install folder
            settings = SettingsManager()
            base = Path(settings.install_path).resolve()
            if base.exists():
                path_to_open = str(base)
        
        if path_to_open:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path_to_open))
        else:
            self.status_label.setText("No download folder found yet.")
