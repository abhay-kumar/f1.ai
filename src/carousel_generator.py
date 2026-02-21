#!/usr/bin/env python3
"""
Instagram Carousel Generator - Creates professional carousel slide images

Uses Playwright (headless Chromium) to render HTML/CSS templates as 1080x1080
JPEG images. Each slide type has a distinct layout, and themes adapt colors
based on F1 team/content context.

Usage:
    python3 src/carousel_generator.py --project {name}
    python3 src/carousel_generator.py --project {name} --slide 3
    python3 src/carousel_generator.py --project {name} --theme ferrari
    python3 src/carousel_generator.py --project {name} --list
"""

import argparse
import atexit
import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    CAROUSEL_JPEG_QUALITY,
    CAROUSEL_MAX_SLIDES,
    CAROUSEL_SLIDE_SIZE,
    SHARED_DIR,
    get_project_dir,
)

# Paths
LOGO_PATH = f"{SHARED_DIR}/assets/logo/logo.png"
F1_FONT_BOLD = f"{SHARED_DIR}/fonts/Formula1-Bold.ttf"
F1_FONT_REGULAR = f"{SHARED_DIR}/fonts/TitilliumWeb-Black.ttf"

# Lazy browser singleton (same pattern as google_image_search.py)
_browser = None
_playwright = None


def _get_browser():
    """Get or create a lazy singleton Playwright browser instance."""
    global _browser, _playwright

    if _browser is not None:
        try:
            _browser.contexts
            return _browser
        except Exception:
            _browser = None
            _playwright = None

    try:
        from playwright.sync_api import sync_playwright

        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox"],
        )
        atexit.register(_cleanup_browser)
        return _browser
    except Exception as e:
        print(f"Error: Playwright launch failed: {e}")
        print("Install with: pip install playwright && playwright install chromium")
        return None


def _cleanup_browser():
    """Cleanup browser on exit."""
    global _browser, _playwright
    try:
        if _browser:
            _browser.close()
        if _playwright:
            _playwright.stop()
    except Exception:
        pass


# ============================================================================
# FONT EMBEDDING
# ============================================================================

_font_css_cache = None


