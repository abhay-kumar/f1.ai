#!/usr/bin/env python3
"""
Batch Assembler — runs each segment in a separate subprocess to avoid OOM.

The parent process is extremely lightweight: only stdlib imports, no heavy
modules. All segment creation, color grading, SFX, and music mixing happen
in isolated subprocesses so memory is fully released between steps.

Usage:
    python3 src/batch_assembler.py --project {name} [--resolution hd|4k] [--no-yt-search]
"""

import argparse
import json
import os
import subprocess
import sys
import time

# Only import lightweight config values — no heavy modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    LONGFORM_AUDIO_BITRATE,
    LONGFORM_OUTPUT_HEIGHT_4K,
    LONGFORM_OUTPUT_HEIGHT_HD,
    LONGFORM_OUTPUT_WIDTH_4K,
    LONGFORM_OUTPUT_WIDTH_HD,
    get_project_dir,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_duration(file_path: str) -> float:
    """Get media duration via ffprobe — no Python imports needed."""
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
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return 0.0


def detect_gpu_encoder() -> list:
    """Detect GPU encoder without importing image_video_assembler."""
    # Check for VideoToolbox (macOS)
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if "h264_videotoolbox" in result.stdout:
        return ["-c:v", "h264_videotoolbox", "-b:v", "12M"]
    elif "h264_nvenc" in result.stdout:
        return ["-c:v", "h264_nvenc", "-b:v", "12M"]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "20"]


def run_segment_subprocess(
    i, script_file, audio_dir, temp_dir, output_path, width, height, no_yt_search
):
    """Run segment creation in a completely isolated subprocess."""
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            f"""
import sys, os, json, shutil
sys.path.insert(0, '{BASE_DIR}')
os.chdir('{BASE_DIR}')

from src.image_video_assembler import (
    create_segment_video, detect_color_grade, apply_color_grade, get_duration
)

with open('{script_file}') as f:
    script = json.load(f)
seg = script['segments'][{i}]

work_dir = '{temp_dir}/visuals'
os.makedirs(work_dir, exist_ok=True)

success, error, vtype = create_segment_video(
    {i}, seg, '{audio_dir}/segment_{i:02d}.mp3',
    work_dir, '{output_path}', {width}, {height},
    use_veo3=False, use_yt_search={not no_yt_search},
)

if success:
    grade = detect_color_grade(seg)
    if grade != 'none':
        graded = '{output_path}.graded.mp4'
        if apply_color_grade('{output_path}', graded, grade):
            os.replace(graded, '{output_path}')
    dur = get_duration('{output_path}')
    print(f'OK|{{vtype}}|{{grade}}|{{dur:.1f}}')
else:
    print(f'FAIL|{{error}}')

# Cleanup work dir for this segment
seg_work = os.path.join(work_dir, f'segment_{i:02d}')
if os.path.exists(seg_work):
    shutil.rmtree(seg_work, ignore_errors=True)
""",
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    return proc


