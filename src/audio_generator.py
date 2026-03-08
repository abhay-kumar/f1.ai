#!/usr/bin/env python3
"""
Audio Generator - Creates voiceovers with caching and concurrency
Supports ElevenLabs and Google Gemini TTS engines
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Optional, Tuple

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    MAX_CONCURRENT_AUDIO,
    MODEL_ID,
    SHARED_DIR,
    SHORTS_AUDIO_SPEED,
    VOICE_ID,
    get_elevenlabs_key,
    get_project_dir,
)

# Gemini TTS Configuration
GEMINI_KEY_FILE = f"{SHARED_DIR}/creds/google_ai"
GEMINI_MODEL_FLASH = "gemini-2.5-flash-preview-tts"
GEMINI_DEFAULT_VOICE = "Alnilam"  # Male, friendly, clean American voice
GEMINI_MAX_CONCURRENT = 2  # Free tier: 10 RPM

# Rate limiting for Gemini free tier
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60  # seconds
MAX_RETRIES = 3
RETRY_BASE_DELAY = 10  # seconds

_rate_limiter_lock = Lock()
_request_timestamps: list = []


def _rate_limit_wait():
    """Wait if necessary to respect Gemini rate limits"""
    global _request_timestamps
    with _rate_limiter_lock:
        now = time.time()
        _request_timestamps = [
            ts for ts in _request_timestamps if now - ts < RATE_LIMIT_WINDOW
        ]
        if len(_request_timestamps) >= RATE_LIMIT_REQUESTS:
            oldest = min(_request_timestamps)
            wait_time = RATE_LIMIT_WINDOW - (now - oldest) + 1
            if wait_time > 0:
                print(f"  [Rate limit] Waiting {wait_time:.1f}s...", flush=True)
                time.sleep(wait_time)
        _request_timestamps.append(time.time())


def get_gemini_key() -> str:
    """Read Gemini API key from credentials file"""
    if not os.path.exists(GEMINI_KEY_FILE):
        raise FileNotFoundError(
            f"Gemini API key not found at {GEMINI_KEY_FILE}\n"
            "Get your free API key at: https://aistudio.google.com/apikey\n"
            f"Then save it: echo 'YOUR_KEY' > {GEMINI_KEY_FILE}"
        )
    with open(GEMINI_KEY_FILE) as f:
        return f.read().strip()


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


def generate_audio_elevenlabs(
    text: str, output_path: str
) -> Tuple[bool, Optional[str]]:
    """Generate audio using ElevenLabs API"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": get_elevenlabs_key(),
    }
    data = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
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


def generate_audio_gemini(
    text: str,
    output_path: str,
    voice: str = GEMINI_DEFAULT_VOICE,
) -> Tuple[bool, Optional[str]]:
    """Generate audio using Google Gemini TTS"""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return False, "google-genai not installed. Run: pip install google-genai"

    try:
        api_key = get_gemini_key()
    except FileNotFoundError as e:
        return False, str(e)

    client = genai.Client(api_key=api_key)

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            _rate_limit_wait()

            response = client.models.generate_content(
                model=GEMINI_MODEL_FLASH,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice,
                            )
                        )
                    ),
                ),
            )

            if not response.candidates:
                return False, "No audio generated - empty response"

            audio_data = response.candidates[0].content.parts[0].inline_data.data
            if not audio_data:
                return False, "No audio data in response"

            # Write PCM to WAV
            wav_path = output_path.replace(".mp3", ".wav")
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(audio_data)

            # Convert WAV to MP3
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                wav_path,
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "256k",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if os.path.exists(wav_path):
                os.remove(wav_path)

            if result.returncode != 0:
                return False, "Failed to convert WAV to MP3"

            return True, None

        except Exception as e:
            error_str = str(e)
            last_error = error_str

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                retry_match = re.search(r"retry in (\d+(?:\.\d+)?)", error_str.lower())
                if retry_match:
                    wait_time = float(retry_match.group(1)) + 1
                else:
                    wait_time = RETRY_BASE_DELAY * (2**attempt)

                if attempt < MAX_RETRIES - 1:
                    print(
                        f"  [Retry {attempt + 1}/{MAX_RETRIES}] Rate limited, waiting {wait_time:.0f}s...",
                        flush=True,
                    )
                    time.sleep(wait_time)
                    continue
            else:
                return False, f"Gemini TTS error: {error_str}"

    return False, f"Max retries exceeded. Last error: {last_error}"