def _get_font_css():
    """Read fonts as base64 and return @font-face CSS rules."""
    global _font_css_cache
    if _font_css_cache is not None:
        return _font_css_cache

    rules = []
    for font_path, font_family in [
        (F1_FONT_BOLD, "F1Bold"),
        (F1_FONT_REGULAR, "F1Regular"),
    ]:
        if os.path.exists(font_path):
            with open(font_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            rules.append(
                f"@font-face {{ font-family: '{font_family}'; "
                f"src: url('data:font/truetype;base64,{b64}') format('truetype'); }}"
            )

    _font_css_cache = "\n".join(rules)
    return _font_css_cache


# ============================================================================
# LOGO EMBEDDING
# ============================================================================

_logo_data_uri_cache = None


def _get_logo_data_uri():
    """Read logo as base64 data URI."""
    global _logo_data_uri_cache
    if _logo_data_uri_cache is not None:
        return _logo_data_uri_cache

    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        _logo_data_uri_cache = f"data:image/png;base64,{b64}"
    else:
        _logo_data_uri_cache = ""

    return _logo_data_uri_cache


# ============================================================================
# THEME SYSTEM
# ============================================================================

THEMES = {
    # F1 Teams
    "ferrari": {
        "primary": "#E8002D",
        "secondary": "#A80020",
        "bg": "#1a0005",
        "text": "#FFFFFF",
        "accent": "#FFD700",
    },
    "redbull": {
        "primary": "#3671C6",
        "secondary": "#1B3A6B",
        "bg": "#0a1628",
        "text": "#FFFFFF",
        "accent": "#FF0000",
    },
    "mercedes": {
        "primary": "#27F4D2",
        "secondary": "#00A88F",
        "bg": "#0a1a17",
        "text": "#FFFFFF",
        "accent": "#FFFFFF",
    },
    "mclaren": {
        "primary": "#FF8000",
        "secondary": "#CC6600",
        "bg": "#1a1000",
        "text": "#FFFFFF",
        "accent": "#FFFFFF",
    },
    "aston_martin": {
        "primary": "#229971",
        "secondary": "#186B50",
        "bg": "#0a1a14",
        "text": "#FFFFFF",
        "accent": "#CEF032",
    },
    "alpine": {
        "primary": "#FF87BC",
        "secondary": "#CC6B96",
        "bg": "#1a0a12",
        "text": "#FFFFFF",
        "accent": "#0093CC",
    },
    "williams": {
        "primary": "#64C4FF",
        "secondary": "#3A96CC",
        "bg": "#0a1520",
        "text": "#FFFFFF",
        "accent": "#FFFFFF",
    },
    "haas": {
        "primary": "#B6BABD",
        "secondary": "#8A8D8F",
        "bg": "#141414",
        "text": "#FFFFFF",
        "accent": "#E8002D",
    },
    "cadillac": {
        "primary": "#C4A747",
        "secondary": "#8B7530",
        "bg": "#141008",
        "text": "#FFFFFF",
        "accent": "#FFFFFF",
    },
    "audi": {
        "primary": "#BB0A1E",
        "secondary": "#8A0716",
        "bg": "#1a0508",
        "text": "#FFFFFF",
        "accent": "#FFFFFF",
    },
    # Generic themes
    "dramatic": {
        "primary": "#E8002D",
        "secondary": "#8B0000",
        "bg": "#0a0a0a",
        "text": "#FFFFFF",
        "accent": "#FFD700",
    },
    "gold": {
        "primary": "#FFD700",
        "secondary": "#DAA520",
        "bg": "#0f0f0f",
        "text": "#FFFFFF",
        "accent": "#FFD700",
    },
    "breaking": {
        "primary": "#FF0000",
        "secondary": "#CC0000",
        "bg": "#1a0000",
        "text": "#FFFFFF",
        "accent": "#FFFF00",
    },
    "stats": {
        "primary": "#00D4FF",
        "secondary": "#0099CC",
        "bg": "#0a0f1a",
        "text": "#FFFFFF",
        "accent": "#00D4FF",
    },
}


def detect_theme(script: dict) -> str:
    """Auto-detect theme from script content based on team/driver mentions."""
    full_text = " ".join(
        [
            s.get("headline", "") + " " + s.get("heading", "") + " " + s.get("body", "")
            for s in script.get("slides", [])
        ]
    ).lower()
    title = script.get("title", "").lower()
    combined = f"{title} {full_text}"

    team_keywords = {
        "ferrari": ["ferrari", "leclerc", "hamilton", "maranello", "sf-"],
        "redbull": ["red bull", "verstappen", "hadjar", "horner", "newey"],
        "mercedes": ["mercedes", "russell", "antonelli", "wolff", "brackley"],
        "mclaren": ["mclaren", "norris", "piastri", "zak brown", "woking"],
        "aston_martin": ["aston martin", "alonso", "stroll", "krack"],
        "alpine": ["alpine", "colapinto", "doohan", "enstone"],
        "williams": ["williams", "sainz", "grove"],
        "haas": ["haas", "ocon", "bearman"],
        "cadillac": ["cadillac", "perez", "bottas"],
        "audi": ["audi", "hulkenberg", "bortoleto"],
    }

    team_counts = {}
    for team, keywords in team_keywords.items():
        count = sum(combined.count(kw) for kw in keywords)
        if count > 0:
            team_counts[team] = count

    if team_counts:
        return max(team_counts, key=team_counts.get)

    return "dramatic"


# ============================================================================
# BASE CSS
# ============================================================================


def _base_css(theme: dict) -> str:
    """Generate base CSS with theme variables and font faces."""
    return f"""
    {_get_font_css()}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    :root {{
        --primary: {theme["primary"]};
        --secondary: {theme["secondary"]};
        --bg: {theme["bg"]};
        --text: {theme["text"]};
        --accent: {theme["accent"]};
    }}
    body {{
        width: {CAROUSEL_SLIDE_SIZE}px;
        height: {CAROUSEL_SLIDE_SIZE}px;
        overflow: hidden;
        font-family: 'F1Regular', 'F1Bold', 'Helvetica Neue', Arial, sans-serif;
        color: var(--text);
        background: var(--bg);
    }}
    .slide {{
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        position: relative;
    }}
    """


# ============================================================================
# SLIDE TEMPLATES
# ============================================================================


def _render_cover(slide: dict, theme: dict) -> str:
    """Cover slide - bold title with gradient background."""
    headline = _escape_html(slide.get("headline", ""))
    subheadline = _escape_html(slide.get("subheadline", ""))
    bg_image = slide.get("background_image", "")

    bg_style = ""
    if bg_image and os.path.exists(bg_image):
        with open(bg_image, "rb") as f:
            ext = bg_image.rsplit(".", 1)[-1].lower()
            mime = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }.get(ext, "image/jpeg")
            b64 = base64.b64encode(f.read()).decode("ascii")
        bg_style = f"""
            background-image: linear-gradient(135deg, {theme["bg"]}ee 0%, {theme["primary"]}aa 50%, {theme["bg"]}dd 100%),
                              url('data:{mime};base64,{b64}');
            background-size: cover;
            background-position: center;
        """
    else:
        bg_style = f"""
            background: linear-gradient(135deg, {theme["bg"]} 0%, {theme["primary"]}33 40%, {theme["bg"]} 60%, {theme["primary"]}22 100%);
        """

    return f"""<!DOCTYPE html><html><head><style>
    {_base_css(theme)}
    .slide {{
        {bg_style}
        justify-content: center;
        align-items: center;
        padding: 60px;
        text-align: center;
    }}
    .accent-line {{
        width: 80px;
        height: 4px;
        background: var(--primary);
        margin: 0 auto 40px;
        border-radius: 2px;
    }}
    .headline {{
        font-family: 'F1Bold', 'Helvetica Neue', sans-serif;
        font-size: 52px;
        line-height: 1.15;
        letter-spacing: -0.5px;
        color: var(--text);
        text-transform: uppercase;
        margin-bottom: 24px;
        text-shadow: 0 2px 20px rgba(0,0,0,0.5);
    }}
    .headline span {{
        color: var(--primary);
    }}
    .subheadline {{
        font-family: 'F1Regular', 'Helvetica Neue', sans-serif;
        font-size: 22px;
        color: var(--text);
        opacity: 0.8;
        letter-spacing: 1px;
    }}
    .swipe {{
        position: absolute;
        bottom: 40px;
        left: 0;
        right: 0;
        text-align: center;
        font-family: 'F1Regular', sans-serif;
        font-size: 16px;
        color: var(--text);
        opacity: 0.5;
        letter-spacing: 2px;
    }}
    .corner-accent {{
        position: absolute;
        width: 60px;
        height: 60px;
        border-color: var(--primary);
        border-style: solid;
        opacity: 0.3;
    }}
    .corner-tl {{ top: 24px; left: 24px; border-width: 3px 0 0 3px; }}
    .corner-br {{ bottom: 24px; right: 24px; border-width: 0 3px 3px 0; }}
    </style></head><body>
    <div class="slide">
        <div class="corner-accent corner-tl"></div>
        <div class="corner-accent corner-br"></div>
        <div class="accent-line"></div>
        <div class="headline">{headline}</div>
        <div class="subheadline">{subheadline}</div>
        <div class="swipe">SWIPE &rarr;</div>
    </div>
    </body></html>"""


