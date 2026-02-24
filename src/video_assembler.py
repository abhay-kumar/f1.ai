#!/usr/bin/env python3
"""
Video Assembler - Creates final short video from audio + footage
Includes all fixes for common issues:
- Consistent framerate (30fps) to avoid timestamp issues
- Split filter for blur-pad effect
- Re-encode during concat to normalize timestamps
- Background music mixing
- Concurrent segment processing for faster assembly
- GPU acceleration support (VideoToolbox on macOS, NVENC on Linux/Windows)
"""

import argparse
import json
import multiprocessing
import os
import platform
import subprocess
import sys
import urllib.request
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    AUDIO_BITRATE,
    BACKGROUND_MUSIC,
    F1_DEFAULT_COLOR,
    F1_TEAM_COLORS,
    FRAME_RATE,
    MIN_SHOT_DURATION,
    MUSIC_VOLUME,
    OUTPUT_HEIGHT,
    OUTPUT_WIDTH,
    SHORTS_BOTTOM_MARGIN,
    SHORTS_IMAGE_AREA_HEIGHT,
    SHORTS_MAX_TEXT_LINES,
    VIDEO_BITRATE,
    get_project_dir,
)
from src.shot_assembler import (
    TRANSITION_DEFAULTS,
    calculate_shot_timings,
    create_shot_clip,
    normalize_segment,
    stitch_shots_with_transitions,
)

# Concurrency settings
MAX_CONCURRENT_SEGMENTS = min(4, multiprocessing.cpu_count())


def get_gpu_encoder() -> Tuple[str, list]:
    """
    Detect available GPU encoder and return encoder name with extra flags.

    Returns:
        Tuple of (encoder_name, extra_flags_list)

    Supported encoders (in priority order):
    - macOS: h264_videotoolbox (Metal acceleration)
    - Linux/Windows with NVIDIA: h264_nvenc (CUDA acceleration)
    - Fallback: libx264 (CPU)
    """
    system = platform.system()

    if system == "Darwin":
        # macOS: VideoToolbox with Metal acceleration
        # Test if videotoolbox is available
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True
        )
        if "h264_videotoolbox" in result.stdout:
            return "h264_videotoolbox", ["-allow_sw", "1"]

    elif system in ("Linux", "Windows"):
        # Check for NVIDIA NVENC
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True
        )
        if "h264_nvenc" in result.stdout:
            # NVENC with quality tuning
            return "h264_nvenc", [
                "-preset",
                "p4",  # Balance speed/quality
                "-tune",
                "hq",
                "-rc",
                "vbr",
                "-cq",
                "23",
            ]

    # Fallback to CPU encoding
    return "libx264", ["-preset", "medium", "-crf", "23"]


# Detect encoder at module load
GPU_ENCODER, GPU_ENCODER_FLAGS = get_gpu_encoder()


def get_duration(file_path):
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


def get_video_stream_duration(file_path):
    """Get duration from the video stream (not container).

    Container duration can be longer than video stream when audio is longer,
    which causes xfade offset miscalculation. This returns the actual video
    frame-based duration.
    """
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=duration,nb_frames,r_frame_rate",
        "-of",
        "json",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        import json as _json

        data = _json.loads(result.stdout)
        stream = data["streams"][0]
        # Prefer stream duration if available
        if stream.get("duration") and stream["duration"] != "N/A":
            return float(stream["duration"])
        # Fall back to nb_frames / fps
        nb_frames = int(stream.get("nb_frames", 0))
        fps_str = stream.get("r_frame_rate", "30/1")
        num, den = fps_str.split("/")
        fps = int(num) / int(den) if int(den) > 0 else 30
        if nb_frames > 0:
            return nb_frames / fps
    except (ValueError, KeyError, IndexError, TypeError):
        pass
    # Fallback to container duration
    return get_duration(file_path)


def download_music_if_needed():
    """Download background music if not present"""
    if os.path.exists(BACKGROUND_MUSIC):
        return True

    os.makedirs(os.path.dirname(BACKGROUND_MUSIC), exist_ok=True)
    print("Downloading background music...", end=" ", flush=True)

    # Try yt-dlp for music
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format",
        "mp3",
        "-o",
        BACKGROUND_MUSIC.replace(".mp3", ".%(ext)s"),
        "https://www.youtube.com/watch?v=MkNeIUgNPQ8",  # Epic cinematic
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(BACKGROUND_MUSIC):
        print("Done")
        return True
    else:
        print("Failed (video will have no background music)")
        return False


def escape_text_for_ffmpeg(text):
    """Escape special characters for FFmpeg drawtext filter"""
    # FFmpeg drawtext requires escaping: ' \ :
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\u2019")  # Replace with curly apostrophe
    text = text.replace(":", "\\:")
    return text


def wrap_text(text, max_chars=35):
    """Wrap text into multiple lines for display"""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def get_team_color(text):
    """Detect team/driver mentions and return appropriate F1 team color"""
    text_lower = text.lower()

    # Check for team/driver mentions (priority: first mentioned)
    for keyword, color in F1_TEAM_COLORS.items():
        if keyword in text_lower:
            return color

    return F1_DEFAULT_COLOR


