#!/usr/bin/env python3
"""
Audio Generator - Creates voiceovers with caching and concurrency
Uses ElevenLabs API with concurrent processing for faster generation
"""
import os
import sys
import json
import argparse
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir, get_elevenlabs_key, VOICE_ID, MODEL_ID, MAX_CONCURRENT_AUDIO

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0

def generate_audio(text: str, output_path: str) -> Tuple[bool, Optional[str]]:
    """Generate audio using ElevenLabs API"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": get_elevenlabs_key()
    }
    data = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True, None
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)


def process_segment(args: Tuple) -> Tuple[int, bool, float, Optional[str]]:
    """Process a single segment (for concurrent execution)"""
    idx, segment, audio_path = args

    if os.path.exists(audio_path):
        duration = get_duration(audio_path)
        return idx, True, duration, "cached"

    success, error = generate_audio(segment['text'], audio_path)
    if success:
        duration = get_duration(audio_path)
        return idx, True, duration, None
    else:
        return idx, False, 0, error

def main():
    parser = argparse.ArgumentParser(description='Generate voiceover audio')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--sequential', action='store_true',
                        help='Disable concurrent processing')
    parser.add_argument('--workers', type=int, default=MAX_CONCURRENT_AUDIO,
                        help=f'Max concurrent workers (default: {MAX_CONCURRENT_AUDIO})')
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    audio_dir = f"{project_dir}/audio"
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    os.makedirs(audio_dir, exist_ok=True)

    print("=" * 50)
    print(f"Audio Generator - Project: {args.project}")
    print("Engine: ElevenLabs (Bradford voice)")
    print(f"Concurrency: {'Sequential' if args.sequential else f'{args.workers} workers'}")
    print("=" * 50)

    with open(script_file) as f:
        script = json.load(f)

    segments = script["segments"]
    generated = 0
    cached = 0
    failed = 0
    results = {}

    # Prepare tasks
    tasks = [
        (i, segment, f"{audio_dir}/segment_{i:02d}.mp3")
        for i, segment in enumerate(segments)
    ]

    if args.sequential:
        # Sequential processing
        for task in tasks:
            idx = task[0]
            segment = task[1]
            print(f"[{idx+1}/{len(segments)}] Processing: {segment['context']}...", end=" ", flush=True)
            idx, success, duration, status = process_segment(task)
            if status == "cached":
                print(f"Cached ({duration:.1f}s)")
                cached += 1
            elif success:
                print(f"Done ({duration:.1f}s)")
                generated += 1
            else:
                print(f"Failed: {status}")
                failed += 1
            results[idx] = (success, duration)
    else:
        # Concurrent processing
        print(f"\nProcessing {len(segments)} segments concurrently...")

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_idx = {executor.submit(process_segment, task): task[0] for task in tasks}

            for future in as_completed(future_to_idx):
                idx, success, duration, status = future.result()
                segment = segments[idx]

                if status == "cached":
                    print(f"[{idx+1}/{len(segments)}] Cached: {duration:.1f}s - {segment['context']}")
                    cached += 1
                elif success:
                    print(f"[{idx+1}/{len(segments)}] Generated: {duration:.1f}s - {segment['context']}")
                    generated += 1
                else:
                    print(f"[{idx+1}/{len(segments)}] Failed: {segment['context']} - {status}")
                    failed += 1

                results[idx] = (success, duration)

    total_duration = sum(
        get_duration(f"{audio_dir}/segment_{i:02d}.mp3")
        for i in range(len(segments))
        if os.path.exists(f"{audio_dir}/segment_{i:02d}.mp3")
    )

    print(f"\n{'=' * 50}")
    print(f"Generated: {generated} | Cached: {cached} | Failed: {failed}")
    print(f"Total duration: {total_duration:.1f}s")
    print(f"Audio saved to: {audio_dir}/")

if __name__ == "__main__":
    main()