def _render_content(slide: dict, theme: dict) -> str:
    """Content slide - numbered point with body text."""
    number = slide.get("number", "")
    heading = _escape_html(slide.get("heading", ""))
    body = _escape_html(slide.get("body", ""), preserve_newlines=True)
    bg_image = slide.get("background_image", "")

    bg_css = ""
    if bg_image and os.path.exists(bg_image):
        with open(bg_image, "rb") as f:
            ext = bg_image.rsplit(".", 1)[-1].lower()
            mime = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }.get(ext, "image/jpeg")
            b64 = base64.b64encode(f.read()).decode("ascii")
        bg_css = f"""
            background-image: linear-gradient(180deg, {theme["bg"]}f0 0%, {theme["bg"]}cc 60%, {theme["bg"]}f0 100%),
                              url('data:{mime};base64,{b64}');
            background-size: cover;
            background-position: center;
        """
    else:
        bg_css = f"background: {theme['bg']};"

    num_html = ""
    if number:
        num_html = (
            f'<div class="number">{number:02d}</div>'
            if isinstance(number, int)
            else f'<div class="number">{number}</div>'
        )

    return f"""<!DOCTYPE html><html><head><style>
    {_base_css(theme)}
    .slide {{
        {bg_css}
        justify-content: center;
        padding: 70px 60px;
    }}
    .number {{
        font-family: 'F1Bold', sans-serif;
        font-size: 120px;
        color: var(--primary);
        opacity: 0.15;
        position: absolute;
        top: 30px;
        right: 50px;
        line-height: 1;
    }}
    .accent-bar {{
        width: 50px;
        height: 4px;
        background: var(--primary);
        margin-bottom: 30px;
        border-radius: 2px;
    }}
    .heading {{
        font-family: 'F1Bold', sans-serif;
        font-size: 36px;
        line-height: 1.2;
        color: var(--text);
        text-transform: uppercase;
        margin-bottom: 24px;
    }}
    .body {{
        font-family: 'F1Regular', sans-serif;
        font-size: 24px;
        line-height: 1.6;
        color: var(--text);
        opacity: 0.85;
    }}
    .side-stripe {{
        position: absolute;
        left: 0;
        top: 0;
        width: 6px;
        height: 100%;
        background: linear-gradient(180deg, var(--primary), transparent);
    }}
    </style></head><body>
    <div class="slide">
        <div class="side-stripe"></div>
        {num_html}
        <div class="accent-bar"></div>
        <div class="heading">{heading}</div>
        <div class="body">{body}</div>
    </div>
    </body></html>"""


