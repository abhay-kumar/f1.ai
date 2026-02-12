#!/usr/bin/env python3
"""
Animated Logo Intro Generator for Long-Form F1 Content

Creates a 3-second animated intro using FFmpeg:
1. 0-0.5s: Black screen, engine rev SFX starts
2. 0.5-2.0s: Logo scales from small to full size with zoom animation
3. 2.0-3.0s: Logo holds, "F1 BURNOUTS" text fades in below

Pure FFmpeg approach — no Node.js/Remotion dependency.
"""

import os
import subprocess
from typing import Tuple

# Asset paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "shared", "assets", "logo", "logo.png")
F1_FONT = os.path.join(BASE_DIR, "shared", "fonts", "Formula1-Bold.ttf")
ENGINE_REV_SFX = os.path.join(BASE_DIR, "shared", "sfx", "engine_rev.mp3")
LOGO_SWOOSH_SFX = os.path.join(BASE_DIR, "shared", "sfx", "logo_swoosh.mp3")

INTRO_DURATION = 3.0
FPS = 30


def create_intro_video(output_path: str, width: int, height: int) -> bool:
    """Create an animated logo intro video.

    Animation sequence:
    - 0.0-0.5s: Black screen (engine rev SFX rumbles in)
    - 0.5-2.0s: Logo zooms from 30% to 100% scale (swoosh SFX at 0.5s)
    - 2.0-3.0s: Logo at full size, "F1 BURNOUTS" text fades in

    Args:
        output_path: Where to save the intro video
        width: Video width (e.g., 3840 for 4K)
        height: Video height (e.g., 2160 for 4K)

    Returns:
        True if intro was created successfully
    """
    if not os.path.exists(LOGO_PATH):
        print(f"    Logo not found: {LOGO_PATH}")
        return False

    # Import GPU encoder
    try:
        from src.image_video_assembler import gpu_enc_args

        enc_args = gpu_enc_args()
    except ImportError:
        enc_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "23"]

    total_frames = int(INTRO_DURATION * FPS)

    # Logo target size: 30% of video height
    logo_h = int(height * 0.30)
    logo_w = int(logo_h * 1.25)  # Logo is roughly 1.25:1 aspect ratio

    # Text sizes based on resolution
    if width >= 3840:
        text_size = 72
    else:
        text_size = 48

    text_y = int(height * 0.58)

    # FFmpeg filter:
    # 1. Create black background
    # 2. Scale logo to target size
    # 3. Use zoompan on logo for scale animation (0.3x → 1.0x from t=0.5 to t=2.0)
    # 4. Overlay logo centered on background
    # 5. Add "F1 BURNOUTS" text with fade-in at t=2.0

    # zoompan expression: logo visible from frame 15 (0.5s), scales up until frame 60 (2.0s)
    # Before frame 15: zoom very high (logo invisible/tiny)
    # Frame 15-60: zoom from 3.3 to 1.0 (inverse = scale from 0.3 to 1.0)
    # After frame 60: zoom = 1.0 (full size)
    zoom_expr = (
        f"if(lt(on,{int(0.5 * FPS)}),10,"  # Before 0.5s: zoomed out (invisible)
        f"if(lt(on,{int(2.0 * FPS)}),"
        f"1+2.3*(1-(on-{int(0.5 * FPS)})/({int(2.0 * FPS)}-{int(0.5 * FPS)})),"  # 0.5-2.0s: zoom 3.3→1.0
        f"1))"  # After 2.0s: full size
    )

    filter_complex = (
        # Black background
        f"color=black:s={width}x{height}:d={INTRO_DURATION}:r={FPS}[bg];"
        # Scale logo and apply zoom animation
        f"[1:v]scale={logo_w * 4}:{logo_h * 4},"
        f"zoompan=z='{zoom_expr}':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s={logo_w}x{logo_h}:fps={FPS},"
        f"format=yuva420p[logo];"
        # Overlay logo centered, with enable for timing (visible from 0.5s)
        f"[bg][logo]overlay=(W-w)/2:(H-h)/2-{int(height * 0.05)}:enable='gte(t,0.5)',"
        # Add channel name text with fade-in at 2.0s
        f"drawtext=text='F1 BURNOUTS':"
        f"fontfile={F1_FONT}:fontsize={text_size}:"
        f"fontcolor=white@{{alpha}}:x=(w-text_w)/2:y={text_y}:"
        f"alpha='if(lt(t,2.0),0,min(1,(t-2.0)/0.5))',"
        f"format=yuv420p[outv]"
    )

    # Fix the alpha expression — FFmpeg uses single braces
    filter_complex = filter_complex.replace("{alpha}", "")
    filter_complex = filter_complex.replace("fontcolor=white@:", "fontcolor=white:")

    # Build audio: mix engine_rev (starts at 0s) + logo_swoosh (starts at 0.5s)
    has_engine = os.path.exists(ENGINE_REV_SFX)
    has_swoosh = os.path.exists(LOGO_SWOOSH_SFX)

    audio_inputs = []
    audio_filter_parts = []

    if has_engine and has_swoosh:
        audio_inputs = ["-i", ENGINE_REV_SFX, "-i", LOGO_SWOOSH_SFX]
        audio_filter_parts = [
            f"[2:a]atrim=0:{INTRO_DURATION},volume=0.7[rev]",
            f"[3:a]adelay=500|500,volume=0.8[swsh]",
            f"[rev][swsh]amix=inputs=2:duration=first:normalize=0[aout]",
        ]
        audio_map = ["-map", "[aout]"]
    elif has_engine:
        audio_inputs = ["-i", ENGINE_REV_SFX]
        audio_filter_parts = [
            f"[2:a]atrim=0:{INTRO_DURATION},volume=0.7[aout]",
        ]
        audio_map = ["-map", "[aout]"]
    else:
        # Silent audio fallback
        audio_inputs = []
        audio_filter_parts = []
        audio_map = []

    # Combine video and audio filters
    if audio_filter_parts:
        full_filter = filter_complex + ";" + ";".join(audio_filter_parts)
    else:
        full_filter = filter_complex

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=black:s={width}x{height}:d={INTRO_DURATION}:r={FPS}",
        "-loop",
        "1",
        "-i",
        LOGO_PATH,
        *audio_inputs,
        "-filter_complex",
        full_filter,
        "-map",
        "[outv]",
        *audio_map,
        *enc_args,
        "-c:a",
        "aac",
        "-b:a",
        "256k",
        "-t",
        str(INTRO_DURATION),
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        return True

    # If complex filter failed, try simpler version without zoompan
    print("    Retrying with simplified intro...")
    simple_filter = (
        f"color=black:s={width}x{height}:d={INTRO_DURATION}:r={FPS}[bg];"
        f"[1:v]scale={logo_w}:{logo_h}[logo];"
        f"[bg][logo]overlay=(W-w)/2:(H-h)/2-{int(height * 0.05)}:enable='gte(t,0.5)',"
        f"drawtext=text='F1 BURNOUTS':"
        f"fontfile={F1_FONT}:fontsize={text_size}:"
        f"fontcolor=white:x=(w-text_w)/2:y={text_y}:"
        f"enable='gte(t,2.0)',"
        f"format=yuv420p[outv]"
    )

    if audio_filter_parts:
        simple_filter = simple_filter + ";" + ";".join(audio_filter_parts)

    cmd_simple = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=black:s={width}x{height}:d={INTRO_DURATION}:r={FPS}",
        "-loop",
        "1",
        "-i",
        LOGO_PATH,
        *audio_inputs,
        "-filter_complex",
        simple_filter,
        "-map",
        "[outv]",
        *audio_map,
        *enc_args,
        "-c:a",
        "aac",
        "-b:a",
        "256k",
        "-t",
        str(INTRO_DURATION),
        output_path,
    ]

    result = subprocess.run(cmd_simple, capture_output=True, text=True)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
