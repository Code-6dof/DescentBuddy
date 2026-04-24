"""Qt stylesheet themes for DescentBuddy.

Each theme is a flat dict of color tokens. The stylesheet template uses
str.format_map() so {{...}} produces literal CSS braces and {TOKEN} is
replaced with the theme value.
"""

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------

THEMES: dict[str, dict[str, str]] = {
    "descent": {
        # Descent — near-black with warm orange/red accents (default)
        "BG_DARK":                "#0d0d0d",
        "BG_PANEL":               "#141414",
        "BG_SIDEBAR":             "#0a0a0a",
        "HEADER_BG":              "#080808",
        "BG_INPUT":               "#1a1a1a",
        "BG_ELEVATED":            "#1e1e1e",
        "BG_ELEVATED_HOVER":      "#2a2a2a",
        "BG_ELEVATED_PRESSED":    "#3a1800",
        "BG_ITEM_HOVER":          "#1e1e1e",
        "BG_ITEM_SELECTED":       "#2a1000",
        "BG_LOG":                 "#080808",
        "BG_ROW_HOVER":           "#191919",
        "BG_MISSION_ROW":         "#181818",
        "BG_MISSION_ROW_HOVER":   "#1e1a14",
        "BG_IMAGE":               "#0c0c0c",
        "BG_SPINBOX_BTN":         "#222222",
        "BG_SPINBOX_BTN_HOVER":   "#2e2e2e",
        "ACCENT_ORANGE":          "#e85c00",
        "ACCENT_RED":             "#cc1a00",
        "ACCENT_ORANGE_LIGHT":    "#ff7a1a",
        "TEXT_PRIMARY":           "#e8e0d0",
        "TEXT_SECONDARY":         "#7a7060",
        "TEXT_DIM":               "#3a3530",
        "TEXT_ON_PRIMARY":        "#ffffff",
        "BORDER_COLOR":           "#1f1f1f",
        "BORDER_ACCENT":          "#3a1800",
        "STATUS_GREEN":           "#3ccc3c",
        "BTN_LAUNCH_PRESSED":     "#8b1000",
        "BTN_LAUNCH_DISABLED_BG": "#3a2020",
        "BTN_LAUNCH_DISABLED_FG": "#5a4040",
    },
    "light": {
        # Light — bright surfaces, dark text, muted copper accents
        "BG_DARK":                "#efefef",
        "BG_PANEL":               "#ffffff",
        "BG_SIDEBAR":             "#e4e4e4",
        "HEADER_BG":              "#d8d8d8",
        "BG_INPUT":               "#f8f8f8",
        "BG_ELEVATED":            "#eaeaea",
        "BG_ELEVATED_HOVER":      "#d8d8d8",
        "BG_ELEVATED_PRESSED":    "#ffd8a0",
        "BG_ITEM_HOVER":          "#e8e8e8",
        "BG_ITEM_SELECTED":       "#ffe0c0",
        "BG_LOG":                 "#f5f5f5",
        "BG_ROW_HOVER":           "#eeeeee",
        "BG_MISSION_ROW":         "#f8f8f8",
        "BG_MISSION_ROW_HOVER":   "#fff4e8",
        "BG_IMAGE":               "#e0e0e0",
        "BG_SPINBOX_BTN":         "#d8d8d8",
        "BG_SPINBOX_BTN_HOVER":   "#c8c8c8",
        "ACCENT_ORANGE":          "#c84800",
        "ACCENT_RED":             "#aa1100",
        "ACCENT_ORANGE_LIGHT":    "#e06820",
        "TEXT_PRIMARY":           "#1a1a1a",
        "TEXT_SECONDARY":         "#606060",
        "TEXT_DIM":               "#aaaaaa",
        "TEXT_ON_PRIMARY":        "#ffffff",
        "BORDER_COLOR":           "#cccccc",
        "BORDER_ACCENT":          "#e09060",
        "STATUS_GREEN":           "#1e8820",
        "BTN_LAUNCH_PRESSED":     "#880000",
        "BTN_LAUNCH_DISABLED_BG": "#e8d8d8",
        "BTN_LAUNCH_DISABLED_FG": "#aaaaaa",
    },
    "mocha": {
        # Mocha — warm dark coffee tones, amber accents, cream text
        "BG_DARK":                "#18100a",
        "BG_PANEL":               "#20160c",
        "BG_SIDEBAR":             "#130d08",
        "HEADER_BG":              "#100a04",
        "BG_INPUT":               "#281a10",
        "BG_ELEVATED":            "#2c1e14",
        "BG_ELEVATED_HOVER":      "#382818",
        "BG_ELEVATED_PRESSED":    "#503018",
        "BG_ITEM_HOVER":          "#2c1e14",
        "BG_ITEM_SELECTED":       "#482a08",
        "BG_LOG":                 "#0e0a06",
        "BG_ROW_HOVER":           "#261810",
        "BG_MISSION_ROW":         "#221608",
        "BG_MISSION_ROW_HOVER":   "#301e0e",
        "BG_IMAGE":               "#140e06",
        "BG_SPINBOX_BTN":         "#322010",
        "BG_SPINBOX_BTN_HOVER":   "#402818",
        "ACCENT_ORANGE":          "#d48828",
        "ACCENT_RED":             "#b04010",
        "ACCENT_ORANGE_LIGHT":    "#f0aa44",
        "TEXT_PRIMARY":           "#f0e4cc",
        "TEXT_SECONDARY":         "#987860",
        "TEXT_DIM":               "#584030",
        "TEXT_ON_PRIMARY":        "#ffffff",
        "BORDER_COLOR":           "#382010",
        "BORDER_ACCENT":          "#5a3820",
        "STATUS_GREEN":           "#78b840",
        "BTN_LAUNCH_PRESSED":     "#882800",
        "BTN_LAUNCH_DISABLED_BG": "#38281c",
        "BTN_LAUNCH_DISABLED_FG": "#785840",
    },
    "nightflight": {
        # Nightflight — deep navy, cyan/teal accents, pale cool text
        "BG_DARK":                "#070b18",
        "BG_PANEL":               "#0b1020",
        "BG_SIDEBAR":             "#050812",
        "HEADER_BG":              "#040710",
        "BG_INPUT":               "#0e1628",
        "BG_ELEVATED":            "#121c30",
        "BG_ELEVATED_HOVER":      "#1c2a40",
        "BG_ELEVATED_PRESSED":    "#0e2244",
        "BG_ITEM_HOVER":          "#121c30",
        "BG_ITEM_SELECTED":       "#0c1e40",
        "BG_LOG":                 "#030610",
        "BG_ROW_HOVER":           "#0e1828",
        "BG_MISSION_ROW":         "#0c1622",
        "BG_MISSION_ROW_HOVER":   "#12203a",
        "BG_IMAGE":               "#070a18",
        "BG_SPINBOX_BTN":         "#161e30",
        "BG_SPINBOX_BTN_HOVER":   "#1e2a40",
        "ACCENT_ORANGE":          "#00c8e0",
        "ACCENT_RED":             "#0068c8",
        "ACCENT_ORANGE_LIGHT":    "#44e0f8",
        "TEXT_PRIMARY":           "#c0daf0",
        "TEXT_SECONDARY":         "#5070a0",
        "TEXT_DIM":               "#283850",
        "TEXT_ON_PRIMARY":        "#ffffff",
        "BORDER_COLOR":           "#162030",
        "BORDER_ACCENT":          "#183a68",
        "STATUS_GREEN":           "#00d878",
        "BTN_LAUNCH_PRESSED":     "#004498",
        "BTN_LAUNCH_DISABLED_BG": "#162030",
        "BTN_LAUNCH_DISABLED_FG": "#365070",
    },
    "reactor": {
        # Reactor Core — dark terminal green, like an old phosphor CRT
        "BG_DARK":                "#040d04",
        "BG_PANEL":               "#071007",
        "BG_SIDEBAR":             "#030903",
        "HEADER_BG":              "#020702",
        "BG_INPUT":               "#091509",
        "BG_ELEVATED":            "#0d1b0d",
        "BG_ELEVATED_HOVER":      "#162616",
        "BG_ELEVATED_PRESSED":    "#183810",
        "BG_ITEM_HOVER":          "#0d1b0d",
        "BG_ITEM_SELECTED":       "#0c3008",
        "BG_LOG":                 "#020702",
        "BG_ROW_HOVER":           "#0b180b",
        "BG_MISSION_ROW":         "#091509",
        "BG_MISSION_ROW_HOVER":   "#0f1e0f",
        "BG_IMAGE":               "#040b04",
        "BG_SPINBOX_BTN":         "#122012",
        "BG_SPINBOX_BTN_HOVER":   "#1a2c1a",
        "ACCENT_ORANGE":          "#00cc44",
        "ACCENT_RED":             "#00881a",
        "ACCENT_ORANGE_LIGHT":    "#44ff80",
        "TEXT_PRIMARY":           "#9ae870",
        "TEXT_SECONDARY":         "#487a38",
        "TEXT_DIM":               "#1e4018",
        "TEXT_ON_PRIMARY":        "#001a00",
        "BORDER_COLOR":           "#0a2008",
        "BORDER_ACCENT":          "#145c10",
        "STATUS_GREEN":           "#00ff60",
        "BTN_LAUNCH_PRESSED":     "#005c10",
        "BTN_LAUNCH_DISABLED_BG": "#0c2808",
        "BTN_LAUNCH_DISABLED_FG": "#285a20",
    },
    "void": {
        # Void — absolute black, electric violet accents, soft lavender text
        "BG_DARK":                "#03000c",
        "BG_PANEL":               "#070010",
        "BG_SIDEBAR":             "#020008",
        "HEADER_BG":              "#010006",
        "BG_INPUT":               "#0e0020",
        "BG_ELEVATED":            "#130028",
        "BG_ELEVATED_HOVER":      "#1c0038",
        "BG_ELEVATED_PRESSED":    "#280050",
        "BG_ITEM_HOVER":          "#130028",
        "BG_ITEM_SELECTED":       "#1e0044",
        "BG_LOG":                 "#020006",
        "BG_ROW_HOVER":           "#10001e",
        "BG_MISSION_ROW":         "#0c001a",
        "BG_MISSION_ROW_HOVER":   "#180030",
        "BG_IMAGE":               "#050010",
        "BG_SPINBOX_BTN":         "#1a002e",
        "BG_SPINBOX_BTN_HOVER":   "#240040",
        "ACCENT_ORANGE":          "#9040f0",
        "ACCENT_RED":             "#6010c8",
        "ACCENT_ORANGE_LIGHT":    "#c080ff",
        "TEXT_PRIMARY":           "#d0b8ff",
        "TEXT_SECONDARY":         "#6848a8",
        "TEXT_DIM":               "#38186a",
        "TEXT_ON_PRIMARY":        "#ffffff",
        "BORDER_COLOR":           "#1c0040",
        "BORDER_ACCENT":          "#4410a8",
        "STATUS_GREEN":           "#40f0a8",
        "BTN_LAUNCH_PRESSED":     "#3c0090",
        "BTN_LAUNCH_DISABLED_BG": "#1c003c",
        "BTN_LAUNCH_DISABLED_FG": "#4c28a0",
    },
}

