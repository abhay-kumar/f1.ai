#!/usr/bin/env python3
"""
Advanced Visual Assembler for Long-Form F1 Content

Creates engaging videos by intelligently blending:
1. YouTube F1 clips as primary visual source
2. High-quality F1 images from Pexels/Unsplash as fallback
3. Quote overlays with speaker images
4. Veo3 AI-generated video for abstract concepts
5. Color grading per-segment (B&W, vintage, cinematic, warm, cool)
6. Transition SFX between segments
7. Animated logo intro

Visual routing based on script content analysis.
YouTube-first approach: downloads real footage matching script descriptions.
"""

import argparse
import hashlib
import json
import multiprocessing
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.color_grader import apply_color_grade, detect_color_grade
from src.config import (
    BACKGROUND_MUSIC,
    BASE_DIR,
    CREDITS_DURATION_LONGFORM,
    LONGFORM_AUDIO_BITRATE,
    LONGFORM_FRAME_RATE,
    LONGFORM_OUTPUT_HEIGHT_4K,
    LONGFORM_OUTPUT_HEIGHT_HD,
    LONGFORM_OUTPUT_WIDTH_4K,
    LONGFORM_OUTPUT_WIDTH_HD,
    MUSIC_VOLUME_ATMOSPHERIC,
    MUSIC_VOLUME_LONGFORM,
    MUSIC_VOLUME_UPLIFTING,
    OUTRO_AUDIO_LONGFORM,
    get_project_dir,
)
from src.intro_generator import create_intro_video
from src.shot_assembler import (
    MIN_SHOT_DURATION_LONGFORM,
    TRANSITION_DEFAULTS,
    TRANSITION_MAP,
    calculate_shot_timings,
    create_shot_clip,
    stitch_shots_with_transitions,
)
from src.shot_assembler import (
    normalize_segment as _normalize_segment,
)

# ============================================================================
# CONFIGURATION
# ============================================================================

MIN_CLIP_DURATION = 3.0  # Minimum seconds per visual
MAX_CLIP_DURATION = 5.0  # Maximum seconds per visual
CROSSFADE_DURATION = 0.5  # Crossfade between clips
API_RATE_LIMIT_DELAY = 0.5  # Seconds between API calls


def get_gpu_encoder() -> Tuple[str, list]:
    """Detect available GPU encoder. Matches video_assembler.py logic."""
    system = platform.system()
    if system == "Darwin":
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True
        )
        if "h264_videotoolbox" in result.stdout:
            return "h264_videotoolbox", ["-allow_sw", "1"]
    elif system in ("Linux", "Windows"):
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True
        )
        if "h264_nvenc" in result.stdout:
            return "h264_nvenc", [
                "-preset",
                "p4",
                "-tune",
                "hq",
                "-rc",
                "vbr",
                "-cq",
                "23",
            ]
    return "libx264", ["-preset", "medium", "-crf", "23"]


GPU_ENCODER, GPU_ENCODER_FLAGS = get_gpu_encoder()


def gpu_enc_args() -> list:
    """Return ffmpeg encoder args: ['-c:v', encoder, ...flags]."""
    return ["-c:v", GPU_ENCODER] + GPU_ENCODER_FLAGS


# Ken Burns effects
KEN_BURNS_EFFECTS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]

# ============================================================================
# VISUAL TYPE DEFINITIONS
# ============================================================================


class VisualType(Enum):
    F1_IMAGE = "f1_image"
    YOUTUBE_CLIP = "youtube_clip"
    QUOTE_OVERLAY = "quote_overlay"
    VEO3_VIDEO = "veo3_video"  # AI-generated video


@dataclass
class VisualDecision:
    primary_type: VisualType
    fallback_type: VisualType
    search_queries: List[str]
    speaker_name: Optional[str] = None
    quote_text: Optional[str] = None
    veo3_prompt: Optional[str] = None  # For AI video generation
    confidence: float = 0.8


# ============================================================================
# F1 KNOWLEDGE BASE
# ============================================================================

F1_DRIVERS = {
    "verstappen": "Max Verstappen",
    "hamilton": "Lewis Hamilton",
    "leclerc": "Charles Leclerc",
    "norris": "Lando Norris",
    "sainz": "Carlos Sainz",
    "russell": "George Russell",
    "perez": "Sergio Perez",
    "alonso": "Fernando Alonso",
    "stroll": "Lance Stroll",
    "ocon": "Esteban Ocon",
    "gasly": "Pierre Gasly",
    "tsunoda": "Yuki Tsunoda",
    "ricciardo": "Daniel Ricciardo",
    "bottas": "Valtteri Bottas",
    "piastri": "Oscar Piastri",
    "lawson": "Liam Lawson",
    "antonelli": "Kimi Antonelli",
    "bearman": "Oliver Bearman",
    "schumacher": "Michael Schumacher",
    "senna": "Ayrton Senna",
    "vettel": "Sebastian Vettel",
    "raikkonen": "Kimi Raikkonen",
    "wolff": "Toto Wolff",
    "horner": "Christian Horner",
    "binotto": "Mattia Binotto",
    "brown": "Zak Brown",
    "newey": "Adrian Newey",
    "brawn": "Ross Brawn",
}

F1_TEAMS = {
    "red bull": "Red Bull Racing",
    "mercedes": "Mercedes F1",
    "ferrari": "Scuderia Ferrari",
    "mclaren": "McLaren F1",
    "aston martin": "Aston Martin F1",
    "alpine": "Alpine F1",
    "williams": "Williams Racing",
    "haas": "Haas F1",
    "sauber": "Sauber F1",
    "rb": "RB F1 Team",
}

FUEL_PARTNERS = {
    "aramco": "Saudi Aramco",
    "shell": "Shell",
    "petronas": "Petronas",
    "mobil": "ExxonMobil",
    "castrol": "Castrol",
    "bp": "BP",
    "gulf": "Gulf Oil",
}

CONCEPT_KEYWORDS = [
    "how",
    "why",
    "explain",
    "concept",
    "basically",
    "essentially",
    "fundamentally",
    "process",
    "mechanism",
    "chemistry",
    "physics",
    "engineering",
    "fischer-tropsch",
    "syngas",
    "catalyst",
    "molecule",
    "carbon capture",
    "efficiency",
    "thermal",
    "combustion",
    "compression ratio",
    "power unit",
    "mgu-h",
    "mgu-k",
    "hybrid",
]

ACTION_KEYWORDS = [
    "race",
    "racing",
    "overtake",
    "crash",
    "pit stop",
    "start",
    "finish",
    "podium",
    "celebration",
    "onboard",
    "battle",
    "wheel to wheel",
    "championship",
    "victory",
    "dramatic",
]

# Keywords that suggest Veo3 AI video would be ideal (abstract/cinematic concepts)
VEO3_KEYWORDS = [
    "future",
    "vision",
    "imagine",
    "revolution",
    "transformation",
    "evolution",
    "innovation",
    "breakthrough",
    "paradigm",
    "frontier",
    "molecular",
    "atomic",
    "chemical reaction",
    "synthesis",
    "production facility",
    "industrial",
    "manufacturing",
    "wind tunnel",
    "aerodynamic",
    "simulation",
]

