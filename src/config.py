"""
Shared configuration for F1 short video creator
"""

import multiprocessing
import os

BASE_DIR = "/Users/abhaykumar/Documents/f1.ai"
PROJECTS_DIR = f"{BASE_DIR}/projects"
SHARED_DIR = f"{BASE_DIR}/shared"

# API Config
ELEVENLABS_KEY_FILE = f"{SHARED_DIR}/creds/elevenlabs"
VOICE_ID = "c6SfcYrb2t09NHXiT80T"  # Jarnathan - Confident and Versatile
MODEL_ID = "eleven_multilingual_v2"

# Concurrency Settings
MAX_CONCURRENT_AUDIO = 4  # API rate limit friendly
MAX_CONCURRENT_DOWNLOADS = 3  # Be respectful to YouTube
MAX_CONCURRENT_SEGMENTS = min(4, multiprocessing.cpu_count())  # For video assembly
MAX_CONCURRENT_FRAMES = 4  # For preview extraction

# YouTube API Config
YOUTUBE_CLIENT_SECRETS = f"{SHARED_DIR}/creds/youtube_client_secrets.json"
YOUTUBE_TOKEN_FILE = f"{SHARED_DIR}/creds/youtube_token.pickle"

# Instagram API Config
INSTAGRAM_CREDENTIALS_FILE = f"{SHARED_DIR}/creds/instagram"
INSTAGRAM_SESSION_FILE = f"{SHARED_DIR}/creds/instagram_session.json"

# Video Config
FRAME_RATE = 30  # CRITICAL: Must be consistent across all segments
VIDEO_BITRATE = "8M"
AUDIO_BITRATE = "192k"
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920  # 9:16 vertical

# YouTube Shorts Safe Zone - bottom margin to avoid UI overlap
# YouTube overlays: title, channel name, "Promote" button, progress bar
# 320px keeps text above all UI elements on mobile and web
SHORTS_BOTTOM_MARGIN = 320

# Max lines of text before splitting into two timed parts
# With 320px bottom margin, 5 lines fits comfortably in the safe zone
SHORTS_MAX_TEXT_LINES = 5

# Audio Pace Config
SHORTS_AUDIO_SPEED = 1.25  # 25% faster for punchy short-form delivery

# Music Config
BACKGROUND_MUSIC = f"{SHARED_DIR}/music/background.mp3"
BACKGROUND_MUSIC_LONGFORM = f"{SHARED_DIR}/music/background_longform.mp3"  # Optional separate music for long-form
MUSIC_VOLUME = 0.04  # Lowered from 0.08 to ensure voiceover dominates
MUSIC_VOLUME_LONGFORM = 0.05  # Very quiet for long-form content (5%)

# Outro Audio (reusable for all long-form videos)
OUTRO_AUDIO_LONGFORM = f"{SHARED_DIR}/audio/outro_longform.mp3"  # ~19s CTA voiceover
CREDITS_DURATION_LONGFORM = 5  # Short credits overlay during outro

# Long-form Video Config (16:9 horizontal)
LONGFORM_FRAME_RATE = 30
LONGFORM_OUTPUT_WIDTH_4K = 3840
LONGFORM_OUTPUT_HEIGHT_4K = 2160
LONGFORM_OUTPUT_WIDTH_HD = 1920
LONGFORM_OUTPUT_HEIGHT_HD = 1080
LONGFORM_VIDEO_BITRATE_4K = "20M"  # Higher quality for 4K
LONGFORM_VIDEO_BITRATE_HD = "12M"  # High quality for HD
LONGFORM_AUDIO_BITRATE = "256k"  # Better audio for long-form
LONGFORM_DURATION_TARGET = 600  # ~10 minutes default

