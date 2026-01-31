#!/usr/bin/env python3
"""
Sleep Video Assembler

Creates long-form sleep videos by combining:
- Looping F1 car onboard/track footage
- Full narration audio

Optimized for 3+ hour videos with hardware-accelerated encoding.

Usage:
    python3 src/sleep_video_assembler.py --project f1-history-sleep
    python3 src/sleep_video_assembler.py --project f1-history-sleep --resolution 4k
    python3 src/sleep_video_assembler.py --project f1-history-sleep --preview
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    PROJECTS_DIR,
    LONGFORM_FRAME_RATE,
    LONGFORM_OUTPUT_WIDTH_HD,
    LONGFORM_OUTPUT_HEIGHT_HD,
    LONGFORM_OUTPUT_WIDTH_4K,
    LONGFORM_OUTPUT_HEIGHT_4K,
    LONGFORM_VIDEO_BITRATE_HD,
    LONGFORM_VIDEO_BITRATE_4K,
    LONGFORM_AUDIO_BITRATE,
)


# ============================================================================
# Configuration
# ============================================================================

# Encoder priority (will use first available)
ENCODER_PRIORITY = [
    ("hevc_videotoolbox", "macOS HEVC hardware"),
    ("h264_videotoolbox", "macOS H.264 hardware"),
    ("hevc_nvenc", "NVIDIA HEVC hardware"),
    ("h264_nvenc", "NVIDIA H.264 hardware"),
    ("libx264", "CPU software encoding"),
]

# Sleep video specific settings
SLEEP_VIDEO_LOUDNESS = "-18"  # LUFS - slightly quieter for sleep content


# ============================================================================
# Helper Functions
# ============================================================================

def detect_encoder() -> str:
    """Detect best available video encoder"""
    cmd = ["ffmpeg", "-hide_banner", "-encoders"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    for encoder, desc in ENCODER_PRIORITY:
        if encoder in result.stdout:
            print(f"Using encoder: {encoder} ({desc})")
            return encoder

    print("Using encoder: libx264 (CPU fallback)")
    return "libx264"


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get audio duration: {result.stderr}")
    return float(result.stdout.strip())


def get_video_info(video_path: str) -> dict:
    """Get video information"""
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
        raise RuntimeError(f"Failed to get video info: {result.stderr}")

    data = json.loads(result.stdout)

    info = {}
    if "streams" in data and data["streams"]:
        stream = data["streams"][0]
        info["width"] = stream.get("width", 0)
        info["height"] = stream.get("height", 0)
        if "r_frame_rate" in stream:
            num, den = stream["r_frame_rate"].split("/")
            info["fps"] = float(num) / float(den) if float(den) > 0 else 30

    if "format" in data:
        info["duration"] = float(data["format"].get("duration", 0))

    return info


def format_duration(seconds: float) -> str:
    """Format duration as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ============================================================================
# Main Assembly Function
# ============================================================================