def _split_into_sentences(text):
    """Split text into sentences at natural break points.

    Splits on sentence-ending punctuation (.!?) and also on commas/semicolons
    when the resulting chunk would be too long for the screen.
    """
    import re

    # Split on sentence boundaries (.!?) keeping the punctuation with the sentence
    raw_parts = re.split(r"(?<=[.!?])\s+", text.strip())

    sentences = []
    for part in raw_parts:
        # If a sentence is very long (>6 words), also split at commas/semicolons
        words = part.split()
        if len(words) > 8:
            # Split at comma/semicolon boundaries
            sub_parts = re.split(r"(?<=[,;])\s+", part)
            for sp in sub_parts:
                if sp.strip():
                    sentences.append(sp.strip())
        else:
            if part.strip():
                sentences.append(part.strip())

    return sentences if sentences else [text]


def build_word_by_word_filters(text, audio_duration, font_path):
    """Build progressive reveal (karaoke-style) caption filters.

    Style: Sentence builds up word by word. Each new word appears alongside
    the previous words in that sentence. When a sentence ends, it clears
    and the next sentence starts building. The current word is highlighted
    with a yellow border while previous words have a black border.

    This matches the popular shorts caption style (MrBeast, Hormozi, etc.)
    where viewers can read along as the narrator speaks.
    """
    words = text.split()
    if not words:
        return "null"

    total_chars = sum(len(w) for w in words)
    if total_chars == 0:
        return "null"

    # Split text into sentences for the "clear and restart" behavior
    sentences = _split_into_sentences(text)

    # Map each word to its sentence index
    word_to_sentence = []
    sent_idx = 0
    sent_words_remaining = sentences[0].split()
    for word in words:
        if not sent_words_remaining and sent_idx + 1 < len(sentences):
            sent_idx += 1
            sent_words_remaining = sentences[sent_idx].split()
        word_to_sentence.append(sent_idx)
        if sent_words_remaining:
            sent_words_remaining.pop(0)

    # Timing: proportional to character count with minimum floor
    MIN_WORD_DURATION = 0.15
    raw_durations = [audio_duration * (len(w) / total_chars) for w in words]

    deficit = sum(max(0, MIN_WORD_DURATION - d) for d in raw_durations)
    surplus_total = sum(max(0, d - MIN_WORD_DURATION) for d in raw_durations)

    adjusted_durations = []
    for d in raw_durations:
        if d < MIN_WORD_DURATION:
            adjusted_durations.append(MIN_WORD_DURATION)
        elif surplus_total > 0:
            surplus = d - MIN_WORD_DURATION
            adjusted_durations.append(d - deficit * (surplus / surplus_total))
        else:
            adjusted_durations.append(d)

    # Calculate start/end times for each word
    word_times = []
    cumulative = 0.0
    for i, dur in enumerate(adjusted_durations):
        word_times.append((cumulative, cumulative + dur))
        cumulative += dur

    # Font settings
    font_size = 64  # Slightly smaller to fit accumulating text
    max_chars_per_line = 25
    line_height = int(font_size * 1.25)

    filters = []

    # For each word, we render ALL accumulated words in the current sentence
    # during that word's time window. This creates the progressive reveal.
    for word_idx in range(len(words)):
        current_sent = word_to_sentence[word_idx]
        word_start = word_times[word_idx][0]

        # End time: when the NEXT word starts (or audio ends for last word)
        if word_idx < len(words) - 1:
            word_end = word_times[word_idx + 1][0]
        else:
            word_end = audio_duration

        # Enable condition for this time window
        if word_idx == 0:
            enable = f"lt(t,{word_end:.3f})"
        elif word_idx == len(words) - 1:
            enable = f"gte(t,{word_start:.3f})"
        else:
            enable = f"gte(t,{word_start:.3f})*lt(t,{word_end:.3f})"

        # Collect all words in current sentence up to and including this word
        sentence_words = []
        for j in range(len(words)):
            if word_to_sentence[j] == current_sent and j <= word_idx:
                sentence_words.append((j, words[j]))

        if not sentence_words:
            continue

        # Build the accumulated text, wrapping into lines
        accumulated = " ".join(w for _, w in sentence_words)
        lines = wrap_text(accumulated, max_chars=max_chars_per_line)

        # Calculate Y position (bottom-anchored)
        total_text_height = len(lines) * line_height
        start_y = OUTPUT_HEIGHT - SHORTS_BOTTOM_MARGIN - total_text_height

        # Render each line — all words in white with black border (the base)
        for line_idx, line in enumerate(lines):
            escaped_line = escape_text_for_ffmpeg(line)
            y_pos = start_y + (line_idx * line_height)

            # Layer 1: Yellow outer glow for the whole line
            filters.append(
                f"drawtext=text='{escaped_line}':"
                f"fontfile={font_path}:"
                f"fontsize={font_size}:"
                f"fontcolor=white:"
                f"borderw=6:bordercolor=#FFD700:"
                f"x=(w-text_w)/2:y={y_pos}:"
                f"enable='{enable}'"
            )
            # Layer 2: Black inner border + white fill
            filters.append(
                f"drawtext=text='{escaped_line}':"
                f"fontfile={font_path}:"
                f"fontsize={font_size}:"
                f"fontcolor=white:"
                f"borderw=3:bordercolor=black:"
                f"x=(w-text_w)/2:y={y_pos}:"
                f"enable='{enable}'"
            )

    return ",".join(filters) if filters else "null"


