#!/usr/bin/env python3
"""
Download F1 car loop footage for sleep video background

Sources F1 onboard/track footage from YouTube or free stock sites.
For best results, use official F1 onboard footage via yt-dlp.

Usage:
    # Download from YouTube (recommended for quality)
    python3 src/download_f1_loop.py --project f1-history-sleep --source youtube

    # Download from free stock footage
    python3 src/download_f1_loop.py --project f1-history-sleep --source stock

    # Custom YouTube search query
    python3 src/download_f1_loop.py --project f1-history-sleep --source youtube \
        --query "F1 night race onboard ambient"

    # Trim to clean loop segment
    python3 src/download_f1_loop.py --project f1-history-sleep --trim \
        --trim-start 30 --trim-duration 60
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PROJECTS_DIR


# ============================================================================
# Configuration
# ============================================================================

# Free stock footage options (CC0/Royalty-free)
STOCK_FOOTAGE_OPTIONS = [
    {
        "name": "pixabay_racing_1",
        "url": "https://cdn.pixabay.com/video/2020/05/25/40302-424891332_large.mp4",
        "description": "Racing car driving footage"
    },
    {
        "name": "pixabay_racing_2",
        "url": "https://cdn.pixabay.com/video/2019/08/23/26313-356076543_large.mp4",
        "description": "Race car POV driving"
    },
]

# YouTube search suggestions for sleep-friendly F1 footage
YOUTUBE_SUGGESTIONS = [
    "F1 onboard full lap no commentary ambient",
    "F1 night race onboard Singapore",
    "Formula 1 cockpit view relaxing",
    "F1 onboard Monaco lap",
    "F1 rain race onboard ambient",
]


# ============================================================================
# Download Functions
# ============================================================================

def download_from_youtube(
    project_name: str,
    query: str,
    output_name: str = "f1_car_loop.mp4",
    max_duration: int = 600
) -> str | None:
    """Download F1 footage from YouTube using yt-dlp

    Args:
        project_name: Project folder name
        query: YouTube search query
        output_name: Output filename
        max_duration: Maximum video duration in seconds (default 10 min)

    Returns:
        Path to downloaded file or None if failed
    """
    project_dir = Path(PROJECTS_DIR) / project_name
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    output_path = assets_dir / output_name

    # Remove existing file if present
    if output_path.exists():
        print(f"Removing existing file: {output_path}")
        output_path.unlink()

    print(f"Searching YouTube for: {query}")
    print(f"Max duration: {max_duration}s")

    # Search and download best quality up to 1080p
    cmd = [
        "yt-dlp",
        f"ytsearch1:{query}",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", str(output_path),
        "--no-playlist",
        "--match-filter", f"duration<{max_duration}",
        "--print", "title",
        "--print", "duration",
    ]

    print(f"Running: {' '.join(cmd[:10])}...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"yt-dlp failed: {result.stderr}")
        return None

    # Print video info
    output_lines = result.stdout.strip().split('\n')
    if len(output_lines) >= 2:
        print(f"Downloaded: {output_lines[0]}")
        print(f"Duration: {output_lines[1]}s")

    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"Saved: {output_path} ({size_mb:.1f} MB)")
        return str(output_path)
    else:
        print("Download completed but file not found")
        return None


def download_stock_footage(project_name: str, option_index: int = 0) -> str | None:
    """Download stock footage from free sources

    Args:
        project_name: Project folder name
        option_index: Index into STOCK_FOOTAGE_OPTIONS

    Returns:
        Path to downloaded file or None if failed
    """
    project_dir = Path(PROJECTS_DIR) / project_name
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    if option_index >= len(STOCK_FOOTAGE_OPTIONS):
        print(f"Invalid option index: {option_index}")
        return None

    option = STOCK_FOOTAGE_OPTIONS[option_index]
    output_path = assets_dir / "f1_car_loop.mp4"

    print(f"Downloading: {option['description']}")
    print(f"URL: {option['url']}")

    cmd = ["curl", "-L", "-o", str(output_path), option["url"]]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Download failed: {result.stderr}")
        return None

    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"Downloaded: {output_path} ({size_mb:.1f} MB)")
        return str(output_path)

    return None


def download_from_url(project_name: str, url: str) -> str | None:
    """Download video from a direct URL

    Args:
        project_name: Project folder name
        url: Direct video URL or YouTube URL

    Returns:
        Path to downloaded file or None if failed
    """
    project_dir = Path(PROJECTS_DIR) / project_name
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    output_path = assets_dir / "f1_car_loop.mp4"

    # Check if it's a YouTube URL
    if "youtube.com" in url or "youtu.be" in url:
        print(f"Downloading from YouTube: {url}")
        cmd = [
            "yt-dlp",
            url,
            "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
            "--merge-output-format", "mp4",
            "-o", str(output_path),
            "--no-playlist",
        ]
    else:
        print(f"Downloading from URL: {url}")
        cmd = ["curl", "-L", "-o", str(output_path), url]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Download failed: {result.stderr}")
        return None

    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"Downloaded: {output_path} ({size_mb:.1f} MB)")
        return str(output_path)

    return None


# ============================================================================
# Video Processing Functions
# ============================================================================

def get_video_info(video_path: str) -> dict:
    """Get video information using ffprobe"""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration,r_frame_rate",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}

    import json
    data = json.loads(result.stdout)

    info = {}
    if "streams" in data and data["streams"]:
        stream = data["streams"][0]
        info["width"] = stream.get("width", 0)
        info["height"] = stream.get("height", 0)
        if "r_frame_rate" in stream:
            num, den = stream["r_frame_rate"].split("/")
            info["fps"] = float(num) / float(den) if float(den) > 0 else 0

    if "format" in data:
        info["duration"] = float(data["format"].get("duration", 0))

    return info


def trim_to_loop(
    input_path: str,
    output_path: str,
    start: float = 0,
    duration: float = 60,
    remove_audio: bool = True
) -> str | None:
    """Trim footage to a clean loop segment

    Args:
        input_path: Source video path
        output_path: Output video path
        start: Start time in seconds
        duration: Duration of loop in seconds
        remove_audio: Remove audio track (recommended for sleep video)

    Returns:
        Path to trimmed video or None if failed
    """
    print(f"Trimming: {start}s to {start + duration}s ({duration}s)")

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
    ]

    if remove_audio:
        cmd.append("-an")
    else:
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])

    cmd.append(output_path)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Trim failed: {result.stderr}")
        return None

    if os.path.exists(output_path):
        info = get_video_info(output_path)
        print(f"Trimmed: {output_path}")
        print(f"Duration: {info.get('duration', 0):.1f}s")
        return output_path

    return None


def create_seamless_loop(input_path: str, output_path: str, crossfade: float = 1.0) -> str | None:
    """Create a seamless loop with crossfade between end and start

    Args:
        input_path: Source video path
        output_path: Output video path
        crossfade: Crossfade duration in seconds

    Returns:
        Path to looped video or None if failed
    """
    info = get_video_info(input_path)
    duration = info.get("duration", 0)

    if duration < crossfade * 3:
        print(f"Video too short for crossfade loop: {duration}s")
        return None

    print(f"Creating seamless loop with {crossfade}s crossfade...")

    # Use xfade filter for smooth transition
    filter_complex = (
        f"[0:v]split[main][end];"
        f"[end]trim=start={duration - crossfade},setpts=PTS-STARTPTS[endclip];"
        f"[main]trim=end={duration - crossfade},setpts=PTS-STARTPTS[mainclip];"
        f"[endclip][mainclip]xfade=transition=fade:duration={crossfade}:offset=0[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-an",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Seamless loop failed: {result.stderr}")
        # Fall back to simple copy
        print("Falling back to simple trim...")
        return None

    if os.path.exists(output_path):
        print(f"Seamless loop created: {output_path}")
        return output_path

    return None


# ============================================================================
# Main Function
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Download F1 car loop footage for sleep video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    # Download from YouTube (search)
    python3 src/download_f1_loop.py --project f1-history-sleep --source youtube

    # Download specific YouTube video
    python3 src/download_f1_loop.py --project f1-history-sleep --url "https://youtube.com/watch?v=..."

    # Download from stock footage
    python3 src/download_f1_loop.py --project f1-history-sleep --source stock

    # Trim existing footage
    python3 src/download_f1_loop.py --project f1-history-sleep --trim --trim-start 30 --trim-duration 60

Suggested YouTube searches:
{chr(10).join(f'  - "{s}"' for s in YOUTUBE_SUGGESTIONS)}
        """
    )

    parser.add_argument(
        "--project",
        required=True,
        help="Project name (folder in projects/)"
    )
    parser.add_argument(
        "--source",
        choices=["youtube", "stock"],
        default="youtube",
        help="Source for footage (default: youtube)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="F1 onboard full lap no commentary ambient",
        help="YouTube search query"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Direct URL to download (YouTube or direct link)"
    )
    parser.add_argument(
        "--stock-option",
        type=int,
        default=0,
        help="Stock footage option index"
    )
    parser.add_argument(
        "--trim",
        action="store_true",
        help="Trim footage to loop segment"
    )
    parser.add_argument(
        "--trim-start",
        type=float,
        default=0,
        help="Trim start time in seconds"
    )
    parser.add_argument(
        "--trim-duration",
        type=float,
        default=60,
        help="Trim duration in seconds"
    )
    parser.add_argument(
        "--seamless",
        action="store_true",
        help="Create seamless loop with crossfade"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show info about existing footage"
    )

    args = parser.parse_args()

    project_dir = Path(PROJECTS_DIR) / args.project
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    loop_path = assets_dir / "f1_car_loop.mp4"

    # Show info about existing footage
    if args.info:
        if loop_path.exists():
            info = get_video_info(str(loop_path))
            print(f"Existing footage: {loop_path}")
            print(f"  Resolution: {info.get('width', 0)}x{info.get('height', 0)}")
            print(f"  Duration: {info.get('duration', 0):.1f}s")
            print(f"  FPS: {info.get('fps', 0):.1f}")
            size_mb = loop_path.stat().st_size / (1024 * 1024)
            print(f"  Size: {size_mb:.1f} MB")
        else:
            print(f"No footage found at: {loop_path}")
        return

    # Download footage
    if args.url:
        downloaded = download_from_url(args.project, args.url)
    elif args.source == "youtube":
        downloaded = download_from_youtube(args.project, args.query)
    else:
        downloaded = download_stock_footage(args.project, args.stock_option)

    if not downloaded and not loop_path.exists():
        print("\nDownload failed. Try manually downloading footage:")
        print("  1. Find F1 onboard footage on YouTube")
        print("  2. Download with: yt-dlp -o 'projects/{project}/assets/f1_car_loop.mp4' URL")
        sys.exit(1)

    # Trim if requested
    if args.trim and loop_path.exists():
        trimmed_path = assets_dir / "f1_car_loop_trimmed.mp4"
        result = trim_to_loop(
            str(loop_path),
            str(trimmed_path),
            args.trim_start,
            args.trim_duration
        )

        if result:
            # Replace original with trimmed version
            loop_path.unlink()
            trimmed_path.rename(loop_path)
            print(f"Replaced original with trimmed version")

    # Create seamless loop if requested
    if args.seamless and loop_path.exists():
        seamless_path = assets_dir / "f1_car_loop_seamless.mp4"
        result = create_seamless_loop(str(loop_path), str(seamless_path))

        if result:
            loop_path.unlink()
            seamless_path.rename(loop_path)
            print(f"Replaced original with seamless loop")

    # Show final info
    if loop_path.exists():
        print(f"\n{'='*60}")
        print("Footage ready!")
        info = get_video_info(str(loop_path))
        print(f"  File: {loop_path}")
        print(f"  Resolution: {info.get('width', 0)}x{info.get('height', 0)}")
        print(f"  Duration: {info.get('duration', 0):.1f}s")


if __name__ == "__main__":
    main()
