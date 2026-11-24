"""Colours, fonts and formatting helpers shared by every screen."""
import sys
from datetime import date, datetime
from decimal import Decimal

import customtkinter as ctk

NAVY = "#0B2545"
NAVY_2 = "#13315C"
NAVY_3 = "#1D4373"
GREEN = "#1E9E6A"
GREEN_DARK = "#157A52"
GREEN_SOFT = "#E4F5EC"
BG = "#F3F6F9"
CARD = "#FFFFFF"
TEXT = "#1B2A41"
MUTED = "#6B7A90"
BORDER = "#E1E7EF"
RED = "#D64545"
RED_SOFT = "#FDECEC"
ORANGE = "#E8912D"
ORANGE_SOFT = "#FFF3E0"
BLUE = "#2F6FDE"
BLUE_SOFT = "#E6EEFC"
STRIPE = "#F8FAFC"

FAMILY = "Segoe UI" if sys.platform.startswith("win") else ("Helvetica Neue" if sys.platform == "darwin" else "DejaVu Sans")


def font(size=13, weight="normal"):
    return ctk.CTkFont(family=FAMILY, size=size, weight=weight)


def money(v, symbol="Rs "):
    if v is None:
        return ""
    v = float(v)
    return f"{symbol}{v:,.0f}" if (v == int(v) or abs(v) >= 1000) else f"{symbol}{v:,.2f}"


def display(v):
    """Turn a database value into text for a table cell."""
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, Decimal):
        return f"{v:,.2f}" if v % 1 else f"{int(v):,}"
    if isinstance(v, float):
        return f"{v:,.2f}" if v % 1 else f"{int(v):,}"
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    return str(v)
