"""KOPYAHON - Imong mga kopya, dili mawala.

Run with:  python main.py
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Keep the source package importable when this file is started by double-clicking
# it or from a different working directory.  The package directory is named
# ``kopyahon`` in this distribution, so the import also works on
# case-sensitive filesystems.
PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def _setup_logging(folder) -> None:
    handler = RotatingFileHandler(folder / "kopyahon.log", maxBytes=512_000, backupCount=2,
                                  encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def main() -> int:
    try:
        import customtkinter as ctk  # noqa: F401
    except ImportError:
        print("KOPYAHON needs its dependencies. Run:  pip install -r requirements.txt")
        return 1

    from kopyahon import utils
    from kopyahon.app import KopyahonApp
    from kopyahon.database import Database
    from kopyahon.settings import Settings

    data_dir = utils.get_data_dir()
    _setup_logging(data_dir)
    utils.set_windows_app_id()

    db = Database(data_dir / "kopyahon.db")
    settings = Settings(db)
    ctk.set_appearance_mode(settings.get("theme"))
    app = KopyahonApp(db, settings)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