def assemble_sleep_video(
    project_dir: Path,
    resolution: str = "hd",
    encoder: str = "auto"
) -> str:
    """
    Assemble the sleep video

    Creates a video by looping F1 car footage and adding narration audio.

    Args:
        project_dir: Path to project directory
        resolution: "hd" (1080p) or "4k" (2160p)
        encoder: Video encoder to use ("auto", "videotoolbox", "nvenc", "cpu")

    Returns:
        Path to output video
    """
    # Resolve paths
    audio_path = project_dir / "audio" / "full_narration.mp3"
    video_loop_path = project_dir / "assets" / "f1_car_loop.mp4"
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "final.mp4"

    # Validate inputs
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    if not video_loop_path.exists():
        raise FileNotFoundError(f"F1 car loop not found: {video_loop_path}")

    # Get durations and info
    audio_duration = get_audio_duration(str(audio_path))
    video_info = get_video_info(str(video_loop_path))
    loop_duration = video_info.get("duration", 0)

    if loop_duration <= 0:
        raise ValueError(f"Invalid video loop duration: {loop_duration}")

    print(f"Audio duration: {format_duration(audio_duration)} ({audio_duration:.0f}s)")
    print(f"Video loop duration: {loop_duration:.1f}s")
    print(f"Video will loop {int(audio_duration / loop_duration) + 1} times")

    # Resolution settings
    if resolution == "4k":
        width = LONGFORM_OUTPUT_WIDTH_4K
        height = LONGFORM_OUTPUT_HEIGHT_4K
        bitrate = LONGFORM_VIDEO_BITRATE_4K
    else:
        width = LONGFORM_OUTPUT_WIDTH_HD
        height = LONGFORM_OUTPUT_HEIGHT_HD
        bitrate = LONGFORM_VIDEO_BITRATE_HD

    print(f"Output resolution: {width}x{height}")
    print(f"Video bitrate: {bitrate}")

    # Select encoder
    if encoder == "auto":
        encoder = detect_encoder()
    elif encoder == "videotoolbox":
        encoder = "hevc_videotoolbox"
    elif encoder == "nvenc":
        encoder = "hevc_nvenc"
    elif encoder == "cpu":
        encoder = "libx264"

    # Calculate loop count (with buffer to ensure we have enough video)
    loop_count = int(audio_duration / loop_duration) + 2

    # Build filter complex
    # Scale video to target resolution, handling aspect ratio
    source_width = video_info.get("width", 1920)
    source_height = video_info.get("height", 1080)
    source_aspect = source_width / source_height
    target_aspect = width / height

    if source_aspect > target_aspect:
        # Source is wider - scale by height, crop width
        filter_complex = (
            f"[0:v]scale=-1:{height},"
            f"crop={width}:{height},"
            f"setpts=PTS-STARTPTS,"
            f"fps={LONGFORM_FRAME_RATE}[v]"
        )
    else:
        # Source is taller - scale by width, crop height
        filter_complex = (
            f"[0:v]scale={width}:-1,"
            f"crop={width}:{height},"
            f"setpts=PTS-STARTPTS,"
            f"fps={LONGFORM_FRAME_RATE}[v]"
        )

    # Audio filter - normalize loudness for sleep content
    audio_filter = f"loudnorm=I={SLEEP_VIDEO_LOUDNESS}:TP=-1.5:LRA=11"

    # Encoder-specific settings
    if "videotoolbox" in encoder:
        encoder_opts = ["-b:v", bitrate, "-tag:v", "hvc1"]
    elif "nvenc" in encoder:
        encoder_opts = ["-b:v", bitrate, "-preset", "p4", "-rc", "vbr"]
    else:
        # CPU encoding - use CRF for quality
        encoder_opts = ["-crf", "23", "-preset", "medium"]

    # Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        # Input: video (will be looped)
        "-stream_loop", str(loop_count),
        "-i", str(video_loop_path),
        # Input: audio
        "-i", str(audio_path),
        # Video filter
        "-filter_complex", filter_complex,
        # Audio filter
        "-af", audio_filter,
        # Map outputs
        "-map", "[v]",
        "-map", "1:a",
        # Video encoding
        "-c:v", encoder,
        *encoder_opts,
        "-pix_fmt", "yuv420p",
        # Audio encoding
        "-c:a", "aac",
        "-b:a", LONGFORM_AUDIO_BITRATE,
        # Duration (match audio exactly)
        "-t", str(audio_duration),
        # Output
        str(output_path)
    ]

    print(f"\n{'='*60}")
    print("Assembling video...")
    print(f"This will take a while for a {format_duration(audio_duration)} video...")
    print(f"{'='*60}\n")

    # Run FFmpeg with progress
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )

    # Monitor progress
    for line in process.stdout:
        # Look for time= in ffmpeg output
        if "time=" in line:
            # Extract time
            try:
                time_str = line.split("time=")[1].split()[0]
                # Parse HH:MM:SS.ms format
                parts = time_str.split(":")
                if len(parts) == 3:
                    current_secs = (
                        float(parts[0]) * 3600 +
                        float(parts[1]) * 60 +
                        float(parts[2])
                    )
                    progress = (current_secs / audio_duration) * 100
                    print(f"\rProgress: {progress:.1f}% ({format_duration(current_secs)} / {format_duration(audio_duration)})", end="")
            except (IndexError, ValueError):
                pass

    process.wait()
    print()  # New line after progress

    if process.returncode != 0:
        raise RuntimeError("Video assembly failed")

    # Verify output
    if not output_path.exists():
        raise RuntimeError("Output file was not created")

    output_info = get_video_info(str(output_path))
    output_duration = output_info.get("duration", 0)
    output_size = output_path.stat().st_size / (1024 * 1024 * 1024)  # GB

    print(f"\n{'='*60}")
    print("Video assembled successfully!")
    print(f"Output: {output_path}")
    print(f"Duration: {format_duration(output_duration)}")
    print(f"Resolution: {output_info.get('width', 0)}x{output_info.get('height', 0)}")
    print(f"Size: {output_size:.2f} GB")
    print(f"{'='*60}")

    return str(output_path)


