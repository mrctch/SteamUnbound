# SteamUnbound

**SteamUnbound** is a dedicated, single-window desktop application built with Python and Tkinter designed to automate the process of retrieving, downloading, unpacking, and localizing Steam games using manifest data. The application unifies store lookup, depot fetching via external downloaders, binary DRM unpacking, and offline emulator configuration under a clean, dark-themed interface.

---

## Architecture and Core Functionality

SteamUnbound operates as a GUI wrapper and orchestration engine for multiple backend tools. Below is an in-depth explanation of how each core system within the app functions:

### 1. Graphical User Interface (GUI) & Styling
- **Single-Tab Layout (`Download`):** Consolidates search inputs, interactive suggestions, metadata displays, terminal execution logs, and continuous progress tracking into a single view.
- **Settings Module:** Centralizes user configuration, including API authentication keys, default player aliases (`SteamUnbound`), and custom profile avatar selection.
- **Custom Dark Theme:** Uses customized `ttk` and `tkinter` widgets configured with deep black (`#0a0710`) and dark violet (`#4a154b`) accents.

### 2. Live Store Search & Metadata Parsing
- **Asynchronous Queries:** Uses Python's `threading` and `urllib.request` modules to query the official Steam Store Search API without freezing the main application UI thread.
- **Debounced Input Handler:** Implements a keystroke delay mechanism (`root.after`) to prevent unnecessary network requests while typing in the search bar.
- **Metadata Retrieval:** Fetches detailed app metadata (developer names, release dates, short descriptions) via the `appdetails` endpoint upon title selection.

### 3. Manifest & Depot Retrieval Pipeline
- **API Connection:** Sends authenticated HTTP requests to the manifest API (`https://hubcapmanifest.com/api/v1`) using the user's configured API Key to request depot keys and manifest data for a target AppID.
- **ZIP Payload Extraction:** Downloads and extracts temporary LUA configuration files and `.manifest` data binaries into a localized `temp_depot_data` directory.
- **Key & Depot Scanning:** Scans retrieved LUA scripts via Regular Expressions (`re`) to pair Depot IDs with their respective decryption keys. Generates a temporary `keys.txt` file formatted specifically for `DepotDownloaderMod.exe`.

### 4. Continuous Multi-Depot Downloading
- **Depot Downloader Execution:** Spawns `DepotDownloaderMod.exe` using Python's `subprocess.Popen` in hidden execution mode (`CREATE_NO_WINDOW`).
- **Unified Progress Bar:** Calculates total required manifests (including base game depots and extra DLCs) and scales progress deterministically from 25% to 65%. The progress bar advances continuously across multiple manifest downloads without resetting to zero.
- **Real-Time Terminal Output Logging:** Intercepts `stdout` lines from the active process and streams download progress and percentage updates directly to an interactive `tk.Text` terminal log widget.

### 5. Executable DRM Unpacking (Steamless)
- **Automatic Directory Traversal:** Scans the destination directory recursively (`os.walk`) for executable files (`.exe`).
- **Steamless CLI Integration:** Passes encrypted binaries to `Steamless.CLI.exe` to strip default Steam DRM wrappers.
- **Binary Replacement:** Detects produced `.unpacked.exe` binaries, deletes original encrypted executables, and renames unpacked binaries back to their target names seamlessly.

### 6. Goldberg Emulator Injection & Personalization
- **Architecture Detection:** Inspects downloaded files for 32-bit (`steam_api.dll`) or 64-bit (`steam_api64.dll`) libraries to copy the appropriate Goldberg emulator binaries from local asset storage (`assets/bge_32` or `assets/bge_64`).
- **Configuration Provisioning:** Automatically creates a `steam_settings` directory containing:
  - `steam_appid.txt`: Target AppID identifier.
  - `force_account_name.txt`: Configured player nickname (defaults to `SteamUnbound`).
  - `offline.txt`: Disables forced network connections.
- **Avatar Processing:** Reads user-selected avatar images, resizes them automatically to 184x184 pixels using `Pillow (PIL)`, and writes a formatted `avatar.png` directly into `steam_settings`.

### 7. Desktop Shortcut Generation
- **Executable Heuristics:** Scans the installation directory to identify the primary executable while filtering out auxiliary launchers, uninstallers, unity helpers, or redistributables.
- **VBScript Execution:** Generates and runs a temporary Windows Visual Basic Script (`create_shortcut.vbs`) using `cscript` under `CREATE_NO_WINDOW` flags to place a `.lnk` shortcut on the user's Desktop.

---

## Application Directory Structure

To compile or run the application from source code, maintain the following directory layout:

```text
SteamUnbound/
├── app.py
├── config.json                 (Generated automatically upon saving settings)
├── assets/
│   ├── icon.ico
│   ├── bge_32/
│   │   └── steam_api.dll
│   └── bge_64/
│       └── steam_api64.dll
├── DepotDownloaderMod/
│   └── DepotDownloaderMod.exe
└── Steamless/
    └── Steamless.CLI.exe
```

---

## Compilation Guide

The application is engineered to run as a single, standalone executable without triggering external command prompt windows or secondary terminal flashes.

### Dependencies
Install the required Python packages before compilation:

```bash
pip install requests pillow pyinstaller
```

### PyInstaller Command
Run the following build command from the root folder of your project:

```bash
pyinstaller --onefile --windowed --name SteamUnbound --icon=assets/icon.ico --add-data "assets;assets" --add-data "DepotDownloaderMod;DepotDownloaderMod" --add-data "Steamless;Steamless" app.py
```

### Flags Breakdown
- `--onefile`: Bundles all Python code, packages, and binaries into a single `.exe`.
- `--windowed`: Suppresses the default Windows console window on startup.
- `--add-data`: Packs required binaries, emulator libraries, and asset subfolders into the compiled binary.

---

## Acknowledgments & Third-Party Credits

SteamUnbound integrates and relies upon several open-source utility tools to complete its automation pipeline. All credit goes to their respective maintainers:

- **[DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod):** For multi-threaded Steam depot downloading, language filtering, and manifest decryption handling.
- **[Steamless](https://github.com/atom0s/Steamless):** Created by *atom0s*, for providing the command-line tool (`Steamless.CLI`) used to unpack Steam DRM wrappers from Windows executables.
- **[Goldberg Steam Emulator](https://github.com/Zachareee/goldberg_emu):** For providing offline replacement libraries (`steam_api.dll` / `steam_api64.dll`) and settings configuration structures.

---

*SteamUnbound is an open-source project intended for automated local game management and offline environment setup.*