# F1 Team Colors (official hex codes for team radio style text)
F1_TEAM_COLORS = {
    # Current teams (2026 grid)
    "red bull": "#3671C6",  # Red Bull Racing blue
    "redbull": "#3671C6",
    "mclaren": "#FF8000",  # McLaren papaya
    "ferrari": "#E8002D",  # Ferrari red
    "mercedes": "#27F4D2",  # Mercedes teal
    "aston martin": "#229971",  # Aston Martin green
    "alpine": "#FF87BC",  # Alpine pink
    "williams": "#64C4FF",  # Williams blue
    "haas": "#B6BABD",  # Haas silver
    "cadillac": "#C4A747",  # Cadillac gold/crest
    "audi": "#BB0A1E",  # Audi red
    "racing bulls": "#6692FF",  # Racing Bulls blue
    # Drivers (mapped to their 2026 teams)
    "vettel": "#3671C6",  # Red Bull era
    "webber": "#3671C6",  # Red Bull
    "norris": "#FF8000",  # McLaren
    "piastri": "#FF8000",  # McLaren
    "verstappen": "#3671C6",  # Red Bull
    "hadjar": "#3671C6",  # Red Bull
    "hamilton": "#E8002D",  # Ferrari (2026)
    "leclerc": "#E8002D",  # Ferrari
    "alonso": "#229971",  # Aston Martin
    "russell": "#27F4D2",  # Mercedes
    "antonelli": "#27F4D2",  # Mercedes
    "perez": "#C4A747",  # Cadillac (2026)
    "bottas": "#C4A747",  # Cadillac (2026)
    "ocon": "#B6BABD",  # Haas (2026)
    "bortoleto": "#BB0A1E",  # Audi
    "hulkenberg": "#BB0A1E",  # Audi
    "colapinto": "#FF87BC",  # Alpine
    "lawson": "#6692FF",  # Racing Bulls
    "palou": "#FF8000",  # McLaren (legal context)
}

# Default text color if no team/driver detected
F1_DEFAULT_COLOR = "#FFFFFF"

# ============================================================================
# VISUAL TYPES CONFIG
# ============================================================================

VISUAL_TYPES = ["footage", "graphic", "animation", "diagram", "library"]

# Default visual type if not specified in script.json
DEFAULT_VISUAL_TYPE = "footage"

# Graphic generation settings (DALL-E)
GRAPHIC_SETTINGS = {
    "backend": "dalle",  # dalle, stability, local
    "default_style": "technical_diagram",
    "ken_burns_duration": 5,
    "ken_burns_effect": "zoom_in",
}

# AI video generation settings (Runway)
AI_VIDEO_SETTINGS = {
    "backend": "runway",  # runway, pika, luma
    "default_duration": 4,
    "default_style": "cinematic",
}

# Manim settings
MANIM_SETTINGS = {
    "quality": "high",  # low, medium, high
    "template_dir": "src/manim_templates",
}

# Asset library location
ASSET_LIBRARY_DIR = f"{SHARED_DIR}/assets"

# ============================================================================
# FOOTAGE VALIDATION CONFIG
# ============================================================================

VALIDATION_ENABLED = True
VALIDATION_THRESHOLDS = {
    "face": 0.4,  # Max face score (0-1), above = reject
    "text": 0.3,  # Max text score (0-1), above = reject
    "clip": 0.4,  # Min CLIP score (0-1), below = reject (if enabled)
}

# Official F1 channels (prioritized in search)
OFFICIAL_F1_CHANNELS = [
    "FORMULA 1",
    "Formula 1",
    "F1",
    "Sky Sports F1",
    "Red Bull Racing",
    "Mercedes-AMG PETRONAS F1 Team",
    "Scuderia Ferrari",
    "McLaren",
    "Aston Martin Aramco F1 Team",
    "BWT Alpine F1 Team",
    "Williams Racing",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_project_dir(project_name):
    return f"{PROJECTS_DIR}/{project_name}"


def get_elevenlabs_key():
    with open(ELEVENLABS_KEY_FILE) as f:
        return f.read().strip()