def _render_content_quote(slide: dict, theme: dict) -> str:
    """Quote slide with large quotation marks."""
    quote = _escape_html(slide.get("quote", ""))
    speaker = _escape_html(slide.get("speaker", ""))
    role = _escape_html(slide.get("role", ""))
    speaker_image = slide.get("speaker_image", "")

    portrait_html = ""
    if speaker_image and os.path.exists(speaker_image):
        with open(speaker_image, "rb") as f:
            ext = speaker_image.rsplit(".", 1)[-1].lower()
            mime = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }.get(ext, "image/jpeg")
            b64 = base64.b64encode(f.read()).decode("ascii")
        portrait_html = f'<img class="portrait" src="data:{mime};base64,{b64}" />'

    return f"""<!DOCTYPE html><html><head><style>
    {_base_css(theme)}
    .slide {{
        background: {theme["bg"]};
        justify-content: center;
        align-items: center;
        padding: 70px 60px;
        text-align: center;
    }}
    .quote-mark {{
        font-family: Georgia, serif;
        font-size: 160px;
        color: var(--primary);
        opacity: 0.25;
        line-height: 0.6;
        margin-bottom: 10px;
    }}
    .quote {{
        font-family: 'F1Regular', sans-serif;
        font-size: 28px;
        line-height: 1.5;
        color: var(--text);
        font-style: italic;
        margin-bottom: 30px;
        max-width: 900px;
    }}
    .attribution {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }}
    .portrait {{
        width: 80px;
        height: 80px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid var(--primary);
        margin-bottom: 8px;
    }}
    .speaker {{
        font-family: 'F1Bold', sans-serif;
        font-size: 22px;
        color: var(--primary);
        text-transform: uppercase;
    }}
    .role {{
        font-family: 'F1Regular', sans-serif;
        font-size: 16px;
        color: var(--text);
        opacity: 0.6;
    }}
    .accent-line {{
        width: 50px;
        height: 3px;
        background: var(--primary);
        margin: 0 auto 16px;
    }}
    </style></head><body>
    <div class="slide">
        <div class="quote-mark">&ldquo;</div>
        <div class="quote">{quote}</div>
        <div class="accent-line"></div>
        <div class="attribution">
            {portrait_html}
            <div class="speaker">{speaker}</div>
            <div class="role">{role}</div>
        </div>
    </div>
    </body></html>"""


