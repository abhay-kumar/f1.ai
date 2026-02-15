#!/usr/bin/env python3
"""
Shot Assembler - Shared module for multi-shot segment assembly

Professional video editing concepts:
- Shot: A single continuous piece of footage/visual within a segment
- Shot List: Ordered sequence of shots with timing and transitions
- B-Roll: Supplementary footage that illustrates the narration
- Transition: How we move between shots (cut, dissolve, wipe, etc.)
- Text Cue: The portion of narration text a shot covers (drives timing)

This module provides shared logic used by both video_assembler.py (shorts)
and image_video_assembler.py (long-form) to assemble multi-shot segments.
"""

import os
import random
import subprocess
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CONSTANTS
# ============================================================================

# Minimum shot duration (seconds) - prevents jarring micro-cuts
MIN_SHOT_DURATION = 1.5  # For shorts (fast-paced)
MIN_SHOT_DURATION_LONGFORM = 2.0  # For long-form (slower pacing)

# Ken Burns effects for image shots
KEN_BURNS_EFFECTS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]

# FFmpeg xfade transition mapping: professional term -> FFmpeg transition name
TRANSITION_MAP = {
    "cut": None,  # No transition, instant switch (0 duration)
    "cross_dissolve": "fade",  # Standard dissolve
    "wipe_left": "wipeleft",  # Left wipe
    "wipe_right": "wiperight",  # Right wipe
    "wipe_up": "wipeup",  # Upward wipe
    "wipe_down": "wipedown",  # Downward wipe
    "whip_pan": "smoothleft",  # Fast horizontal wipe simulating camera whip
    "fade_to_black": "fadeblack",  # Fade through black
    "fade_to_white": "fadewhite",  # Fade through white
    "slide_left": "slideleft",  # Slide left
    "slide_right": "slideright",  # Slide right
    "circle_open": "circleopen",  # Iris open
    "circle_close": "circleclose",  # Iris close
}

# Default transition durations (seconds)
TRANSITION_DEFAULTS = {
    "cut": 0.0,
    "cross_dissolve": 0.4,
    "wipe_left": 0.3,
    "wipe_right": 0.3,
    "wipe_up": 0.3,
    "wipe_down": 0.3,
    "whip_pan": 0.2,
    "fade_to_black": 0.3,
    "fade_to_white": 0.3,
    "slide_left": 0.3,
    "slide_right": 0.3,
    "circle_open": 0.4,
    "circle_close": 0.4,
}

# Valid source types for shots
VALID_SOURCE_TYPES = [
    "youtube_clip",
    "image",
    "quote_overlay",
    "veo3_video",
    "remotion_animation",
    "graphic",
]


# ============================================================================
# SEGMENT NORMALIZATION
# ============================================================================


def normalize_segment(segment: dict) -> dict:
    """Ensure every segment has a shots array, even legacy single-footage ones.

    If the segment already has a 'shots' array, returns it unchanged.
    Otherwise, wraps the legacy footage_query/footage/footage_start fields
    into a single-element shots array covering the entire segment.

    This provides backwards compatibility -- all downstream code only needs
    to handle the shots array format.
    """
    if "shots" in segment and segment["shots"]:
        return segment

    # Legacy format: single footage = single shot covering entire segment
    shot = {
        "label": segment.get("visual", segment.get("context", "Main shot")),
        "text_cue": segment.get("text", ""),
        "source_type": "youtube_clip",
        "transition_in": "cut",
    }

    # Carry over legacy fields
    if segment.get("footage_query"):
        shot["footage_query"] = segment["footage_query"]
    if segment.get("footage"):
        shot["footage"] = segment["footage"]
    if "footage_start" in segment:
        shot["footage_start"] = segment["footage_start"]
    if segment.get("image_query"):
        shot["source_type"] = "image"
        shot["image_query"] = segment["image_query"]

    segment["shots"] = [shot]
    return segment


# ============================================================================
# SHOT TIMING CALCULATION
# ============================================================================