def preview_assembly(project_dir: Path):
    """Preview what would be assembled without running FFmpeg"""
    audio_path = project_dir / "audio" / "full_narration.mp3"
    video_loop_path = project_dir / "assets" / "f1_car_loop.mp4"

    print(f"Project: {project_dir.name}")
    print(f"\n{'='*60}")
    print("INPUTS:")
    print(f"{'='*60}")

    # Audio info
    if audio_path.exists():
        duration = get_audio_duration(str(audio_path))
        size_mb = audio_path.stat().st_size / (1024 * 1024)
        print(f"\nAudio: {audio_path.name}")
        print(f"  Duration: {format_duration(duration)}")
        print(f"  Size: {size_mb:.1f} MB")
    else:
        print(f"\nAudio: NOT FOUND")
        print(f"  Expected: {audio_path}")
        print(f"  Run: python3 src/qwen_sleep_audio_generator.py --project {project_dir.name}")

    # Video loop info
    if video_loop_path.exists():
        info = get_video_info(str(video_loop_path))
        size_mb = video_loop_path.stat().st_size / (1024 * 1024)
        print(f"\nF1 Car Loop: {video_loop_path.name}")
        print(f"  Resolution: {info.get('width', 0)}x{info.get('height', 0)}")
        print(f"  Duration: {info.get('duration', 0):.1f}s (will loop)")
        print(f"  FPS: {info.get('fps', 30):.1f}")
        print(f"  Size: {size_mb:.1f} MB")
    else:
        print(f"\nF1 Car Loop: NOT FOUND")
        print(f"  Expected: {video_loop_path}")
        print(f"  Run: python3 src/download_f1_loop.py --project {project_dir.name}")

    # Estimate output
    print(f"\n{'='*60}")
    print("ESTIMATED OUTPUT:")
    print(f"{'='*60}")

    if audio_path.exists():
        duration = get_audio_duration(str(audio_path))
        # Rough estimates based on bitrate
        hd_size_gb = (12 * duration / 8) / 1024  # 12 Mbps
        fourk_size_gb = (20 * duration / 8) / 1024  # 20 Mbps

        print(f"\nHD (1080p):")
        print(f"  Resolution: 1920x1080")
        print(f"  Estimated size: ~{hd_size_gb:.1f} GB")
        print(f"  Encoding time: ~{duration/3600 * 0.5:.1f} hours (with GPU)")

        print(f"\n4K (2160p):")
        print(f"  Resolution: 3840x2160")
        print(f"  Estimated size: ~{fourk_size_gb:.1f} GB")
        print(f"  Encoding time: ~{duration/3600 * 1.5:.1f} hours (with GPU)")

    # Check encoder availability
    print(f"\n{'='*60}")
    print("ENCODER CHECK:")
    print(f"{'='*60}")
    detect_encoder()


def create_test_clip(project_dir: Path, duration: int = 60):
    """Create a short test clip to verify assembly works"""
    audio_path = project_dir / "audio" / "full_narration.mp3"
    video_loop_path = project_dir / "assets" / "f1_car_loop.mp4"
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)
    test_path = output_dir / "test_clip.mp4"

    if not audio_path.exists() or not video_loop_path.exists():
        print("Missing required files. Run --preview first to see what's needed.")
        return

    print(f"Creating {duration}s test clip...")

    video_info = get_video_info(str(video_loop_path))
    width = LONGFORM_OUTPUT_WIDTH_HD
    height = LONGFORM_OUTPUT_HEIGHT_HD

    encoder = detect_encoder()

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "5",
        "-i", str(video_loop_path),
        "-i", str(audio_path),
        "-filter_complex", f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", encoder,
        "-b:v", "8M",
        "-c:a", "aac",
        "-t", str(duration),
        str(test_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0 and test_path.exists():
        size_mb = test_path.stat().st_size / (1024 * 1024)
        print(f"\nTest clip created: {test_path}")
        print(f"Size: {size_mb:.1f} MB")
        print(f"\nPlay it to verify quality before running full assembly.")
    else:
        print(f"Test clip failed: {result.stderr}")


# ============================================================================
# Main Function
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Assemble sleep video with looping F1 car footage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview assembly (check inputs)
    python3 src/sleep_video_assembler.py --project f1-history-sleep --preview

    # Create short test clip
    python3 src/sleep_video_assembler.py --project f1-history-sleep --test

    # Assemble full video (HD)
    python3 src/sleep_video_assembler.py --project f1-history-sleep

    # Assemble full video (4K)
    python3 src/sleep_video_assembler.py --project f1-history-sleep --resolution 4k

    # Force specific encoder
    python3 src/sleep_video_assembler.py --project f1-history-sleep --encoder cpu
        """
    )

    parser.add_argument(
        "--project",
        required=True,
        help="Project name (folder in projects/)"
    )
    parser.add_argument(
        "--resolution",
        choices=["hd", "4k"],
        default="hd",
        help="Output resolution: hd (1080p) or 4k (2160p). Default: hd"
    )
    parser.add_argument(
        "--encoder",
        choices=["auto", "videotoolbox", "nvenc", "cpu"],
        default="auto",
        help="Video encoder. Default: auto-detect"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview assembly without running (check inputs)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Create 60s test clip to verify quality"
    )

    args = parser.parse_args()

    project_dir = Path(PROJECTS_DIR) / args.project
    if not project_dir.exists():
        print(f"Error: Project not found: {project_dir}")
        sys.exit(1)

    if args.preview:
        preview_assembly(project_dir)
    elif args.test:
        create_test_clip(project_dir)
    else:
        assemble_sleep_video(project_dir, args.resolution, args.encoder)


if __name__ == "__main__":
    main()