def _create_multishot_segment(
    segment_idx,
    segment,
    shots,
    audio_path,
    audio_duration,
    footage_dir,
    output_path,
    video_encoder,
    encoder_flags,
    word_by_word=False,
):
    """Create a segment video from multiple shots with transitions.

    Each shot is rendered as a separate clip (blur-pad for video, Ken Burns
    for images, etc.), then stitched together with the specified transitions.
    Text captions and audio are applied on top of the final stitched video.

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    import tempfile

    work_dir = os.path.join(os.path.dirname(output_path), f"shots_{segment_idx:02d}")
    os.makedirs(work_dir, exist_ok=True)

    # Calculate timing for each shot from text_cue positions
    shot_timings = calculate_shot_timings(
        segment.get("text", ""), shots, audio_duration, MIN_SHOT_DURATION
    )

    # Calculate total xfade overlap so we can inflate shot durations.
    # Each non-cut transition between shots shortens the stitched video by
    # its transition_duration.  We distribute that lost time across shots
    # proportionally so the final stitched video length == audio_duration.
    total_overlap = 0.0
    for s_idx in range(1, len(shots)):
        tr = shots[s_idx].get("transition_in", "cut")
        if tr != "cut":
            total_overlap += shots[s_idx].get(
                "transition_duration",
                TRANSITION_DEFAULTS.get(tr, 0.3),
            )

    # Distribute overlap across shots proportionally to their duration
    if total_overlap > 0:
        total_shot_time = sum(e - s for s, e in shot_timings)
        inflated_timings = []
        for s_idx, (start, end) in enumerate(shot_timings):
            raw_dur = end - start
            extra = (
                total_overlap * (raw_dur / total_shot_time)
                if total_shot_time > 0
                else 0
            )
            inflated_timings.append((start, end, raw_dur + extra))
    else:
        inflated_timings = [(s, e, e - s) for s, e in shot_timings]

    # Create each shot as a separate clip
    shot_clips = []
    for shot_idx, (shot, (start_time, end_time, shot_duration)) in enumerate(
        zip(shots, inflated_timings)
    ):
        clip_path = os.path.join(work_dir, f"shot_{shot_idx:02d}.mp4")

        # Fill in missing footage field using naming convention
        if not shot.get("footage"):
            from src.shot_assembler import get_shot_source_ext, shot_footage_filename

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

        # Fit image shots into upper zone so text below doesn't overlap
        shot_image_area = (
            SHORTS_IMAGE_AREA_HEIGHT if shot.get("source_type") == "image" else None
        )
        success = create_shot_clip(
            shot=shot,
            clip_path=clip_path,
            duration=shot_duration,
            footage_dir=footage_dir,
            width=OUTPUT_WIDTH,
            height=OUTPUT_HEIGHT,
            is_shorts=True,
            gpu_encoder=video_encoder,
            gpu_flags=encoder_flags,
            image_area_height=shot_image_area,
        )

        if success and os.path.exists(clip_path):
            shot_clips.append(clip_path)
        else:
            src_type = shot.get("source_type", "unknown")
            footage = shot.get("footage", "none")
            print(
                f"      Shot {shot_idx} failed ({src_type}: {shot.get('label', 'unknown')[:30]}, footage={footage})"
            )

    if not shot_clips:
        return False, "No shot clips created"

    if len(shot_clips) == 1:
        # Only one shot succeeded -- use it directly
        stitched_path = shot_clips[0]
    else:
        # Stitch shots together with transitions
        stitched_path = os.path.join(work_dir, "stitched.mp4")

        # Build the list of shots/timings matching only successful clips
        successful_shots = []
        successful_timings = []
        for shot_idx, (shot, timing) in enumerate(zip(shots, shot_timings)):
            clip_path = os.path.join(work_dir, f"shot_{shot_idx:02d}.mp4")
            if clip_path in shot_clips:
                successful_shots.append(shot)
                successful_timings.append(timing)

        success = stitch_shots_with_transitions(
            clip_paths=shot_clips,
            shots=successful_shots,
            shot_timings=successful_timings,
            output_path=stitched_path,
            gpu_encoder=video_encoder,
            gpu_flags=encoder_flags,
        )

        if not success:
            return False, "Failed to stitch shots"

    # Build text caption filters
    f1_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"

    if segment.get("no_text", False):
        text_filter = "null"
    elif word_by_word:
        text_filter = build_word_by_word_filters(
            segment["text"], audio_duration, f1_font
        )
    else:
        lines = wrap_text(segment["text"], max_chars=25)
        team_color = get_team_color(segment["text"])

        base_font_size = 72
        if len(lines) > 3:
            font_size = 52
        elif len(lines) > 2:
            font_size = 60
        else:
            font_size = base_font_size

        line_height = int(font_size * 1.2)
        drawtext_filters = []

        if len(lines) >= SHORTS_MAX_TEXT_LINES:
            text = segment["text"]
            max_lines_per_part = SHORTS_MAX_TEXT_LINES - 1

            parts = []
            remaining = text.strip()
            while remaining:
                words = remaining.split()
                best_split = 0
                for i in range(1, len(words) + 1):
                    candidate = " ".join(words[:i])
                    if len(wrap_text(candidate, max_chars=25)) <= max_lines_per_part:
                        best_split = i
                    else:
                        break
                if best_split == 0:
                    best_split = 1

                candidate_text = " ".join(words[:best_split])
                for boundary in [". ", "! ", "? ", ", ", "; ", " - "]:
                    pos = candidate_text.rfind(boundary)
                    if pos > len(candidate_text) * 0.3:
                        test_part = candidate_text[: pos + len(boundary)].strip()
                        if len(wrap_text(test_part, max_chars=25)) >= 2:
                            candidate_text = test_part
                            best_split = len(candidate_text.split())
                            break

                part_text = " ".join(words[:best_split])
                parts.append(part_text)
                remaining = " ".join(words[best_split:]).strip()

            total_chars = sum(len(p) for p in parts)

            def _part_font_size(num_lines):
                if num_lines > 3:
                    return 52
                elif num_lines > 2:
                    return 60
                return base_font_size

            cumulative_time = 0.0
            for part_idx, part_text in enumerate(parts):
                part_lines = wrap_text(part_text, max_chars=25)
                part_duration = audio_duration * (len(part_text) / total_chars)
                start_time_part = cumulative_time
                end_time_part = cumulative_time + part_duration
                cumulative_time = end_time_part

                p_fs = _part_font_size(len(part_lines))
                p_lh = int(p_fs * 1.2)
                p_start_y = (
                    OUTPUT_HEIGHT - SHORTS_BOTTOM_MARGIN - len(part_lines) * p_lh
                )

                for i, line in enumerate(part_lines):
                    escaped_line = escape_text_for_ffmpeg(line)
                    y_pos = p_start_y + (i * p_lh)

                    if part_idx == 0:
                        base_enable = f"lt(t,{end_time_part:.2f})"
                    elif part_idx == len(parts) - 1:
                        base_enable = f"gte(t,{start_time_part:.2f})"
                    else:
                        base_enable = (
                            f"gte(t,{start_time_part:.2f})*lt(t,{end_time_part:.2f})"
                        )

                    drawtext_filters.append(
                        f"drawtext=text='{escaped_line}':"
                        f"fontfile={f1_font}:"
                        f"fontsize={p_fs}:fontcolor=black@0.5:"
                        f"x=(w-text_w)/2+3:y={y_pos}+3:"
                        f"enable='{base_enable}'"
                    )
                    drawtext_filters.append(
                        f"drawtext=text='{escaped_line}':"
                        f"fontfile={f1_font}:"
                        f"fontsize={p_fs}:fontcolor={team_color}:"
                        f"x=(w-text_w)/2:y={y_pos}:"
                        f"enable='{base_enable}'"
                    )

        if not drawtext_filters:
            total_text_height = len(lines) * line_height
            start_y = OUTPUT_HEIGHT - SHORTS_BOTTOM_MARGIN - total_text_height

            for i, line in enumerate(lines):
                escaped_line = escape_text_for_ffmpeg(line)
                y_pos = start_y + (i * line_height)
                drawtext_filters.append(
                    f"drawtext=text='{escaped_line}':"
                    f"fontfile={f1_font}:"
                    f"fontsize={font_size}:fontcolor=black@0.5:"
                    f"x=(w-text_w)/2+3:y={y_pos}+3"
                )
                drawtext_filters.append(
                    f"drawtext=text='{escaped_line}':"
                    f"fontfile={f1_font}:"
                    f"fontsize={font_size}:fontcolor={team_color}:"
                    f"x=(w-text_w)/2:y={y_pos}"
                )

        text_filter = ",".join(drawtext_filters) if drawtext_filters else "null"

    # Pad the stitched video to match audio duration.
    # After xfade stitching, the video can be slightly shorter than the audio
    # due to transition overlaps and rounding. tpad clones the last frame to
    # fill the gap, preventing video freeze in the final output.
    total_frames_needed = int(audio_duration * FRAME_RATE) + 1
    pad_filter = f"tpad=stop=-1:stop_mode=clone:stop_duration={audio_duration + 0.5}"

    # Apply text overlay and audio on top of stitched video
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        stitched_path,
        "-i",
        audio_path,
        "-filter_complex",
        f"[0:v]{pad_filter},{text_filter}[out]",
        "-map",
        "[out]",
        "-map",
        "1:a",
        "-c:v",
        video_encoder,
        *encoder_flags,
        "-b:v",
        VIDEO_BITRATE,
        "-r",
        str(FRAME_RATE),
        "-c:a",
        "aac",
        "-b:a",
        AUDIO_BITRATE,
        "-t",
        str(audio_duration),
        "-movflags",
        "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up work directory
    import shutil

    shutil.rmtree(work_dir, ignore_errors=True)

    if os.path.exists(output_path):
        return True, None
    return False, result.stderr[
        -500:
    ] if result.stderr else "Multi-shot assembly failed"


def create_segment_video(
    segment_idx,
    segment,
    audio_path,
    footage_dir,
    output_path,
    encoder=None,
    encoder_flags=None,
    word_by_word=False,
):
    """Create video segment with blur-pad effect and text captions.

    Supports multi-shot segments: if the segment has a 'shots' array with
    more than one shot, each shot is rendered as a separate clip with its
    own visual source, then stitched together with transitions. Text captions
    and audio are applied on top of the stitched video.

    For legacy single-shot segments (no 'shots' array or single shot),
    the original single-footage path is used.

    If word_by_word=True, uses viral shorts-style captions: 2-3 words at a
    time, large white text with black outline, centered on screen.
    """
    # Use provided encoder or fall back to detected GPU encoder
    video_encoder = encoder or GPU_ENCODER
    extra_flags = encoder_flags if encoder_flags is not None else GPU_ENCODER_FLAGS

    audio_duration = get_duration(audio_path)

    # Normalize segment to ensure shots array exists
    segment = normalize_segment(segment)
    shots = segment.get("shots", [])

    # Multi-shot path: 2+ shots with actual footage/source files
    if len(shots) > 1:
        try:
            result = _create_multishot_segment(
                segment_idx,
                segment,
                shots,
                audio_path,
                audio_duration,
                footage_dir,
                output_path,
                video_encoder,
                extra_flags,
                word_by_word=word_by_word,
            )
            if result[0]:  # Success
                return result
            # If multi-shot fails, fall through to single-shot path
            print(f"      Multi-shot failed: {result[1]}")
            print(f"      Trying single-shot fallback...")
        except Exception as e:
            import traceback

            print(f"      Multi-shot EXCEPTION: {e}")
            traceback.print_exc()
            print(f"      Trying single-shot fallback...")

    # Single-shot path (original logic)
    footage_name = segment.get("footage", f"segment_{segment_idx:02d}.mp4")
    # Also check first shot's footage field
    if shots and shots[0].get("footage"):
        footage_name = shots[0]["footage"]
    footage_file = f"{footage_dir}/{footage_name}"
    if not os.path.exists(footage_file):
        return False, f"Missing footage: {footage_name}"
    start_time = segment.get("footage_start", 0)

    # Build text caption filters
    f1_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"

    if segment.get("no_text"):
        text_filter = "null"
    elif word_by_word:
        text_filter = build_word_by_word_filters(
            segment["text"], audio_duration, f1_font
        )
    else:
        # Wrap and escape text for FFmpeg
        lines = wrap_text(
            segment["text"], max_chars=25
        )  # Shorter lines for bigger font

        # Get F1 team color based on narration content
        team_color = get_team_color(segment["text"])

        # Dynamic font size: smaller for more lines to prevent overflow
        base_font_size = 72
        if len(lines) > 3:
            font_size = 52
        elif len(lines) > 2:
            font_size = 60
        else:
            font_size = base_font_size

        line_height = int(font_size * 1.2)

        # For long text (5+ lines), split into multiple timed parts.
        # Each part displays sequentially, timed proportionally to character count.
        drawtext_filters = []

        if len(lines) >= SHORTS_MAX_TEXT_LINES:
            text = segment["text"]
            max_lines_per_part = SHORTS_MAX_TEXT_LINES - 1  # 4 lines max per part

            # Split text into parts that each fit within max_lines_per_part
            parts = []
            remaining = text.strip()

            while remaining:
                words = remaining.split()

                # Find the longest prefix that fits within max_lines_per_part
                best_split = 0
                for i in range(1, len(words) + 1):
                    candidate = " ".join(words[:i])
                    if len(wrap_text(candidate, max_chars=25)) <= max_lines_per_part:
                        best_split = i
                    else:
                        break

                if best_split == 0:
                    # Single word too long - just take it
                    best_split = 1

                # Prefer to split at sentence/clause boundaries if possible
                candidate_text = " ".join(words[:best_split])

                # Look for natural break points within candidate
                for boundary in [". ", "! ", "? ", ", ", "; ", " - "]:
                    pos = candidate_text.rfind(boundary)
                    if pos > len(candidate_text) * 0.3:  # At least 30% through
                        test_part = candidate_text[: pos + len(boundary)].strip()
                        if (
                            len(wrap_text(test_part, max_chars=25)) >= 2
                        ):  # At least 2 lines
                            candidate_text = test_part
                            best_split = len(candidate_text.split())
                            break

                part_text = " ".join(words[:best_split])
                parts.append(part_text)
                remaining = " ".join(words[best_split:]).strip()

            # Calculate timing for each part based on character proportion
            total_chars = sum(len(p) for p in parts)

            def _part_font_size(num_lines):
                if num_lines > 3:
                    return 52
                elif num_lines > 2:
                    return 60
                return base_font_size

            # Generate drawtext filters for each part
            cumulative_time = 0.0
            for part_idx, part_text in enumerate(parts):
                part_lines = wrap_text(part_text, max_chars=25)
                part_duration = audio_duration * (len(part_text) / total_chars)
                start_time_part = cumulative_time
                end_time_part = cumulative_time + part_duration
                cumulative_time = end_time_part

                p_fs = _part_font_size(len(part_lines))
                p_lh = int(p_fs * 1.2)
                p_start_y = (
                    OUTPUT_HEIGHT - SHORTS_BOTTOM_MARGIN - len(part_lines) * p_lh
                )

                for i, line in enumerate(part_lines):
                    escaped_line = escape_text_for_ffmpeg(line)
                    y_pos = p_start_y + (i * p_lh)

                    # Enable condition: show this part during its time window
                    if part_idx == 0:
                        enable_cond = f"lt(t,{end_time_part:.2f})"
                    elif part_idx == len(parts) - 1:
                        enable_cond = f"gte(t,{start_time_part:.2f})"
                    else:
                        enable_cond = (
                            f"gte(t,{start_time_part:.2f})*lt(t,{end_time_part:.2f})"
                        )

                    # Shadow
                    drawtext_filters.append(
                        f"drawtext=text='{escaped_line}':"
                        f"fontfile={f1_font}:"
                        f"fontsize={p_fs}:fontcolor=black@0.5:"
                        f"x=(w-text_w)/2+3:y={y_pos}+3:"
                        f"enable='{enable_cond}'"
                    )
                    # Main text
                    drawtext_filters.append(
                        f"drawtext=text='{escaped_line}':"
                        f"fontfile={f1_font}:"
                        f"fontsize={p_fs}:fontcolor={team_color}:"
                        f"x=(w-text_w)/2:y={y_pos}:"
                        f"enable='{enable_cond}'"
                    )

        # Default: all text at the bottom (for <5 lines or if no break point found)
        if not drawtext_filters:
            total_text_height = len(lines) * line_height
            start_y = OUTPUT_HEIGHT - SHORTS_BOTTOM_MARGIN - total_text_height

            for i, line in enumerate(lines):
                escaped_line = escape_text_for_ffmpeg(line)
                y_pos = start_y + (i * line_height)
                drawtext_filters.append(
                    f"drawtext=text='{escaped_line}':"
                    f"fontfile={f1_font}:"
                    f"fontsize={font_size}:fontcolor=black@0.5:"
                    f"x=(w-text_w)/2+3:y={y_pos}+3"
                )
                drawtext_filters.append(
                    f"drawtext=text='{escaped_line}':"
                    f"fontfile={f1_font}:"
                    f"fontsize={font_size}:fontcolor={team_color}:"
                    f"x=(w-text_w)/2:y={y_pos}"
                )

        text_filter = ",".join(drawtext_filters) if drawtext_filters else "null"

    # Blur-pad filter with SPLIT (critical fix!)
    # Creates blurred background + centered sharp footage + text captions
    filter_complex = (
        f"[0:v]trim=start={start_time}:duration={audio_duration},setpts=PTS-STARTPTS,split=2[for_bg][for_fg];"
        f"[for_bg]scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},boxblur=20:5[bg];"
        f"[for_fg]scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,{text_filter}[out]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        footage_file,
        "-i",
        audio_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-map",
        "1:a",
        "-c:v",
        video_encoder,
        *extra_flags,
        "-b:v",
        VIDEO_BITRATE,
        "-r",
        str(FRAME_RATE),  # CRITICAL: Consistent framerate
        "-c:a",
        "aac",
        "-b:a",
        AUDIO_BITRATE,
        "-t",
        str(audio_duration),
        "-movflags",
        "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(output_path):
        return False, result.stderr[-200:] if result.stderr else "Unknown error"
    return True, None


def process_segment_video(args: Tuple) -> Tuple[int, bool, float, Optional[str]]:
    """Process a single segment video (for concurrent execution)"""
    # Support both old 7-element and new 8-element tuple
    if len(args) >= 8:
        (
            idx,
            segment,
            audio_path,
            footage_dir,
            output_path,
            encoder,
            encoder_flags,
            word_by_word,
        ) = args
    else:
        idx, segment, audio_path, footage_dir, output_path, encoder, encoder_flags = (
            args
        )
        word_by_word = False

    success, error = create_segment_video(
        idx,
        segment,
        audio_path,
        footage_dir,
        output_path,
        encoder=encoder,
        encoder_flags=encoder_flags,
        word_by_word=word_by_word,
    )

    if success:
        duration = get_duration(output_path)
        return idx, True, duration, None
    return idx, False, 0, error


def add_background_music(video_path, output_path):
    """Mix background music under video audio"""
    if not os.path.exists(BACKGROUND_MUSIC):
        subprocess.run(["cp", video_path, output_path])
        return True

    video_duration = get_duration(video_path)

    filter_complex = (
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{video_duration},"
        f"afade=t=out:st={video_duration - 2}:d=2,"
        f"volume={MUSIC_VOLUME}[music];"
        f"[0:a][music]amix=inputs=2:duration=first[aout]"
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
        AUDIO_BITRATE,
        "-movflags",
        "+faststart",
        output_path,
    ]

    subprocess.run(cmd, capture_output=True)
    return os.path.exists(output_path)


def verify_output(video_path):
    """Verify video duration and frame count are consistent.

    Checks both container duration and the actual video stream frame count
    to detect the common xfade bug where container is long but video frames
    are truncated (video freezes while audio keeps playing).
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-show_entries",
        "stream=nb_frames,r_frame_rate,codec_type,duration",
        "-of",
        "json",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    try:
        data = json.loads(result.stdout)
        container_dur = float(data["format"]["duration"])
    except (ValueError, AttributeError, KeyError):
        return False, "Could not determine video duration"

    if container_dur < 5.0:
        return False, f"Video too short: {container_dur:.1f}s"

    # Check video stream frame count vs container duration
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            nb_frames = int(stream.get("nb_frames", 0))
            fps_str = stream.get("r_frame_rate", "30/1")
            try:
                num, den = fps_str.split("/")
                fps = int(num) / int(den) if int(den) > 0 else 30
            except (ValueError, ZeroDivisionError):
                fps = 30
            if nb_frames > 0:
                video_dur = nb_frames / fps
                if video_dur < container_dur * 0.9:
                    return False, (
                        f"Frame mismatch: video has {nb_frames} frames "
                        f"({video_dur:.1f}s at {fps:.0f}fps) but container is "
                        f"{container_dur:.1f}s — video will freeze at {video_dur:.1f}s"
                    )
            break

    return True, f"Duration: {container_dur:.1f}s"