def calculate_shot_timings(
    segment_text: str,
    shots: List[dict],
    audio_duration: float,
    min_duration: float = MIN_SHOT_DURATION,
) -> List[Tuple[float, float]]:
    """Calculate actual start/end times for each shot based on text_cue position.

    Uses proportional character-position mapping: since speech rate is roughly
    proportional to character count, the character position of each text_cue
    in the segment text maps to a proportional time offset.

    Args:
        segment_text: Full narration text of the segment
        shots: List of shot dicts with 'text_cue' and optional 'duration_weight'
        audio_duration: Total audio duration in seconds
        min_duration: Minimum shot duration in seconds

    Returns:
        List of (start_time, end_time) tuples, one per shot
    """
    if not shots:
        return []

    if len(shots) == 1:
        return [(0.0, audio_duration)]

    text_lower = segment_text.lower()
    total_chars = len(segment_text)

    if total_chars == 0:
        # Edge case: empty text, distribute evenly
        even_dur = audio_duration / len(shots)
        return [(i * even_dur, (i + 1) * even_dur) for i in range(len(shots))]

    # Calculate raw timing from text_cue positions
    raw_timings = []
    for shot in shots:
        if "duration_weight" in shot:
            raw_timings.append({"mode": "weight", "weight": shot["duration_weight"]})
        else:
            cue = shot.get("text_cue", "")
            cue_lower = cue.lower()
            start_pos = text_lower.find(cue_lower)

            if start_pos >= 0:
                end_pos = start_pos + len(cue)
                raw_timings.append(
                    {
                        "mode": "position",
                        "start_frac": start_pos / total_chars,
                        "end_frac": min(end_pos / total_chars, 1.0),
                    }
                )
            else:
                # text_cue not found -- fallback to even distribution
                raw_timings.append({"mode": "weight", "weight": 1.0})

    # Check if all timings use weight mode (fallback)
    all_weights = all(t["mode"] == "weight" for t in raw_timings)

    if all_weights:
        # Distribute by weights
        total_weight = sum(t["weight"] for t in raw_timings)
        if total_weight == 0:
            total_weight = len(shots)
        timings = []
        current = 0.0
        for t in raw_timings:
            dur = audio_duration * (t["weight"] / total_weight)
            timings.append((current, current + dur))
            current += dur
        return _clamp_timings(timings, audio_duration, min_duration)

    # Position-based timing: use start_frac of each shot
    timings = []
    for i, t in enumerate(raw_timings):
        if t["mode"] == "position":
            start_time = t["start_frac"] * audio_duration
            if i + 1 < len(raw_timings) and raw_timings[i + 1]["mode"] == "position":
                end_time = raw_timings[i + 1]["start_frac"] * audio_duration
            else:
                end_time = t["end_frac"] * audio_duration
        else:
            # Weight-mode shot sandwiched between position-mode shots
            # Will be resolved in gap-filling below
            if timings:
                start_time = timings[-1][1]
            else:
                start_time = 0.0
            end_time = start_time  # Zero-duration placeholder
        timings.append((start_time, end_time))

    # Ensure last shot extends to end of audio
    if timings:
        last_start, _ = timings[-1]
        timings[-1] = (last_start, audio_duration)

    # Fill gaps: ensure each shot starts where the previous one ended
    filled = []
    for i, (start, end) in enumerate(timings):
        if i == 0:
            actual_start = 0.0
        else:
            actual_start = filled[-1][1]

        if i == len(timings) - 1:
            actual_end = audio_duration
        elif i + 1 < len(timings):
            actual_end = timings[i + 1][0] if timings[i + 1][0] > actual_start else end
        else:
            actual_end = end

        if actual_end <= actual_start:
            actual_end = actual_start + min_duration

        filled.append((actual_start, actual_end))

    return _clamp_timings(filled, audio_duration, min_duration)


