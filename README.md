# KOPYAHON

**Imong mga kopya, dili mawala.** *(Your copies won't be lost.)*

KOPYAHON is a private, local clipboard history manager for the desktop with a Cebuano-inspired identity. It quietly remembers the text you copy, lets you search, favorite and re-copy it, and keeps your reusable text snippets one click away. The name comes from the Cebuano word *kopya* - "a copy".

Everything stays on your computer in a local SQLite file. Nothing is sent over a network.

## Screenshots

| | |
|---|---|
| ![Dashboard](docs/screenshots/01-DASHBOARD.png) | ![Clipboard History](docs/screenshots/02-HISTORY.png) |
| ![Favorites](docs/screenshots/03-FAVORITES.png) | ![Text Snippets](docs/screenshots/04-SNIPPETS.png) |
| ![Settings](docs/screenshots/05-SETTING.png) | ![About](docs/screenshots/06-ABOUT.png) |

## Features

- **Automatic recording** of copied text in a background thread, with line breaks and original text preserved exactly.
- **Never records unchanged content twice**; choose what happens to repeats (move to top, ignore, or keep every copy).
- **Search** (multi-word, case-insensitive, Unicode-aware) and **sort** (newest, oldest, longest, shortest, A-Z).
- **Preview pane** with full text, timestamp, character/word/line counts.
- **Copy, favorite, delete** any clip, plus **bulk selection and deletion**.
- **Favorites** are kept safe from the history limit.
- **Text snippets**: create, edit, delete and copy frequently used text.
- **Dashboard** with total / today / favorite counts, recent activity and quick actions.
- **Settings**: dark/light theme, pause monitoring, maximum history, duplicate preference, clear history, open data folder. All settings persist.
- **Transparent and user-controlled**: monitoring status is always visible in the sidebar, can be paused in one click, and anything copied while paused is never saved.
- Confirmation dialogs for destructive actions, toast notifications, and error handling that never freezes the UI.

## Installation

Requires Python 3.9+ with Tk (included in the standard Windows and macOS installers; on Debian/Ubuntu install `python3-tk`; Linux clipboard access also needs `xclip` or `xsel`).

```bash
git clone <your-repo-url> kopyahon
cd kopyahon
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python main.py
```

## Usage

1. Launch with `python main.py`. Monitoring starts automatically.
2. Copy text anywhere (Ctrl+C). It appears in **History**.
3. Click a clip to preview it; use the icons to favorite, copy back or delete it. Tick the checkboxes for bulk deletion.
4. Use **Pause monitoring** in the sidebar before copying passwords or other secrets.
5. Save reusable text under **Snippets**.

Data lives in `%APPDATA%\KOPYAHON` on Windows, `~/Library/Application Support/KOPYAHON` on macOS and `~/.local/share/kopyahon` on Linux (override with the `KOPYAHON_DATA_DIR` environment variable). **Settings → Open folder** takes you there.

## Technology stack

Python 3 · CustomTkinter · SQLite (`sqlite3`) · Pillow · Pyperclip · `threading` for background clipboard monitoring.

## Project structure

```
main.py                     entry point
kopyahon/
  app.py                    main window; wires monitor, database and pages
  clipboard_monitor.py      background clipboard watcher (thread)
  database.py               SQLite: clips, snippets, settings
  settings.py               typed, persistent settings
  theme.py  icons.py        design tokens, Pillow-drawn icons
  assets.py                 logo + Windows icon generator
  strings.py  constants.py  Cebuano phrases, app constants
  utils.py                  paths, time and text helpers
  ui/                       sidebar, components, and one module per page
assets/                     logo.png, icon.ico
tests/                      unit tests (database, monitor)
```

## Running the tests

```bash
python -m unittest discover -s tests -t .
```

The tests cover the database and the clipboard monitor (using a fake clipboard) and need no GUI.

## Packaging (optional)

```bash
pip install pyinstaller
pyinstaller --noconsole --name KOPYAHON --icon assets/icon.ico --add-data "assets;assets" --collect-data customtkinter main.py
```
(On macOS/Linux use `:` instead of `;` in `--add-data`.)

## Credits

Developed by Joshua C. Arao (change in `kopyahon/constants.py`). Logo and icons are original artwork generated with Pillow.
