#!/usr/bin/env python3
"""
Long-form Video Assembler - Creates final 16:9 horizontal video from audio + footage
Supports 4K (3840x2160) and HD (1920x1080) resolutions

Features:
- 16:9 horizontal format (standard YouTube video)
- 4K or HD resolution options
- Higher bitrate for quality
- End credits with references
- Concurrent segment processing
- GPU acceleration support
"""
import os
import sys
import json
import argparse
import subprocess
import platform
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Tuple, Optional, List, Dict
import multiprocessing

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    get_project_dir, BACKGROUND_MUSIC,
    LONGFORM_FRAME_RATE, LONGFORM_AUDIO_BITRATE,
    LONGFORM_OUTPUT_WIDTH_4K, LONGFORM_OUTPUT_HEIGHT_4K,
    LONGFORM_OUTPUT_WIDTH_HD, LONGFORM_OUTPUT_HEIGHT_HD,
    LONGFORM_VIDEO_BITRATE_4K, LONGFORM_VIDEO_BITRATE_HD,
    MUSIC_VOLUME_LONGFORM, F1_TEAM_COLORS, F1_DEFAULT_COLOR,
    OUTRO_AUDIO_LONGFORM, CREDITS_DURATION_LONGFORM
)

# Concurrency settings
MAX_CONCURRENT_SEGMENTS = min(4, multiprocessing.cpu_count())

# Credits settings (now uses config value, outro audio is ~19s)
CREDITS_DURATION = CREDITS_DURATION_LONGFORM  # Short visual credits overlay
CREDITS_FADE_IN = 0.5
CREDITS_FADE_OUT = 0.5


def get_gpu_encoder() -> Tuple[str, list]:
    """
    Detect available GPU encoder and return encoder name with extra flags.
    For 4K, we need efficient encoding.
    """
    system = platform.system()

    if system == "Darwin":
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True
        )
        if "hevc_videotoolbox" in result.stdout:
            # Use HEVC for better 4K compression
            return "hevc_videotoolbox", ["-allow_sw", "1", "-alpha_quality", "0.75"]
        if "h264_videotoolbox" in result.stdout:
            return "h264_videotoolbox", ["-allow_sw", "1"]

    elif system in ("Linux", "Windows"):
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True
        )
        if "hevc_nvenc" in result.stdout:
            return "hevc_nvenc", ["-preset", "p4", "-tune", "hq", "-rc", "vbr", "-cq", "20"]
        if "h264_nvenc" in result.stdout:
            return "h264_nvenc", ["-preset", "p4", "-tune", "hq", "-rc", "vbr", "-cq", "20"]

    return "libx264", ["-preset", "medium", "-crf", "20"]


GPU_ENCODER, GPU_ENCODER_FLAGS = get_gpu_encoder()


def get_duration(file_path: str) -> float:
    """Get duration of media file in seconds"""
    cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0