def _clamp_timings(
    timings: List[Tuple[float, float]],
    audio_duration: float,
    min_duration: float,
) -> List[Tuple[float, float]]:
    """Clamp shot timings to ensure minimum duration and full coverage.

    Adjusts timings so that:
    - No shot is shorter than min_duration
    - Shots are contiguous (no gaps)
    - Total coverage equals audio_duration
    """
    if not timings:
        return timings

    # If total duration available is less than min_duration * num_shots,
    # just distribute evenly
    if audio_duration < min_duration * len(timings):
        even_dur = audio_duration / len(timings)
        return [(i * even_dur, (i + 1) * even_dur) for i in range(len(timings))]

    # Enforce minimum duration by stealing from neighbors
    adjusted = list(timings)
    for i in range(len(adjusted)):
        start, end = adjusted[i]
        dur = end - start
        if dur < min_duration:
            deficit = min_duration - dur
            adjusted[i] = (start, start + min_duration)
            # Push subsequent shots forward
            for j in range(i + 1, len(adjusted)):
                s, e = adjusted[j]
                adjusted[j] = (s + deficit, e + deficit)

    # Clamp last shot to audio_duration
    last_start, _ = adjusted[-1]
    if last_start >= audio_duration:
        # Redistribution needed -- fall back to even split
        even_dur = audio_duration / len(adjusted)
        return [(i * even_dur, (i + 1) * even_dur) for i in range(len(adjusted))]
    adjusted[-1] = (last_start, audio_duration)

    # Ensure contiguous coverage
    result = []
    for i, (start, end) in enumerate(adjusted):
        if i == 0:
            actual_start = 0.0
        else:
            actual_start = result[-1][1]
        actual_end = end if end > actual_start else actual_start + min_duration
        if i == len(adjusted) - 1:
            actual_end = audio_duration
        result.append((actual_start, actual_end))

    return result


# ============================================================================
# SHOT CLIP CREATION (source-type routing)
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


