#!/usr/bin/env python3
"""
Veo3 Video Generator - Generate AI videos using Google's Veo 3 API.

Uses the Gemini API to generate high-quality video clips for segments
where stock footage or images aren't suitable.

Setup:
1. Install: pip install google-genai
2. Get API key from https://aistudio.google.com/apikey
3. Save key to: shared/creds/google_ai or set GOOGLE_AI_API_KEY env var

Pricing (as of 2025):
- Veo 3 Fast: $0.15/second
- Veo 3 Standard: $0.40/second
- 8 second video = $1.20 (Fast) or $3.20 (Standard)
"""

import os
import subprocess
import sys
import time
from typing import Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check for google-genai library
VEO3_AVAILABLE = False
try:
    from google import genai
    from google.genai import types

    VEO3_AVAILABLE = True
except ImportError:
    pass


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


def is_veo3_available() -> Tuple[bool, str]:
    """
    Check if Veo3 is available and configured.

    Returns: (available, message)
    """
    if not VEO3_AVAILABLE:
        return (
            False,
            "google-genai library not installed. Run: pip install google-genai",
        )

    api_key = get_api_key("google_ai")
    if not api_key:
        return False, "Google AI API key not found. Add it to shared/creds/google_ai"

    return True, "Veo3 ready"


def generate_veo3_video(
    prompt: str,
    output_path: str,
    duration: int = 8,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    use_fast: bool = True,
    negative_prompt: Optional[str] = None,
    reference_image: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Generate a video using Google Veo 3 API.

    Args:
        prompt: Text description of the video to generate
        output_path: Path to save the generated video
        duration: Video duration in seconds (4, 6, or 8)
        aspect_ratio: "16:9" or "9:16"
        resolution: "720p" or "1080p" (1080p only for Veo 3.1)
        use_fast: Use Veo 3 Fast (cheaper, quicker) vs Standard
        negative_prompt: Content to avoid generating
        reference_image: Path to image for image-to-video generation

    Returns:
        (success, error_message)
    """
    if not VEO3_AVAILABLE:
        return False, "google-genai library not installed"

    api_key = get_api_key("google_ai")
    if not api_key:
        return False, "Google AI API key not found"

    # Validate duration
    if duration not in [4, 6, 8]:
        duration = 8

    try:
        # Initialize client
        client = genai.Client(api_key=api_key)

        # Choose model (updated Mar 2026: -preview suffix → -001)
        if use_fast:
            model = "veo-3.0-fast-generate-001"
        else:
            model = "veo-3.0-generate-001"

        # Build config
        config_params = {
            "aspect_ratio": aspect_ratio,
            "duration_seconds": duration,
        }

        if negative_prompt:
            config_params["negative_prompt"] = negative_prompt

        if resolution == "1080p":
            config_params["resolution"] = "1080p"

        config = types.GenerateVideosConfig(**config_params)

        # Generate video
        if reference_image and os.path.exists(reference_image):
            # Image-to-video generation
            with open(reference_image, "rb") as f:
                image_data = f.read()

            operation = client.models.generate_videos(
                model=model,
                prompt=prompt,
                image=image_data,
                config=config,
            )
        else:
            # Text-to-video generation
            operation = client.models.generate_videos(
                model=model,
                prompt=prompt,
                config=config,
            )

        # Wait for completion (with timeout)
        max_wait = 300  # 5 minutes max
        waited = 0
        poll_interval = 10

        while not operation.done and waited < max_wait:
            time.sleep(poll_interval)
            waited += poll_interval
            operation = client.operations.get(operation)

            if waited % 30 == 0:
                print(f"      Veo3 generating... ({waited}s elapsed)")

        if not operation.done:
            return False, f"Timeout waiting for Veo3 (>{max_wait}s)"

        if not operation.result or not operation.result.generated_videos:
            return False, "No video generated"

        # Download and save the video
        generated_video = operation.result.generated_videos[0]
        client.files.download(file=generated_video.video)
        generated_video.video.save(output_path)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
            return True, ""

        return False, "Downloaded file is too small or missing"

    except Exception as e:
        return False, f"Veo3 error: {str(e)}"


def generate_f1_scene(
    scene_description: str,
    output_path: str,
    duration: int = 8,
    width: int = 1920,
    height: int = 1080,
    use_fast: bool = True,
) -> Tuple[bool, str]:
    """
    Generate an F1-themed video scene using Veo3.

    Adds F1-specific styling to the prompt for better results.

    Args:
        scene_description: What the scene should show
        output_path: Path to save the video
        duration: Video duration (4, 6, or 8 seconds)
        width, height: Output dimensions (for aspect ratio)
        use_fast: Use faster/cheaper model

    Returns:
        (success, error_message)
    """
    # Determine aspect ratio
    if width > height:
        aspect_ratio = "16:9"
    else:
        aspect_ratio = "9:16"

    # Enhance prompt with F1 styling
    enhanced_prompt = (
        f"Cinematic, high-quality Formula 1 motorsport footage: {scene_description}. "
        f"Professional broadcast quality, dramatic lighting, smooth camera movement, "
        f"realistic physics and motion blur. 4K cinematic look."
    )

    # F1-specific negative prompt
    negative_prompt = (
        "text, watermark, logo overlay, low quality, blurry, "
        "unrealistic physics, cartoon, animation, CGI look"
    )

    return generate_veo3_video(
        prompt=enhanced_prompt,
        output_path=output_path,
        duration=duration,
        aspect_ratio=aspect_ratio,
        resolution="720p",  # 720p is default and most reliable
        use_fast=use_fast,
        negative_prompt=negative_prompt,
    )


def process_veo3_video(
    input_path: str, output_path: str, target_duration: float, width: int, height: int
) -> bool:
    """
    Process Veo3 video to match target specs (duration, resolution).

    Veo3 generates fixed durations (4/6/8s), so we may need to trim or loop.
    """
    # Get actual duration
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        input_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    actual_duration = float(result.stdout.strip()) if result.stdout.strip() else 0

    if actual_duration <= 0:
        return False

    # Build filter
    filters = [
        f"scale={width}:{height}:force_original_aspect_ratio=increase",
        f"crop={width}:{height}",
        "setsar=1",
        "format=yuv420p",
    ]

    # Handle duration mismatch
    if target_duration <= actual_duration:
        # Trim to target duration
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-t",
            str(target_duration),
            "-vf",
            ",".join(filters),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-an",  # Remove audio (we'll add voiceover separately)
            output_path,
        ]
    else:
        # Need to extend - use slow-motion or loop
        speed_factor = actual_duration / target_duration
        if speed_factor >= 0.5:
            # Slow down the video
            filters.insert(0, f"setpts={1 / speed_factor}*PTS")
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-vf",
                ",".join(filters),
                "-t",
                str(target_duration),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "20",
                "-an",
                output_path,
            ]
        else:
            # Loop the video
            loops_needed = int(target_duration / actual_duration) + 1
            cmd = [
                "ffmpeg",
                "-y",
                "-stream_loop",
                str(loops_needed),
                "-i",
                input_path,
                "-t",
                str(target_duration),
                "-vf",
                ",".join(filters),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "20",
                "-an",
                output_path,
            ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 10000


# Example prompts for different F1 scenarios
VEO3_PROMPT_TEMPLATES = {
    "pit_stop": "Formula 1 pit stop in progress, mechanics changing tires in under 2 seconds, dramatic lighting, smoke and tire marks",
    "race_start": "Formula 1 race start, cars launching off the grid, rear wings and DRS, dramatic slow motion",
    "overtake": "Formula 1 overtaking maneuver, two cars wheel to wheel through a corner, motion blur, broadcast angle",
    "engine": "Close-up of Formula 1 power unit, hybrid engine technology, turbo and MGU-K visible, technical detail",
    "fuel": "Sustainable fuel production facility, industrial chemistry equipment, modern laboratory, green technology",
    "wind_tunnel": "F1 car in wind tunnel testing, aerodynamic visualization, smoke trails over bodywork",
    "factory": "F1 team factory, engineers working on car components, high-tech manufacturing, carbon fiber",
    "podium": "F1 podium celebration, champagne spray, trophies, confetti, dramatic lighting",
    "circuit": "Aerial view of F1 circuit, cars racing through corners, beautiful landscape, golden hour lighting",
    "technology": "Futuristic motorsport technology visualization, data streams, holographic displays, innovation",
}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate video using Veo3")
    parser.add_argument("--prompt", required=True, help="Video description")
    parser.add_argument("--output", required=True, help="Output video path")
    parser.add_argument(
        "--duration", type=int, default=8, choices=[4, 6, 8], help="Duration in seconds"
    )
    parser.add_argument("--fast", action="store_true", help="Use Veo 3 Fast (cheaper)")
    parser.add_argument(
        "--check", action="store_true", help="Check if Veo3 is available"
    )
    args = parser.parse_args()

    if args.check:
        available, message = is_veo3_available()
        print(f"Veo3 available: {available}")
        print(f"Message: {message}")
        sys.exit(0 if available else 1)

    print(f"Generating {args.duration}s video...")
    success, error = generate_f1_scene(
        args.prompt, args.output, duration=args.duration, use_fast=args.fast or True
    )

    if success:
        print(f"Success! Video saved to {args.output}")
    else:
        print(f"Failed: {error}")
        sys.exit(1)
