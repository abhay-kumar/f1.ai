#!/usr/bin/env python3
"""
Podcast Cover Art Generator - Creates episode-specific cover art

Uses FFmpeg to composite logo with episode text on a branded background.
Output: Square image (1400x1400 or 3000x3000) suitable for podcast platforms.
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import SHARED_DIR, get_project_dir
from channels import channel_asset, load_channel_from_script

FALLBACK_FONT = "Arial Bold"

# Cover art settings
COVER_SIZE = 3000  # Higher resolution for quality

# Text sizing - bigger and bolder
EPISODE_FONT_SIZE = 180  # Large episode number
TITLE_FONT_SIZE = 120  # Large title text
TITLE_LINE_HEIGHT = 140  # Spacing between title lines
MAX_CHARS_PER_LINE = 28  # Characters per line before wrapping


def wrap_title(title: str, max_chars: int = MAX_CHARS_PER_LINE) -> list:
    """Wrap title into multiple lines for display"""
    words = title.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_len = len(word)
        # +1 for space between words
        if current_length + word_len + (1 if current_line else 0) <= max_chars:
            current_line.append(word)
            current_length += word_len + (1 if len(current_line) > 1 else 0)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_len

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def generate_cover_art(
    project_name: str,
    episode_num: int = None,
    title: str = None,
    output_path: str = None,
) -> str:
    """Generate podcast episode cover art"""

    project_dir = get_project_dir(project_name)
    script_path = f"{project_dir}/script.json"

    # Default output path
    if not output_path:
        output_path = f"{project_dir}/output/cover_art.jpg"

    # Load script for title and channel config
    script = {}
    if os.path.exists(script_path):
        with open(script_path) as f:
            script = json.load(f)
            if not title:
                title = script.get("title", "Podcast Episode")
                # Clean up title prefix if it matches channel name
                channel_name = load_channel_from_script(script).get("name", "")
                prefix = f"{channel_name}:"
                if title.lower().startswith(prefix.lower()):
                    title = title[len(prefix):].strip()

    channel = load_channel_from_script(script)
    if not title:
        show_name = channel.get("podcast", {}).get("show_name", "Podcast")
        title = f"{show_name} Episode"

    LOGO_PATH = channel_asset(channel, channel["logo"])
    FONT_PATH = channel_asset(channel, channel["font_bold"])
    BACKGROUND_COLOR = channel.get("cover_bg_color", "0x1a1a2e")
    ACCENT_COLOR = channel.get("cover_accent_color", "0xff8000")

    # Wrap title into multiple lines instead of truncating
    title_lines = wrap_title(title)

    # Episode text
    if episode_num:
        ep_text = f"EPISODE {episode_num}"
    else:
        ep_text = "NEW EPISODE"

    # Escape special characters for FFmpeg drawtext
    title_lines = [line.replace("'", "\\'").replace(":", "\\:") for line in title_lines]

    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Generating cover art...")
    print(f"  Title lines: {title_lines}")
    print(f"  Episode: {ep_text}")
    print(f"  Using channel font: {os.path.exists(FONT_PATH)}")

    # Determine font to use — prefer channel font if available
    if os.path.exists(FONT_PATH):
        font_spec = f"fontfile='{FONT_PATH}'"
        print(f"  Font: {os.path.basename(FONT_PATH)}")
    else:
        font_spec = f"font='{FALLBACK_FONT}'"
        print(f"  Font: {FALLBACK_FONT} (fallback)")

    # FFmpeg command to create cover art
    # 1. Create solid color background
    # 2. Overlay logo (scaled and centered in top portion)
    # 3. Add episode number text (bigger, bolder, F1 font)
    # 4. Add title text lines (multi-line, bigger, bolder, F1 font)

    # Calculate title starting position based on number of lines
    num_title_lines = len(title_lines)
    # Position title lines from bottom, accounting for all lines
    title_base_y = COVER_SIZE - 150 - (num_title_lines * TITLE_LINE_HEIGHT)

    # Episode number positioned above title with proper spacing
    episode_y = (
        title_base_y - EPISODE_FONT_SIZE - 60
    )  # 60px gap between episode and title

    # Build filter complex with logo and episode text
    filter_complex = (
        # Create background
        f"color=c={BACKGROUND_COLOR}:s={COVER_SIZE}x{COVER_SIZE}:d=1[bg];"
        # Scale logo larger for quality (logo already has F1 BURNOUTS text)
        f"[1:v]scale=1800:-1[logo];"
        # Overlay logo centered, higher up to make room for text
        f"[bg][logo]overlay=(W-w)/2:(H-h)/2-400[with_logo];"
        # Add episode number below logo - bigger and bolder with F1 font
        f"[with_logo]drawtext=text='{ep_text}':"
        f"{font_spec}:fontsize={EPISODE_FONT_SIZE}:fontcolor={ACCENT_COLOR}:"
        f"x=(w-text_w)/2:y={episode_y}"
    )

    # Add each title line as a separate drawtext
    for i, line in enumerate(title_lines):
        y_pos = title_base_y + (i * TITLE_LINE_HEIGHT)
        input_label = f"[title_{i}]" if i < len(title_lines) - 1 else ""
        prev_label = "[with_ep]" if i == 0 else f"[title_{i - 1}]"

        if i == 0:
            filter_complex += f"[with_ep];"

        filter_complex += (
            f"{prev_label}drawtext=text='{line}':"
            f"{font_spec}:fontsize={TITLE_FONT_SIZE}:fontcolor=white:"
            f"x=(w-text_w)/2:y={y_pos}{input_label}"
        )

        if i < len(title_lines) - 1:
            filter_complex += ";"

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={BACKGROUND_COLOR}:s={COVER_SIZE}x{COVER_SIZE}:d=1",
        "-i",
        LOGO_PATH,
        "-filter_complex",
        filter_complex,
        "-frames:v",
        "1",
        "-update",
        "1",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr}")
        # Try simpler version without text (in case font issues)
        print("Trying simplified version...")

        simple_filter = (
            f"color=c={BACKGROUND_COLOR}:s={COVER_SIZE}x{COVER_SIZE}:d=1[bg];"
            f"[1:v]scale=900:-1[logo];"
            f"[bg][logo]overlay=(W-w)/2:(H-h)/2"
        )

        cmd_simple = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={BACKGROUND_COLOR}:s={COVER_SIZE}x{COVER_SIZE}:d=1",
            "-i",
            LOGO_PATH,
            "-filter_complex",
            simple_filter,
            "-frames:v",
            "1",
            "-update",
            "1",
            output_path,
        ]

        result = subprocess.run(cmd_simple, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Simple version also failed: {result.stderr}")
            return None

    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / 1024
        print(f"Cover art created: {output_path} ({file_size:.1f}KB)")
        return output_path

    return None


def main():
    parser = argparse.ArgumentParser(description="Generate podcast episode cover art")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--episode", type=int, help="Episode number")
    parser.add_argument("--title", help="Override title")
    parser.add_argument(
        "--output", help="Output path (default: project/output/cover_art.jpg)"
    )

    args = parser.parse_args()

    cover_path = generate_cover_art(
        project_name=args.project,
        episode_num=args.episode,
        title=args.title,
        output_path=args.output,
    )

    if cover_path:
        print(f"\nSuccess! Cover art saved to: {cover_path}")
    else:
        print("\nFailed to generate cover art")
        sys.exit(1)


if __name__ == "__main__":
    main()
