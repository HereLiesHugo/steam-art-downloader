import os
import shutil
from pathlib import Path
from typing import Optional

class ImageCache:
    """
    Simple file-based cache for downloaded images.
    """
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.ensure_cache_dir()

    def ensure_cache_dir(self):
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_image_path(self, app_id: str, image_type: str) -> Path:
        """
        Returns the expected path for a cached image.
        Format: cache/appid_type.jpg
        """
        return self.cache_dir / f"{app_id}_{image_type}.jpg"

    def has_image(self, app_id: str, image_type: str) -> bool:
        return self.get_image_path(app_id, image_type).exists()

    def save_image(self, app_id: str, image_type: str, data: bytes) -> Optional[Path]:
        """
        Saves image bytes to cache.
        """
        try:
            path = self.get_image_path(app_id, image_type)
            # Simple logging (don't overdo it for every file if batching, but fine for now)
            # logger.debug(f"Caching image {path}") 
            with open(path, "wb") as f:
                f.write(data)
            return path
        except OSError as e:
            print(f"Error caching image: {e}")
            return None

    def get_image_data(self, app_id: str, image_type: str) -> Optional[bytes]:
        """
        Reads image bytes from cache.
        """
        try:
            path = self.get_image_path(app_id, image_type)
            if path.exists():
                with open(path, "rb") as f:
                    return f.read()
        except OSError:
            pass
        return None

    def clear_cache(self):
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.ensure_cache_dir()
