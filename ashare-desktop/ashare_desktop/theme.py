"""Central palette + global stylesheet for the TradeMind A-share desktop app.

Dark, modern, "cockpit" look. A-share colour convention is honoured elsewhere
(红涨绿跌): red = up / positive, green = down / negative.
"""
from __future__ import annotations


class Color:
    # base surfaces
    BG_0 = "#0a0e17"      # window backdrop
    BG_1 = "#0f1420"      # panels
    BG_2 = "#151d2e"      # cards
    BG_3 = "#1c2740"      # hovered / raised
    STROKE = "#243049"    # hairline borders

    # text
    TEXT = "#e8eef9"
    TEXT_DIM = "#93a1bd"
    TEXT_FAINT = "#5f6f8f"

    # brand accents
    ACCENT = "#4f8cff"    # primary blue
    ACCENT_2 = "#7c5cff"  # indigo
    GOLD = "#f5c451"      # highlight / KPI

    # market (China convention)
    UP = "#ff5a68"        # 红 = 涨
    DOWN = "#26d07c"      # 绿 = 跌

    # status
    OK = "#26d07c"
    WARN = "#f5c451"
    BAD = "#ff5a68"
    LIVE = "#38e0c8"


def app_qss() -> str:
    c = Color
    return f"""
    * {{
        font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
        color: {c.TEXT};
        outline: none;
    }}
    QWidget#Root {{ background: {c.BG_0}; }}

    QLabel[role="h1"]   {{ font-size: 24px; font-weight: 800; }}
    QLabel[role="h2"]   {{ font-size: 17px; font-weight: 700; }}
    QLabel[role="dim"]  {{ color: {c.TEXT_DIM}; font-size: 13px; }}
    QLabel[role="faint"]{{ color: {c.TEXT_FAINT}; font-size: 12px; }}

    /* ---- Card ---- */
    QFrame#Card {{
        background: {c.BG_2};
        border: 1px solid {c.STROKE};
        border-radius: 16px;
    }}

    /* ---- Sidebar ---- */
    QFrame#Sidebar {{ background: {c.BG_1}; border-right: 1px solid {c.STROKE}; }}

    /* ---- Tables ---- */
    QTableView {{
        background: transparent;
        border: none;
        gridline-color: transparent;
        selection-background-color: {c.BG_3};
        selection-color: {c.TEXT};
        font-size: 13px;
    }}
    QHeaderView::section {{
        background: transparent;
        color: {c.TEXT_FAINT};
        border: none;
        border-bottom: 1px solid {c.STROKE};
        padding: 8px 10px;
        font-size: 12px;
        font-weight: 700;
    }}
    QTableView::item {{ padding: 6px 10px; border-bottom: 1px solid rgba(36,48,73,0.5); }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px; }}
    QScrollBar::handle:vertical {{ background: {c.BG_3}; border-radius: 5px; min-height: 30px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

    /* ---- Buttons ---- */
    QPushButton[role="ghost"] {{
        background: {c.BG_2};
        border: 1px solid {c.STROKE};
        border-radius: 10px;
        padding: 9px 16px;
        color: {c.TEXT_DIM};
        font-weight: 600;
    }}
    QPushButton[role="ghost"]:hover {{ background: {c.BG_3}; color: {c.TEXT}; }}
    QToolTip {{ background: {c.BG_3}; color: {c.TEXT}; border: 1px solid {c.STROKE}; }}
    """