# Veo3 prompt templates for common F1 scenarios
VEO3_PROMPTS = {
    "fuel_production": "Industrial fuel production facility with advanced chemistry equipment, glowing reactors, sustainable energy, futuristic laboratory",
    "carbon_capture": "Carbon capture technology visualization, CO2 molecules being absorbed, green industrial facility, environmental technology",
    "engine_tech": "Formula 1 power unit internal visualization, turbo spinning, energy flow through MGU-K, high-tech engineering",
    "wind_tunnel": "F1 car in wind tunnel, smoke particles flowing over aerodynamic bodywork, technical testing facility",
    "chemistry": "Chemical synthesis process visualization, molecular bonds forming, laboratory equipment, scientific innovation",
    "factory": "High-tech F1 factory floor, carbon fiber components being manufactured, robotic precision, clean room environment",
    "data_analysis": "F1 data analysis visualization, telemetry streams, holographic displays, race strategy simulation",
    "sustainable": "Sustainable energy technology, green fuel production, environmental innovation, clean energy future",
}

# ============================================================================
# GLOBAL CACHES
# ============================================================================

_IMAGE_CACHE: Dict[str, List[str]] = {}
_LAST_API_CALL = 0


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_duration(file_path: str) -> float:
    """Get duration of media file in seconds."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0


def get_api_key(name: str) -> Optional[str]:
    """Load API key from shared/creds folder."""
    creds_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "shared",
        "creds",
        name,
    )
    if os.path.exists(creds_path):
        with open(creds_path) as f:
            return f.read().strip()
    return os.environ.get(f"{name.upper()}_API_KEY")


def download_file(url: str, output_path: str, timeout: int = 30) -> bool:
    """Download a file from URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception:
        return False


# ============================================================================
# VISUAL ROUTING - Decides what visual type to use
# ============================================================================


