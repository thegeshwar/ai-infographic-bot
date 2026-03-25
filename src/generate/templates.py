"""Visual template definitions for infographics."""

# ---------------------------------------------------------------------------
# Category colors & icons
# ---------------------------------------------------------------------------

CATEGORY_COLORS = {
    "breakthrough": {"primary": "#FF6B35", "accent": "#FFB563"},
    "product": {"primary": "#4ECDC4", "accent": "#A8E6CF"},
    "research": {"primary": "#6C5CE7", "accent": "#A29BFE"},
    "industry": {"primary": "#0984E3", "accent": "#74B9FF"},
    "policy": {"primary": "#E17055", "accent": "#FAB1A0"},
}

CATEGORY_ICONS = {
    "breakthrough": "\U0001f52c",  # microscope
    "product": "\U0001f4f1",       # mobile phone
    "research": "\U0001f4ca",      # bar chart
    "industry": "\U0001f3ed",      # factory
    "policy": "\U0001f3db",        # classical building
}

# ---------------------------------------------------------------------------
# Font definitions
# ---------------------------------------------------------------------------

FONTS = {
    "title": {"size": 48, "weight": "bold"},
    "headline": {"size": 32, "weight": "bold"},
    "bullet": {"size": 22, "weight": "regular"},
    "tag": {"size": 16, "weight": "bold"},
    "date": {"size": 22, "weight": "regular"},
    "footer": {"size": 16, "weight": "regular"},
    "watermark": {"size": 14, "weight": "light"},
}

# ---------------------------------------------------------------------------
# Template styles
# ---------------------------------------------------------------------------

TEMPLATE_STYLES = {
    "dark": {
        "background": "#1A1A2E",
        "text_primary": "#FFFFFF",
        "text_secondary": "#CCCCCC",
        "text_muted": "#888888",
        "accent": "#333355",
        "card_bg": "#16213E",
        "margin": 60,
        "card_padding": 20,
        "card_radius": 12,
    },
    "light": {
        "background": "#F5F5F5",
        "text_primary": "#1A1A2E",
        "text_secondary": "#444444",
        "text_muted": "#888888",
        "accent": "#DDDDDD",
        "card_bg": "#FFFFFF",
        "margin": 60,
        "card_padding": 20,
        "card_radius": 12,
    },
    "gradient": {
        "background": "#0F0C29",
        "gradient_start": "#0F0C29",
        "gradient_end": "#302B63",
        "text_primary": "#FFFFFF",
        "text_secondary": "#D0D0E0",
        "text_muted": "#9090B0",
        "accent": "#4A4580",
        "card_bg": "#1C1848",
        "margin": 60,
        "card_padding": 20,
        "card_radius": 12,
    },
    "minimal": {
        "background": "#FFFFFF",
        "text_primary": "#111111",
        "text_secondary": "#555555",
        "text_muted": "#999999",
        "accent": "#E0E0E0",
        "card_bg": "#FAFAFA",
        "margin": 70,
        "card_padding": 16,
        "card_radius": 8,
    },
}

# ---------------------------------------------------------------------------
# Output formats (aspect ratios)
# ---------------------------------------------------------------------------

OUTPUT_FORMATS = {
    "instagram": {"width": 1080, "height": 1350},
    "twitter": {"width": 1200, "height": 675},
    "linkedin": {"width": 1200, "height": 627},
}

# Keep legacy constants for backwards compatibility
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350


# ---------------------------------------------------------------------------
# Accessor helpers
# ---------------------------------------------------------------------------

def get_template(style: str) -> dict:
    """Return the template dict for *style*, falling back to 'dark'."""
    return TEMPLATE_STYLES.get(style, TEMPLATE_STYLES["dark"])


def get_output_format(fmt: str) -> dict:
    """Return the output-format dict for *fmt*, falling back to 'instagram'."""
    return OUTPUT_FORMATS.get(fmt, OUTPUT_FORMATS["instagram"])
