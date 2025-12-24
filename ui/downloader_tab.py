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
        # Calculate total steps: games * artwork_types
        # We need to skip game name fetch in the count or just add it? 
        # Let's count (fetch name + fetch each image) per game? 
        # For simplicity, let's just count images. 
        artwork_keys = list(SteamDBFetcher.URL_TEMPLATES.keys())
        total_steps = len(self.app_ids) * len(artwork_keys)
        current_step = 0
        
        success_count = 0
        
        # Get install path from settings
        settings = SettingsManager()
        install_root = Path(settings.install_path)
        
        for app_id in self.app_ids:
            # 1. Fetch Game Name (Not counted in progress steps for simplicity, or we could add 1)
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
                # Skip this app's progress steps? Or mark them done?
                current_step += len(artwork_keys)
                self.progress.emit(current_step, total_steps)
                continue

            # 2. Fetch and Save Images Loop
            results = {} # Store results for preview
            local_saved = 0
            
            # Mapping for local filenames
            local_mapping = {
                "header": "header.jpg",
                "library_600x900_2x": "library_600x900_2x.jpg",
                "library_hero_2x": "library_hero_2x.jpg",
                "logo": "logo.png",
                "capsule_231x87": "capsule_231x87.jpg"
            }
            
            for key in artwork_keys:
                # Fetch
                img_data = SteamDBFetcher.fetch_image(app_id, key)
                results[key] = img_data
                
                # Save if successful
                if img_data:
                    if key in local_mapping:
                        target = base_dir / local_mapping[key]
                        if SteamDBFetcher.save_image(img_data, str(target)):
                            local_saved += 1
                
                # Update Progress
                current_step += 1
                self.progress.emit(current_step, total_steps)

            # Check success for this game
            if local_saved > 0:
                success_count += 1
                msg = f"Downloaded {local_saved} images for '{game_name}'."
                self.last_path = str(base_dir.resolve())
                self.item_finished.emit(results, msg, self.last_path)
            else:
                self.item_finished.emit({}, f"Failed to save {game_name}.", "")

        # Final progress update
        self.progress.emit(total_steps, total_steps)
        self.finished_batch.emit(f"Batch completed. Successfully downloaded {success_count}/{len(self.app_ids)} games.")

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

        # Inline Log Label
        self.log_label = QLabel("")
        self.log_label.setAlignment(Qt.AlignLeft)
        self.log_label.setStyleSheet("color: gray; font-size: 10px;")
        self.log_label.setWordWrap(True)
        self.log_label.setFixedHeight(30) # Roughly 2 lines
        layout.addWidget(self.log_label)

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

        # Setup inline logging
        self.setup_inline_logging()

    def setup_inline_logging(self):
        from ui.log_window import QtLogHandler
        import logging

        self.inline_handler = QtLogHandler()
        # Only show simple message, no timestamp for inline
        self.inline_handler.setFormatter(logging.Formatter('%(message)s'))
        self.inline_handler.log_signal.connect(self.update_inline_log)
        
        logging.getLogger().addHandler(self.inline_handler)

    def update_inline_log(self, message):
        # Keep last 2 lines
        current_text = self.log_label.text()
        lines = current_text.split('\n') if current_text else []
        lines.append(message)
        
        # Trim to last 2
        if len(lines) > 2:
            lines = lines[-2:]
        
        self.log_label.setText("\n".join(lines))



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