def _render_content_stat(slide: dict, theme: dict) -> str:
    """Big statistic callout slide."""
    stat = _escape_html(slide.get("stat", ""))
    label = _escape_html(slide.get("label", ""))

    return f"""<!DOCTYPE html><html><head><style>
    {_base_css(theme)}
    .slide {{
        background: {theme["bg"]};
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 60px;
    }}
    .stat {{
        font-family: 'F1Bold', sans-serif;
        font-size: 140px;
        color: var(--primary);
        line-height: 1;
        margin-bottom: 24px;
        text-shadow: 0 0 60px {theme["primary"]}44;
    }}
    .label {{
        font-family: 'F1Regular', sans-serif;
        font-size: 24px;
        line-height: 1.5;
        color: var(--text);
        opacity: 0.8;
        max-width: 700px;
    }}
    .divider {{
        width: 60px;
        height: 3px;
        background: var(--accent);
        margin: 24px auto;
        opacity: 0.5;
    }}
    .glow {{
        position: absolute;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, {theme["primary"]}15, transparent 70%);
        top: 50%;
        left: 50%;
        transform: translate(-50%, -60%);
        pointer-events: none;
    }}
    </style></head><body>
    <div class="slide">
        <div class="glow"></div>
        <div class="stat">{stat}</div>
        <div class="divider"></div>
        <div class="label">{label}</div>
    </div>
    </body></html>"""


def _render_content_image(slide: dict, theme: dict) -> str:
    """Full-bleed image slide with text overlay."""
    heading = _escape_html(slide.get("heading", ""))
    bg_image = slide.get("background_image", "")

    bg_css = f"background: {theme['bg']};"
    if bg_image and os.path.exists(bg_image):
        with open(bg_image, "rb") as f:
            ext = bg_image.rsplit(".", 1)[-1].lower()
            mime = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }.get(ext, "image/jpeg")
            b64 = base64.b64encode(f.read()).decode("ascii")
        bg_css = f"""
            background-image: url('data:{mime};base64,{b64}');
            background-size: cover;
            background-position: center;
        """

    return f"""<!DOCTYPE html><html><head><style>
    {_base_css(theme)}
    .slide {{
        {bg_css}
        justify-content: flex-end;
    }}
    .overlay {{
        background: linear-gradient(0deg, {theme["bg"]}ee 0%, {theme["bg"]}cc 40%, transparent 100%);
        padding: 60px;
        padding-top: 120px;
    }}
    .heading {{
        font-family: 'F1Bold', sans-serif;
        font-size: 34px;
        line-height: 1.25;
        color: var(--text);
        text-transform: uppercase;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }}
    .bar {{
        width: 50px;
        height: 4px;
        background: var(--primary);
        margin-bottom: 16px;
    }}
    </style></head><body>
    <div class="slide">
        <div class="overlay">
            <div class="bar"></div>
            <div class="heading">{heading}</div>
        </div>
    </div>
    </body></html>"""


def _render_cta(theme: dict) -> str:
    """Standard CTA slide - logo + follow prompt. Reusable across all carousels."""
    logo_uri = _get_logo_data_uri()

    return f"""<!DOCTYPE html><html><head><style>
    {_base_css(theme)}
    .slide {{
        background: linear-gradient(135deg, {theme["bg"]} 0%, {theme["primary"]}1a 50%, {theme["bg"]} 100%);
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 60px;
    }}
    .logo {{
        width: 280px;
        height: auto;
        margin-bottom: 40px;
        filter: drop-shadow(0 4px 20px rgba(0,0,0,0.3));
    }}
    .cta-text {{
        font-family: 'F1Bold', sans-serif;
        font-size: 32px;
        color: var(--text);
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 30px;
    }}
    .actions {{
        display: flex;
        gap: 30px;
        justify-content: center;
        align-items: center;
    }}
    .action {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }}
    .action-icon {{
        width: 52px;
        height: 52px;
        border-radius: 50%;
        background: var(--primary);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }}
    .action-label {{
        font-family: 'F1Regular', sans-serif;
        font-size: 14px;
        color: var(--text);
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .corner-accent {{
        position: absolute;
        width: 50px;
        height: 50px;
        border-color: var(--primary);
        border-style: solid;
        opacity: 0.2;
    }}
    .corner-tl {{ top: 24px; left: 24px; border-width: 3px 0 0 3px; }}
    .corner-tr {{ top: 24px; right: 24px; border-width: 3px 3px 0 0; }}
    .corner-bl {{ bottom: 24px; left: 24px; border-width: 0 0 3px 3px; }}
    .corner-br {{ bottom: 24px; right: 24px; border-width: 0 3px 3px 0; }}
    .handle {{
        position: absolute;
        bottom: 40px;
        font-family: 'F1Regular', sans-serif;
        font-size: 18px;
        color: var(--primary);
        letter-spacing: 1px;
    }}
    </style></head><body>
    <div class="slide">
        <div class="corner-accent corner-tl"></div>
        <div class="corner-accent corner-tr"></div>
        <div class="corner-accent corner-bl"></div>
        <div class="corner-accent corner-br"></div>
        <img class="logo" src="{logo_uri}" alt="F1 Burnouts" />
        <div class="cta-text">Follow for more</div>
        <div class="actions">
            <div class="action">
                <div class="action-icon">&hearts;</div>
                <div class="action-label">Like</div>
            </div>
            <div class="action">
                <div class="action-icon">&#10148;</div>
                <div class="action-label">Share</div>
            </div>
            <div class="action">
                <div class="action-icon">+</div>
                <div class="action-label">Follow</div>
            </div>
        </div>
        <div class="handle">@f1burnouts</div>
    </div>
    </body></html>"""