def escape_text_for_ffmpeg(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter"""
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\u2019")
    text = text.replace(":", "\\:")
    text = text.replace("%", "\\%")
    return text


def wrap_text(text: str, max_chars: int = 60) -> List[str]:
    """Wrap text into multiple lines for display (wider for 16:9)"""
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


def get_team_color(text: str) -> str:
    """Detect team/driver mentions and return appropriate F1 team color"""
    text_lower = text.lower()
    for keyword, color in F1_TEAM_COLORS.items():
        if keyword in text_lower:
            return color
    return F1_DEFAULT_COLOR


def create_segment_video(segment_idx: int, segment: Dict, audio_path: str,
                         footage_dir: str, output_path: str,
                         width: int, height: int, bitrate: str,
                         encoder: str = None, encoder_flags: list = None,
                         no_text: bool = False) -> Tuple[bool, Optional[str]]:
    """Create video segment with letterbox effect and optional text captions for 16:9"""
    footage_file = f"{footage_dir}/{segment['footage']}"
    if not os.path.exists(footage_file):
        return False, f"Missing footage: {segment['footage']}"

    audio_duration = get_duration(audio_path)
    start_time = segment.get('footage_start', 0)

    # Text overlay (only if not disabled)
    if no_text:
        text_filter = "null"
    else:
        # Wrap text for wider 16:9 format
        lines = wrap_text(segment['text'], max_chars=70)
        team_color = get_team_color(segment['text'])

        # Font and sizing for 16:9 (larger screen = can use bigger fonts)
        f1_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"

        # Dynamic font size based on resolution and line count
        if width >= 3840:  # 4K
            base_font_size = 64
            if len(lines) > 3:
                font_size = 48
            elif len(lines) > 2:
                font_size = 54
            else:
                font_size = base_font_size
        else:  # HD
            base_font_size = 42
            if len(lines) > 3:
                font_size = 32
            elif len(lines) > 2:
                font_size = 36
            else:
                font_size = base_font_size

        line_height = int(font_size * 1.3)

        # Position text at bottom of screen with margin
        total_text_height = len(lines) * line_height
        bottom_margin = int(height * 0.08)  # 8% from bottom
        start_y = height - bottom_margin - total_text_height

        # Build drawtext filters
        drawtext_filters = []
        for i, line in enumerate(lines):
            escaped_line = escape_text_for_ffmpeg(line)
            y_pos = start_y + (i * line_height)

            # Semi-transparent background box for readability
            drawtext_filters.append(
                f"drawtext=text='{escaped_line}':"
                f"fontfile={f1_font}:"
                f"fontsize={font_size}:fontcolor=black@0.7:"
                f"x=(w-text_w)/2+3:y={y_pos}+3:"
                f"box=1:boxcolor=black@0.4:boxborderw=8"
            )
            # Main text
            drawtext_filters.append(
                f"drawtext=text='{escaped_line}':"
                f"fontfile={f1_font}:"
                f"fontsize={font_size}:fontcolor={team_color}:"
                f"x=(w-text_w)/2:y={y_pos}"
            )

        text_filter = ",".join(drawtext_filters) if drawtext_filters else "null"

    # Check if footage is long enough, if not loop it
    footage_duration = get_duration(footage_file)
    available_duration = footage_duration - start_time

    # Scale to fit 16:9 with letterboxing/pillarboxing as needed
    if available_duration >= audio_duration:
        # Footage is long enough, just trim
        filter_complex = (
            f"[0:v]trim=start={start_time}:duration={audio_duration},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"{text_filter}[out]"
        )
    else:
        # Footage too short, loop it to fill audio duration
        loop_count = int(audio_duration / max(available_duration, 1)) + 2
        filter_complex = (
            f"[0:v]trim=start={start_time},setpts=PTS-STARTPTS,"
            f"loop=loop={loop_count}:size=9999:start=0,"
            f"trim=duration={audio_duration},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"{text_filter}[out]"
        )

    video_encoder = encoder or GPU_ENCODER
    extra_flags = encoder_flags if encoder_flags is not None else GPU_ENCODER_FLAGS

    cmd = [
        "ffmpeg", "-y",
        "-i", footage_file,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "1:a",
        "-c:v", video_encoder,
        *extra_flags,
        "-b:v", bitrate,
        "-r", str(LONGFORM_FRAME_RATE),
        "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
        "-t", str(audio_duration),
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(output_path):
        return False, result.stderr[-500:] if result.stderr else "Unknown error"
    return True, None


def process_segment_video(args: Tuple) -> Tuple[int, bool, float, Optional[str]]:
    """Process a single segment video (for concurrent execution)"""
    idx, segment, audio_path, footage_dir, output_path, width, height, bitrate, encoder, encoder_flags, no_text = args

    success, error = create_segment_video(
        idx, segment, audio_path, footage_dir, output_path,
        width, height, bitrate, encoder, encoder_flags, no_text
    )

    if success:
        duration = get_duration(output_path)
        return idx, True, duration, None
    return idx, False, 0, error


def create_outro_video(script: Dict, output_path: str, width: int, height: int,
                       bitrate: str, encoder: str, encoder_flags: list) -> bool:
    """Create outro video with reusable voiceover and brief credits overlay.

    Uses pre-generated outro audio (~19s) with a short credits visual overlay
    at the beginning, then shows channel branding for the rest.
    """

    # Check if outro audio exists
    if not os.path.exists(OUTRO_AUDIO_LONGFORM):
        print(f"Warning: Outro audio not found at {OUTRO_AUDIO_LONGFORM}")
        return False

    outro_duration = get_duration(OUTRO_AUDIO_LONGFORM)

    f1_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"

    if width >= 3840:
        title_size = 72
        channel_size = 96
        cta_size = 48
    else:
        title_size = 48
        channel_size = 64
        cta_size = 32

    # Simple credits text - just show "Sources in description" briefly
    credits_text = "Sources & References in Description"

    # Channel branding for the rest of the outro
    channel_name = "F1 BURNOUTS"
    cta_text = "LIKE • SUBSCRIBE • BELL"

    # Video filter: show credits briefly, then channel branding
    # Credits shown for first CREDITS_DURATION seconds, then fade to channel branding
    center_y = int(height * 0.45)
    cta_y = int(height * 0.58)

    filter_complex = (
        f"color=black:s={width}x{height}:d={outro_duration}:r={LONGFORM_FRAME_RATE},"
        f"format=yuv420p,"
        # Credits text (visible 0 to CREDITS_DURATION)
        f"drawtext=text='{escape_text_for_ffmpeg(credits_text)}':"
        f"fontfile={f1_font}:fontsize={title_size}:"
        f"fontcolor=white:x=(w-text_w)/2:y={center_y}:"
        f"enable='lt(t,{CREDITS_DURATION})',"
        # Channel name (visible after CREDITS_DURATION)
        f"drawtext=text='{channel_name}':"
        f"fontfile={f1_font}:fontsize={channel_size}:"
        f"fontcolor=#E8002D:x=(w-text_w)/2:y={center_y}:"
        f"enable='gte(t,{CREDITS_DURATION})',"
        # CTA text (visible after CREDITS_DURATION)
        f"drawtext=text='{cta_text}':"
        f"fontfile={f1_font}:fontsize={cta_size}:"
        f"fontcolor=white:x=(w-text_w)/2:y={cta_y}:"
        f"enable='gte(t,{CREDITS_DURATION})',"
        # Fade in/out
        f"fade=t=in:st=0:d={CREDITS_FADE_IN},"
        f"fade=t=out:st={outro_duration - CREDITS_FADE_OUT}:d={CREDITS_FADE_OUT}[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=black:s={width}x{height}:d={outro_duration}:r={LONGFORM_FRAME_RATE}",
        "-i", OUTRO_AUDIO_LONGFORM,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "1:a",
        "-c:v", encoder,
        *encoder_flags,
        "-b:v", bitrate,
        "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
        "-t", str(outro_duration),
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(output_path):
        print(f"Outro creation failed: {result.stderr[-300:] if result.stderr else 'Unknown error'}")
        return False
    return True


def create_credits_video(script: Dict, output_path: str, width: int, height: int,
                         bitrate: str, encoder: str, encoder_flags: list) -> bool:
    """Create end credits video with references (legacy, use create_outro_video instead)"""

    # Gather all references from script
    references = []
    references_summary = script.get("references_summary", [])

    # Also gather from segments
    for segment in script.get("segments", []):
        segment_refs = segment.get("references", [])
        for ref in segment_refs:
            if ref not in references:
                references.append(ref)

    if not references and not references_summary:
        # No references, create simple credits
        references_summary = [{"source": "F1.ai", "url": ""}]

    # Use references_summary if available, otherwise use segment references
    if references_summary:
        sources = references_summary
    else:
        # Deduplicate by source name
        seen = set()
        sources = []
        for ref in references:
            if ref.get("source") not in seen:
                seen.add(ref.get("source"))
                sources.append(ref)

    # Build credits text
    f1_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"

    if width >= 3840:
        title_size = 72
        source_size = 42
        url_size = 32
    else:
        title_size = 48
        source_size = 28
        url_size = 22

    # Create filter for credits
    filters = []

    # Title
    title_y = int(height * 0.15)
    filters.append(
        f"drawtext=text='SOURCES & REFERENCES':"
        f"fontfile={f1_font}:fontsize={title_size}:"
        f"fontcolor=white:x=(w-text_w)/2:y={title_y}"
    )

    # Sources list
    current_y = int(height * 0.28)
    line_spacing = int(height * 0.07)

    max_sources = min(len(sources), 8)  # Limit to 8 sources to fit on screen

    for i, source in enumerate(sources[:max_sources]):
        source_name = escape_text_for_ffmpeg(source.get("source", "Unknown"))
        source_url = escape_text_for_ffmpeg(source.get("url", "")[:60])  # Truncate long URLs

        # Source name
        filters.append(
            f"drawtext=text='{source_name}':"
            f"fontfile={f1_font}:fontsize={source_size}:"
            f"fontcolor=#E8002D:x=(w-text_w)/2:y={current_y}"
        )

        # URL (if present)
        if source_url:
            filters.append(
                f"drawtext=text='{source_url}':"
                f"fontfile={f1_font}:fontsize={url_size}:"
                f"fontcolor=#888888:x=(w-text_w)/2:y={current_y + int(source_size * 1.2)}"
            )

        current_y += line_spacing

    # Footer
    footer_y = int(height * 0.88)
    filters.append(
        f"drawtext=text='Created with F1.ai':"
        f"fontfile={f1_font}:fontsize={url_size}:"
        f"fontcolor=#666666:x=(w-text_w)/2:y={footer_y}"
    )

    filter_chain = ",".join(filters)

    # Create black background with fade
    filter_complex = (
        f"color=black:s={width}x{height}:d={CREDITS_DURATION}:r={LONGFORM_FRAME_RATE},"
        f"format=yuv420p,{filter_chain},"
        f"fade=t=in:st=0:d={CREDITS_FADE_IN},"
        f"fade=t=out:st={CREDITS_DURATION - CREDITS_FADE_OUT}:d={CREDITS_FADE_OUT}[out];"
        f"anullsrc=r=48000:cl=stereo:d={CREDITS_DURATION}[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=black:s={width}x{height}:d={CREDITS_DURATION}:r={LONGFORM_FRAME_RATE}",
        "-f", "lavfi",
        "-i", f"anullsrc=r=48000:cl=stereo:d={CREDITS_DURATION}",
        "-filter_complex",
        f"[0:v]{filter_chain},"
        f"fade=t=in:st=0:d={CREDITS_FADE_IN},"
        f"fade=t=out:st={CREDITS_DURATION - CREDITS_FADE_OUT}:d={CREDITS_FADE_OUT}[out]",
        "-map", "[out]",
        "-map", "1:a",
        "-c:v", encoder,
        *encoder_flags,
        "-b:v", bitrate,
        "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
        "-t", str(CREDITS_DURATION),
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)


def add_background_music(video_path: str, output_path: str, music_volume: float = MUSIC_VOLUME_LONGFORM) -> bool:
    """Mix background music under video audio at lower volume for long-form.

    Converts voiceover to stereo, then mixes with stereo background music.
    Uses amix with normalize=0 to preserve original voiceover volume.
    """
    if not os.path.exists(BACKGROUND_MUSIC):
        subprocess.run(["cp", video_path, output_path])
        return True

    video_duration = get_duration(video_path)

    # Convert voiceover to stereo (mono -> stereo) to match background music
    # Then mix with background music at low volume
    # normalize=0 prevents volume reduction of voiceover
    filter_complex = (
        f"[0:a]aformat=channel_layouts=stereo[voice];"
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{video_duration},"
        f"afade=t=in:st=0:d=3,"
        f"afade=t=out:st={video_duration-3}:d=3,"
        f"volume={music_volume}[music];"
        f"[voice][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", BACKGROUND_MUSIC,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(output_path):
        print(f"Music mixing failed: {result.stderr[-300:] if result.stderr else 'Unknown'}")
        return False
    return True


def generate_srt_captions(script: Dict, audio_dir: str, output_path: str) -> bool:
    """Generate SRT caption file from script segments with accurate timings"""
    segments = script.get("segments", [])

    srt_content = []
    current_time = 0.0

    for i, segment in enumerate(segments):
        audio_file = f"{audio_dir}/segment_{i:02d}.mp3"
        if os.path.exists(audio_file):
            duration = get_duration(audio_file)
        else:
            # Estimate based on word count (150 words/min average)
            word_count = len(segment['text'].split())
            duration = word_count / 2.5  # ~150 wpm

        start_time = current_time
        end_time = current_time + duration

        # Format times as HH:MM:SS,mmm
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

        srt_content.append(f"{i + 1}")
        srt_content.append(f"{format_time(start_time)} --> {format_time(end_time)}")
        srt_content.append(segment['text'])
        srt_content.append("")  # Blank line between entries

        current_time = end_time

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
        return True
    except Exception as e:
        print(f"Failed to generate SRT: {e}")
        return False


def verify_output(video_path: str) -> Tuple[bool, str]:
    """Verify video and audio durations match and check resolution"""
    # Check streams
    cmd = ["ffprobe", "-v", "error", "-show_entries",
           "stream=codec_type,duration,width,height",
           "-of", "json", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    try:
        data = json.loads(result.stdout)
        streams = data.get("streams", [])

        video_dur = audio_dur = 0
        width = height = 0

        for stream in streams:
            if stream.get("codec_type") == "video":
                video_dur = float(stream.get("duration", 0))
                width = stream.get("width", 0)
                height = stream.get("height", 0)
            elif stream.get("codec_type") == "audio":
                audio_dur = float(stream.get("duration", 0))

        diff = abs(video_dur - audio_dur)

        info = f"Resolution: {width}x{height}, Video: {video_dur:.1f}s, Audio: {audio_dur:.1f}s"

        if diff > 2.0:  # Allow slightly more tolerance for long-form
            return False, f"Duration mismatch! {info}"

        # Verify 16:9 aspect ratio
        if width > 0 and height > 0:
            aspect = width / height
            if abs(aspect - 16/9) > 0.1:
                return False, f"Aspect ratio issue (expected 16:9). {info}"

        return True, info

    except Exception as e:
        return False, f"Verification error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description='Assemble long-form 16:9 video')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--resolution', choices=['4k', 'hd'], default='4k',
                        help='Output resolution (default: 4k)')
    parser.add_argument('--no-music', action='store_true', help='Skip background music')
    parser.add_argument('--no-text', action='store_true', help='No burned-in text/captions (use separate SRT file)')
    parser.add_argument('--no-credits', action='store_true', help='Skip end credits')
    parser.add_argument('--sequential', action='store_true', help='Disable concurrent processing')
    parser.add_argument('--workers', type=int, default=MAX_CONCURRENT_SEGMENTS,
                        help=f'Max concurrent workers (default: {MAX_CONCURRENT_SEGMENTS})')
    parser.add_argument('--encoder', choices=['auto', 'hevc', 'h264', 'cpu'],
                        default='auto', help='Video encoder (default: auto-detect)')
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

    # Set resolution
    if args.resolution == '4k':
        width, height = LONGFORM_OUTPUT_WIDTH_4K, LONGFORM_OUTPUT_HEIGHT_4K
        bitrate = LONGFORM_VIDEO_BITRATE_4K
    else:
        width, height = LONGFORM_OUTPUT_WIDTH_HD, LONGFORM_OUTPUT_HEIGHT_HD
        bitrate = LONGFORM_VIDEO_BITRATE_HD

    # Determine encoder
    if args.encoder == 'auto':
        encoder, encoder_flags = GPU_ENCODER, GPU_ENCODER_FLAGS
    elif args.encoder == 'hevc':
        if platform.system() == "Darwin":
            encoder, encoder_flags = "hevc_videotoolbox", ["-allow_sw", "1"]
        else:
            encoder, encoder_flags = "hevc_nvenc", ["-preset", "p4", "-tune", "hq"]
    elif args.encoder == 'h264':
        if platform.system() == "Darwin":
            encoder, encoder_flags = "h264_videotoolbox", ["-allow_sw", "1"]
        else:
            encoder, encoder_flags = "h264_nvenc", ["-preset", "p4", "-tune", "hq"]
    else:  # cpu
        encoder, encoder_flags = "libx264", ["-preset", "medium", "-crf", "18"]

    print("=" * 70)
    print(f"Long-Form Video Assembler - Project: {args.project}")
    print(f"Resolution: {width}x{height} ({args.resolution.upper()})")
    print(f"Bitrate: {bitrate}, Framerate: {LONGFORM_FRAME_RATE}fps")
    print(f"Encoder: {encoder}")
    print(f"Concurrency: {'Sequential' if args.sequential else f'{args.workers} workers'}")
    print("=" * 70)

    with open(script_file) as f:
        script = json.load(f)

    segments = script["segments"]

    # Check audio exists
    missing_audio = [i for i in range(len(segments))
                    if not os.path.exists(f"{audio_dir}/segment_{i:02d}.mp3")]
    if missing_audio:
        print(f"\nMissing audio for segments: {missing_audio}")
        print(f"Run: python3 src/audio_generator.py --project {args.project}")
        sys.exit(1)

    # Create segments
    print(f"\nCreating {len(segments)} segments...\n")
    segment_videos = []
    results = {}

    # Prepare tasks
    tasks = [
        (i, segment, f"{audio_dir}/segment_{i:02d}.mp3", footage_dir,
         f"{temp_dir}/segment_{i:02d}.mp4", width, height, bitrate, encoder, encoder_flags, args.no_text)
        for i, segment in enumerate(segments)
    ]

    if args.sequential:
        for task in tasks:
            idx = task[0]
            segment = segments[idx]
            context = segment.get('context', segment.get('section', 'segment'))
            print(f"[{idx+1}/{len(segments)}] {context}...", end=" ", flush=True)

            idx, success, duration, error = process_segment_video(task)
            if success:
                segment_videos.append(f"{temp_dir}/segment_{idx:02d}.mp4")
                print(f"Done ({duration:.1f}s)")
            else:
                print(f"Failed: {error}")
            results[idx] = (success, duration)
    else:
        print(f"Processing {len(tasks)} segments concurrently...\n")

        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            future_to_idx = {executor.submit(process_segment_video, task): task[0] for task in tasks}

            for future in as_completed(future_to_idx):
                idx, success, duration, error = future.result()
                segment = segments[idx]
                context = segment.get('context', segment.get('section', 'segment'))

                if success:
                    segment_videos.append(f"{temp_dir}/segment_{idx:02d}.mp4")
                    print(f"[{idx+1}/{len(segments)}] Done: {context} ({duration:.1f}s)")
                else:
                    print(f"[{idx+1}/{len(segments)}] Failed: {context} - {error}")

                results[idx] = (success, duration)

        segment_videos.sort(key=lambda x: int(x.split('_')[-1].replace('.mp4', '')))

    if not segment_videos:
        print("\nNo segments created!")
        sys.exit(1)

    # Create outro with reusable voiceover and brief credits overlay
    if not args.no_credits:
        print("\nCreating outro with credits...")
        outro_path = f"{temp_dir}/outro.mp4"
        if create_outro_video(script, outro_path, width, height, bitrate, encoder, encoder_flags):
            segment_videos.append(outro_path)
            outro_dur = get_duration(outro_path)
            print(f"Outro created successfully ({outro_dur:.1f}s)")
        else:
            print("Warning: Failed to create outro, falling back to legacy credits...")
            credits_path = f"{temp_dir}/credits.mp4"
            if create_credits_video(script, credits_path, width, height, bitrate, encoder, encoder_flags):
                segment_videos.append(credits_path)
                print("Legacy credits created")

    # Concatenate
    print(f"\nConcatenating {len(segment_videos)} segments...")

    concat_file = f"{temp_dir}/concat.txt"
    with open(concat_file, "w") as f:
        for video in segment_videos:
            f.write(f"file '{video}'\n")

    concat_output = f"{temp_dir}/concat.mp4"

    # Use same encoder for concat to maintain quality
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c:v", encoder,
        *encoder_flags,
        "-b:v", bitrate,
        "-c:a", "aac", "-b:a", LONGFORM_AUDIO_BITRATE,
        "-movflags", "+faststart",
        concat_output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not os.path.exists(concat_output):
        print(f"Concat failed: {result.stderr[-500:] if result.stderr else 'Unknown error'}")
        sys.exit(1)

    # Add music
    final_output = f"{output_dir}/final.mp4"
    if not args.no_music:
        print("Adding background music...")
        add_background_music(concat_output, final_output)
    else:
        subprocess.run(["cp", concat_output, final_output])

    # Generate SRT caption file if no-text mode
    if args.no_text:
        srt_output = f"{output_dir}/captions.srt"
        print("Generating SRT caption file...")
        if generate_srt_captions(script, audio_dir, srt_output):
            print(f"Captions saved to: {srt_output}")
        else:
            print("Warning: Failed to generate captions")

    # Verify
    if os.path.exists(final_output):
        ok, msg = verify_output(final_output)
        size_mb = os.path.getsize(final_output) / (1024 * 1024)
        duration = get_duration(final_output)

        print(f"\n{'=' * 70}")
        if ok:
            print(f"SUCCESS: {final_output}")
            print(f"{msg}")
            print(f"Duration: {duration/60:.1f} minutes ({duration:.0f}s)")
            print(f"Size: {size_mb:.1f}MB")
            if args.no_text:
                print(f"Captions: {output_dir}/captions.srt")
        else:
            print(f"WARNING: {msg}")
            print(f"Output: {final_output}")
    else:
        print("\nFailed to create final video")
        sys.exit(1)


if __name__ == "__main__":
    main()
