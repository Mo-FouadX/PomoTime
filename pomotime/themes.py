"""
Visual themes for PomoTime.

Four built-in color themes used across the application for light/dark styling
and the circular timer widget ring.
"""

THEMES = {
    "default": {
        "bg": "#F1F5F9",
        "card": "#FFFFFF",
        "text": "#0F172A",
        "subtext": "#64748B",
        "accent": "#2563EB",
        "accent_hover": "#1D4ED8",
        "border": "#CBD5E1",
        "tab_bg": "#E2E8F0",
    },
    "forest": {
        "bg": "#F0FDF4",
        "card": "#FFFFFF",
        "text": "#064E3B",
        "subtext": "#047857",
        "accent": "#059669",
        "accent_hover": "#047857",
        "border": "#A7F3D0",
        "tab_bg": "#D1FAE5",
    },
    "midnight": {
        "bg": "#090D16",
        "card": "#131C2E",
        "text": "#F8FAFC",
        "subtext": "#94A3B8",
        "accent": "#6366F1",
        "accent_hover": "#4F46E5",
        "border": "#1E293B",
        "tab_bg": "#1E293B",
    },
    "sunset": {
        "bg": "#FFFBEB",
        "card": "#FFFFFF",
        "text": "#7C2D12",
        "subtext": "#9A3412",
        "accent": "#EA580C",
        "accent_hover": "#C2410C",
        "border": "#FED7AA",
        "tab_bg": "#FEF3C7",
    },
}

DEFAULT_THEME = "default"

SUPPORTED_THEMES = ["default", "forest", "midnight", "sunset"]

# Theme names keyed to translation keys for i18n lookup.
THEME_TRANSLATION_KEYS = {
    "default": "theme_default",
    "forest": "theme_forest",
    "midnight": "theme_midnight",
    "sunset": "theme_sunset",
}

__all__ = ["THEMES", "DEFAULT_THEME", "SUPPORTED_THEMES", "THEME_TRANSLATION_KEYS"]
