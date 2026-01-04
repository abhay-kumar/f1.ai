"""
Shared configuration for F1 short video creator
"""
import os
import multiprocessing

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

# Video Config
FRAME_RATE = 30  # CRITICAL: Must be consistent across all segments
VIDEO_BITRATE = "8M"
AUDIO_BITRATE = "192k"
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920  # 9:16 vertical

# Music Config
BACKGROUND_MUSIC = f"{SHARED_DIR}/music/background.mp3"
BACKGROUND_MUSIC_LONGFORM = f"{SHARED_DIR}/music/background_longform.mp3"  # Optional separate music for long-form
MUSIC_VOLUME = 0.15
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
LONGFORM_AUDIO_BITRATE = "256k"    # Better audio for long-form
LONGFORM_DURATION_TARGET = 600     # ~10 minutes default

# F1 Team Colors (official hex codes for team radio style text)
F1_TEAM_COLORS = {
    # Current teams
    "red bull": "#3671C6",      # Red Bull Racing blue
    "redbull": "#3671C6",
    "mclaren": "#FF8000",       # McLaren papaya
    "ferrari": "#E8002D",       # Ferrari red
    "mercedes": "#27F4D2",      # Mercedes teal
    "aston martin": "#229971",  # Aston Martin green
    "alpine": "#FF87BC",        # Alpine pink
    "williams": "#64C4FF",      # Williams blue
    "haas": "#B6BABD",          # Haas silver
    "kick sauber": "#52E252",   # Sauber green
    "sauber": "#52E252",

    # Drivers (mapped to their teams)
    "vettel": "#3671C6",        # Red Bull era
    "webber": "#3671C6",        # Red Bull
    "norris": "#FF8000",        # McLaren
    "piastri": "#FF8000",       # McLaren
    "verstappen": "#3671C6",    # Red Bull
    "hamilton": "#27F4D2",      # Mercedes
    "leclerc": "#E8002D",       # Ferrari
    "sainz": "#E8002D",         # Ferrari
    "alonso": "#229971",        # Aston Martin
    "russell": "#27F4D2",       # Mercedes
    "perez": "#3671C6",         # Red Bull
}

# Default text color if no team/driver detected
F1_DEFAULT_COLOR = "#FFFFFF"

def get_project_dir(project_name):
    return f"{PROJECTS_DIR}/{project_name}"

def get_elevenlabs_key():
    with open(ELEVENLABS_KEY_FILE) as f:
        return f.read().strip()
