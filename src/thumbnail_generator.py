#!/usr/bin/env python3
"""
Thumbnail Generator - Creates eye-catching, viral thumbnails for F1 videos
Uses FFmpeg for image manipulation and text overlay

Features:
- Extracts compelling frames from video
- Adds bold, readable text overlays
- Uses F1 brand colors for visual impact
- Creates high-contrast, attention-grabbing thumbnails
- Optimized for YouTube (1280x720, 16:9)
"""
import os
import sys
import json
import argparse
import subprocess
import re
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir, SHARED_DIR, F1_TEAM_COLORS

# Thumbnail settings
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720
THUMBNAIL_QUALITY = 2  # JPEG quality (1-31, lower is better)

# Font path
F1_FONT = f"{SHARED_DIR}/fonts/Formula1-Bold.ttf"
F1_FONT_REGULAR = f"{SHARED_DIR}/fonts/Formula1-Regular.ttf"

# Viral thumbnail color schemes
COLOR_SCHEMES = {
    "ferrari": {"bg": "#E8002D", "text": "#FFFFFF", "accent": "#FFD700"},
    "redbull": {"bg": "#1E41FF", "text": "#FFFFFF", "accent": "#FF0000"},
    "mercedes": {"bg": "#00D2BE", "text": "#000000", "accent": "#FFFFFF"},
    "mclaren": {"bg": "#FF8700", "text": "#000000", "accent": "#FFFFFF"},
    "default": {"bg": "#E8002D", "text": "#FFFFFF", "accent": "#FFD700"},
    "dramatic": {"bg": "#000000", "text": "#FFFFFF", "accent": "#E8002D"},
    "gold": {"bg": "#1a1a1a", "text": "#FFD700", "accent": "#FFFFFF"},
}

# Viral words/phrases that increase CTR
VIRAL_WORDS = [
    "SHOCKING", "REVEALED", "SECRET", "UNTOLD", "LEGENDARY",
    "EPIC", "INSANE", "BRUTAL", "DOMINANT", "HISTORIC",
    "REVOLUTION", "CONTROVERSY", "DRAMA", "BATTLE", "WAR"
]


def get_duration(file_path: str) -> float:
    """Get duration of media file in seconds"""
    cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0


def detect_team_colors(script: Dict) -> str:
    """Detect dominant team/driver in script and return color scheme"""
    full_text = " ".join([seg.get("text", "") for seg in script.get("segments", [])]).lower()
    title = script.get("title", "").lower()
    combined = f"{title} {full_text}"

    team_keywords = {
        "ferrari": ["ferrari", "leclerc", "sainz", "maranello", "prancing horse"],
        "redbull": ["red bull", "verstappen", "perez", "horner", "newey"],
        "mercedes": ["mercedes", "hamilton", "russell", "wolff", "brackley"],
        "mclaren": ["mclaren", "norris", "piastri", "zak brown", "woking"],
    }

    team_counts = {}
    for team, keywords in team_keywords.items():
        count = sum(combined.count(kw) for kw in keywords)
        if count > 0:
            team_counts[team] = count

    if team_counts:
        dominant_team = max(team_counts, key=team_counts.get)
        return dominant_team

    return "default"


