# Contributing to KOPYAHON

Salamat for helping! This guide is specific to this codebase.

## Principles

1. **Privacy first.** Clipboard data stays on the user's machine. Do not add network calls, telemetry or cloud sync.
2. **Transparent and user-controlled.** Monitoring state must stay visible (sidebar status) and pausable. Text copied while paused must never be stored (see `ClipboardMonitor.resume`).
3. **Never freeze the UI.** Clipboard polling runs on a background thread and talks to the UI only through the queue drained in `KopyahonApp._drain_events`. Never touch Tk widgets from the monitor thread.
4. **Preserve the user's text exactly.** Normalise newlines for *display* only (`utils.normalize_newlines`), never before saving.
5. **Every visible button must work.** No placeholder controls.

## Setup

```bash
python -m venv .venv && .venv\Scripts\activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
python -m unittest discover -s tests -t .
```

## Code layout and conventions

- One module per page in `kopyahon/ui/`; each page subclasses `Page` and implements `refresh()` (and `on_show()` if it takes arguments).
- Reusable widgets live in `ui/components.py`. Prefer `button()`, `label()`, `card()` over raw CustomTkinter calls so styling stays consistent.
- **Colours** are `(light, dark)` tuples in `theme.C`. Never hard-code hex values in UI modules; add a token instead. This is what makes live theme switching work.
- **Icons** are drawn in `icons.py` on a 24x24 grid. Add a drawer function and register it in `_DRAWERS`.
- **Cebuano text** (greetings, captions, toasts, empty states) lives in `strings.py`. Native-speaker corrections are very welcome.
- **Database access** goes through `database.py` only. Use parameterised SQL. Schema changes: bump `SCHEMA_VERSION` and add a migration step; never edit existing data destructively.
- Add new user settings to `DEFAULTS` in `settings.py` (with validation in `_coerce`) and a control in `ui/settings_page.py`.
- Keep `constants`, `strings`, `utils`, `database`, `settings` and `clipboard_monitor` free of CustomTkinter imports so they stay testable headlessly.
- Style: type hints, short docstrings, 100-column lines, no unused dependencies.

## Adding a page

1. Create `kopyahon/ui/<name>.py` with a `Page` subclass.
2. Register it in `KopyahonApp.pages` (`app.py`) and add a row to `NAV_ITEMS` in `ui/sidebar.py`.
3. Use `page_header()` and the shared margins (`theme.PAD`, `theme.GAP`) so layouts match.

## Testing

- Add unit tests in `tests/` for any change to `database.py`, `settings.py` or `clipboard_monitor.py`. Use `Database(":memory:")` and the fake clipboard in `tests/test_clipboard_monitor.py`.
- For UI changes, manually check: dark and light themes, resizing down to the minimum window size, empty states, and both with monitoring on and paused. Attach screenshots to your pull request.

## Pull requests

- Branch from `main`, keep PRs focused, and describe the user-visible change.
- Make sure the tests pass and the app launches.
- Mention any new strings so they can be reviewed for Cebuano wording.