def main():
    parser = argparse.ArgumentParser(description="Assemble final video")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--no-music", action="store_true", help="Skip background music")
    parser.add_argument(
        "--sequential", action="store_true", help="Disable concurrent processing"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=MAX_CONCURRENT_SEGMENTS,
        help=f"Max concurrent workers (default: {MAX_CONCURRENT_SEGMENTS})",
    )
    parser.add_argument(
        "--encoder",
        choices=["auto", "videotoolbox", "nvenc", "cpu"],
        default="auto",
        help="Video encoder (default: auto-detect)",
    )
    parser.add_argument(
        "--segment-transition",
        choices=["cut", "cross_dissolve", "fade_to_black"],
        default="cross_dissolve",
        help="Transition between segments (default: cross_dissolve)",
    )
    parser.add_argument(
        "--word-by-word",
        action="store_true",
        help="Use word-by-word caption style (2-3 words at a time, white with black outline, centered)",
    )
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    audio_dir = f"{project_dir}/audio"
    footage_dir = f"{project_dir}/footage"
    temp_dir = f"{project_dir}/temp"
    output_dir = f"{project_dir}/output"
    script_file = f"{project_dir}/script.json"

    for d in [temp_dir, output_dir]:
        os.makedirs(d, exist_ok=True)

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    # Determine encoder
    if args.encoder == "auto":
        encoder, encoder_flags = GPU_ENCODER, GPU_ENCODER_FLAGS
    elif args.encoder == "videotoolbox":
        encoder, encoder_flags = "h264_videotoolbox", ["-allow_sw", "1"]
    elif args.encoder == "nvenc":
        encoder, encoder_flags = (
            "h264_nvenc",
            ["-preset", "p4", "-tune", "hq", "-rc", "vbr", "-cq", "23"],
        )
    else:  # cpu
        encoder, encoder_flags = "libx264", ["-preset", "medium", "-crf", "23"]

    print("=" * 60)
    print(f"Video Assembler - Project: {args.project}")
    print(f"Settings: {FRAME_RATE}fps, {OUTPUT_WIDTH}x{OUTPUT_HEIGHT}")
    print(f"Encoder: {encoder} (GPU: {encoder != 'libx264'})")
    print(
        f"Concurrency: {'Sequential' if args.sequential else f'{args.workers} workers'}"
    )
    print("=" * 60)

    with open(script_file) as f:
        script = json.load(f)

    segments = script["segments"]

    # Check audio exists
    missing_audio = [
        i
        for i in range(len(segments))
        if not os.path.exists(f"{audio_dir}/segment_{i:02d}.mp3")
    ]
    if missing_audio:
        print(f"\nMissing audio for segments: {missing_audio}")
        print(f"Run: python3 src/audio_generator.py --project {args.project}")
        sys.exit(1)

    # Download music
    if not args.no_music:
        print()
        download_music_if_needed()

    # Create segments
    print(f"\nCreating {len(segments)} segments...\n")
    segment_videos = []
    results = {}

    # Prepare tasks
    tasks = [
        (
            i,
            segment,
            f"{audio_dir}/segment_{i:02d}.mp3",
            footage_dir,
            f"{temp_dir}/segment_{i:02d}.mp4",
            encoder,
            encoder_flags,
            getattr(args, "word_by_word", False),
        )
        for i, segment in enumerate(segments)
    ]

    if args.sequential:
        # Sequential processing
        for task in tasks:
            idx = task[0]
            segment = segments[idx]
            print(
                f"[{idx + 1}/{len(segments)}] {segment['context']}...",
                end=" ",
                flush=True,
            )

            idx, success, duration, error = process_segment_video(task)
            if success:
                segment_videos.append(f"{temp_dir}/segment_{idx:02d}.mp4")
                print(f"Done ({duration:.1f}s)")
            else:
                print(f"Failed: {error}")
            results[idx] = (success, duration)
    else:
        # Concurrent processing using ProcessPoolExecutor
        # Note: Using processes instead of threads for CPU-bound FFmpeg work
        print(f"Processing {len(tasks)} segments concurrently...\n")

        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            future_to_idx = {
                executor.submit(process_segment_video, task): task[0] for task in tasks
            }

            for future in as_completed(future_to_idx):
                idx, success, duration, error = future.result()
                segment = segments[idx]

                if success:
                    segment_videos.append(f"{temp_dir}/segment_{idx:02d}.mp4")
                    print(
                        f"[{idx + 1}/{len(segments)}] Done: {segment['context']} ({duration:.1f}s)"
                    )
                else:
                    print(
                        f"[{idx + 1}/{len(segments)}] Failed: {segment['context']} - {error}"
                    )

                results[idx] = (success, duration)

        # Sort segment videos by index to maintain order
        segment_videos.sort(key=lambda x: int(x.split("_")[-1].replace(".mp4", "")))

    if not segment_videos:
        print("\nNo segments created!")
        sys.exit(1)

    # Concatenate with transitions
    seg_transition = args.segment_transition
    print(
        f"\nConcatenating {len(segment_videos)} segments (transition: {seg_transition})..."
    )

    concat_output = f"{temp_dir}/concat.mp4"

    if seg_transition == "cut" or len(segment_videos) < 2:
        # Simple concat (hard cuts)
        concat_file = f"{temp_dir}/concat.txt"
        with open(concat_file, "w") as f:
            for video in segment_videos:
                f.write(f"file '{video}'\n")

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
            "h264_videotoolbox",
            "-b:v",
            VIDEO_BITRATE,
            "-c:a",
            "aac",
            "-b:a",
            AUDIO_BITRATE,
            "-movflags",
            "+faststart",
            concat_output,
        ]
        subprocess.run(cmd, capture_output=True)
    else:
        # Transitions between segments using xfade for VIDEO only.
        # Audio is concatenated separately without any crossfade or trimming
        # to preserve complete speech at segment boundaries.
        ffmpeg_transition = {
            "cross_dissolve": "fade",
            "fade_to_black": "fadeblack",
        }.get(seg_transition, "fade")
        transition_dur = 0.3

        # Get VIDEO STREAM durations (not container) for accurate xfade offsets.
        # Container duration can exceed video stream when audio is longer,
        # causing xfade to produce truncated output (video freezes mid-playback).
        seg_durations = []
        for sv in segment_videos:
            seg_durations.append(get_video_stream_duration(sv))

        # Step 1: Concat all audio tracks untouched (preserves full speech)
        audio_concat_file = f"{temp_dir}/audio_concat.txt"
        audio_concat_path = f"{temp_dir}/audio_full.m4a"
        with open(audio_concat_file, "w") as f:
            for sv in segment_videos:
                f.write(f"file '{sv}'\n")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                audio_concat_file,
                "-vn",
                "-c:a",
                "aac",
                "-b:a",
                AUDIO_BITRATE,
                audio_concat_path,
            ],
            capture_output=True,
        )

        # Step 2: Apply xfade to VIDEO streams only
        inputs = []
        for sv in segment_videos:
            inputs.extend(["-i", sv])

        v_filters = []
        current_offset = seg_durations[0] - transition_dur

        for i in range(1, len(segment_videos)):
            in_v = f"[v{i - 1}]" if i > 1 else "[0:v]"
            out_v = f"[v{i}]"
            v_filters.append(
                f"{in_v}[{i}:v]xfade=transition={ffmpeg_transition}"
                f":duration={transition_dur}:offset={current_offset:.3f}{out_v}"
            )

            if i < len(segment_videos) - 1:
                current_offset += seg_durations[i] - transition_dur

        last_v_idx = len(segment_videos) - 1
        filter_complex = ";".join(v_filters)

        # Render video-only with xfade
        video_only_path = f"{temp_dir}/video_xfade.mp4"
        cmd = [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            f"[v{last_v_idx}]",
            "-an",
            "-c:v",
            "h264_videotoolbox",
            "-b:v",
            VIDEO_BITRATE,
            "-movflags",
            "+faststart",
            video_only_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Step 3: Mux video + untouched audio together
        if os.path.exists(video_only_path) and os.path.exists(audio_concat_path):
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_only_path,
                "-i",
                audio_concat_path,
                "-c:v",
                "copy",
                "-c:a",
                "copy",
                "-shortest",
                "-movflags",
                "+faststart",
                concat_output,
            ]
            subprocess.run(cmd, capture_output=True, text=True)

        if not os.path.exists(concat_output) or os.path.getsize(concat_output) == 0:
            if os.path.exists(concat_output):
                os.remove(concat_output)
            # Fallback to simple concat if xfade fails
            stderr_tail = result.stderr[-500:] if result.stderr else "no stderr"
            print(f"  Transition concat failed: {stderr_tail}")
            print(f"  Falling back to hard cuts...")
            concat_file = f"{temp_dir}/concat.txt"
            with open(concat_file, "w") as f:
                for video in segment_videos:
                    f.write(f"file '{video}'\n")
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
                "h264_videotoolbox",
                "-b:v",
                VIDEO_BITRATE,
                "-c:a",
                "aac",
                "-b:a",
                AUDIO_BITRATE,
                "-movflags",
                "+faststart",
                concat_output,
            ]
            subprocess.run(cmd, capture_output=True)

    # Add music
    final_output = f"{output_dir}/final.mp4"
    if not args.no_music:
        print("Adding background music...")
        add_background_music(concat_output, final_output)
    else:
        subprocess.run(["cp", concat_output, final_output])

    # Verify
    if os.path.exists(final_output):
        ok, msg = verify_output(final_output)
        size_mb = os.path.getsize(final_output) / (1024 * 1024)

        print(f"\n{'=' * 60}")
        if ok:
            print(f"SUCCESS: {final_output}")
            print(f"Duration: {msg}")
            print(f"Size: {size_mb:.1f}MB")
        else:
            print(f"WARNING: {msg}")
            print(f"Output: {final_output}")
    else:
        print("\nFailed to create final video")
        sys.exit(1)


if __name__ == "__main__":
    main()