def run_post_processing(
    temp_dir,
    output_dir,
    segment_videos,
    segment_durations,
    segments,
    width,
    height,
    intro_path,
    args,
):
    """Run all post-processing (concat, SFX, music, captions) in a subprocess."""
    # Write segment info to a temp JSON for the subprocess
    post_info = {
        "segment_videos": segment_videos,
        "segment_durations": segment_durations,
        "temp_dir": temp_dir,
        "output_dir": output_dir,
        "width": width,
        "height": height,
        "intro_path": intro_path,
        "no_sfx": args.no_sfx,
        "no_music": args.no_music,
        "no_credits": args.no_credits,
        "script_file": f"{get_project_dir(args.project)}/script.json",
        "audio_dir": f"{get_project_dir(args.project)}/audio",
    }
    info_path = os.path.join(temp_dir, "post_info.json")
    with open(info_path, "w") as f:
        json.dump(post_info, f)

    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            f"""
import sys, os, json
sys.path.insert(0, '{BASE_DIR}')
os.chdir('{BASE_DIR}')

with open('{info_path}') as f:
    info = json.load(f)

from src.image_video_assembler import (
    gpu_enc_args, add_transition_sfx, add_background_music,
    detect_music_mood, generate_srt_captions, create_outro_video
)
from src.config import (
    LONGFORM_AUDIO_BITRATE, MUSIC_VOLUME_LONGFORM,
    MUSIC_VOLUME_UPLIFTING, MUSIC_VOLUME_ATMOSPHERIC,
)
from channels import channel_asset, load_channel_from_script
import subprocess as sp

segment_videos = info['segment_videos']
segment_durations = info['segment_durations']
temp_dir = info['temp_dir']
output_dir = info['output_dir']
width = info['width']
height = info['height']

# Outro
if not info['no_credits']:
    outro_path = os.path.join(temp_dir, 'outro.mp4')
    if not os.path.exists(outro_path):
        if create_outro_video(outro_path, width, height):
            segment_videos.append(outro_path)
            print('Outro created')

# Concatenate
print(f'Concatenating {{len(segment_videos)}} segments...')
concat_file = os.path.join(temp_dir, 'concat.txt')
with open(concat_file, 'w') as f:
    for v in segment_videos:
        f.write(f"file '{{v}}'\\n")

concat_output = os.path.join(temp_dir, 'concat.mp4')
enc = gpu_enc_args()
cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
       *enc, '-c:a', 'aac', '-b:a', LONGFORM_AUDIO_BITRATE, concat_output]
sp.run(cmd, capture_output=True, text=True, timeout=600)

if not os.path.exists(concat_output):
    print('FAIL|Concatenation failed')
    sys.exit(1)

# SFX
if not info['no_sfx'] and segment_durations:
    print('Adding transition SFX...')
    sfx_output = os.path.join(temp_dir, 'with_sfx.mp4')
    if add_transition_sfx(concat_output, sfx_output, segment_durations):
        concat_output = sfx_output

# Music
final_output = os.path.join(output_dir, 'final.mp4')
if not info['no_music']:
    print('Adding background music...')
    with open(info['script_file']) as f:
        script = json.load(f)
    segments = script['segments']

    segment_volumes = []
    intro_offset = 0.0
    intro_p = info.get('intro_path')
    if intro_p and os.path.exists(intro_p):
        from src.image_video_assembler import get_duration
        intro_dur = get_duration(intro_p)
        segment_volumes.append((0.0, intro_dur, MUSIC_VOLUME_UPLIFTING))
        intro_offset = intro_dur

    cumulative = intro_offset
    for idx, dur in enumerate(segment_durations):
        if idx < len(segments):
            mood = detect_music_mood(segments[idx])
            vol = {{'uplifting': MUSIC_VOLUME_UPLIFTING,
                    'atmospheric': MUSIC_VOLUME_ATMOSPHERIC}}.get(mood, MUSIC_VOLUME_LONGFORM)
        else:
            vol = MUSIC_VOLUME_LONGFORM
        segment_volumes.append((cumulative, cumulative + dur, vol))
        cumulative += dur

    add_background_music(concat_output, final_output, segment_volumes=segment_volumes)
else:
    sp.run(['cp', concat_output, final_output])

# Captions
with open(info['script_file']) as f:
    script = json.load(f)
generate_srt_captions(script, info['audio_dir'], os.path.join(output_dir, 'captions.srt'))

if os.path.exists(final_output):
    from src.image_video_assembler import get_duration as gd
    size_mb = os.path.getsize(final_output) / (1024 * 1024)
    duration = gd(final_output)
    print(f'OK|{{duration:.0f}}|{{size_mb:.1f}}')
else:
    print('FAIL|No final output')
""",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    return proc


