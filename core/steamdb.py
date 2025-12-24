import requests
from typing import Optional, Dict, Tuple
import time

class SteamDBFetcher:
    """
    Handles fetching game artwork URLs and downloading images.
    """
    
    # URL Templates for various assets
    # These are standard Steam CDN paths.
    URL_TEMPLATES = {
        "header": "https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/header.jpg",
        "library_600x900_2x": "https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/library_600x900_2x.jpg",
        "library_hero_2x": "https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/library_hero_2x.jpg",
        "logo": "https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/logo.png",
        "capsule_231x87": "https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/capsule_231x87.jpg"
    }

    # Suggested filenames for saving to Steam Grid
    # Steam Custom Images usually expect specific naming for the vertical grid, 
    # but for "header" or "hero" in the new library, they use different naming or the user manually sets them.
    # However, common tools naming convention is often used.
    # We will use keys as internal identifiers.
    FILE_EXTENSIONS = {
        "header": ".jpg",
        "library_600x900_2x": ".jpg",
        "library_hero_2x": ".jpg",
        "logo": ".png",
        "capsule_231x87": ".jpg"
    }

    HEADERS = {
        "User-Agent": "SteamArtDownloader/1.0 (Educational/Personal Project)"
    }

    @staticmethod
    def fetch_all_artwork(app_id: str) -> Dict[str, Optional[bytes]]:
        """
        Downloads all defined artwork types for the given AppID.
        Returns a dictionary {type_key: image_bytes or None}.
        """
        results = {}
        
        if not app_id.isdigit():
            print(f"Invalid AppID: {app_id}")
            return results

        for key, url_template in SteamDBFetcher.URL_TEMPLATES.items():
            url = url_template.format(app_id=app_id)
            print(f"Fetching {key}: {url}")
            
            try:
                # Short timeout to keep UI snappy if threaded
                response = requests.get(url, headers=SteamDBFetcher.HEADERS, timeout=5)
                
                if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
                    results[key] = response.content
                else:
                    print(f"Failed to fetch {key} (Status: {response.status_code})")
                    results[key] = None
            
            except requests.RequestException as e:
                print(f"Error fetching {key}: {e}")
                results[key] = None
                
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
            print(f"Error fetching game name: {e}")
        
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
            print(f"Error searching games: {e}")
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
            print(f"Error saving file to {file_path}: {e}")
            return False
