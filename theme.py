"""ParkGuard AI — Design System / Theme Constants"""

# ── Background palette ────────────────────────────────────────────
BG_ROOT        = "#0D0D0D"   # deepest background
BG_SIDEBAR     = "#111111"   # sidebar
BG_CARD        = "#1A1A1A"   # cards, panels
BG_ROW         = "#1E1E1E"   # table rows
BG_ROW_ALT    = "#161616"   # alt rows / scrollable bg
BG_HEADER_ROW  = "#252525"   # column header rows

# ── Accent palette ────────────────────────────────────────────────
ACCENT         = "#F5A623"   # amber / gold  – primary accent
ACCENT_HOVER   = "#E0941A"
ACCENT_DARK    = "#3A2A00"   # muted amber for selected sidebar item

ACCENT2        = "#4C9BE8"   # sky blue  – secondary accent
ACCENT2_HOVER  = "#3A87D4"

# ── Semantic colors ───────────────────────────────────────────────
SUCCESS        = "#27AE60"
SUCCESS_HOVER  = "#219A52"
SUCCESS_MUTED  = "#1B3A28"

DANGER         = "#E74C3C"
DANGER_HOVER   = "#C0392B"
DANGER_MUTED   = "#3A1010"

WARNING        = "#F39C12"
WARNING_MUTED  = "#3A2A00"

PURPLE         = "#8E44AD"
PURPLE_MUTED   = "#2A1535"

# ── Text palette ──────────────────────────────────────────────────
TEXT_PRIMARY   = "#F0F0F0"
TEXT_SECONDARY = "#909090"
TEXT_MUTED     = "#555555"
TEXT_ACCENT    = ACCENT

# ── Borders & separators ──────────────────────────────────────────
BORDER         = "#2A2A2A"

# ── Corner radii ─────────────────────────────────────────────────
RADIUS_CARD    = 14
RADIUS_BTN     = 8
RADIUS_SMALL   = 6

# ── Sidebar navigation items ──────────────────────────────────────
NAV_ITEMS = [
    ("dashboard", "  Dashboard",    "📊"),
    ("camera",    "  Live Camera",  "📷"),
    ("clients",   "  Clients",      "👥"),
    ("payments",  "  Payments",     "💳"),
    ("logs",      "  Access Logs",  "📋"),
]
