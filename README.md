# Steam Art Downloader

A desktop application to search for and download official Steam store artwork for any game. This tool is useful for collecting high-quality assets for game libraries, custom launchers, or archival purposes.

## Features

- **Search & Fetch**: Find games by Name or Steam AppID.
- **Batch Processing**: Download artwork for multiple games at once by entering space-separated AppIDs.
- **Comprehensive Assets**: Downloads Header, Library (Vertical), Hero, Logo, and Capsule images.
- **Configurable Paths**: Choose exactly where you want your downloads to be saved. Default is an 'art-downloads' folder in the application directory.
- **Logging**:
  - **Inline**: View real-time progress directly under the progress bar.
  - **GUI Window**: View detailed history in a dedicated "Show Application Logs" popup.
  - **File**: Logs are automatically saved to `downloader.log` for troubleshooting.
- **Granular Progress**: The progress bar updates for every individual file downloaded, ensuring accurate feedback during large batches.

## Installation

### Option 1: Precompiled (Windows Only)

The easiest way to use the application is to download the standalone executable.

1. Download the latest version from [GitHub Releases](https://github.com/HereLiesHugo/steam-art-downloader/releases).
2. Extract the files to a directory of your choice.
3. Run `SteamArtDownloader.exe`.

### Option 2: Running from Source

If you are on Linux/macOS or prefer to run the Python code directly:

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/HereLiesHugo/steam-art-downloader.git
    cd steam-art-downloader
    ```

2.  **Install Dependencies**:
    This application requires Python 3.11+.

    ```bash
    pip install -r requirements.txt
    ```

    _Note: On some systems, use `pip3` instead of `pip`._

3.  **Run the Application**:
    ```bash
    python main.py
    ```

### Option 3: Building the Executable

To create a standalone EXE yourself (e.g., for development):

1.  **Install PyInstaller**:

    ```bash
    pip install pyinstaller
    ```

2.  **Build**:

    ```bash
    pyinstaller steam_art_downloader.spec
    ```

3.  **Find Output**:
    The executable will be generated in the `dist/SteamArtDownloader` directory.

## Usage

1.  **Download Artwork**:

    - **Single Game**: Enter a Game Name (e.g., "Portal 2") or AppID (e.g., "620") and click "Fetch & Install". If you search by name, a selection dialog will appear.
    - **Batch**: Enter multiple AppIDs separated by spaces (e.g., "620 400 220") to download artwork for all of them sequentially.

2.  **Settings**:
    - NAVIGATE to the **Settings** tab to change the default download folder.
    - CLICK "Show Application Logs" to view the internal log history.

## Project Structure

- `main.py`: Application entry point.
- `core/`: Contains logic for SteamDB communication, settings management, and path handling.
- `ui/`: Contains the PySide6 user interface implementation (Main Window, Downloader Tab, Settings Tab).
- `downloader.log`: Automatically generated log file tracking application activity.

## License

[MIT License](LICENSE)
