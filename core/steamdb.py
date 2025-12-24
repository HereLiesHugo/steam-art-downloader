import requests
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class SteamDBFetcher:
    """
    Handles fetching game artwork URLs and downloading images.
    """
    
    # URL Templates for various assets
    URL_TEMPLATES = {
        "header": "https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/header.jpg",
        "library_600x900_2x": "https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/library_600x900_2x.jpg",
        "library_hero_2x": "https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/library_hero_2x.jpg",
        "logo": "https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/logo.png",
        "capsule_231x87": "https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/capsule_231x87.jpg"
    }

    HEADERS = {
        "User-Agent": "SteamArtDownloader/1.0 (Educational/Personal Project)"
    }

    @staticmethod
    def fetch_image(app_id: str, key: str) -> Optional[bytes]:
        """
        Fetches a single artwork image by key (e.g., 'header', 'logo').
        """
        if not app_id.isdigit():
            logger.error(f"Invalid AppID: {app_id}")
            return None
            
        url_template = SteamDBFetcher.URL_TEMPLATES.get(key)
        if not url_template:
            logger.error(f"Invalid artwork type: {key}")
            return None
            
        url = url_template.format(app_id=app_id)
        logger.info(f"Fetching {key}: {url}")
        
        try:
            # Short timeout to keep UI snappy if threaded
            response = requests.get(url, headers=SteamDBFetcher.HEADERS, timeout=5)
            
            if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
                return response.content
            else:
                logger.warning(f"Failed to fetch {key} (Status: {response.status_code})")
                return None
        
        except requests.RequestException as e:
            logger.error(f"Error fetching {key}: {e}")
            return None

    @staticmethod
    def fetch_all_artwork(app_id: str) -> Dict[str, Optional[bytes]]:
        """
        Downloads all defined artwork types for the given AppID.
        Returns a dictionary {type_key: image_bytes or None}.
        """
        results = {}
        for key in SteamDBFetcher.URL_TEMPLATES.keys():
            results[key] = SteamDBFetcher.fetch_image(app_id, key)
        return results

    @staticmethod
    def get_game_name(app_id: str) -> str:
        """
        Fetches the game name from the Steam Store API.
        Returns "Unknown Game" if fetch fails.
        """
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        try:
            response = requests.get(url, headers=SteamDBFetcher.HEADERS, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and str(app_id) in data and data[str(app_id)]['success']:
                    return data[str(app_id)]['data']['name']
        except Exception as e:
            logger.error(f"Error fetching game name: {e}")
        
        return "Unknown Game"

    @staticmethod
    def search_games(query: str) -> list[dict]:
        """
        Searches for games by name using the Steam Store Search API.
        Returns a list of dicts: [{'id': 123, 'name': 'Game', 'img': 'url'}]
        """
        url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US"
        results = []
        try:
            response = requests.get(url, headers=SteamDBFetcher.HEADERS, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and 'items' in data:
                    for item in data['items']:
                        results.append({
                            'id': item['id'],
                            'name': item['name'],
                            'img': item.get('tiny_image', '')
                        })
        except Exception as e:
            logger.error(f"Error searching games: {e}")
        return results

    @staticmethod
    def save_image(img_data: bytes, file_path: str) -> bool:
        """
        Saves the image data to the specified location.
        """
        try:
            with open(file_path, "wb") as f:
                f.write(img_data)
            return True
        except OSError as e:
            logger.error(f"Error saving file to {file_path}: {e}")
            return False