def _render_content_meme(slide: dict, theme: dict) -> str:
    """Meme comparison slide — two panels with a punchline caption."""
    top_text = _escape_html(slide.get("top_text", ""))
    panel_left_label = _escape_html(slide.get("panel_left", ""))
    panel_right_label = _escape_html(slide.get("panel_right", ""))
    bottom_text = _escape_html(slide.get("bottom_text", ""))

    # Optional panel images
    panel_left_img = slide.get("panel_left_image", "")
    panel_right_img = slide.get("panel_right_image", "")

    def _img_tag(path, fallback_text):
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                ext = path.rsplit(".", 1)[-1].lower()
                mime = {
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                    "webp": "image/webp",
                }.get(ext, "image/jpeg")
                b64 = base64.b64encode(f.read()).decode("ascii")
            return f'<img class="panel-img" src="data:{mime};base64,{b64}" />'
        return f'<div class="panel-placeholder">{fallback_text}</div>'

    left_html = _img_tag(panel_left_img, panel_left_label)
    right_html = _img_tag(panel_right_img, panel_right_label)

    return f"""<!DOCTYPE html><html><head><style>
    {_base_css(theme)}
    .slide {{
        background: {theme["bg"]};
        justify-content: center;
        align-items: center;
        padding: 40px 40px;
        text-align: center;
    }}
    .top-text {{
        font-family: 'F1Regular', sans-serif;
        font-size: 22px;
        color: var(--text);
        opacity: 0.7;
        margin-bottom: 30px;
        letter-spacing: 0.5px;
        line-height: 1.4;
    }}
    .panels {{
        display: flex;
        gap: 24px;
        justify-content: center;
        align-items: stretch;
        width: 100%;
        margin-bottom: 30px;
    }}
    .panel {{
        flex: 1;
        background: {theme["primary"]}15;
        border: 2px solid {theme["primary"]}40;
        border-radius: 16px;
        padding: 24px 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 16px;
        min-height: 340px;
    }}
    .panel-img {{
        width: 100%;
        max-height: 240px;
        object-fit: cover;
        border-radius: 10px;
    }}
    .panel-placeholder {{
        font-family: 'F1Bold', sans-serif;
        font-size: 20px;
        color: var(--primary);
        text-align: center;
        padding: 40px 10px;
    }}
    .panel-label {{
        font-family: 'F1Bold', sans-serif;
        font-size: 18px;
        color: var(--text);
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .bottom-text {{
        font-family: 'F1Bold', sans-serif;
        font-size: 30px;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 1px;
        line-height: 1.3;
    }}
    .emoji {{
        font-size: 36px;
        margin-bottom: 6px;
    }}
    </style></head><body>
    <div class="slide">
        <div class="top-text">{top_text}</div>
        <div class="panels">
            <div class="panel">
                {left_html}
                <div class="panel-label">{panel_left_label}</div>
            </div>
            <div class="panel">
                {right_html}
                <div class="panel-label">{panel_right_label}</div>
            </div>
        </div>
        <div class="bottom-text">{bottom_text}</div>
    </div>
    </body></html>"""


