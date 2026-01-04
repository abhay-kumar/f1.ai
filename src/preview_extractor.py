#!/usr/bin/env python3
"""
Preview Extractor - Extracts frames from footage for visual verification
CRITICAL: Always verify footage matches narrative before assembly!
Supports concurrent frame extraction for faster processing.
"""
import os
import sys
import json
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, List, Optional
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir

# Concurrency settings
MAX_CONCURRENT_EXTRACTIONS = 4

# Thread-safe print
print_lock = threading.Lock()

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0

def extract_single_frame(args: Tuple) -> Tuple[int, str, bool]:
    """Extract a single frame (for concurrent execution)"""
    t, video_path, output_path = args
    cmd = [
        "ffmpeg", "-y", "-ss", str(t), "-i", video_path,
        "-vframes", "1", "-q:v", "2", output_path
    ]
    subprocess.run(cmd, capture_output=True)
    return t, output_path, os.path.exists(output_path)


def extract_frames(video_path: str, output_dir: str, name: str, interval: int = 10,
                   concurrent: bool = True) -> List[Tuple[int, str]]:
    """Extract frames at regular intervals (optionally concurrent)"""
    duration = get_duration(video_path)
    frames = []

    # Prepare extraction tasks
    tasks = []
    for t in range(0, int(duration), interval):
        output_path = f"{output_dir}/{name}_t{t:03d}.jpg"
        tasks.append((t, video_path, output_path))

    if concurrent and len(tasks) > 1:
        # Concurrent extraction
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_EXTRACTIONS) as executor:
            futures = [executor.submit(extract_single_frame, task) for task in tasks]
            for future in as_completed(futures):
                t, output_path, success = future.result()
                if success:
                    frames.append((t, output_path))
        # Sort by timestamp
        frames.sort(key=lambda x: x[0])
    else:
        # Sequential extraction
        for task in tasks:
            t, output_path, success = extract_single_frame(task)
            if success:
                frames.append((t, output_path))

    return frames


def extract_segment_frames(args: Tuple) -> Tuple[int, str, List[Tuple[int, str]]]:
    """Extract frames for a single segment (for concurrent execution across segments)"""
    idx, segment, footage_dir, preview_dir, interval = args

    footage_file = segment.get('footage', f'segment_{idx:02d}.mp4')
    full_path = f"{footage_dir}/{footage_file}"

    if not os.path.exists(full_path):
        return idx, segment.get('context', ''), []

    name = f"seg{idx:02d}"
    frames = extract_frames(full_path, preview_dir, name, interval, concurrent=False)
    return idx, segment.get('context', ''), frames


def safe_print(msg: str):
    """Thread-safe printing"""
    with print_lock:
        print(msg, flush=True)

def main():
    parser = argparse.ArgumentParser(description='Extract preview frames from footage')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--segment', type=int, help='Extract for specific segment only')
    parser.add_argument('--interval', type=int, default=10, help='Seconds between frames (default: 10)')
    parser.add_argument('--sequential', action='store_true', help='Disable concurrent processing')
    parser.add_argument('--workers', type=int, default=MAX_CONCURRENT_EXTRACTIONS,
                        help=f'Max concurrent workers (default: {MAX_CONCURRENT_EXTRACTIONS})')
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
    print(f"Concurrency: {'Sequential' if args.sequential else f'{args.workers} workers'}")
    print("=" * 60)
    print("\nIMPORTANT: Review these frames to verify footage matches narrative!")
    print("Update 'footage_start' in script.json based on visual inspection.\n")

    if args.segment is not None:
        segments_to_process = [(args.segment, segments[args.segment])]
    else:
        segments_to_process = list(enumerate(segments))

    total_frames = 0

    if args.sequential or len(segments_to_process) == 1:
        # Sequential processing
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
            total_frames += len(frames)

            print(f"    Extracted {len(frames)} frames:")
            for t, path in frames:
                print(f"      t={t:3d}s -> {os.path.basename(path)}")
    else:
        # Concurrent processing across segments
        print(f"Extracting frames from {len(segments_to_process)} segments concurrently...\n")

        tasks = [
            (i, segment, footage_dir, preview_dir, args.interval)
            for i, segment in segments_to_process
        ]

        results = {}
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_idx = {executor.submit(extract_segment_frames, task): task[0] for task in tasks}

            for future in as_completed(future_to_idx):
                idx, context, frames = future.result()
                results[idx] = (context, frames)
                total_frames += len(frames)

                if frames:
                    safe_print(f"[{idx}] Extracted {len(frames)} frames: {context}")
                else:
                    safe_print(f"[{idx}] MISSING or no frames: {context}")

        # Print detailed results in order
        print("\n" + "-" * 60)
        print("Detailed Results:")
        for i, segment in segments_to_process:
            if i in results:
                context, frames = results[i]
                print(f"\n[{i}] {context}")
                print(f"    Text: {segment['text'][:60]}...")
                print(f"    Current footage_start: {segment.get('footage_start', 0)}s")
                print(f"    Frames: {len(frames)}")
                for t, path in frames:
                    print(f"      t={t:3d}s -> {os.path.basename(path)}")

    print(f"\n{'=' * 60}")
    print(f"Total frames extracted: {total_frames}")
    print(f"Previews saved to: {preview_dir}/")
    print("\nNext steps:")
    print("1. Open preview folder and review images")
    print("2. Find the timestamp that best matches each segment's narrative")
    print("3. Update 'footage_start' in script.json")
    print("4. Run video assembler")

if __name__ == "__main__":
    main()