def detect_quote(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect if text contains a quote and extract speaker name."""
    speaker = None
    quote = None

    # Quote patterns
    quote_match = re.search(r'"([^"]{20,})"', text)
    if quote_match:
        quote = quote_match.group(1)

    # Speaker patterns
    speaker_patterns = [
        r"([A-Z][a-z]+ [A-Z][a-z]+) (?:said|stated|explained|mentioned|noted)",
        r"(?:said|stated|explained) ([A-Z][a-z]+ [A-Z][a-z]+)",
        r"as ([A-Z][a-z]+ [A-Z][a-z]+) (?:put it|noted|explained)",
        r"according to ([A-Z][a-z]+ [A-Z][a-z]+)",
    ]

    for pattern in speaker_patterns:
        match = re.search(pattern, text)
        if match:
            speaker = match.group(1)
            break

    # Check for known F1 figures
    if not speaker:
        text_lower = text.lower()
        for key, name in F1_DRIVERS.items():
            if key in text_lower and any(
                w in text_lower for w in ["said", "stated", "explained", "according"]
            ):
                speaker = name
                break

    return speaker, quote


def detect_f1_entities(text: str) -> Dict[str, List[str]]:
    """Detect F1-related entities in text."""
    text_lower = text.lower()
    entities = {"drivers": [], "teams": [], "fuel_partners": []}

    for key, name in F1_DRIVERS.items():
        if key in text_lower:
            entities["drivers"].append(name)

    for key, name in F1_TEAMS.items():
        if key in text_lower:
            entities["teams"].append(name)

    for key, name in FUEL_PARTNERS.items():
        if key in text_lower:
            entities["fuel_partners"].append(name)

    return entities


def get_veo3_prompt(text: str, context: str) -> Optional[str]:
    """Generate an appropriate Veo3 prompt based on content."""
    text_lower = f"{text} {context}".lower()

    # Check for matching templates
    if any(
        kw in text_lower
        for kw in ["fuel production", "sustainable fuel", "synthetic fuel"]
    ):
        return VEO3_PROMPTS["fuel_production"]
    if any(kw in text_lower for kw in ["carbon capture", "co2", "carbon dioxide"]):
        return VEO3_PROMPTS["carbon_capture"]
    if any(kw in text_lower for kw in ["power unit", "engine", "mgu", "turbo"]):
        return VEO3_PROMPTS["engine_tech"]
    if any(kw in text_lower for kw in ["wind tunnel", "aerodynamic", "downforce"]):
        return VEO3_PROMPTS["wind_tunnel"]
    if any(
        kw in text_lower
        for kw in ["chemistry", "chemical", "molecule", "synthesis", "fischer-tropsch"]
    ):
        return VEO3_PROMPTS["chemistry"]
    if any(kw in text_lower for kw in ["factory", "manufacturing", "production"]):
        return VEO3_PROMPTS["factory"]
    if any(kw in text_lower for kw in ["data", "telemetry", "analysis", "strategy"]):
        return VEO3_PROMPTS["data_analysis"]
    if any(
        kw in text_lower for kw in ["sustainable", "green", "environment", "future"]
    ):
        return VEO3_PROMPTS["sustainable"]

    return None


def route_visual(segment: Dict, use_veo3: bool = True) -> VisualDecision:
    """Determine the best visual type for a segment.

    YouTube-first approach: most segments use YouTube clips as primary source.
    F1 images (Pexels/Unsplash) serve as fallback when YouTube clips aren't found.
    """
    text = segment.get("text", "")
    context = segment.get("context", "")
    footage_query = segment.get("footage_query", "")
    image_query = segment.get("image_query", "")

    combined_text = f"{text} {context} {footage_query}"
    text_lower = combined_text.lower()

    # Check for quotes first
    speaker, quote = detect_quote(text)
    if speaker and quote:
        return VisualDecision(
            primary_type=VisualType.QUOTE_OVERLAY,
            fallback_type=VisualType.F1_IMAGE,
            search_queries=[f"{speaker} F1", f"{speaker} portrait"],
            speaker_name=speaker,
            quote_text=quote,
            confidence=0.95,
        )

    # Detect F1 entities
    entities = detect_f1_entities(combined_text)

    # Build search queries — prefer footage_query, then image_query
    search_queries = []
    if footage_query and not footage_query.startswith("GRAPHIC:"):
        search_queries.append(footage_query)
    if image_query:
        search_queries.append(image_query)

    for driver in entities["drivers"][:2]:
        search_queries.append(f"{driver} F1 2024")
    for team in entities["teams"][:2]:
        search_queries.append(f"{team} F1 car")
    for partner in entities["fuel_partners"][:1]:
        search_queries.append(f"{partner} F1")

    is_veo3_suitable = any(kw in text_lower for kw in VEO3_KEYWORDS)
    has_f1_content = any(entities[k] for k in entities)

    # Check for Veo3-suitable content (abstract concepts, visualizations)
    if use_veo3 and is_veo3_suitable and not has_f1_content:
        veo3_prompt = get_veo3_prompt(text, context)
        if veo3_prompt:
            return VisualDecision(
                primary_type=VisualType.VEO3_VIDEO,
                fallback_type=VisualType.F1_IMAGE,
                search_queries=search_queries or ["F1 technology"],
                veo3_prompt=veo3_prompt,
                confidence=0.85,
            )

    # Default: YouTube clips as primary, F1 images as fallback
    return VisualDecision(
        primary_type=VisualType.YOUTUBE_CLIP,
        fallback_type=VisualType.F1_IMAGE,
        search_queries=search_queries
        or [f"F1 {context}" if context else "Formula 1 racing"],
        confidence=0.8,
    )


# ============================================================================
# IMAGE FETCHING - Multiple sources for best F1 images
# ============================================================================


def search_images_pexels(query: str, num_images: int = 5) -> List[str]:
    """Search Pexels for images."""
    global _LAST_API_CALL

    cache_key = f"pexels_{query}_{num_images}"
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    api_key = get_api_key("pexels")
    if not api_key:
        return []

    # Rate limiting
    elapsed = time.time() - _LAST_API_CALL
    if elapsed < API_RATE_LIMIT_DELAY:
        time.sleep(API_RATE_LIMIT_DELAY - elapsed)

    urls = []
    try:
        search_url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page={num_images}&orientation=landscape"
        req = urllib.request.Request(
            search_url,
            headers={
                "Authorization": api_key,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            },
        )

        _LAST_API_CALL = time.time()

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())

        for photo in data.get("photos", []):
            urls.append(photo["src"]["large2x"])

        _IMAGE_CACHE[cache_key] = urls
    except Exception:
        pass

    return urls


def search_images_unsplash(query: str, num_images: int = 5) -> List[str]:
    """Search Unsplash for images."""
    global _LAST_API_CALL

    cache_key = f"unsplash_{query}_{num_images}"
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    api_key = get_api_key("unsplash")
    if not api_key:
        return []

    elapsed = time.time() - _LAST_API_CALL
    if elapsed < API_RATE_LIMIT_DELAY:
        time.sleep(API_RATE_LIMIT_DELAY - elapsed)

    urls = []
    try:
        search_url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(query)}&per_page={num_images}&orientation=landscape"
        req = urllib.request.Request(
            search_url,
            headers={
                "Authorization": f"Client-ID {api_key}",
                "User-Agent": "Mozilla/5.0",
            },
        )

        _LAST_API_CALL = time.time()

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())

        for photo in data.get("results", []):
            urls.append(photo["urls"]["regular"])

        _IMAGE_CACHE[cache_key] = urls
    except Exception:
        pass

    return urls


def search_f1_images(queries: List[str], num_per_query: int = 3) -> List[str]:
    """
    Search for F1 images from multiple sources.
    Prioritizes quality and relevance.
    """
    all_urls = []

    for query in queries[:4]:  # Limit queries
        # Add F1-specific terms for better results
        f1_query = f"{query} Formula 1" if "f1" not in query.lower() else query

        # Try Pexels first (better for racing/cars)
        urls = search_images_pexels(f1_query, num_per_query)
        all_urls.extend(urls)

        # Try Unsplash as backup
        if len(urls) < num_per_query:
            unsplash_urls = search_images_unsplash(f1_query, num_per_query - len(urls))
            all_urls.extend(unsplash_urls)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


# ============================================================================
# YOUTUBE CLIP FETCHING
# ============================================================================


def search_youtube_f1_clips(query: str, max_results: int = 3) -> List[Dict]:
    """Search YouTube for F1 clips, prioritizing official F1 channel."""
    try:
        # Add F1 to query for better results
        search_query = f"F1 {query}" if "f1" not in query.lower() else query

        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--no-check-formats",
            "--print",
            "%(id)s|%(title)s|%(duration)s|%(channel)s",
            f"ytsearch{max_results * 2}:{search_query}",
            "--no-warnings",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)

        clips = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 4:
                    video_id, title, duration_str, channel = parts[:4]
                    try:
                        duration = (
                            float(duration_str)
                            if duration_str and duration_str != "NA"
                            else 60
                        )
                    except ValueError:
                        duration = 60

                    # Skip very long videos
                    if duration > 600:
                        continue

                    # Prioritize official F1 content
                    priority = 0
                    if "formula 1" in channel.lower() or "f1" in channel.lower():
                        priority = 2
                    elif "motorsport" in channel.lower() or "racing" in channel.lower():
                        priority = 1

                    clips.append(
                        {
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "title": title,
                            "duration": duration,
                            "channel": channel,
                            "priority": priority,
                        }
                    )

        # Sort by priority (official F1 content first)
        clips.sort(key=lambda x: -x["priority"])
        return clips[:max_results]

    except Exception as e:
        print(f"    YouTube search error: {e}")
        return []


def download_youtube_clip(
    url: str, output_path: str, start_time: int = 10, duration: int = 10
) -> bool:
    """Download a short clip from YouTube with speed optimizations."""
    try:
        cmd = [
            "yt-dlp",
            "-f",
            "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]",
            "--merge-output-format",
            "mp4",
            "--no-check-formats",
            "--concurrent-fragments",
            "4",
            "--extractor-args",
            "youtube:player_client=web",
            "-o",
            output_path,
            "--download-sections",
            f"*{start_time}-{start_time + duration}",
            "--no-playlist",
            "--no-warnings",
            "--quiet",
            url,
        ]

        subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 10000
    except Exception:
        return False


# ============================================================================
# QUOTE OVERLAY GENERATION
# ============================================================================


def search_person_image(name: str) -> Optional[str]:
    """Search for an image of a specific person."""
    queries = [f"{name} portrait", f"{name} F1", f"{name} Formula 1"]

    for query in queries:
        urls = search_images_pexels(query, 2)
        if urls:
            return urls[0]

        urls = search_images_unsplash(query, 2)
        if urls:
            return urls[0]

    return None


def create_quote_overlay_clip(
    audio_path: str,
    output_path: str,
    quote_text: str,
    speaker_name: str,
    speaker_image_url: Optional[str],
    work_dir: str,
    width: int,
    height: int,
) -> bool:
    """Create a clip showing a quote with speaker's image."""
    duration = get_duration(audio_path)
    if duration <= 0:
        return False

    # Download speaker image or use placeholder
    speaker_img_path = os.path.join(work_dir, "speaker.jpg")
    if speaker_image_url:
        download_file(speaker_image_url, speaker_img_path)

    has_speaker_image = (
        os.path.exists(speaker_img_path) and os.path.getsize(speaker_img_path) > 1000
    )

    fps = LONGFORM_FRAME_RATE
    f1_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"
    regular_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Regular.ttf"

    # Font sizes based on resolution
    if width >= 3840:
        quote_size, name_size = 56, 40
    else:
        quote_size, name_size = 36, 28

    # Wrap quote text (max ~50 chars per line)
    words = quote_text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= 50:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    wrapped_quote = "\\n".join(lines)

    if has_speaker_image:
        # Create with speaker image on left, quote on right
        img_size = int(height * 0.5)
        img_x = int(width * 0.08)
        img_y = int((height - img_size) / 2)
        text_x = int(width * 0.4)
        text_y = int(height * 0.35)
        name_y = int(height * 0.65)

        filter_complex = (
            f"[0:v]scale={img_size}:{img_size}:force_original_aspect_ratio=decrease,"
            f"pad={img_size}:{img_size}:(ow-iw)/2:(oh-ih)/2:black[speaker];"
            f"color=c=#1a1a1a:s={width}x{height}:d={duration}:r={fps}[bg];"
            f"[bg][speaker]overlay={img_x}:{img_y},"
            f"drawtext=text='\"'{wrapped_quote}'\"':"
            f"fontfile={regular_font}:fontsize={quote_size}:"
            f"fontcolor=white:x={text_x}:y={text_y}:line_spacing=20,"
            f"drawtext=text='— {speaker_name}':"
            f"fontfile={f1_font}:fontsize={name_size}:"
            f"fontcolor=#E8002D:x={text_x}:y={name_y},"
            f"format=yuv420p[outv]"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            speaker_img_path,
            "-i",
            audio_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",
            "-map",
            "1:a",
            *gpu_enc_args(),
            "-c:a",
            "aac",
            "-b:a",
            LONGFORM_AUDIO_BITRATE,
            "-t",
            str(duration),
            output_path,
        ]
    else:
        # Quote-only overlay (no speaker image)
        text_y = int(height * 0.4)
        name_y = int(height * 0.6)

        filter_complex = (
            f"color=c=#1a1a1a:s={width}x{height}:d={duration}:r={fps},"
            f"drawtext=text='\"'{wrapped_quote}'\"':"
            f"fontfile={regular_font}:fontsize={quote_size}:"
            f"fontcolor=white:x=(w-text_w)/2:y={text_y}:line_spacing=20,"
            f"drawtext=text='— {speaker_name}':"
            f"fontfile={f1_font}:fontsize={name_size}:"
            f"fontcolor=#E8002D:x=(w-text_w)/2:y={name_y},"
            f"format=yuv420p[outv]"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=#1a1a1a:s={width}x{height}:d={duration}:r={fps}",
            "-i",
            audio_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",
            "-map",
            "1:a",
            *gpu_enc_args(),
            "-c:a",
            "aac",
            "-b:a",
            LONGFORM_AUDIO_BITRATE,
            "-t",
            str(duration),
            output_path,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


# ============================================================================
# VIDEO CLIP CREATION (Ken Burns effect on images)
# ============================================================================


def create_image_clip(
    image_path: str,
    output_path: str,
    duration: float,
    width: int,
    height: int,
    effect: str = "zoom_in",
) -> bool:
    """Create a video clip from an image with simple scale effect.

    Uses scale+crop instead of zoompan to minimize memory usage.
    """
    fps = LONGFORM_FRAME_RATE

    # Simple approach: scale image to fill frame, hold for duration
    # This is far more memory-efficient than zoompan
    filter_complex = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"setsar=1,format=yuv420p"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        image_path,
        "-vf",
        filter_complex,
        "-t",
        str(duration),
        "-r",
        str(fps),
        *gpu_enc_args(),
        "-pix_fmt",
        "yuv420p",
        "-an",
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


def process_video_clip(
    input_path: str,
    output_path: str,
    duration: float,
    width: int,
    height: int,
    start_time: float = 0,
) -> bool:
    """Process a video clip to match target resolution and duration."""
    filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1,format=yuv420p"

    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start_time),
        "-i",
        input_path,
        "-t",
        str(duration),
        "-vf",
        filter_complex,
        *gpu_enc_args(),
        "-an",
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


# ============================================================================
# SEGMENT ASSEMBLY - Combines multiple visual sources
# ============================================================================


def _create_multishot_longform_segment(
    segment_idx: int,
    segment: Dict,
    audio_path: str,
    audio_duration: float,
    segment_work_dir: str,
    output_path: str,
    width: int,
    height: int,
) -> Tuple[bool, str, str]:
    """Create a long-form segment from multiple shots with transitions.

    Each shot is rendered as a separate clip based on its source_type,
    then stitched together with specified transitions. Audio is added last.

    Returns: (success, error_message, visual_type_used)
    """
    shots = segment["shots"]
    footage_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(segment_work_dir.rstrip("/")))),
        "footage",
    )
    footage_dir = os.path.normpath(footage_dir)

    # Calculate timing for each shot from text_cue positions
    shot_timings = calculate_shot_timings(
        segment.get("text", ""), shots, audio_duration, MIN_SHOT_DURATION_LONGFORM
    )

    # Create each shot as a separate clip
    shot_clips = []
    successful_shots = []
    successful_timings = []
    visual_types_used = set()

    for shot_idx, (shot, (start_time, end_time)) in enumerate(zip(shots, shot_timings)):
        shot_duration = end_time - start_time
        clip_path = os.path.join(segment_work_dir, f"shot_{shot_idx:02d}.mp4")

        # Fill in missing footage field using naming convention
        if not shot.get("footage"):
            from shot_assembler import get_shot_source_ext, shot_footage_filename

            ext = get_shot_source_ext(shot.get("source_type", "youtube_clip"))
            convention_name = shot_footage_filename(segment_idx, shot_idx, ext)
            convention_path = os.path.join(footage_dir, convention_name)
            if os.path.exists(convention_path):
                shot["footage"] = convention_name
            # Fallback: segment-level footage (for single-shot normalized segments)
            elif segment.get("footage") and os.path.exists(
                os.path.join(footage_dir, segment["footage"])
            ):
                shot["footage"] = segment["footage"]

        success = create_shot_clip(
            shot=shot,
            clip_path=clip_path,
            duration=shot_duration,
            footage_dir=footage_dir,
            width=width,
            height=height,
            is_shorts=False,
            gpu_encoder=GPU_ENCODER,
            gpu_flags=GPU_ENCODER_FLAGS,
        )

        if success:
            # Apply per-shot color grading if specified
            color_grade = shot.get("color_grade")
            if not color_grade:
                color_grade = detect_color_grade(shot)
            if color_grade and color_grade != "none":
                graded_path = clip_path.replace(".mp4", "_graded.mp4")
                if apply_color_grade(clip_path, graded_path, color_grade):
                    os.replace(graded_path, clip_path)

            shot_clips.append(clip_path)
            successful_shots.append(shot)
            successful_timings.append((start_time, end_time))
            visual_types_used.add(shot.get("source_type", "youtube_clip"))
        else:
            print(
                f"      Shot {shot_idx} failed ({shot.get('label', 'unknown')}), skipping"
            )

    if not shot_clips:
        return False, "No shot clips created", ""

    # Stitch shots together
    if len(shot_clips) == 1:
        stitched_path = shot_clips[0]
    else:
        stitched_path = os.path.join(segment_work_dir, "stitched.mp4")
        success = stitch_shots_with_transitions(
            clip_paths=shot_clips,
            shots=successful_shots,
            shot_timings=successful_timings,
            output_path=stitched_path,
            gpu_encoder=GPU_ENCODER,
            gpu_flags=GPU_ENCODER_FLAGS,
        )
        if not success:
            return False, "Failed to stitch shots", ""

    # Add audio
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        stitched_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        LONGFORM_AUDIO_BITRATE,
        "-t",
        str(audio_duration),
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(output_path):
        vt = "+".join(sorted(visual_types_used)) if visual_types_used else "multi_shot"
        return True, "", vt

    return False, "Failed to add audio to multi-shot segment", ""


