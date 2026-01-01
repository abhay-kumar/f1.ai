"""
Shared configuration for F1 short video creator
"""
import os

BASE_DIR = "/Users/abhaykumar/Documents/f1.ai"
PROJECTS_DIR = f"{BASE_DIR}/projects"
SHARED_DIR = f"{BASE_DIR}/shared"

# API Config
ELEVENLABS_KEY_FILE = f"{SHARED_DIR}/creds/elevenlabs"
VOICE_ID = "NNl6r8mD7vthiJatiJt1"  # Bradford - Expressive British
MODEL_ID = "eleven_multilingual_v2"

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
MUSIC_VOLUME = 0.15

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