def generate_thumbnail_text(script: Dict) -> Tuple[str, str]:
    """Generate catchy thumbnail text from script.

    Returns (main_text, sub_text) for the thumbnail.
    Main text: Short, punchy (2-4 words)
    Sub text: Supporting context (optional)
    """
    title = script.get("title", "F1 Video")

    # Try to extract key dramatic words from title
    title_upper = title.upper()

    # Check for viral words in title
    for word in VIRAL_WORDS:
        if word in title_upper:
            # Use the viral word as main text
            return word, title.replace(word.lower(), "").strip()[:30]

    # Extract key phrases based on common patterns
    patterns = [
        # "The X of Y" -> "X"
        (r"the\s+(\w+)\s+of", lambda m: m.group(1).upper()),
        # "How X Changed Y" -> "X CHANGED"
        (r"how\s+(\w+)\s+changed", lambda m: f"{m.group(1).upper()} CHANGED"),
        # "Why X" -> "WHY X"
        (r"why\s+(\w+)", lambda m: f"WHY {m.group(1).upper()}"),
        # "The Secret/Truth" -> "THE SECRET"
        (r"(secret|truth|mystery)", lambda m: f"THE {m.group(1).upper()}"),
        # Year patterns "2026" -> "2026"
        (r"(20\d{2})", lambda m: m.group(1)),
    ]

    for pattern, extractor in patterns:
        match = re.search(pattern, title.lower())
        if match:
            main_text = extractor(match)
            return main_text[:20], ""

    # Fallback: Use first 2-3 impactful words from title
    words = title.split()
    if len(words) >= 3:
        # Skip common words
        skip_words = {"the", "a", "an", "of", "and", "or", "in", "on", "at", "to", "for"}
        key_words = [w for w in words if w.lower() not in skip_words][:3]
        main_text = " ".join(key_words).upper()
        return main_text[:25], ""

    return title.upper()[:20], ""


def extract_best_frame(video_path: str, output_path: str,
                       timestamps: List[float] = None) -> bool:
    """Extract a visually interesting frame from the video.

    Tries multiple timestamps to find a good frame.
    """
    duration = get_duration(video_path)

    if timestamps is None:
        # Try frames at different points - avoid very start/end
        timestamps = [
            duration * 0.1,   # 10% in
            duration * 0.25,  # 25% in
            duration * 0.4,   # 40% in
            duration * 0.15,  # 15% in
            30,               # 30 seconds in
        ]

    # Filter valid timestamps
    timestamps = [t for t in timestamps if 0 < t < duration]

    if not timestamps:
        timestamps = [min(30, duration / 2)]

    # Try each timestamp until we get a good frame
    for ts in timestamps:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(ts),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", str(THUMBNAIL_QUALITY),
            "-vf", f"scale={THUMBNAIL_WIDTH}:{THUMBNAIL_HEIGHT}:force_original_aspect_ratio=decrease,"
                   f"pad={THUMBNAIL_WIDTH}:{THUMBNAIL_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return True

    return False


def add_text_overlay(input_path: str, output_path: str,
                     main_text: str, sub_text: str = "",
                     color_scheme: str = "default") -> bool:
    """Add bold text overlay to thumbnail image.

    Creates a viral-style thumbnail with:
    - Large, bold main text
    - Optional subtitle
    - Color gradient/overlay for contrast
    - Drop shadow for readability
    """
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])

    # Escape text for FFmpeg
    main_text = main_text.replace("'", "\u2019").replace(":", "\\:")
    sub_text = sub_text.replace("'", "\u2019").replace(":", "\\:") if sub_text else ""

    # Calculate font sizes based on text length
    main_font_size = 100 if len(main_text) <= 10 else (80 if len(main_text) <= 15 else 60)
    sub_font_size = 36

    # Position calculations
    main_y = 280 if sub_text else 320  # Center vertically, adjust if subtitle
    sub_y = main_y + main_font_size + 20

    # Build filter complex
    filters = []

    # Add semi-transparent gradient overlay at bottom for text readability
    filters.append(
        f"drawbox=x=0:y=ih*0.5:w=iw:h=ih*0.5:color=black@0.6:t=fill"
    )

    # Add accent color bar at bottom
    filters.append(
        f"drawbox=x=0:y=ih-8:w=iw:h=8:color={colors['accent']}:t=fill"
    )

    # Main text - shadow first
    filters.append(
        f"drawtext=text='{main_text}':"
        f"fontfile={F1_FONT}:fontsize={main_font_size}:"
        f"fontcolor=black@0.8:x=(w-text_w)/2+4:y={main_y}+4"
    )

    # Main text - actual
    filters.append(
        f"drawtext=text='{main_text}':"
        f"fontfile={F1_FONT}:fontsize={main_font_size}:"
        f"fontcolor={colors['text']}:x=(w-text_w)/2:y={main_y}:"
        f"borderw=3:bordercolor={colors['bg']}"
    )

    # Subtitle if present
    if sub_text:
        filters.append(
            f"drawtext=text='{sub_text}':"
            f"fontfile={F1_FONT}:fontsize={sub_font_size}:"
            f"fontcolor={colors['text']}@0.9:x=(w-text_w)/2:y={sub_y}"
        )

    # Add small F1 BURNOUTS branding in corner
    filters.append(
        f"drawtext=text='F1 BURNOUTS':"
        f"fontfile={F1_FONT}:fontsize=24:"
        f"fontcolor=white@0.7:x=w-text_w-20:y=20"
    )

    filter_complex = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_complex,
        "-q:v", str(THUMBNAIL_QUALITY),
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not os.path.exists(output_path):
        print(f"Text overlay failed: {result.stderr[-300:] if result.stderr else 'Unknown error'}")
        return False

    return True