def create_segment_video(
    segment_idx: int,
    segment: Dict,
    audio_path: str,
    work_dir: str,
    output_path: str,
    width: int,
    height: int,
    use_veo3: bool = False,
    use_yt_search: bool = True,
) -> Tuple[bool, str, str]:
    """
    Create a segment video by intelligently blending visual sources.
    YouTube-first: tries YouTube clips, falls back to F1 images.

    Supports multi-shot segments: if the segment has a 'shots' array with
    more than one shot, each shot is rendered individually and stitched with
    specified transitions. This replaces the mechanical 3-5 second clip splitting
    with content-driven visual changes.

    Returns: (success, error_message, visual_type_used)
    """
    audio_duration = get_duration(audio_path)
    if audio_duration <= 0:
        return False, "Invalid audio duration", ""

    segment_work_dir = os.path.join(work_dir, f"segment_{segment_idx:02d}")
    os.makedirs(segment_work_dir, exist_ok=True)

    # Multi-shot path: content-driven visual changes
    has_shots = "shots" in segment and len(segment.get("shots", [])) > 1
    if has_shots:
        result = _create_multishot_longform_segment(
            segment_idx,
            segment,
            audio_path,
            audio_duration,
            segment_work_dir,
            output_path,
            width,
            height,
        )
        if result[0]:
            return result
        print(f"      Multi-shot failed, falling back to auto-routing...")

    # Get visual routing decision (single-shot / legacy path)
    decision = route_visual(segment, use_veo3=use_veo3)
    visual_type_used = decision.primary_type.value

    # Handle quote overlays
    if (
        decision.primary_type == VisualType.QUOTE_OVERLAY
        and decision.speaker_name
        and decision.quote_text
    ):
        speaker_image_url = search_person_image(decision.speaker_name)
        success = create_quote_overlay_clip(
            audio_path,
            output_path,
            decision.quote_text,
            decision.speaker_name,
            speaker_image_url,
            segment_work_dir,
            width,
            height,
        )
        if success:
            return True, "", "quote_overlay"

    # Handle Veo3 AI-generated video
    if (
        decision.primary_type == VisualType.VEO3_VIDEO
        and decision.veo3_prompt
        and use_veo3
    ):
        try:
            from src.veo3_generator import (
                generate_f1_scene,
                is_veo3_available,
                process_veo3_video,
            )

            available, msg = is_veo3_available()
            if available:
                veo3_raw = os.path.join(segment_work_dir, "veo3_raw.mp4")
                veo3_processed = os.path.join(segment_work_dir, "veo3_clip.mp4")

                success, error = generate_f1_scene(
                    decision.veo3_prompt,
                    veo3_raw,
                    duration=8,
                    width=width,
                    height=height,
                    use_fast=True,
                )

                if success:
                    if process_veo3_video(
                        veo3_raw, veo3_processed, audio_duration, width, height
                    ):
                        cmd = [
                            "ffmpeg",
                            "-y",
                            "-i",
                            veo3_processed,
                            "-i",
                            audio_path,
                            "-c:v",
                            "copy",
                            "-c:a",
                            "aac",
                            "-b:a",
                            LONGFORM_AUDIO_BITRATE,
                            "-shortest",
                            output_path,
                        ]
                        subprocess.run(cmd, capture_output=True, text=True)
                        if os.path.exists(output_path):
                            return True, "", "veo3_video"
                else:
                    print(f"      Veo3 failed: {error}, trying fallback...")
        except ImportError:
            print("      Veo3 module not available, using fallback...")

    # Calculate how many clips we need (change visuals every 3-5 seconds)
    num_clips = max(2, int(audio_duration / MAX_CLIP_DURATION) + 1)
    clip_duration = audio_duration / num_clips

    # Gather visuals — YouTube first, then F1 images as fallback
    clip_files = []
    effect_idx = 0

    # Use pre-downloaded footage if available (from footage_downloader.py)
    footage_file = segment.get("footage")
    if footage_file:
        project_dir = os.path.dirname(os.path.dirname(segment_work_dir.rstrip("/")))
        # Walk up from work_dir to project dir
        footage_path = os.path.join(
            os.path.dirname(work_dir.rstrip("/")),  # temp/
            "..",  # project dir
            "footage",
            footage_file,
        )
        footage_path = os.path.normpath(footage_path)
        if os.path.exists(footage_path):
            clip_path = os.path.join(segment_work_dir, "clip_00.mp4")
            start_time = segment.get("footage_start", 0)
            if process_video_clip(
                footage_path,
                clip_path,
                audio_duration,
                width,
                height,
                start_time=start_time,
            ):
                clip_files.append(clip_path)
                visual_type_used = "pre_downloaded"

    # Try YouTube clips if no pre-downloaded footage and YouTube routing decided
    if (
        not clip_files
        and use_yt_search
        and (
            decision.primary_type == VisualType.YOUTUBE_CLIP
            or decision.fallback_type == VisualType.YOUTUBE_CLIP
        )
    ):
        for query in decision.search_queries[:1]:
            if len(clip_files) >= num_clips:
                break
            clips = search_youtube_f1_clips(query, 1)
            for clip_info in clips[:1]:
                if len(clip_files) >= num_clips:
                    break
                clip_idx = len(clip_files)
                raw_path = os.path.join(segment_work_dir, f"yt_raw_{clip_idx}.mp4")
                clip_path = os.path.join(segment_work_dir, f"clip_{clip_idx:02d}.mp4")
                this_duration = (
                    clip_duration
                    if clip_idx < num_clips - 1
                    else audio_duration - clip_idx * clip_duration
                )

                start_time = segment.get("footage_start", 15)
                if download_youtube_clip(
                    clip_info["url"],
                    raw_path,
                    start_time=start_time,
                    duration=int(this_duration) + 3,
                ):
                    if process_video_clip(
                        raw_path, clip_path, this_duration, width, height
                    ):
                        clip_files.append(clip_path)
                        visual_type_used = "youtube_clip"
                    # Clean up raw download to free memory
                    if os.path.exists(raw_path):
                        os.remove(raw_path)

    # Fallback: F1 images with Ken Burns effects (skip if we have pre-downloaded footage)
    if len(clip_files) < num_clips and visual_type_used != "pre_downloaded":
        image_urls = search_f1_images(decision.search_queries, num_per_query=4)

        for i, url in enumerate(image_urls):
            if len(clip_files) >= num_clips:
                break

            clip_idx = len(clip_files)
            img_path = os.path.join(segment_work_dir, f"img_{clip_idx:02d}.jpg")
            clip_path = os.path.join(segment_work_dir, f"clip_{clip_idx:02d}.mp4")
            this_duration = (
                clip_duration
                if clip_idx < num_clips - 1
                else audio_duration - clip_idx * clip_duration
            )

            if download_file(url, img_path):
                effect = KEN_BURNS_EFFECTS[effect_idx % len(KEN_BURNS_EFFECTS)]
                effect_idx += 1
                if create_image_clip(
                    img_path, clip_path, this_duration, width, height, effect
                ):
                    clip_files.append(clip_path)
                    if visual_type_used == "youtube_clip":
                        visual_type_used = "youtube_clip+f1_image"
                    else:
                        visual_type_used = "f1_image"

    if not clip_files:
        return False, "No visuals created", ""

    # If only one clip, add audio and done
    if len(clip_files) == 1:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            clip_files[0],
            "-i",
            audio_path,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            LONGFORM_AUDIO_BITRATE,
            "-shortest",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, text=True)
        return os.path.exists(output_path), "", visual_type_used

    # Create crossfade transitions
    xfade_duration = min(CROSSFADE_DURATION, clip_duration / 4)
    inputs = []
    for clip in clip_files:
        inputs.extend(["-i", clip])

    # Build xfade chain
    if len(clip_files) == 2:
        offset = clip_duration - xfade_duration
        filter_complex = f"[0:v][1:v]xfade=transition=fade:duration={xfade_duration}:offset={offset},format=yuv420p[outv]"
    else:
        current_offset = clip_duration - xfade_duration
        filter_complex = f"[0:v][1:v]xfade=transition=fade:duration={xfade_duration}:offset={current_offset}[v1]"
        for i in range(2, len(clip_files)):
            current_offset += clip_duration - xfade_duration
            if i == len(clip_files) - 1:
                filter_complex += f";[v{i - 1}][{i}:v]xfade=transition=fade:duration={xfade_duration}:offset={current_offset},format=yuv420p[outv]"
            else:
                filter_complex += f";[v{i - 1}][{i}:v]xfade=transition=fade:duration={xfade_duration}:offset={current_offset}[v{i}]"

    temp_video = os.path.join(segment_work_dir, "temp_video.mp4")
    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",
            *gpu_enc_args(),
            temp_video,
        ]
    )

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not os.path.exists(temp_video):
        # Fallback: simple concat
        concat_file = os.path.join(segment_work_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for clip in clip_files:
                f.write(f"file '{clip}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            *gpu_enc_args(),
            temp_video,
        ]
        subprocess.run(cmd, capture_output=True, text=True)

    if not os.path.exists(temp_video):
        return False, "Failed to create transition video", ""

    # Add audio
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        temp_video,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        LONGFORM_AUDIO_BITRATE,
        "-t",
        str(audio_duration),
        "-shortest",
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(output_path):
        return True, "", visual_type_used

    return False, "Failed to add audio", ""


# ============================================================================
# TRANSITION SFX
# ============================================================================

SFX_SWOOSH = os.path.join(BASE_DIR, "shared", "sfx", "swoosh.mp3")
SFX_FADE = os.path.join(BASE_DIR, "shared", "sfx", "fade.mp3")


def add_transition_sfx(
    video_path: str,
    output_path: str,
    segment_durations: List[float],
    sfx_path: str = SFX_SWOOSH,
    sfx_volume: float = 0.6,
) -> bool:
    """Overlay transition SFX at each segment boundary.

    Args:
        video_path: Input video with audio
        output_path: Output video with SFX overlaid
        segment_durations: List of durations for each segment (to calculate boundaries)
        sfx_path: Path to the SFX audio file
        sfx_volume: Volume multiplier for SFX (0.0-1.0)

    Returns:
        True if SFX was applied successfully
    """
    if not os.path.exists(sfx_path):
        subprocess.run(["cp", video_path, output_path])
        return True

    # Calculate boundary timestamps (skip first and last)
    boundaries = []
    cumulative = 0.0
    for dur in segment_durations[:-1]:  # Skip last segment (no transition after it)
        cumulative += dur
        boundaries.append(cumulative)

    if not boundaries:
        subprocess.run(["cp", video_path, output_path])
        return True

    # Build FFmpeg filter: overlay SFX at each boundary
    # Input 0 = video, Input 1 = SFX file
    # For each boundary, delay the SFX and mix it in
    sfx_duration = get_duration(sfx_path)
    delay_filters = []
    mix_labels = ["[orig]"]

    for i, ts in enumerate(boundaries):
        # Offset SFX to start slightly before the boundary for smooth transition
        offset_ms = max(0, int((ts - sfx_duration / 2) * 1000))
        delay_filters.append(
            f"[1:a]adelay={offset_ms}|{offset_ms},volume={sfx_volume}[sfx{i}]"
        )
        mix_labels.append(f"[sfx{i}]")

    filter_parts = [f"[0:a]aformat=channel_layouts=stereo[orig]"]
    filter_parts.extend(delay_filters)
    filter_parts.append(
        f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=0:normalize=0[aout]"
    )
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        sfx_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        LONGFORM_AUDIO_BITRATE,
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 1000


# ============================================================================
# OUTRO AND MUSIC
# ============================================================================


def create_outro_video(output_path: str, width: int, height: int) -> bool:
    """Create outro video with credits."""
    if not os.path.exists(OUTRO_AUDIO_LONGFORM):
        return False

    outro_duration = get_duration(OUTRO_AUDIO_LONGFORM)
    f1_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"

    if width >= 3840:
        title_size, channel_size, cta_size = 72, 96, 48
    else:
        title_size, channel_size, cta_size = 48, 64, 32

    center_y = int(height * 0.45)
    cta_y = int(height * 0.58)

    filter_complex = (
        f"color=black:s={width}x{height}:d={outro_duration}:r={LONGFORM_FRAME_RATE},"
        f"format=yuv420p,"
        f"drawtext=text='Sources & References in Description':"
        f"fontfile={f1_font}:fontsize={title_size}:"
        f"fontcolor=white:x=(w-text_w)/2:y={center_y}:"
        f"enable='lt(t,{CREDITS_DURATION_LONGFORM})',"
        f"drawtext=text='F1 BURNOUTS':"
        f"fontfile={f1_font}:fontsize={channel_size}:"
        f"fontcolor=#E8002D:x=(w-text_w)/2:y={center_y}:"
        f"enable='gte(t,{CREDITS_DURATION_LONGFORM})',"
        f"drawtext=text='LIKE • SUBSCRIBE • BELL':"
        f"fontfile={f1_font}:fontsize={cta_size}:"
        f"fontcolor=white:x=(w-text_w)/2:y={cta_y}:"
        f"enable='gte(t,{CREDITS_DURATION_LONGFORM})'[outv]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=black:s={width}x{height}:d={outro_duration}:r={LONGFORM_FRAME_RATE}",
        "-i",
        OUTRO_AUDIO_LONGFORM,
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        "1:a",
        *gpu_enc_args(),
        "-c:a",
        "aac",
        "-b:a",
        LONGFORM_AUDIO_BITRATE,
        "-t",
        str(outro_duration),
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


def detect_music_mood(segment: Dict) -> str:
    """Detect the music mood for a segment based on context keywords."""
    # Check explicit override
    explicit = segment.get("music_mood", "").strip().lower()
    if explicit in ("uplifting", "atmospheric", "default"):
        return explicit

    context = segment.get("context", "").lower()
    section = segment.get("section", "").lower()
    text = segment.get("text", "").lower()
    combined = f"{context} {section} {text}"

    uplifting_keywords = [
        "celebration",
        "victory",
        "joy",
        "triumph",
        "uplifting",
        "positive",
        "success",
        "achievement",
        "proud",
        "exciting",
        "winner",
        "champion",
        "podium",
        "feel good",
    ]
    atmospheric_keywords = [
        "history",
        "historical",
        "legacy",
        "classic",
        "origins",
        "technical",
        "engineering",
        "regulation",
        "specification",
        "analysis",
        "data",
        "quiet",
        "reflective",
        "contemplative",
    ]

    uplifting_score = sum(1 for kw in uplifting_keywords if kw in combined)
    atmospheric_score = sum(1 for kw in atmospheric_keywords if kw in combined)

    if uplifting_score > atmospheric_score and uplifting_score > 0:
        return "uplifting"
    elif atmospheric_score > uplifting_score and atmospheric_score > 0:
        return "atmospheric"
    return "default"


def add_background_music(
    video_path: str,
    output_path: str,
    music_volume: float = MUSIC_VOLUME_LONGFORM,
    segment_volumes: Optional[List[Tuple[float, float, float]]] = None,
) -> bool:
    """Mix background music under video audio with dynamic volume.

    Args:
        video_path: Input video
        output_path: Output with music
        music_volume: Base volume (used if no segment_volumes)
        segment_volumes: List of (start_time, end_time, volume) for per-segment volume
    """
    if not os.path.exists(BACKGROUND_MUSIC):
        subprocess.run(["cp", video_path, output_path])
        return True

    video_duration = get_duration(video_path)

    if segment_volumes:
        # Build dynamic volume expression using enable= clauses
        # Each segment gets its own volume level
        vol_parts = []
        for start, end, vol in segment_volumes:
            vol_parts.append(f"volume={vol}:enable='between(t,{start:.2f},{end:.2f})'")

        # Chain volume filters with commas
        volume_chain = ",".join(vol_parts)

        filter_complex = (
            f"[0:a]aformat=channel_layouts=stereo[voice];"
            f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{video_duration},"
            f"afade=t=in:st=0:d=3,afade=t=out:st={video_duration - 3}:d=3,"
            f"{volume_chain}[music];"
            f"[voice][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
        )
    else:
        filter_complex = (
            f"[0:a]aformat=channel_layouts=stereo[voice];"
            f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{video_duration},"
            f"afade=t=in:st=0:d=3,afade=t=out:st={video_duration - 3}:d=3,"
            f"volume={music_volume}[music];"
            f"[voice][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
        )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        BACKGROUND_MUSIC,
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        LONGFORM_AUDIO_BITRATE,
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


def generate_srt_captions(script: Dict, audio_dir: str, output_path: str) -> bool:
    """Generate SRT caption file."""
    segments = script.get("segments", [])
    srt_content = []
    current_time = 0.0

    for i, segment in enumerate(segments):
        audio_file = f"{audio_dir}/segment_{i:02d}.mp3"
        duration = (
            get_duration(audio_file)
            if os.path.exists(audio_file)
            else len(segment["text"].split()) / 2.5
        )

        start_time = current_time
        end_time = current_time + duration

        def fmt(s):
            h, m = int(s // 3600), int((s % 3600) // 60)
            return f"{h:02d}:{m:02d}:{s % 60:06.3f}".replace(".", ",")

        srt_content.extend(
            [str(i + 1), f"{fmt(start_time)} --> {fmt(end_time)}", segment["text"], ""]
        )
        current_time = end_time

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_content))
    return True


# ============================================================================
# MAIN
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Advanced Visual Assembler for F1 Videos"
    )
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument(
        "--resolution",
        choices=["4k", "hd"],
        default="4k",
        help="Output resolution (default: 4k)",
    )
    parser.add_argument("--no-music", action="store_true", help="Skip background music")
    parser.add_argument("--no-credits", action="store_true", help="Skip end credits")
    parser.add_argument(
        "--no-sfx", action="store_true", help="Skip transition SFX between segments"
    )
    parser.add_argument(
        "--no-intro", action="store_true", help="Skip animated logo intro"
    )
    parser.add_argument(
        "--no-yt-search",
        action="store_true",
        help="Skip inline YouTube search during assembly (use pre-downloaded footage + images only)",
    )
    parser.add_argument(
        "--veo3", action="store_true", help="Enable Veo3 AI video generation"
    )
    parser.add_argument(
        "--analyze", action="store_true", help="Analyze script and show visual routing"
    )
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    audio_dir = f"{project_dir}/audio"
    work_dir = f"{project_dir}/temp/visuals"
    temp_dir = f"{project_dir}/temp"
    output_dir = f"{project_dir}/output"
    script_file = f"{project_dir}/script.json"

    for d in [work_dir, temp_dir, output_dir]:
        os.makedirs(d, exist_ok=True)

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    # Resolution
    if args.resolution == "4k":
        width, height = LONGFORM_OUTPUT_WIDTH_4K, LONGFORM_OUTPUT_HEIGHT_4K
    else:
        width, height = LONGFORM_OUTPUT_WIDTH_HD, LONGFORM_OUTPUT_HEIGHT_HD

    with open(script_file) as f:
        script = json.load(f)

    segments = script["segments"]

    # Check Veo3 availability if enabled
    veo3_available = False
    if args.veo3:
        try:
            from src.veo3_generator import is_veo3_available

            veo3_available, veo3_msg = is_veo3_available()
            if not veo3_available:
                print(f"WARNING: Veo3 requested but not available: {veo3_msg}")
                print("         Will fall back to other visual types.")
        except ImportError:
            print("WARNING: Veo3 module not found. Run: pip install google-genai")

    # Analyze mode
    if args.analyze:
        print("=" * 70)
        print(f"Visual Routing Analysis - Project: {args.project}")
        print(f"Veo3 enabled: {args.veo3} (available: {veo3_available})")
        print("=" * 70)

        type_counts = {}
        for i, seg in enumerate(segments):
            decision = route_visual(seg, use_veo3=args.veo3)
            vtype = decision.primary_type.value
            type_counts[vtype] = type_counts.get(vtype, 0) + 1

            context = seg.get("context", seg.get("text", "")[:30])
            print(f"[{i:02d}] {vtype:15} | {context[:45]}")
            if decision.speaker_name:
                print(f"      Speaker: {decision.speaker_name}")
            if decision.veo3_prompt:
                print(f"      Veo3: {decision.veo3_prompt[:50]}...")
            print(f"      Queries: {decision.search_queries[:2]}")

        print("-" * 70)
        print("Summary:")
        for vtype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            pct = count / len(segments) * 100
            print(f"  {vtype}: {count} segments ({pct:.0f}%)")
        return

    print("=" * 70)
    print(f"Advanced Visual Assembler - Project: {args.project}")
    print(f"Resolution: {width}x{height} ({args.resolution.upper()})")
    print(f"Visual Duration: {MIN_CLIP_DURATION}-{MAX_CLIP_DURATION}s per clip")
    print(f"Encoder: {GPU_ENCODER} ({'GPU' if GPU_ENCODER != 'libx264' else 'CPU'})")
    yt_label = "Disabled" if args.no_yt_search else "YouTube-first"
    print(f"Visual Source: {yt_label} (F1 images fallback)")
    print(f"Veo3 AI Video: {'Enabled' if args.veo3 else 'Disabled'}")
    print("=" * 70)

    # Check audio
    missing = [
        i
        for i in range(len(segments))
        if not os.path.exists(f"{audio_dir}/segment_{i:02d}.mp3")
    ]
    if missing:
        print(f"\nMissing audio: {missing}")
        sys.exit(1)

    # Generate intro
    if not args.no_intro:
        print("Creating animated intro...")
        intro_path = f"{temp_dir}/intro.mp4"
        if create_intro_video(intro_path, width, height):
            print("    Intro created")
        else:
            print("    Intro creation failed, skipping")
            intro_path = None
    else:
        intro_path = None

    print(f"\nProcessing {len(segments)} segments...\n")

    segment_videos = []
    segment_durations = []  # Track durations for SFX placement
    visual_stats = {}

    for i, segment in enumerate(segments):
        context = segment.get("context", segment.get("section", "segment"))[:40]
        print(f"[{i + 1}/{len(segments)}] {context}...")

        output_path = f"{temp_dir}/segment_{i:02d}.mp4"
        audio_path = f"{audio_dir}/segment_{i:02d}.mp3"

        success, error, vtype = create_segment_video(
            i,
            segment,
            audio_path,
            work_dir,
            output_path,
            width,
            height,
            use_veo3=args.veo3,
            use_yt_search=not args.no_yt_search,
        )

        if success:
            # Apply color grading
            grade = detect_color_grade(segment)
            if grade != "none":
                graded_path = f"{temp_dir}/segment_{i:02d}_graded.mp4"
                if apply_color_grade(output_path, graded_path, grade):
                    os.replace(graded_path, output_path)

            segment_videos.append(output_path)
            dur = get_duration(output_path)
            segment_durations.append(dur)
            visual_stats[vtype] = visual_stats.get(vtype, 0) + 1
            grade_label = f" grade={grade}" if grade != "none" else ""
            print(f"    Done ({dur:.1f}s) [{vtype}{grade_label}]")
        else:
            print(f"    Failed: {error}")

        # Clean up segment work dir to free memory/disk between segments
        seg_work = os.path.join(work_dir, f"segment_{i:02d}")
        if os.path.exists(seg_work):
            shutil.rmtree(seg_work, ignore_errors=True)

    if not segment_videos:
        print("\nNo segments created!")
        sys.exit(1)

    # Prepend intro
    if intro_path and os.path.exists(intro_path):
        segment_videos.insert(0, intro_path)

    # Outro
    if not args.no_credits:
        print("\nCreating outro...")
        outro_path = f"{temp_dir}/outro.mp4"
        if create_outro_video(outro_path, width, height):
            segment_videos.append(outro_path)

    # Concatenate
    print(f"\nConcatenating {len(segment_videos)} segments...")
    concat_file = f"{temp_dir}/concat.txt"
    with open(concat_file, "w") as f:
        for v in segment_videos:
            f.write(f"file '{v}'\n")

    concat_output = f"{temp_dir}/concat.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_file,
        *gpu_enc_args(),
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "1",
        "-b:a",
        LONGFORM_AUDIO_BITRATE,
        concat_output,
    ]
    subprocess.run(cmd, capture_output=True, text=True)

    # Add transition SFX
    if not args.no_sfx and segment_durations:
        print("Adding transition SFX...")
        sfx_output = f"{temp_dir}/with_sfx.mp4"
        if add_transition_sfx(concat_output, sfx_output, segment_durations):
            concat_output = sfx_output

    # Add music with context-aware volume
    final_output = f"{output_dir}/final.mp4"
    if not args.no_music:
        print("Adding background music...")
        # Build per-segment volume map from durations and moods
        segment_volumes = []
        # Account for intro duration if present
        intro_offset = 0.0
        if intro_path and os.path.exists(intro_path):
            intro_dur = get_duration(intro_path)
            segment_volumes.append((0.0, intro_dur, MUSIC_VOLUME_UPLIFTING))
            intro_offset = intro_dur

        cumulative = intro_offset
        for i, dur in enumerate(segment_durations):
            if i < len(segments):
                mood = detect_music_mood(segments[i])
                if mood == "uplifting":
                    vol = MUSIC_VOLUME_UPLIFTING
                elif mood == "atmospheric":
                    vol = MUSIC_VOLUME_ATMOSPHERIC
                else:
                    vol = MUSIC_VOLUME_LONGFORM
            else:
                vol = MUSIC_VOLUME_LONGFORM
            segment_volumes.append((cumulative, cumulative + dur, vol))
            cumulative += dur

        add_background_music(
            concat_output, final_output, segment_volumes=segment_volumes
        )
    else:
        subprocess.run(["cp", concat_output, final_output])

    # Captions
    generate_srt_captions(script, audio_dir, f"{output_dir}/captions.srt")

    if os.path.exists(final_output):
        size_mb = os.path.getsize(final_output) / (1024 * 1024)
        duration = get_duration(final_output)
        print(f"\n{'=' * 70}")
        print(f"SUCCESS: {final_output}")
        print(f"Duration: {duration / 60:.1f} minutes ({duration:.0f}s)")
        print(f"Size: {size_mb:.1f}MB")
        print(f"\nVisual breakdown:")
        for vtype, count in sorted(visual_stats.items(), key=lambda x: -x[1]):
            print(f"  {vtype}: {count} segments")
        print(f"{'=' * 70}")
    else:
        print("\nFailed to create final video")
        sys.exit(1)


if __name__ == "__main__":
    main()
