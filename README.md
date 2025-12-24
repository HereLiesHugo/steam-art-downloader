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

1.  **Clone the repository** or download the source code.
2.  **Install Dependencies**: This application requires Python 3 and the following packages:

    ```bash
    pip install -r requirements.txt
    ```
    or (MacOS/Linux)

    ```bash
    pip3 install -r requirements.txt
    ```

    **Option 1:** Build the application from source
    1. Install PyInstaller
    ```bash
    pip install pyinstaller
    ```
    2. Build the application
    ```bash
    pyinstaller steam_art_downloader.spec
    ```
    3. Run the application

    **Option 2:** Just run the application (requires Python 3.11+)
    1. Run the application
    ```bash
    python main.py
    ```



## Installation (Windows only)

1. Download the precompiled version from [here](https://github.com/HereLiesHugo/steam-art-downloader/releases)
2. Extract the files to a directory of your choice
3. Run the application from the directory

## Usage

1.  **Run the Application**:

    ```bash
    python main.py
    ```
    or (windows only):
    download the precompiled version from [here](https://github.com/HereLiesHugo/steam-art-downloader/releases)

2.  **Download Artwork**:

    - **Single Game**: Enter a Game Name (e.g., "Portal 2") or AppID (e.g., "620") and click "Fetch & Install". if you search by name, a selection dialog will appear.
    - **Batch**: Enter multiple AppIDs separated by spaces (e.g., "620 400 220") to download artwork for all of them sequentially.

3.  **Settings**:
    - Navigate to the **Settings** tab to change the default download folder.
    - Click "Show Application Logs" to view the internal log history.

## Project Structure

- `main.py`: Application entry point.
- `core/`: Contains logic for SteamDB communication, settings management, and path handling.
- `ui/`: Contains the PySide6 user interface implementation (Main Window, Downloader Tab, Settings Tab).
- `downloader.log`: Automatically generated log file tracking application activity.

## License

[MIT License](LICENSE)