THEME_LABELS: dict[str, str] = {
    "descent":    "Original",
    "light":      "Light",
    "mocha":      "Mocha",
    "nightflight": "Midnight",
    "reactor":    "Dark Green",
    "void":       "Dark Purple",
}

_active_theme: str = "descent"

# ---------------------------------------------------------------------------
# Stylesheet template
# CSS braces are escaped as {{ }} so format_map can substitute {TOKEN} values.
# ---------------------------------------------------------------------------

_STYLESHEET_TEMPLATE = """
/* ── Global ─────────────────────────────────────────── */
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "DejaVu Sans", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {BG_DARK};
}}

/* ── Header ─────────────────────────────────────────── */
QWidget#app-header {{
    background-color: {HEADER_BG};
    border-bottom: 1px solid {BORDER_COLOR};
}}

QLabel#header-logo-main {{
    font-size: 17px;
    font-weight: bold;
    color: {TEXT_PRIMARY};
    letter-spacing: 2px;
    background: transparent;
}}

QLabel#header-logo-accent {{
    font-size: 17px;
    font-weight: bold;
    color: {ACCENT_ORANGE};
    letter-spacing: 2px;
    background: transparent;
}}

QLabel#header-tagline {{
    font-size: 11px;
    color: {TEXT_SECONDARY};
    letter-spacing: 1px;
    background: transparent;
}}

QPushButton#account-btn {{
    background: transparent;
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    color: {TEXT_SECONDARY};
    font-size: 11px;
    letter-spacing: 1px;
    padding: 4px 10px;
    min-height: 26px;
}}

QPushButton#account-btn:hover {{
    border-color: {ACCENT_ORANGE};
    color: {TEXT_PRIMARY};
}}

QPushButton#account-btn::menu-indicator {{
    image: none;
    width: 0px;
}}

QPushButton#inbox-btn {{
    background: transparent;
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    color: {TEXT_SECONDARY};
    font-size: 11px;
    letter-spacing: 1px;
    padding: 4px 10px;
    min-height: 26px;
}}

QPushButton#inbox-btn:hover {{
    border-color: {ACCENT_ORANGE};
    color: {TEXT_PRIMARY};
}}

QPushButton#inbox-btn-unread {{
    background: transparent;
    border: 1px solid {ACCENT_ORANGE};
    border-radius: 4px;
    color: {ACCENT_ORANGE_LIGHT};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 4px 10px;
    min-height: 26px;
}}

QPushButton#inbox-btn-unread:hover {{
    color: {TEXT_PRIMARY};
}}

QFrame#notification-popup {{
    background-color: {BG_SIDEBAR};
    border: 1px solid {BORDER_COLOR};
}}

QWidget#notification-popup-header {{
    background-color: {BG_ELEVATED};
}}

QWidget#notif-row-unread {{
    background-color: {BG_ELEVATED};
    border-left: 3px solid {ACCENT_ORANGE};
}}

QWidget#notif-row {{
    background: transparent;
}}

QLabel#notif-title {{
    font-weight: bold;
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QLabel#notif-age {{
    color: {TEXT_DIM};
    font-size: 11px;
    background: transparent;
}}

QLabel#notif-message {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
    background: transparent;
}}

QMenu {{
    background-color: {BG_SIDEBAR};
    border: 1px solid {BORDER_COLOR};
    color: {TEXT_PRIMARY};
    padding: 4px 0px;
}}

QMenu::item {{
    padding: 6px 20px;
    background: transparent;
}}

QMenu::item:selected {{
    background-color: {BG_ITEM_SELECTED};
    color: {ACCENT_ORANGE_LIGHT};
}}

QMenu::separator {{
    background-color: {BORDER_COLOR};
    height: 1px;
    margin: 2px 8px;
}}

/* ── Sidebar ─────────────────────────────────────────── */
QListWidget#sidebar {{
    background-color: {BG_SIDEBAR};
    border: none;
    border-right: 1px solid {BORDER_COLOR};
    outline: none;
    padding: 6px 0px;
}}

QListWidget#sidebar::item {{
    padding: 12px 20px;
    border-left: 3px solid transparent;
    color: {TEXT_SECONDARY};
    font-size: 13px;
    letter-spacing: 0.5px;
}}

QListWidget#sidebar::item:hover {{
    background-color: {BG_ITEM_HOVER};
    color: {TEXT_PRIMARY};
    border-left: 3px solid {ACCENT_ORANGE};
}}

QListWidget#sidebar::item:selected {{
    background-color: {BG_ITEM_SELECTED};
    color: {ACCENT_ORANGE_LIGHT};
    border-left: 3px solid {ACCENT_ORANGE};
    font-weight: bold;
}}

/* ── Panels ─────────────────────────────────────────── */
QWidget#panel {{
    background-color: {BG_PANEL};
}}

QLabel#panel-title {{
    font-size: 22px;
    font-weight: bold;
    color: {ACCENT_ORANGE};
    letter-spacing: 2px;
    padding-bottom: 4px;
    background: transparent;
}}

QLabel {{
    background: transparent;
}}

QLabel#section-label {{
    color: {TEXT_SECONDARY};
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

QLabel#version-label {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
    padding: 4px 0px;
}}

QLabel#status-label {{
    font-size: 12px;
    color: {TEXT_SECONDARY};
}}

QLabel#status-running {{
    font-size: 12px;
    color: {STATUS_GREEN};
}}

QLabel#status-error {{
    font-size: 12px;
    color: {ACCENT_RED};
}}

/* ── Inputs ─────────────────────────────────────────── */
QLineEdit {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 6px 10px;
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_ORANGE};
}}

QLineEdit:focus {{
    border: 1px solid {ACCENT_ORANGE};
}}

/* ── Combo boxes ─────────────────────────────────────── */
QComboBox {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    color: {TEXT_PRIMARY};
    min-height: 26px;
    padding: 4px 8px;
}}

QComboBox:hover {{
    border-color: {ACCENT_ORANGE};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_SIDEBAR};
    border: 1px solid {BORDER_COLOR};
    color: {TEXT_PRIMARY};
    selection-background-color: {BG_ITEM_SELECTED};
    selection-color: {ACCENT_ORANGE_LIGHT};
    outline: none;
}}

QComboBox#theme-combo {{
    background-color: transparent;
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    color: {TEXT_SECONDARY};
    font-size: 11px;
    letter-spacing: 1px;
    min-height: 24px;
    padding: 2px 6px;
}}

QComboBox#theme-combo:hover {{
    border-color: {ACCENT_ORANGE};
    color: {TEXT_PRIMARY};
}}

/* ── Buttons ─────────────────────────────────────────── */
QPushButton {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    color: {TEXT_PRIMARY};
    min-height: 26px;
    padding: 6px 16px;
}}

QPushButton:hover {{
    background-color: {BG_ELEVATED_HOVER};
    border: 1px solid {ACCENT_ORANGE};
    color: {ACCENT_ORANGE_LIGHT};
}}

QPushButton:pressed {{
    background-color: {BG_ELEVATED_PRESSED};
}}

QPushButton:disabled {{
    color: {TEXT_DIM};
    border-color: {TEXT_DIM};
}}

QPushButton#launch-btn {{
    background-color: {ACCENT_RED};
    border: none;
    border-radius: 6px;
    color: {TEXT_ON_PRIMARY};
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 3px;
    padding: 10px 16px;
}}

QPushButton#launch-btn:hover {{
    background-color: {ACCENT_ORANGE};
}}

QPushButton#launch-btn:pressed {{
    background-color: {BTN_LAUNCH_PRESSED};
}}

QPushButton#launch-btn:disabled {{
    background-color: {BTN_LAUNCH_DISABLED_BG};
    color: {BTN_LAUNCH_DISABLED_FG};
}}

/* ── Separators ─────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {BORDER_COLOR};
}}

/* ── Scrollbars ─────────────────────────────────────── */
QScrollBar:vertical {{
    background: {BG_DARK};
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BG_ELEVATED_HOVER};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ── Tooltip ─────────────────────────────────────────── */
QToolTip {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {ACCENT_ORANGE};
    padding: 4px 8px;
    border-radius: 3px;
}}

/* ── Checkboxes ──────────────────────────────────────── */
QCheckBox {{
    spacing: 0px;
    color: {TEXT_PRIMARY};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {BORDER_COLOR};
    border-radius: 3px;
    background-color: {BG_INPUT};
}}

QCheckBox::indicator:hover {{
    border-color: {ACCENT_ORANGE};
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_RED};
    border-color: {ACCENT_RED};
}}

QCheckBox::indicator:checked:hover {{
    background-color: {ACCENT_ORANGE};
    border-color: {ACCENT_ORANGE};
}}

QCheckBox::indicator:disabled {{
    background-color: {BG_DARK};
    border-color: {BG_INPUT};
}}

/* ── Spinboxes ───────────────────────────────────────── */
QSpinBox {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px 6px;
    color: {TEXT_PRIMARY};
}}

QSpinBox:focus {{
    border-color: {ACCENT_ORANGE};
}}

QSpinBox:disabled {{
    color: {TEXT_DIM};
    border-color: {BORDER_COLOR};
    background-color: {BG_DARK};
}}

QSpinBox::up-button,
QSpinBox::down-button {{
    width: 18px;
    background-color: {BG_SPINBOX_BTN};
    border: none;
}}

QSpinBox::up-button:hover,
QSpinBox::down-button:hover {{
    background-color: {BG_SPINBOX_BTN_HOVER};
}}

/* ── Scroll areas ────────────────────────────────────── */
QScrollArea {{
    background: transparent;
    border: none;
}}

/* ── Settings panel ──────────────────────────────────── */
QWidget#settings-content {{
    background: transparent;
}}

QWidget#settings-row {{
    background: transparent;
    border-radius: 3px;
}}

QWidget#settings-row:hover {{
    background: {BG_ROW_HOVER};
}}

QLabel#settings-adv-label {{
    color: {ACCENT_ORANGE};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
}}

QPushButton#settings-collapse-btn {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER_ACCENT};
    border-radius: 4px;
    color: {ACCENT_ORANGE};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
    padding: 6px 12px;
    text-align: left;
}}

QPushButton#settings-collapse-btn:hover {{
    background-color: {BG_ELEVATED_PRESSED};
    border-color: {ACCENT_ORANGE};
}}

QPushButton#settings-collapse-btn:checked {{
    background-color: {BG_ELEVATED_PRESSED};
    border-color: {ACCENT_ORANGE};
}}

/* ── Missions panel ──────────────────────────────────── */
QWidget#mission-tab-bar {{
    background-color: {BG_PANEL};
}}

QPushButton#mission-tab {{
    background-color: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0px;
    color: {TEXT_SECONDARY};
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 0px 12px;
}}

QPushButton#mission-tab:hover {{
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {BORDER_ACCENT};
}}

QPushButton#mission-tab-active {{
    background-color: transparent;
    border: none;
    border-bottom: 2px solid {ACCENT_ORANGE};
    border-radius: 0px;
    color: {ACCENT_ORANGE_LIGHT};
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 0px 12px;
}}

QWidget#mission-row {{
    background-color: {BG_MISSION_ROW};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
}}

QWidget#mission-row:hover {{
    background-color: {BG_MISSION_ROW_HOVER};
    border-color: {BORDER_ACCENT};
}}

QLabel#mission-name {{
    font-size: 13px;
    font-weight: bold;
    color: {TEXT_PRIMARY};
}}

QLabel#mission-location {{
    font-size: 11px;
    color: {TEXT_SECONDARY};
}}

QLabel#mission-tag {{
    background-color: {BG_ELEVATED_PRESSED};
    border: 1px solid {BORDER_ACCENT};
    border-radius: 3px;
    color: {ACCENT_ORANGE};
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.5px;
    padding: 1px 5px;
}}

/* ── Log panels ──────────────────────────────────────── */
QTextEdit#gamelog-content {{
    background-color: {BG_LOG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_ORANGE};
}}

QPushButton#link-btn {{
    background-color: transparent;
    border: none;
    color: {TEXT_SECONDARY};
    font-size: 11px;
    padding: 0px;
    text-align: left;
}}

QPushButton#link-btn:hover {{
    color: {ACCENT_ORANGE_LIGHT};
}}

QPushButton#select-btn {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    color: {TEXT_SECONDARY};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    min-height: 26px;
    padding: 4px 10px;
}}

QPushButton#select-btn:hover {{
    border-color: {ACCENT_ORANGE};
    color: {TEXT_PRIMARY};
}}

QPushButton#select-btn:checked {{
    background-color: {BG_ITEM_SELECTED};
    border: 1px solid {ACCENT_ORANGE};
    color: {ACCENT_ORANGE_LIGHT};
}}

QPushButton#filter-btn {{
    background-color: transparent;
    border: 1px solid {BORDER_COLOR};
    border-radius: 3px;
    color: {TEXT_SECONDARY};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 4px 8px;
}}

QPushButton#filter-btn:hover {{
    color: {TEXT_PRIMARY};
    border-color: {ACCENT_ORANGE};
}}

QPushButton#filter-btn-active {{
    background-color: {BG_ITEM_SELECTED};
    border: 1px solid {ACCENT_ORANGE};
    border-radius: 3px;
    color: {ACCENT_ORANGE_LIGHT};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 4px 8px;
}}

/* ── Mission detail image ───────────────────────────────────── */
QLabel#mission-image {{
    background-color: {BG_IMAGE};
    border: 1px solid {BORDER_COLOR};
    color: {TEXT_SECONDARY};
    font-size: 11px;
}}

/* ── Mission table ───────────────────────────────────── */
QTableWidget#mission-table {{
    background-color: {BG_PANEL};
    border: none;
    gridline-color: transparent;
    outline: none;
}}

QTableWidget#mission-table::item {{
    padding: 0px 6px;
    border-bottom: 1px solid {BG_ROW_HOVER};
}}

QTableWidget#mission-table::item:selected {{
    background-color: {BG_ITEM_SELECTED};
    color: {TEXT_PRIMARY};
}}

QHeaderView::section {{
    background-color: {BG_SIDEBAR};
    color: {TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 4px 6px;
    font-size: 11px;
    letter-spacing: 1px;
}}

/* ── Browser toolbar panels ──────────────────────────── */
QWidget#browser-divider {{
    background-color: {BORDER_COLOR};
}}

QWidget#browser-toolbar {{
    background-color: {BG_SIDEBAR};
    border: none;
}}

QLabel#browser-url {{
    color: {TEXT_DIM};
    font-size: 11px;
    letter-spacing: 1px;
    background: transparent;
}}

/* ── Launch panel ────────────────────────────────────── */
QLabel#filename-main {{
    font-size: 14px;
    font-weight: bold;
    color: {TEXT_PRIMARY};
    background: transparent;
}}

/* ── Community panel ─────────────────────────────────── */
QLabel#login-error {{
    color: {ACCENT_RED};
    font-size: 12px;
    background: transparent;
}}

QLabel#community-username {{
    font-size: 15px;
    font-weight: bold;
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QLabel#fetch-status {{
    color: {TEXT_DIM};
    font-size: 11px;
    background: transparent;
}}

/* ── Settings panel ──────────────────────────────────── */
QLabel#exe-path-display {{
    font-size: 12px;
    color: {TEXT_SECONDARY};
    background: transparent;
}}

/* ── Demos panel ─────────────────────────────────────── */
QWidget#demo-rename-row {{
    background: transparent;
}}

QLabel#source-label {{
    font-size: 13px;
    color: {TEXT_PRIMARY};
    background: transparent;
}}
"""


def _make_stylesheet(colors: dict[str, str]) -> str:
    return _STYLESHEET_TEMPLATE.format_map(colors)


def apply_theme(app: QApplication, theme_name: str = "descent") -> None:
    """Apply a named theme to the running application."""
    global _active_theme
    if theme_name not in THEMES:
        theme_name = "descent"
    _active_theme = theme_name
    colors = THEMES[theme_name]

    app.setStyleSheet(_make_stylesheet(colors))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors["BG_DARK"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["TEXT_PRIMARY"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors["BG_PANEL"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["BG_SIDEBAR"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors["TEXT_PRIMARY"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["TEXT_PRIMARY"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["ACCENT_ORANGE"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["TEXT_ON_PRIMARY"]))
    app.setPalette(palette)


def get_active_theme() -> str:
    return _active_theme


def list_theme_keys() -> list[str]:
    return list(THEMES.keys())
