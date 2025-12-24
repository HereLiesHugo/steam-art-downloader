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
    pip install pyside6 requests
    ```

## Usage

1.  **Run the Application**:

    ```bash
    python main.py
    ```

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

This project is for educational and personal use. All downloaded artwork is property of their respective owners and Valve Corporation.