# ============================================================================
# RENDERING
# ============================================================================

SLIDE_RENDERERS = {
    "cover": _render_cover,
    "content": _render_content,
    "content_quote": _render_content_quote,
    "content_stat": _render_content_stat,
    "content_image": _render_content_image,
    "content_meme": _render_content_meme,
}


def _escape_html(text: str, preserve_newlines: bool = False) -> str:
    """Escape HTML special characters. Optionally convert newlines to <br>."""
    result = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    if preserve_newlines:
        result = result.replace("\n", "<br>")
    return result


def _resolve_images(project_dir: str, slides: list) -> list:
    """Resolve background_image paths - download URLs, resolve relative paths."""
    images_dir = os.path.join(project_dir, "images")

    for slide in slides:
        for key in ("background_image", "speaker_image"):
            path = slide.get(key, "")
            if not path:
                continue

            # Already an absolute path that exists
            if os.path.isabs(path) and os.path.exists(path):
                continue

            # Relative to project dir
            rel_path = os.path.join(project_dir, path)
            if os.path.exists(rel_path):
                slide[key] = rel_path
                continue

            # Relative to images dir
            img_path = os.path.join(images_dir, os.path.basename(path))
            if os.path.exists(img_path):
                slide[key] = img_path
                continue

            # URL - download to images/
            if path.startswith("http://") or path.startswith("https://"):
                os.makedirs(images_dir, exist_ok=True)
                ext = path.rsplit(".", 1)[-1].split("?")[0][:4]
                if ext not in ("jpg", "jpeg", "png", "webp"):
                    ext = "jpg"
                filename = f"slide_img_{slides.index(slide):02d}.{ext}"
                dest = os.path.join(images_dir, filename)

                if not os.path.exists(dest):
                    print(f"  Downloading image: {path[:80]}...")
                    try:
                        req = urllib.request.Request(
                            path,
                            headers={"User-Agent": "Mozilla/5.0"},
                        )
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            with open(dest, "wb") as f:
                                f.write(resp.read())
                    except Exception as e:
                        print(f"  Warning: Failed to download {path}: {e}")
                        slide[key] = ""
                        continue

                slide[key] = dest
                continue

            # Can't resolve - clear it
            slide[key] = ""

    return slides


def render_slide(html: str, output_path: str) -> bool:
    """Render an HTML string to a JPEG image using Playwright."""
    browser = _get_browser()
    if not browser:
        return False

    try:
        page = browser.new_page(
            viewport={"width": CAROUSEL_SLIDE_SIZE, "height": CAROUSEL_SLIDE_SIZE},
            device_scale_factor=1,
        )
        page.set_content(html, wait_until="networkidle")
        # Small delay for font rendering
        page.wait_for_timeout(300)
        page.screenshot(
            path=output_path,
            type="jpeg",
            quality=CAROUSEL_JPEG_QUALITY,
            full_page=False,
        )
        page.close()
        return True
    except Exception as e:
        print(f"  Error rendering slide: {e}")
        return False