def apply_speed(audio_path: str, speed: float) -> Tuple[bool, Optional[str]]:
    """Speed up or slow down audio using FFmpeg atempo filter"""
    temp_path = audio_path + ".speed.mp3"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        audio_path,
        "-filter:a",
        f"atempo={speed}",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "256k",
        temp_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and os.path.exists(temp_path):
        os.replace(temp_path, audio_path)
        return True, None
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return False, f"FFmpeg atempo failed: {result.stderr[:100]}"


def process_segment(args: Tuple) -> Tuple[int, bool, float, Optional[str]]:
    """Process a single segment (for concurrent execution)"""
    idx, segment, audio_path, engine, gemini_voice, speed = args

    if os.path.exists(audio_path):
        duration = get_duration(audio_path)
        return idx, True, duration, "cached"

    # Prefer tts_text for pronunciation overrides, fall back to text
    tts_text = segment.get("tts_text", segment["text"])

    if engine == "gemini":
        success, error = generate_audio_gemini(tts_text, audio_path, voice=gemini_voice)
    else:
        success, error = generate_audio_elevenlabs(tts_text, audio_path)

    if success:
        # Apply speed adjustment if not 1.0x
        if speed and speed != 1.0:
            speed_ok, speed_err = apply_speed(audio_path, speed)
            if not speed_ok:
                return idx, False, 0, speed_err
        duration = get_duration(audio_path)
        return idx, True, duration, None
    else:
        return idx, False, 0, error


def main():
    parser = argparse.ArgumentParser(description="Generate voiceover audio")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument(
        "--engine",
        choices=["elevenlabs", "gemini"],
        default="gemini",
        help="TTS engine (default: gemini)",
    )
    parser.add_argument(
        "--voice",
        default=GEMINI_DEFAULT_VOICE,
        help=f"Gemini voice name (default: {GEMINI_DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=SHORTS_AUDIO_SPEED,
        help=f"Playback speed multiplier (default: {SHORTS_AUDIO_SPEED}x from config). Applied via FFmpeg atempo.",
    )
    parser.add_argument(
        "--sequential", action="store_true", help="Disable concurrent processing"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Max concurrent workers (default: auto based on engine)",
    )
    args = parser.parse_args()

    # Set default workers based on engine
    if args.workers is None:
        args.workers = (
            GEMINI_MAX_CONCURRENT if args.engine == "gemini" else MAX_CONCURRENT_AUDIO
        )

    project_dir = get_project_dir(args.project)
    audio_dir = f"{project_dir}/audio"
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    os.makedirs(audio_dir, exist_ok=True)

    if args.engine == "gemini":
        engine_label = f"Gemini TTS ({args.voice} voice)"
    else:
        engine_label = "ElevenLabs (Jarnathan voice)"

    speed_label = f" @ {args.speed}x speed" if args.speed != 1.0 else ""

    print("=" * 50)
    print(f"Audio Generator - Project: {args.project}")
    print(f"Engine: {engine_label}{speed_label}")
    print(
        f"Concurrency: {'Sequential' if args.sequential else f'{args.workers} workers'}"
    )
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
        (
            i,
            segment,
            f"{audio_dir}/segment_{i:02d}.mp3",
            args.engine,
            args.voice,
            args.speed,
        )
        for i, segment in enumerate(segments)
    ]

    if args.sequential:
        # Sequential processing
        for task in tasks:
            idx = task[0]
            segment = task[1]
            print(
                f"[{idx + 1}/{len(segments)}] Processing: {segment['context']}...",
                end=" ",
                flush=True,
            )
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
            future_to_idx = {
                executor.submit(process_segment, task): task[0] for task in tasks
            }

            for future in as_completed(future_to_idx):
                idx, success, duration, status = future.result()
                segment = segments[idx]

                if status == "cached":
                    print(
                        f"[{idx + 1}/{len(segments)}] Cached: {duration:.1f}s - {segment['context']}"
                    )
                    cached += 1
                elif success:
                    print(
                        f"[{idx + 1}/{len(segments)}] Generated: {duration:.1f}s - {segment['context']}"
                    )
                    generated += 1
                else:
                    print(
                        f"[{idx + 1}/{len(segments)}] Failed: {segment['context']} - {status}"
                    )
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