def create_blurpad_clip(
    footage_path: str,
    output_path: str,
    duration: float,
    start_time: float,
    width: int,
    height: int,
    gpu_encoder: str = "h264_videotoolbox",
    gpu_flags: list = None,
) -> bool:
    """Create a blur-pad clip for shorts (9:16) from footage.

    Blurred, zoomed-in version of the footage as background,
    with the sharp original overlaid centered.
    """
    if not os.path.exists(footage_path):
        return False

    if gpu_flags is None:
        gpu_flags = ["-allow_sw", "1"]

    # Extra footage to avoid freeze at end
    trim_duration = duration + 1.0

    filter_complex = (
        f"[0:v]trim=start={start_time}:duration={trim_duration},setpts=PTS-STARTPTS,"
        f"split=2[for_bg][for_fg];"
        f"[for_bg]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},boxblur=20:5[bg];"
        f"[for_fg]scale={width}:{height}:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[out]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        footage_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-c:v",
        gpu_encoder,
        *gpu_flags,
        "-r",
        "30",
        "-t",
        str(duration),
        "-an",
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


def _get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """Get image width and height using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        image_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        w, h = result.stdout.strip().split("x")
        return int(w), int(h)
    except (ValueError, AttributeError):
        return 0, 0


def create_kenburns_clip(
    image_path: str,
    output_path: str,
    duration: float,
    width: int,
    height: int,
    effect: str = "zoom_in",
    gpu_encoder: str = "h264_videotoolbox",
    gpu_flags: list = None,
) -> bool:
    """Create a Ken Burns clip from a static image with blurred background.

    For images that don't match the target aspect ratio (e.g., landscape image
    in 9:16 frame), creates a blurred background and overlays the animated
    image at correct aspect ratio. Prevents unnatural stretching.
    """
    if not os.path.exists(image_path):
        return False

    if gpu_flags is None:
        gpu_flags = ["-allow_sw", "1"]

    fps = 30
    total_frames = int(duration * fps)

    # Get source image dimensions to calculate proper foreground size
    src_w, src_h = _get_image_dimensions(image_path)
    target_aspect = width / height  # 0.5625 for 9:16

    if src_w > 0 and src_h > 0:
        src_aspect = src_w / src_h
        # Calculate foreground size that fits within frame without stretching
        if abs(src_aspect - target_aspect) < 0.05:
            # Close enough to target aspect — fill the frame
            fg_w, fg_h = width, height
        elif src_aspect > target_aspect:
            # Landscape image in portrait frame — fit to width, letterbox vertically
            fg_w = width
            fg_h = int(width / src_aspect)
            # Ensure even dimensions
            fg_h = fg_h - (fg_h % 2)
        else:
            # Portrait image taller than frame — fit to height, pillarbox horizontally
            fg_h = height
            fg_w = int(height * src_aspect)
            fg_w = fg_w - (fg_w % 2)
    else:
        fg_w, fg_h = width, height

    needs_blur_bg = fg_w != width or fg_h != height

    # Build zoompan expression based on effect
    if effect == "zoom_in":
        zoom_expr = "min(zoom+0.002,1.15)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif effect == "zoom_out":
        zoom_expr = "max(1.15-on*0.002,1.0)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif effect == "pan_left":
        zoom_expr = "1.1"
        x_expr = (
            f"max(0,(iw*1.1-iw)*{total_frames - 1}-on*(iw*1.1-iw))/{total_frames - 1}"
        )
        y_expr = "ih/2-(ih/zoom/2)"
    elif effect == "pan_right":
        zoom_expr = "1.1"
        x_expr = f"on*(iw*1.1-iw)/{total_frames - 1}"
        y_expr = "ih/2-(ih/zoom/2)"
    else:
        zoom_expr = "min(zoom+0.002,1.15)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    if needs_blur_bg:
        # Two-layer approach: blurred background + Ken Burns foreground
        filter_complex = (
            # Background: scale up, crop to fill, blur heavily, force fps
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},boxblur=25:5,setsar=1,fps={fps}[bg];"
            # Foreground: Ken Burns at correct aspect ratio
            f"[0:v]zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}'"
            f":d={total_frames}:s={fg_w}x{fg_h}:fps={fps}[fg];"
            # Overlay centered
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[out]"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[out]",
            "-c:v",
            gpu_encoder,
            *gpu_flags,
            "-r",
            str(fps),
            "-t",
            str(duration),
            "-an",
            output_path,
        ]
    else:
        # Image matches target aspect — full frame zoompan (no stretching)
        filter_vf = (
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}'"
            f":d={total_frames}:s={width}x{height}:fps={fps},"
            f"format=yuv420p"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-vf",
            filter_vf,
            "-c:v",
            gpu_encoder,
            *gpu_flags,
            "-r",
            str(fps),
            "-t",
            str(duration),
            "-an",
            output_path,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not os.path.exists(output_path):
        # Fallback: simpler scale+crop without animation
        filter_simple = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1,format=yuv420p"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-vf",
            filter_simple,
            "-c:v",
            gpu_encoder,
            *gpu_flags,
            "-t",
            str(duration),
            "-r",
            str(fps),
            "-an",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, text=True)

    return os.path.exists(output_path)


def create_quote_clip(
    output_path: str,
    quote_text: str,
    speaker_name: str,
    duration: float,
    width: int,
    height: int,
    gpu_encoder: str = "h264_videotoolbox",
    gpu_flags: list = None,
    font_path: str = None,
) -> bool:
    """Create a quote overlay clip with speaker name and quote text.

    Dark background with centered quote text and speaker attribution.
    """
    if gpu_flags is None:
        gpu_flags = ["-allow_sw", "1"]

    if font_path is None:
        font_path = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"

    # Escape text for FFmpeg
    safe_quote = (
        quote_text.replace("'", "\u2019").replace(":", "\\:").replace("\\", "\\\\")
    )
    safe_speaker = (
        speaker_name.replace("'", "\u2019").replace(":", "\\:").replace("\\", "\\\\")
    )

    # Wrap quote text
    max_chars = 30 if width <= 1080 else 45
    words = safe_quote.split()
    lines = []
    current = []
    for word in words:
        if sum(len(w) for w in current) + len(current) + len(word) <= max_chars:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    font_size = 48 if width <= 1080 else 72
    line_height = int(font_size * 1.4)
    total_text_height = len(lines) * line_height + 80  # +80 for speaker name
    start_y = (height - total_text_height) // 2

    # Build drawtext filters
    drawtext_parts = []
    for i, line in enumerate(lines):
        y_pos = start_y + i * line_height
        drawtext_parts.append(
            f"drawtext=text='{line}':"
            f"fontfile={font_path}:"
            f"fontsize={font_size}:fontcolor=white:"
            f"x=(w-text_w)/2:y={y_pos}"
        )

    # Speaker name in red
    speaker_y = start_y + len(lines) * line_height + 30
    speaker_font_size = int(font_size * 0.7)
    drawtext_parts.append(
        f"drawtext=text='— {safe_speaker}':"
        f"fontfile={font_path}:"
        f"fontsize={speaker_font_size}:fontcolor=#E8002D:"
        f"x=(w-text_w)/2:y={speaker_y}"
    )

    filter_str = ",".join(drawtext_parts)

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=#1a1a1a:s={width}x{height}:d={duration}:r=30",
        "-vf",
        filter_str + ",format=yuv420p",
        "-c:v",
        gpu_encoder,
        *gpu_flags,
        "-r",
        "30",
        "-an",
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


def create_longform_clip(
    footage_path: str,
    output_path: str,
    duration: float,
    start_time: float,
    width: int,
    height: int,
    gpu_encoder: str = "h264_videotoolbox",
    gpu_flags: list = None,
) -> bool:
    """Create a scale-and-crop clip for long-form (16:9) from footage."""
    if not os.path.exists(footage_path):
        return False

    if gpu_flags is None:
        gpu_flags = ["-allow_sw", "1"]

    trim_duration = duration + 1.0

    filter_complex = (
        f"trim=start={start_time}:duration={trim_duration},setpts=PTS-STARTPTS,"
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1,format=yuv420p"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        footage_path,
        "-vf",
        filter_complex,
        "-c:v",
        gpu_encoder,
        *gpu_flags,
        "-r",
        "30",
        "-t",
        str(duration),
        "-an",
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


def create_shot_clip(
    shot: dict,
    clip_path: str,
    duration: float,
    footage_dir: str,
    width: int,
    height: int,
    is_shorts: bool = False,
    gpu_encoder: str = "h264_videotoolbox",
    gpu_flags: list = None,
) -> bool:
    """Create a video clip for a single shot based on its source_type.

    Routes to the appropriate clip creation function based on the shot's
    source type (youtube_clip, image, quote_overlay, etc.).

    Args:
        shot: Shot dict with source_type and relevant fields
        clip_path: Output path for the generated clip
        duration: Target duration in seconds
        footage_dir: Directory containing footage/image files
        width: Output width in pixels
        height: Output height in pixels
        is_shorts: True for 9:16 vertical (blur-pad), False for 16:9 horizontal
        gpu_encoder: FFmpeg encoder name
        gpu_flags: FFmpeg encoder flags

    Returns:
        True if clip was created successfully
    """
    source_type = shot.get("source_type", "youtube_clip")

    if source_type == "youtube_clip":
        footage_file = shot.get("footage", "")
        footage_path = os.path.join(footage_dir, footage_file) if footage_file else ""
        start = shot.get("footage_start", 0)

        if not footage_path or not os.path.exists(footage_path):
            return False

        if is_shorts:
            return create_blurpad_clip(
                footage_path,
                clip_path,
                duration,
                start,
                width,
                height,
                gpu_encoder,
                gpu_flags,
            )
        else:
            return create_longform_clip(
                footage_path,
                clip_path,
                duration,
                start,
                width,
                height,
                gpu_encoder,
                gpu_flags,
            )

    elif source_type == "image":
        image_file = shot.get("footage", "")
        image_path = os.path.join(footage_dir, image_file) if image_file else ""

        if not image_path or not os.path.exists(image_path):
            return False

        effect = shot.get("ken_burns", random.choice(KEN_BURNS_EFFECTS))
        return create_kenburns_clip(
            image_path,
            clip_path,
            duration,
            width,
            height,
            effect,
            gpu_encoder,
            gpu_flags,
        )

    elif source_type == "quote_overlay":
        quote_text = shot.get("quote_text", "")
        speaker_name = shot.get("speaker_name", "Unknown")
        if not quote_text:
            return False
        return create_quote_clip(
            clip_path,
            quote_text,
            speaker_name,
            duration,
            width,
            height,
            gpu_encoder,
            gpu_flags,
        )

    elif source_type in ("remotion_animation", "graphic", "veo3_video"):
        # These are pre-rendered clips -- just check if the file exists
        footage_file = shot.get("footage", "")
        footage_path = os.path.join(footage_dir, footage_file) if footage_file else ""
        if footage_path and os.path.exists(footage_path):
            if is_shorts:
                return create_blurpad_clip(
                    footage_path,
                    clip_path,
                    duration,
                    0,
                    width,
                    height,
                    gpu_encoder,
                    gpu_flags,
                )
            else:
                return create_longform_clip(
                    footage_path,
                    clip_path,
                    duration,
                    0,
                    width,
                    height,
                    gpu_encoder,
                    gpu_flags,
                )
        return False

    return False


# ============================================================================
# SHOT STITCHING WITH TRANSITIONS
# ============================================================================


def stitch_shots_with_transitions(
    clip_paths: List[str],
    shots: List[dict],
    shot_timings: List[Tuple[float, float]],
    output_path: str,
    gpu_encoder: str = "h264_videotoolbox",
    gpu_flags: list = None,
) -> bool:
    """Stitch shot clips together using specified transitions.

    Builds an FFmpeg xfade filter chain where each pair of adjacent clips
    uses the transition_in type specified by the second clip's shot definition.

    For "cut" transitions (no visual effect), clips are concatenated directly.
    For other transitions, FFmpeg xfade is used with the appropriate type.

    Args:
        clip_paths: List of paths to shot clip files
        shots: List of shot dicts with transition_in fields
        shot_timings: List of (start, end) tuples for each shot
        output_path: Output path for stitched video
        gpu_encoder: FFmpeg encoder name
        gpu_flags: FFmpeg encoder flags

    Returns:
        True if stitching succeeded
    """
    if gpu_flags is None:
        gpu_flags = ["-allow_sw", "1"]

    if not clip_paths:
        return False

    if len(clip_paths) == 1:
        # Single shot: just copy
        cmd = ["ffmpeg", "-y", "-i", clip_paths[0], "-c", "copy", output_path]
        subprocess.run(cmd, capture_output=True, text=True)
        return os.path.exists(output_path)

    # Check if all transitions are cuts (simple concat, no xfade needed)
    all_cuts = all(
        shots[i].get("transition_in", "cut") == "cut" for i in range(1, len(shots))
    )

    if all_cuts:
        return _concat_clips(clip_paths, output_path, gpu_encoder, gpu_flags)

    # Build xfade filter chain for non-cut transitions
    return _xfade_clips(
        clip_paths, shots, shot_timings, output_path, gpu_encoder, gpu_flags
    )


def _concat_clips(
    clip_paths: List[str],
    output_path: str,
    gpu_encoder: str,
    gpu_flags: list,
) -> bool:
    """Simple concat without transitions (hard cuts)."""
    import tempfile

    concat_file = output_path + ".concat.txt"
    try:
        with open(concat_file, "w") as f:
            for clip in clip_paths:
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
            "-c:v",
            gpu_encoder,
            *gpu_flags,
            "-r",
            "30",
            "-an",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, text=True)
    finally:
        if os.path.exists(concat_file):
            os.remove(concat_file)

    return os.path.exists(output_path)


def _xfade_clips(
    clip_paths: List[str],
    shots: List[dict],
    shot_timings: List[Tuple[float, float]],
    output_path: str,
    gpu_encoder: str,
    gpu_flags: list,
) -> bool:
    """Stitch clips using FFmpeg xfade transitions."""
    inputs = []
    for clip in clip_paths:
        inputs.extend(["-i", clip])

    # Build xfade filter chain
    filter_parts = []
    current_offset = 0.0

    for i in range(1, len(clip_paths)):
        shot = shots[i] if i < len(shots) else {}
        transition_name = shot.get("transition_in", "cut")
        transition_duration = shot.get(
            "transition_duration",
            TRANSITION_DEFAULTS.get(transition_name, 0.3),
        )

        ffmpeg_transition = TRANSITION_MAP.get(transition_name)

        # Calculate clip duration from timings
        if i - 1 < len(shot_timings):
            prev_duration = shot_timings[i - 1][1] - shot_timings[i - 1][0]
        else:
            prev_duration = get_duration(clip_paths[i - 1])

        if ffmpeg_transition is None or transition_duration <= 0:
            # Hard cut: advance offset by full clip duration
            current_offset += prev_duration
        else:
            # Transition: overlap by transition_duration
            if i == 1:
                current_offset = prev_duration - transition_duration
            else:
                current_offset += prev_duration - transition_duration

            in_label = f"[{i - 1}:v]" if i == 1 else f"[v{i - 1}]"
            if i == len(clip_paths) - 1:
                out_label = ",format=yuv420p[outv]"
            else:
                out_label = f"[v{i}]"

            filter_parts.append(
                f"{in_label}[{i}:v]xfade=transition={ffmpeg_transition}"
                f":duration={transition_duration}:offset={current_offset:.3f}{out_label}"
            )

    if not filter_parts:
        # All were cuts -- fall back to concat
        return _concat_clips(clip_paths, output_path, gpu_encoder, gpu_flags)

    # If we have a mix of cuts and transitions, we need to handle this
    # For simplicity, if there are any xfade transitions, use the xfade chain
    # and treat cuts as very short dissolves (0.01s)
    if len(filter_parts) < len(clip_paths) - 1:
        # Rebuild with micro-dissolves for cuts
        filter_parts = []
        current_offset = 0.0
        for i in range(1, len(clip_paths)):
            shot = shots[i] if i < len(shots) else {}
            transition_name = shot.get("transition_in", "cut")
            ffmpeg_transition = TRANSITION_MAP.get(transition_name)

            if i - 1 < len(shot_timings):
                prev_duration = shot_timings[i - 1][1] - shot_timings[i - 1][0]
            else:
                prev_duration = get_duration(clip_paths[i - 1])

            if ffmpeg_transition is None:
                ffmpeg_transition = "fade"
                transition_duration = 0.05  # Near-instant cut
            else:
                transition_duration = shot.get(
                    "transition_duration",
                    TRANSITION_DEFAULTS.get(transition_name, 0.3),
                )

            if i == 1:
                current_offset = prev_duration - transition_duration
            else:
                current_offset += prev_duration - transition_duration

            in_label = f"[{i - 1}:v]" if i == 1 else f"[v{i - 1}]"
            if i == len(clip_paths) - 1:
                out_label = ",format=yuv420p[outv]"
            else:
                out_label = f"[v{i}]"

            filter_parts.append(
                f"{in_label}[{i}:v]xfade=transition={ffmpeg_transition}"
                f":duration={transition_duration}:offset={current_offset:.3f}{out_label}"
            )

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-c:v",
        gpu_encoder,
        *gpu_flags,
        "-r",
        "30",
        "-an",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        # Clean up empty file if xfade created one
        if os.path.exists(output_path):
            os.remove(output_path)
        # Fallback: simple concat (transitions failed)
        stderr_msg = result.stderr[-500:] if result.stderr else ""
        print(f"      xfade failed ({len(clip_paths)} clips), falling back to concat")
        print(f"      xfade stderr: {stderr_msg}")
        print(f"      xfade filter: {filter_complex}")
        return _concat_clips(clip_paths, output_path, gpu_encoder, gpu_flags)

    return True


# ============================================================================
# SHOT FILE NAMING
# ============================================================================


def shot_footage_filename(segment_idx: int, shot_idx: int, ext: str = "mp4") -> str:
    """Generate the standard filename for a shot's footage/image file.

    Convention: segment_XX_shot_YY.ext
    """
    return f"segment_{segment_idx:02d}_shot_{shot_idx:02d}.{ext}"


def get_shot_source_ext(source_type: str) -> str:
    """Get the file extension for a shot's source type."""
    if source_type == "image":
        return "jpg"
    return "mp4"
