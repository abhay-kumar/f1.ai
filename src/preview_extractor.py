#!/usr/bin/env python3
"""
Preview Extractor - Extracts frames from footage for visual verification
CRITICAL: Always verify footage matches narrative before assembly!
"""
import os
import sys
import json
import argparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0

def extract_frames(video_path, output_dir, name, interval=10):
    """Extract frames at regular intervals"""
    duration = get_duration(video_path)
    frames = []

    for t in range(0, int(duration), interval):
        output_path = f"{output_dir}/{name}_t{t:03d}.jpg"
        cmd = [
            "ffmpeg", "-y", "-ss", str(t), "-i", video_path,
            "-vframes", "1", "-q:v", "2", output_path
        ]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(output_path):
            frames.append((t, output_path))

    return frames

def main():
    parser = argparse.ArgumentParser(description='Extract preview frames from footage')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--segment', type=int, help='Extract for specific segment only')
    parser.add_argument('--interval', type=int, default=10, help='Seconds between frames (default: 10)')
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    footage_dir = f"{project_dir}/footage"
    preview_dir = f"{project_dir}/previews"
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    os.makedirs(preview_dir, exist_ok=True)

    with open(script_file) as f:
        script = json.load(f)

    segments = script["segments"]

    print("=" * 60)
    print(f"Preview Extractor - Project: {args.project}")
    print("=" * 60)
    print("\nIMPORTANT: Review these frames to verify footage matches narrative!")
    print("Update 'footage_start' in script.json based on visual inspection.\n")

    if args.segment is not None:
        segments_to_process = [(args.segment, segments[args.segment])]
    else:
        segments_to_process = list(enumerate(segments))

    for i, segment in segments_to_process:
        footage_file = segment.get('footage', f'segment_{i:02d}.mp4')
        full_path = f"{footage_dir}/{footage_file}"

        if not os.path.exists(full_path):
            print(f"[{i}] MISSING: {footage_file}")
            continue

        print(f"\n[{i}] {segment['context']}")
        print(f"    Text: {segment['text'][:60]}...")
        print(f"    Current footage_start: {segment.get('footage_start', 0)}s")

        name = f"seg{i:02d}"
        frames = extract_frames(full_path, preview_dir, name, args.interval)

        print(f"    Extracted {len(frames)} frames:")
        for t, path in frames:
            print(f"      t={t:3d}s -> {os.path.basename(path)}")

    print(f"\n{'=' * 60}")
    print(f"Previews saved to: {preview_dir}/")
    print("\nNext steps:")
    print("1. Open preview folder and review images")
    print("2. Find the timestamp that best matches each segment's narrative")
    print("3. Update 'footage_start' in script.json")
    print("4. Run video assembler")

if __name__ == "__main__":
    main()
