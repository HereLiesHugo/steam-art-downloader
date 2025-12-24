import json
from pathlib import Path
from typing import Optional, Dict, Any

class SettingsManager:
    """
    Manages persistent application settings using a JSON file.
    """
    SETTINGS_FILE = Path("settings.json")
    
    DEFAULT_SETTINGS = {
        "steam_path": "",
        "download_types": {
            "header": True,
            "capsule": True,
            "hero": True,
            "logo": True,
            "library_600x900": True
        }
    }

    def __init__(self):
        self._settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        """
        Loads settings from disk, or returns defaults if file doesn't exist.
        """
        if not self.SETTINGS_FILE.exists():
            return self.DEFAULT_SETTINGS.copy()
        
        try:
            with open(self.SETTINGS_FILE, "r") as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = self.DEFAULT_SETTINGS.copy()
                settings.update(data)
                return settings
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading settings: {e}")
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self):
        """
        Saves current settings to disk.
        """
        try:
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(self._settings, f, indent=4)
        except OSError as e:
            print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        self._settings[key] = value
        self.save_settings()

    @property
    def install_path(self) -> str:
        """
        Returns the custom install path for downloads.
        Defaults to 'art-downloads' key if present, otherwise returns empty string
        (which logic elsewhere will interpret as 'use local folder').
        """
        return self._settings.get("install_path", "art-downloads")

    @install_path.setter
    def install_path(self, path: str):
        self._settings["install_path"] = path
        self.save_settings()
