#!/usr/bin/env python3
"""
Logo Intro Generator for Long-Form F1 Content

Uses the logo2.mp4 animation (F1 car burnout + logo reveal), sped up to
match the voiceover duration, scaled to the target resolution.
"""

import os
import subprocess

# Asset paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO2_VIDEO = os.path.join(BASE_DIR, "shared", "assets", "logo", "logo2.mp4")
INTRO_VOICEOVER = os.path.join(BASE_DIR, "shared", "audio", "intro_voiceover.mp3")
ENGINE_REV_SFX = os.path.join(BASE_DIR, "shared", "sfx", "engine_rev.mp3")
FPS = 30


def _get_duration(path: str) -> float:
    """Get media file duration in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def create_intro_video(output_path: str, width: int, height: int) -> bool:
    """Create intro: logo2.mp4 sped up to match voiceover + engine rev SFX.

    The full logo2.mp4 animation is shown sped up so its duration matches the
    voiceover audio ("You are watching F1 Burnouts"). This ensures the complete
    animation plays without cutting any frames.

    Args:
        output_path: Where to save the intro video
        width: Video width (e.g., 3840 for 4K)
        height: Video height (e.g., 2160 for 4K)

    Returns:
        True if intro was created successfully
    """
    if not os.path.exists(LOGO2_VIDEO):
        print(f"    Logo2 video not found: {LOGO2_VIDEO}")
        return False

    try:
        from src.image_video_assembler import gpu_enc_args

        enc_args = gpu_enc_args()
    except ImportError:
        enc_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "23"]

    video_dur = _get_duration(LOGO2_VIDEO)
    has_vo = os.path.exists(INTRO_VOICEOVER)
    has_sfx = os.path.exists(ENGINE_REV_SFX)

    # Determine target duration from voiceover (+ 0.5s padding for delay)
    if has_vo:
        vo_dur = _get_duration(INTRO_VOICEOVER)
        target_dur = vo_dur + 0.5  # 0.5s delay before VO starts
    else:
        target_dur = 4.0  # fallback

    # Speed factor to fit full video into target duration
    speed = video_dur / target_dur if video_dur > 0 else 1.0
    pts_factor = 1.0 / speed  # setpts multiplier (< 1.0 = faster)

    # Build video filter: speed up + scale to target resolution
    video_filter = (
        f"[0:v]setpts={pts_factor:.4f}*PTS,"
        f"scale={width}:{height}:flags=lanczos,setsar=1,fps={FPS},"
        f"format=yuv420p[outv]"
    )

    # Build audio inputs and filter
    audio_inputs = []
    audio_filter = ""
    audio_map = []

    if has_vo and has_sfx:
        audio_inputs = ["-i", INTRO_VOICEOVER, "-i", ENGINE_REV_SFX]
        audio_filter = (
            "[1:a]adelay=500|500,volume=1.0[vo];"
            "[2:a]volume=0.6[sfx];"
            "[vo][sfx]amix=inputs=2:duration=longest:normalize=0[aout]"
        )
        audio_map = ["-map", "[aout]"]
    elif has_vo:
        audio_inputs = ["-i", INTRO_VOICEOVER]
        audio_filter = "[1:a]adelay=500|500[aout]"
        audio_map = ["-map", "[aout]"]
    elif has_sfx:
        audio_inputs = ["-i", ENGINE_REV_SFX]
        audio_filter = "[1:a]volume=0.7[aout]"
        audio_map = ["-map", "[aout]"]

    if audio_filter:
        full_filter = video_filter + ";" + audio_filter
    else:
        full_filter = video_filter

    # If no audio assets, add silent audio
    if not audio_inputs:
        audio_inputs = ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        audio_map = ["-map", "1:a"]
        full_filter = video_filter

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        LOGO2_VIDEO,
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
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        return True

    print(f"    Intro failed: {result.stderr[-200:]}")
    return False