def generate_carousel(
    project_name: str, theme_override: str = None, single_slide: int = None
) -> list:
    """Generate carousel slide images from script.json.

    Args:
        project_name: Project directory name
        theme_override: Override auto-detected theme
        single_slide: If set, only regenerate this slide number (1-indexed)

    Returns:
        List of generated slide file paths
    """
    project_dir = get_project_dir(project_name)
    script_path = os.path.join(project_dir, "script.json")
    output_dir = os.path.join(project_dir, "output")

    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        return []

    with open(script_path) as f:
        script = json.load(f)

    if script.get("format") != "carousel":
        print(
            f"Error: Script format is '{script.get('format', 'unknown')}', expected 'carousel'"
        )
        return []

    slides = script.get("slides", [])
    if not slides:
        print("Error: No slides found in script.json")
        return []

    # Theme
    theme_name = theme_override or script.get("theme") or detect_theme(script)
    theme = THEMES.get(theme_name, THEMES["dramatic"])
    print(f"Theme: {theme_name}")

    # Resolve image paths
    slides = _resolve_images(project_dir, slides)

    # Add CTA as last slide
    total_slides = len(slides) + 1  # +1 for CTA
    if total_slides > CAROUSEL_MAX_SLIDES:
        print(
            f"Warning: {total_slides} slides exceeds Instagram limit of {CAROUSEL_MAX_SLIDES}"
        )

    os.makedirs(output_dir, exist_ok=True)

    generated = []

    print(f"\nGenerating {total_slides} slides...\n")

    for i, slide in enumerate(slides):
        slide_num = i + 1

        if single_slide and slide_num != single_slide:
            continue

        slide_type = slide.get("type", "content")
        renderer = SLIDE_RENDERERS.get(slide_type)
        if not renderer:
            print(f"  Slide {slide_num}: Unknown type '{slide_type}', skipping")
            continue

        output_path = os.path.join(output_dir, f"slide_{slide_num:02d}.jpg")
        print(
            f"  Slide {slide_num}/{total_slides}: {slide_type} - {slide.get('headline') or slide.get('heading') or slide.get('stat') or slide.get('speaker', '')[:40]}"
        )

        html = renderer(slide, theme)
        if render_slide(html, output_path):
            size_kb = os.path.getsize(output_path) / 1024
            print(f"    -> {output_path} ({size_kb:.0f}KB)")
            generated.append(output_path)
        else:
            print(f"    -> FAILED")

    # CTA slide (always last)
    cta_num = len(slides) + 1
    if not single_slide or single_slide == cta_num:
        cta_path = os.path.join(output_dir, f"slide_{cta_num:02d}.jpg")
        print(f"  Slide {cta_num}/{total_slides}: cta - Follow / Like / Share")

        html = _render_cta(theme)
        if render_slide(html, cta_path):
            size_kb = os.path.getsize(cta_path) / 1024
            print(f"    -> {cta_path} ({size_kb:.0f}KB)")
            generated.append(cta_path)
        else:
            print(f"    -> FAILED")

    print(f"\nDone! {len(generated)}/{total_slides} slides generated in {output_dir}/")
    return generated


def list_slides(project_name: str):
    """Preview slide plan without generating images."""
    project_dir = get_project_dir(project_name)
    script_path = os.path.join(project_dir, "script.json")

    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        return

    with open(script_path) as f:
        script = json.load(f)

    slides = script.get("slides", [])
    theme_name = script.get("theme") or detect_theme(script)

    print(f"Project: {project_name}")
    print(f"Title: {script.get('title', 'Untitled')}")
    print(f"Theme: {theme_name}")
    print(f"Slides: {len(slides) + 1} (including CTA)\n")

    for i, slide in enumerate(slides):
        slide_type = slide.get("type", "content")
        label = (
            slide.get("headline")
            or slide.get("heading")
            or slide.get("stat")
            or slide.get("quote", "")[:50]
        )
        has_image = bool(slide.get("background_image") or slide.get("speaker_image"))
        img_tag = " [has image]" if has_image else ""
        print(f"  {i + 1}. [{slide_type}] {label}{img_tag}")

    print(f"  {len(slides) + 1}. [cta] Follow / Like / Share + Logo")


def main():
    parser = argparse.ArgumentParser(description="Generate Instagram carousel slides")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument(
        "--theme",
        choices=list(THEMES.keys()),
        help="Override theme (default: auto-detect)",
    )
    parser.add_argument(
        "--slide", type=int, help="Regenerate a single slide (1-indexed)"
    )
    parser.add_argument(
        "--list", action="store_true", help="Preview slide plan without generating"
    )
    args = parser.parse_args()

    print("=" * 50)
    print("Instagram Carousel Generator")
    print("=" * 50)

    if args.list:
        list_slides(args.project)
        return

    result = generate_carousel(
        args.project,
        theme_override=args.theme,
        single_slide=args.slide,
    )

    if not result:
        print("\nCarousel generation failed")
        sys.exit(1)

    print("\nSlides ready for manual Instagram upload!")


if __name__ == "__main__":
    main()
