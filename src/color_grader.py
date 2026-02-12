#!/usr/bin/env python3
"""
Color Grading System for Long-Form F1 Content

Applies FFmpeg-based color grading per-segment based on script context.
Supports: B&W, vintage, cinematic (teal-orange), warm, cool, or none.

Auto-detects appropriate grade from segment context/section keywords,
or uses explicit `color_grade` field from script.json.
"""

import os
import subprocess
from typing import Dict, Optional

# ============================================================================
# COLOR GRADE PRESETS
# ============================================================================

GRADE_FILTERS = {
    "bw": "eq=saturation=0",
    "vintage": "curves=vintage,noise=alls=25:allf=t+u",
    "cinematic": "colorbalance=rs=-0.15:bs=0.15:rh=0.15:bh=-0.15",
    "warm": "colortemperature=temperature=6500",
    "cool": "colortemperature=temperature=4500",
    "none": "",
}

# Keywords mapped to grades for auto-detection
GRADE_KEYWORDS = {
    "bw": [
        "dramatic",
        "shocking",
        "controversial",
        "tragedy",
        "fatal",
        "death",
        "mourning",
        "black and white",
        "monochrome",
    ],
    "vintage": [
        "history",
        "historical",
        "past",
        "legacy",
        "classic",
        "retro",
        "archive",
        "era",
        "decade",
        "vintage",
        "origins",
        "founding",
        "early days",
        "throwback",
    ],
    "cinematic": [
        "cinematic",
        "epic",
        "showdown",
        "rivalry",
        "battle",
        "intense",
        "climax",
        "finale",
    ],
    "warm": [
        "celebration",
        "victory",
        "joy",
        "feel good",
        "triumph",
        "uplifting",
        "heartwarming",
        "positive",
        "success",
        "achievement",
        "proud",
    ],
    "cool": [
        "technical",
        "engineering",
        "data",
        "analysis",
        "aerodynamic",
        "wind tunnel",
        "simulation",
        "technology",
        "regulation",
        "specification",
    ],
}


def detect_color_grade(segment: Dict) -> str:
    """Auto-detect the best color grade for a segment based on context.

    Checks segment fields in order:
    1. Explicit `color_grade` field (user override)
    2. Keyword matching against context, section, and text
    3. Falls back to "none"
    """
    # Check explicit override
    explicit = segment.get("color_grade", "").strip().lower()
    if explicit in GRADE_FILTERS:
        return explicit

    # Build text to search from segment metadata
    context = segment.get("context", "").lower()
    section = segment.get("section", "").lower()
    text = segment.get("text", "").lower()
    combined = f"{context} {section} {text}"

    # Score each grade by keyword matches
    best_grade = "none"
    best_score = 0

    for grade, keywords in GRADE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > best_score:
            best_score = score
            best_grade = grade

    return best_grade


def get_grade_filter(grade: str) -> str:
    """Get the FFmpeg filter string for a grade preset."""
    return GRADE_FILTERS.get(grade, "")


def apply_color_grade(input_path: str, output_path: str, grade: str) -> bool:
    """Apply a color grade to a video file.

    Args:
        input_path: Source video file
        output_path: Graded output file
        grade: Grade preset name (bw, vintage, cinematic, warm, cool, none)

    Returns:
        True if grading was applied successfully
    """
    ffmpeg_filter = get_grade_filter(grade)

    # No grading needed
    if not ffmpeg_filter or grade == "none":
        if input_path != output_path:
            subprocess.run(["cp", input_path, output_path])
        return True

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vf",
        ffmpeg_filter,
        "-c:v",
        "copy",  # Will be overridden below
        "-c:a",
        "copy",
        output_path,
    ]

    # Color filters require re-encoding video
    # Detect GPU encoder (import from assembler at runtime to avoid circular deps)
    try:
        from src.image_video_assembler import gpu_enc_args

        enc_args = gpu_enc_args()
    except ImportError:
        enc_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "23"]

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vf",
        ffmpeg_filter,
        *enc_args,
        "-c:a",
        "copy",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