def main():
    parser = argparse.ArgumentParser(description="Batch assembler (OOM-safe)")
    parser.add_argument("--project", required=True)
    parser.add_argument("--resolution", choices=["4k", "hd"], default="hd")
    parser.add_argument("--no-yt-search", action="store_true")
    parser.add_argument("--no-sfx", action="store_true")
    parser.add_argument("--no-intro", action="store_true")
    parser.add_argument("--no-music", action="store_true")
    parser.add_argument("--no-credits", action="store_true")
    parser.add_argument(
        "--start-from", type=int, default=0, help="Resume from segment N"
    )
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    audio_dir = f"{project_dir}/audio"
    temp_dir = f"{project_dir}/temp"
    output_dir = f"{project_dir}/output"
    script_file = f"{project_dir}/script.json"

    for d in [temp_dir, output_dir]:
        os.makedirs(d, exist_ok=True)

    with open(script_file) as f:
        script = json.load(f)
    segments = script["segments"]

    if args.resolution == "4k":
        width, height = LONGFORM_OUTPUT_WIDTH_4K, LONGFORM_OUTPUT_HEIGHT_4K
    else:
        width, height = LONGFORM_OUTPUT_WIDTH_HD, LONGFORM_OUTPUT_HEIGHT_HD

    print("=" * 70)
    print(f"Batch Assembler - Project: {args.project}")
    print(f"Resolution: {width}x{height} | Segments: {len(segments)}")
    print(f"Starting from: segment {args.start_from}")
    print("=" * 70)
    sys.stdout.flush()

    # Phase 1: Create intro in subprocess
    intro_path = f"{temp_dir}/intro.mp4"
    if not args.no_intro and not os.path.exists(intro_path):
        print("\n[Intro] Creating animated intro...")
        sys.stdout.flush()
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"""
import sys; sys.path.insert(0, '{BASE_DIR}')
import os; os.chdir('{BASE_DIR}')
from src.intro_generator import create_intro_video
ok = create_intro_video('{intro_path}', {width}, {height})
print('OK' if ok else 'FAIL')
""",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if "OK" in result.stdout:
            print("    Intro created")
        else:
            print(f"    Intro failed: {result.stderr[:100]}")
            intro_path = None
    elif args.no_intro:
        intro_path = None
    else:
        print(f"\n[Intro] Using cached: {intro_path}")
    sys.stdout.flush()

    # Phase 2: Process each segment in a subprocess
    print(f"\nProcessing {len(segments)} segments (subprocess per segment)...\n")
    sys.stdout.flush()

    segment_durations = []
    failed_segments = []

    for i in range(len(segments)):
        output_path = f"{temp_dir}/segment_{i:02d}.mp4"

        # Skip already-created segments (for resume)
        if i < args.start_from and os.path.exists(output_path):
            dur = get_duration(output_path)
            segment_durations.append(dur)
            print(f"[{i + 1}/{len(segments)}] Cached ({dur:.1f}s)")
            sys.stdout.flush()
            continue

        if os.path.exists(output_path) and i >= args.start_from:
            os.remove(output_path)

        seg = segments[i]
        context = seg.get("context", "segment")[:40]
        print(f"[{i + 1}/{len(segments)}] {context}...", end=" ", flush=True)

        start_time = time.time()
        try:
            proc = run_segment_subprocess(
                i,
                script_file,
                audio_dir,
                temp_dir,
                output_path,
                width,
                height,
                args.no_yt_search,
            )
            elapsed = time.time() - start_time

            output_line = (
                proc.stdout.strip().split("\n")[-1] if proc.stdout.strip() else ""
            )

            if output_line.startswith("OK|"):
                parts = output_line.split("|")
                vtype = parts[1] if len(parts) > 1 else "?"
                grade = parts[2] if len(parts) > 2 else "none"
                dur_str = parts[3] if len(parts) > 3 else "?"
                grade_label = f" grade={grade}" if grade != "none" else ""
                print(
                    f"Done ({dur_str}s) [{vtype}{grade_label}] ({elapsed:.0f}s elapsed)"
                )
                if os.path.exists(output_path):
                    segment_durations.append(float(dur_str))
                else:
                    print(f"    WARNING: output file missing")
                    segment_durations.append(0)
                    failed_segments.append(i)
            else:
                error_msg = (
                    output_line.replace("FAIL|", "")
                    if output_line
                    else proc.stderr[:200]
                )
                print(f"Failed ({elapsed:.0f}s): {error_msg}")
                failed_segments.append(i)

        except subprocess.TimeoutExpired:
            print(f"Timed out (180s)")
            failed_segments.append(i)

        sys.stdout.flush()

    # Summary
    created = sum(
        1
        for i in range(len(segments))
        if os.path.exists(f"{temp_dir}/segment_{i:02d}.mp4")
    )
    print(f"\nSegments created: {created}/{len(segments)}")
    if failed_segments:
        print(f"Failed segments: {failed_segments}")
    sys.stdout.flush()

    if created == 0:
        print("\nNo segments created!")
        sys.exit(1)

    # Collect existing segment files
    segment_videos = []
    if intro_path and os.path.exists(intro_path):
        segment_videos.append(intro_path)

    for i in range(len(segments)):
        path = f"{temp_dir}/segment_{i:02d}.mp4"
        if os.path.exists(path):
            segment_videos.append(path)

    # Phase 3: Post-processing (concat, SFX, music) in subprocess
    print(f"\nPost-processing {len(segment_videos)} videos...")
    sys.stdout.flush()

    proc = run_post_processing(
        temp_dir,
        output_dir,
        segment_videos,
        segment_durations,
        segments,
        width,
        height,
        intro_path,
        args,
    )

    output_line = proc.stdout.strip().split("\n")[-1] if proc.stdout.strip() else ""
    # Print all subprocess output
    for line in proc.stdout.strip().split("\n"):
        if line and not line.startswith("OK|") and not line.startswith("FAIL|"):
            print(f"  {line}")

    if output_line.startswith("OK|"):
        parts = output_line.split("|")
        duration = float(parts[1]) if len(parts) > 1 else 0
        size_mb = float(parts[2]) if len(parts) > 2 else 0
        final_path = f"{output_dir}/final.mp4"
        print(f"\n{'=' * 70}")
        print(f"SUCCESS: {final_path}")
        print(f"Duration: {duration / 60:.1f} minutes ({duration:.0f}s)")
        print(f"Size: {size_mb:.1f}MB")
        if failed_segments:
            print(f"Note: {len(failed_segments)} segments failed and were skipped")
        print(f"{'=' * 70}")
    else:
        print(f"\nPost-processing failed: {proc.stderr[:300]}")
        # Fallback: just concat without SFX/music
        print("Attempting simple concat fallback...")
        concat_file = f"{temp_dir}/concat.txt"
        with open(concat_file, "w") as cf:
            for v in segment_videos:
                cf.write(f"file '{v}'\n")

        final_path = f"{output_dir}/final.mp4"
        enc = detect_gpu_encoder()
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            *enc,
            "-c:a",
            "aac",
            "-b:a",
            LONGFORM_AUDIO_BITRATE,
            final_path,
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if os.path.exists(final_path):
            size_mb = os.path.getsize(final_path) / (1024 * 1024)
            duration = get_duration(final_path)
            print(f"\n{'=' * 70}")
            print(f"SUCCESS (simple concat): {final_path}")
            print(f"Duration: {duration / 60:.1f} minutes ({duration:.0f}s)")
            print(f"Size: {size_mb:.1f}MB")
            print(f"{'=' * 70}")
        else:
            print("Concat fallback also failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()
