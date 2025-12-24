import platform
import os
from pathlib import Path
from typing import Optional, List

# Try to import winreg for Windows registry access
try:
    import winreg
except ImportError:
    winreg = None

class SteamPathDetector:
    """
    Detects Steam installation and userdata directories across platforms.
    """

    @staticmethod
    def get_steam_install_path(settings_path: str = "") -> Optional[Path]:
        """
        Returns the Steam installation path.
        Priority:
        1. settings_path (if valid)
        2. Registry (Windows)
        3. Default locations (All OS)
        """
        # 1. Check settings path override
        if settings_path:
            path = Path(settings_path)
            if path.exists() and path.is_dir():
                return path

        system = platform.system()
        user_home = Path.home()
        candidates = []

        if system == "Windows":
            # 2. Check Registry on Windows
            if winreg:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                        val, _ = winreg.QueryValueEx(key, "SteamPath")
                        # Registry paths often use forward slashes or backslashes
                        reg_path = Path(val)
                        if reg_path.exists():
                            return reg_path
                except OSError:
                    pass

            candidates = [
                Path("C:/Program Files (x86)/Steam"),
                Path("C:/Program Files/Steam"),
            ]
        elif system == "Linux":
            candidates = [
                user_home / ".local/share/Steam",
                user_home / ".steam/steam",
            ]
        elif system == "Darwin":  # macOS
            candidates = [
                user_home / "Library/Application Support/Steam",
            ]

        for path in candidates:
            if path.exists() and path.is_dir():
                return path
        
        return None

    @staticmethod
    def get_userdata_path(steam_root: Optional[Path] = None, override_path: str = "") -> Optional[Path]:
        """
        Returns the 'userdata' directory.
        Priority:
        1. override_path
        2. steam_root / "userdata"
        """
        if override_path:
            path = Path(override_path)
            if path.exists() and path.is_dir():
                return path

        if steam_root is None:
            steam_root = SteamPathDetector.get_steam_install_path()
        
        if steam_root and (steam_root / "userdata").exists():
            return steam_root / "userdata"
        
        return None

    @staticmethod
    def get_grid_paths(userdata_path: Path) -> List[Path]:
        """
        Returns a list of 'config/grid' paths for all users found in userdata.
        Each user has a directory named after their steam account ID (32-bit).
        """
        grid_paths = []
        if not userdata_path.exists():
            return grid_paths

        # Iterate over user directories (directories that are digits)
        for user_dir in userdata_path.iterdir():
            if user_dir.is_dir() and user_dir.name.isdigit():
                grid_dir = user_dir / "config" / "grid"
                grid_paths.append(grid_dir)
        
        return grid_paths

    @staticmethod
    def ensure_grid_dir(grid_path: Path) -> bool:
        """
        Ensures the grid directory exists. Returns True if successful.
        """
        try:
            grid_path.mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            return False
