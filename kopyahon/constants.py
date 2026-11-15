"""Application-wide constants. Keep this module free of third-party imports."""

APP_NAME = "KOPYAHON"
APP_ID = "kopyahon.clipboard.manager"
TAGLINE = "Imong mga kopya, dili mawala."
VERSION = "1.0.0"
AUTHOR = "Joshua C. Arao"          # shown on the About page; change as needed
DESCRIPTION = (
    "A private, local clipboard history manager. KOPYAHON remembers the text "
    "you copy, lets you search it, favorite it and copy it back, and keeps "
    "your reusable snippets one click away."
)

POLL_INTERVAL = 0.4        # seconds between clipboard checks
MAX_CLIP_CHARS = 200_000   # clips longer than this are ignored
PAGE_SIZE = 40             # clips loaded per "page" in the history lists
RECENT_LIMIT = 15          # rows shown in the dashboard's recent activity
HISTORY_LIMITS = (50, 100, 250, 500, 1000, 2500, 5000)
