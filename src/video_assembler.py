#!/usr/bin/env python3
"""
Video Assembler - Creates final short video from audio + footage
Includes all fixes for common issues:
- Consistent framerate (30fps) to avoid timestamp issues
- Split filter for blur-pad effect
- Re-encode during concat to normalize timestamps
- Background music mixing
"""
import os
import sys
import json
import argparse
import subprocess
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    get_project_dir, FRAME_RATE, VIDEO_BITRATE, AUDIO_BITRATE,
    OUTPUT_WIDTH, OUTPUT_HEIGHT, BACKGROUND_MUSIC, MUSIC_VOLUME,
    F1_TEAM_COLORS, F1_DEFAULT_COLOR
)

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0

def download_music_if_needed():
    """Download background music if not present"""
    if os.path.exists(BACKGROUND_MUSIC):
        return True

    os.makedirs(os.path.dirname(BACKGROUND_MUSIC), exist_ok=True)
    print("Downloading background music...", end=" ", flush=True)

    # Try yt-dlp for music
    cmd = [
        "yt-dlp", "-x", "--audio-format", "mp3",
        "-o", BACKGROUND_MUSIC.replace('.mp3', '.%(ext)s'),
        "https://www.youtube.com/watch?v=MkNeIUgNPQ8"  # Epic cinematic
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

def create_segment_video(segment_idx, segment, audio_path, footage_dir, output_path):
    """Create video segment with blur-pad effect and text captions"""
    footage_file = f"{footage_dir}/{segment['footage']}"
    if not os.path.exists(footage_file):
        return False, f"Missing footage: {segment['footage']}"

    audio_duration = get_duration(audio_path)
    start_time = segment.get('footage_start', 0)

    # Wrap and escape text for FFmpeg
    lines = wrap_text(segment['text'], max_chars=25)  # Shorter lines for bigger font

    # Get F1 team color based on narration content
    team_color = get_team_color(segment['text'])

    # Build drawtext filters for each line
    # F1 Team Radio style: big bold font, subtle shadow, team colors
    # Using official F1 Display Black font
    f1_font = "/Users/abhaykumar/Documents/f1.ai/shared/fonts/Formula1-Bold.ttf"

    # Dynamic font size: smaller for more lines to prevent overflow
    base_font_size = 72
    if len(lines) > 3:
        font_size = 52
    elif len(lines) > 2:
        font_size = 60
    else:
        font_size = base_font_size

    line_height = int(font_size * 1.2)

    # Position text at bottom of screen (in the blur area)
    # Calculate total text block height and position from bottom
    total_text_height = len(lines) * line_height
    bottom_margin = 120  # Distance from bottom edge
    start_y = OUTPUT_HEIGHT - bottom_margin - total_text_height

    drawtext_filters = []
    for i, line in enumerate(lines):
        escaped_line = escape_text_for_ffmpeg(line)
        y_pos = start_y + (i * line_height)
        # Shadow layer (offset by 3px, soft black shadow)
        drawtext_filters.append(
            f"drawtext=text='{escaped_line}':"
            f"fontfile={f1_font}:"
            f"fontsize={font_size}:fontcolor=black@0.5:"
            f"x=(w-text_w)/2+3:y={y_pos}+3"
        )
        # Main text layer
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
        "ffmpeg", "-y",
        "-i", footage_file,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "1:a",
        "-c:v", "h264_videotoolbox",
        "-b:v", VIDEO_BITRATE,
        "-r", str(FRAME_RATE),  # CRITICAL: Consistent framerate
        "-c:a", "aac", "-b:a", AUDIO_BITRATE,
        "-t", str(audio_duration),
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(output_path):
        return False, result.stderr[-200:] if result.stderr else "Unknown error"
    return True, None

def add_background_music(video_path, output_path):
    """Mix background music under video audio"""
    if not os.path.exists(BACKGROUND_MUSIC):
        subprocess.run(["cp", video_path, output_path])
        return True

    video_duration = get_duration(video_path)

    filter_complex = (
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{video_duration},"
        f"afade=t=out:st={video_duration-2}:d=2,"
        f"volume={MUSIC_VOLUME}[music];"
        f"[0:a][music]amix=inputs=2:duration=first[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", BACKGROUND_MUSIC,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        output_path
    ]

    subprocess.run(cmd, capture_output=True)
    return os.path.exists(output_path)

def verify_output(video_path):
    """Verify video and audio durations match"""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration",
           "-of", "csv=p=0", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    video_dur = audio_dur = 0
    for line in result.stdout.strip().split('\n'):
        parts = line.split(',')
        if len(parts) == 2:
            if parts[0] == 'video':
                video_dur = float(parts[1])
            elif parts[0] == 'audio':
                audio_dur = float(parts[1])

    diff = abs(video_dur - audio_dur)
    if diff > 1.0:
        return False, f"Duration mismatch! Video: {video_dur:.1f}s, Audio: {audio_dur:.1f}s"
    return True, f"Video: {video_dur:.1f}s, Audio: {audio_dur:.1f}s"

def main():
    parser = argparse.ArgumentParser(description='Assemble final video')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--no-music', action='store_true', help='Skip background music')
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

    print("=" * 60)
    print(f"Video Assembler - Project: {args.project}")
    print(f"Settings: {FRAME_RATE}fps, {OUTPUT_WIDTH}x{OUTPUT_HEIGHT}")
    print("=" * 60)

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

    # Download music
    if not args.no_music:
        print()
        download_music_if_needed()

    # Create segments
    print(f"\nCreating {len(segments)} segments...\n")
    segment_videos = []

    for i, segment in enumerate(segments):
        audio_path = f"{audio_dir}/segment_{i:02d}.mp3"
        video_path = f"{temp_dir}/segment_{i:02d}.mp4"

        print(f"[{i+1}/{len(segments)}] {segment['context']}...", end=" ", flush=True)

        success, error = create_segment_video(i, segment, audio_path, footage_dir, video_path)
        if success:
            segment_videos.append(video_path)
            duration = get_duration(video_path)
            print(f"Done ({duration:.1f}s)")
        else:
            print(f"Failed: {error}")

    if not segment_videos:
        print("\nNo segments created!")
        sys.exit(1)

    # Concatenate (re-encode to fix timestamps)
    print(f"\nConcatenating {len(segment_videos)} segments...")

    concat_file = f"{temp_dir}/concat.txt"
    with open(concat_file, "w") as f:
        for video in segment_videos:
            f.write(f"file '{video}'\n")

    concat_output = f"{temp_dir}/concat.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c:v", "h264_videotoolbox",  # Re-encode to normalize timestamps
        "-b:v", VIDEO_BITRATE,
        "-c:a", "aac", "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        concat_output
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
