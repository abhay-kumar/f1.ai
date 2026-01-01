#!/usr/bin/env python3
"""
Audio Generator - Creates voiceovers with caching
Uses ElevenLabs API, only regenerates if audio doesn't exist
"""
import os
import sys
import json
import argparse
import requests
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir, get_elevenlabs_key, VOICE_ID, MODEL_ID

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0

def generate_audio(text, output_path):
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

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    else:
        print(f"    Error: {response.status_code} - {response.text[:100]}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate voiceover audio')
    parser.add_argument('--project', required=True, help='Project name')
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
    print("Voice: Bradford (ElevenLabs)")
    print("=" * 50)

    with open(script_file) as f:
        script = json.load(f)

    segments = script["segments"]
    generated = 0
    cached = 0

    for i, segment in enumerate(segments):
        audio_path = f"{audio_dir}/segment_{i:02d}.mp3"

        if os.path.exists(audio_path):
            duration = get_duration(audio_path)
            print(f"[{i+1}/{len(segments)}] Cached: {duration:.1f}s - {segment['context']}")
            cached += 1
        else:
            print(f"[{i+1}/{len(segments)}] Generating: {segment['context']}...", end=" ", flush=True)
            if generate_audio(segment['text'], audio_path):
                duration = get_duration(audio_path)
                print(f"Done ({duration:.1f}s)")
                generated += 1
            else:
                print("Failed")

    total_duration = sum(
        get_duration(f"{audio_dir}/segment_{i:02d}.mp3")
        for i in range(len(segments))
        if os.path.exists(f"{audio_dir}/segment_{i:02d}.mp3")
    )

    print(f"\n{'=' * 50}")
    print(f"Generated: {generated} | Cached: {cached}")
    print(f"Total duration: {total_duration:.1f}s")
    print(f"Audio saved to: {audio_dir}/")

if __name__ == "__main__":
    main()