def generate_thumbnail(project_name: str, custom_text: str = None,
                       color_scheme: str = None) -> Optional[str]:
    """Generate a viral thumbnail for the project.

    Args:
        project_name: Name of the project
        custom_text: Override auto-generated text
        color_scheme: Override auto-detected color scheme

    Returns:
        Path to generated thumbnail, or None if failed
    """
    project_dir = get_project_dir(project_name)
    video_path = f"{project_dir}/output/final.mp4"
    script_path = f"{project_dir}/script.json"
    output_path = f"{project_dir}/output/thumbnail.jpg"
    temp_frame = f"{project_dir}/output/temp_frame.jpg"

    # Validate inputs
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        return None

    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        return None

    # Load script
    with open(script_path) as f:
        script = json.load(f)

    print("=" * 50)
    print(f"Thumbnail Generator - Project: {project_name}")
    print("=" * 50)

    # Detect color scheme from content
    if color_scheme is None:
        color_scheme = detect_team_colors(script)
    print(f"Color scheme: {color_scheme}")

    # Generate text
    if custom_text:
        main_text = custom_text.upper()
        sub_text = ""
    else:
        main_text, sub_text = generate_thumbnail_text(script)
    print(f"Main text: {main_text}")
    if sub_text:
        print(f"Sub text: {sub_text}")

    # Extract frame from video
    print("\nExtracting frame from video...")
    if not extract_best_frame(video_path, temp_frame):
        print("Failed to extract frame")
        return None

    # Add text overlay
    print("Adding text overlay...")
    if not add_text_overlay(temp_frame, output_path, main_text, sub_text, color_scheme):
        print("Failed to add text overlay")
        # Clean up temp file
        if os.path.exists(temp_frame):
            os.remove(temp_frame)
        return None

    # Clean up temp file
    if os.path.exists(temp_frame):
        os.remove(temp_frame)

    # Verify output
    if os.path.exists(output_path):
        size_kb = os.path.getsize(output_path) / 1024
        print(f"\n✅ Thumbnail generated: {output_path}")
        print(f"   Size: {size_kb:.1f}KB")
        return output_path

    return None


def main():
    parser = argparse.ArgumentParser(description="Generate viral thumbnail for F1 video")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--text", help="Custom thumbnail text (overrides auto-generation)")
    parser.add_argument("--color", choices=list(COLOR_SCHEMES.keys()),
                        help="Color scheme (default: auto-detect from content)")
    parser.add_argument("--timestamp", type=float,
                        help="Specific timestamp to extract frame from (seconds)")
    args = parser.parse_args()

    result = generate_thumbnail(
        args.project,
        custom_text=args.text,
        color_scheme=args.color
    )

    if result:
        print("\nThumbnail ready for upload!")
    else:
        print("\nThumbnail generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
