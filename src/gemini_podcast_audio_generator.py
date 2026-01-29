#!/usr/bin/env python3
"""
Gemini Podcast Audio Generator - Creates podcast audio using Google Gemini TTS

IMPORTANT: Generates the ENTIRE podcast in a SINGLE TTS request to ensure
consistent voice characteristics throughout. This prevents the "different
people talking" issue that occurs with segment-by-segment generation.

Key Features:
- Single-request generation for voice consistency (up to 32k tokens / ~24k words)
- Audio Profile prompting for consistent character voice
- Director's Notes for performance guidance
- Natural pacing and breathing between segments

Uses Gemini 2.5 Pro/Flash TTS models for high-quality, expressive speech synthesis.

Free tier: Gemini 2.5 Flash TTS (free, good quality)
Pro tier: Gemini 2.5 Pro TTS (paid, highest quality)
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
from typing import Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import SHARED_DIR, get_project_dir
from src.ssml_generator import generate_ssml

# Lower concurrency for Gemini free tier (10 RPM limit)
# Using 2 workers with rate limiting is optimal
GEMINI_MAX_CONCURRENT = 2

# Gemini TTS Configuration
GEMINI_KEY_FILE = f"{SHARED_DIR}/creds/google_ai"
GEMINI_MODEL_PRO = "gemini-2.5-pro-preview-tts"
GEMINI_MODEL_FLASH = "gemini-2.5-flash-preview-tts"

# Voice options for Gemini TTS
# Each voice has a distinctive characteristic
GEMINI_VOICES = {
    # Bright/Energetic voices
    "zephyr": "Zephyr",  # Bright
    "puck": "Puck",  # Upbeat
    "fenrir": "Fenrir",  # Excitable
    # Warm/Conversational voices
    "kore": "Kore",  # Firm
    "aoede": "Aoede",  # Breezy
    "leda": "Leda",  # Youthful
    # Deep/Authoritative voices
    "charon": "Charon",  # Informative
    "orus": "Orus",  # Firm
    # Soft/Calm voices
    "enceladus": "Enceladus",  # Breathy
    "vale": "Vale",  # Mellow
}

# Default voice for F1 Burnouts podcast (conversational, engaging)
DEFAULT_VOICE = "Charon"  # Informative tone, good for podcast hosting

# Rate limiting for free tier (10 requests per minute)
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60  # seconds
MAX_RETRIES = 3
RETRY_BASE_DELAY = 10  # seconds

# Global rate limiter state
_rate_limiter_lock = Lock()
_request_timestamps: list = []


def _rate_limit_wait():
    """Wait if necessary to respect rate limits"""
    global _request_timestamps

    with _rate_limiter_lock:
        now = time.time()

        # Remove timestamps older than the window
        _request_timestamps = [
            ts for ts in _request_timestamps if now - ts < RATE_LIMIT_WINDOW
        ]

        # If we've hit the limit, wait
        if len(_request_timestamps) >= RATE_LIMIT_REQUESTS:
            oldest = min(_request_timestamps)
            wait_time = RATE_LIMIT_WINDOW - (now - oldest) + 1
            if wait_time > 0:
                print(f"  [Rate limit] Waiting {wait_time:.1f}s...", flush=True)
                time.sleep(wait_time)

        # Record this request
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


def wave_file_write(
    filename: str,
    pcm_data: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2,
) -> None:
    """Write PCM data to a WAV file"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def convert_wav_to_mp3(wav_path: str, mp3_path: str, bitrate: str = "256k") -> bool:
    """Convert WAV to MP3 using FFmpeg"""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        wav_path,
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        mp3_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up WAV file
    if result.returncode == 0 and os.path.exists(wav_path):
        os.remove(wav_path)

    return result.returncode == 0


def get_duration(file_path: str) -> float:
    """Get audio duration in seconds using ffprobe"""
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


# =============================================================================
# VOICE PROFILE FOR CONSISTENT PODCAST VOICE
# =============================================================================

PODCAST_VOICE_PROFILE = """
## Audio Profile
You are the host of "F1 Burnouts", a passionate and knowledgeable Formula 1 podcast host.

Character traits:
- Expert in F1 engineering, regulations, and history
- Conversational and engaging, like talking to a friend
- Witty with well-timed humor and occasional sarcasm
- Genuinely passionate about the sport
- Speaks with natural flow and breathing

Voice characteristics:
- Warm, confident, and authoritative
- Natural conversational pacing - not rushed, not slow
- Varied intonation to keep listeners engaged
- Clear articulation but not overly formal

## Director's Notes
- Maintain consistent voice throughout the entire podcast
- Use natural pauses between topics (like taking a breath)
- Build energy during exciting moments, soften during reflective ones
- Keep the same fundamental voice character from start to finish
- Speak as one continuous monologue, not separate disconnected pieces

## Performance Style
- Conversational podcast host speaking directly to the audience
- Natural transitions between topics
- Occasional emphasis on key words for impact
- Breathing pauses between paragraphs
"""


def build_podcast_transcript(script: dict) -> str:
    """
    Build a complete podcast transcript from all segments.

    Combines all segments into a single flowing script with natural
    paragraph breaks for breathing pauses.
    """
    segments = script.get("segments", [])

    # Combine all segment text with paragraph breaks
    paragraphs = []
    for segment in segments:
        text = segment.get("text", "").strip()
        if text:
            paragraphs.append(text)

    # Join with double newlines for natural paragraph pauses
    full_transcript = "\n\n".join(paragraphs)

    return full_transcript


def generate_full_podcast_audio(
    script: dict,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    model: str = GEMINI_MODEL_FLASH,
) -> Tuple[bool, Optional[str]]:
    """
    Generate the ENTIRE podcast in a single TTS request.

    This ensures consistent voice characteristics throughout the podcast,
    preventing the "different people talking" issue that occurs with
    segment-by-segment generation.

    Args:
        script: Full podcast script dict with segments
        output_path: Path for output MP3 file
        voice: Gemini voice name
        model: Gemini model to use

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return False, "google-genai not installed. Run: pip install google-genai"

    # Get API key
    try:
        api_key = get_gemini_key()
    except FileNotFoundError as e:
        return False, str(e)

    # Build the complete transcript
    transcript = build_podcast_transcript(script)

    # Estimate tokens (rough: 1 token ≈ 4 chars)
    estimated_tokens = len(transcript) // 4
    if estimated_tokens > 30000:
        return (
            False,
            f"Script too long ({estimated_tokens} tokens). Max is ~30k tokens for single request.",
        )

    # Build the complete prompt with voice profile and transcript
    full_prompt = f"""{PODCAST_VOICE_PROFILE}

## Transcript
Read the following podcast script naturally, as one continuous performance:

{transcript}
"""

    print(
        f"  Transcript length: {len(transcript):,} chars (~{estimated_tokens:,} tokens)"
    )

    # Initialize client
    client = genai.Client(api_key=api_key)

    # Retry loop
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            _rate_limit_wait()

            print(f"  Generating audio (attempt {attempt + 1}/{MAX_RETRIES})...")

            # Generate audio with voice profile
            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
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

            # Extract audio data
            if not response.candidates:
                return False, "No audio generated - empty response"

            audio_data = response.candidates[0].content.parts[0].inline_data.data

            if not audio_data:
                return False, "No audio data in response"

            # Write to WAV file first (Gemini outputs PCM)
            wav_path = output_path.replace(".mp3", ".wav")
            wave_file_write(wav_path, audio_data)

            # Convert to MP3
            if not convert_wav_to_mp3(wav_path, output_path):
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
                    print(f"  Rate limited, waiting {wait_time:.0f}s...")
                    time.sleep(wait_time)
                    continue
            else:
                return False, f"Gemini TTS error: {error_str}"

    return False, f"Max retries exceeded. Last error: {last_error}"


def generate_audio_gemini(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    model: str = GEMINI_MODEL_FLASH,
    use_ssml: bool = True,
    emotion: str = "energetic",
) -> Tuple[bool, Optional[str]]:
    """
    Generate audio using Google Gemini TTS

    Args:
        text: Text to synthesize (plain or SSML-enhanced)
        output_path: Path for output MP3 file
        voice: Gemini voice name (e.g., "Charon", "Kore")
        model: Gemini model to use (flash or pro)
        use_ssml: Whether to enhance text with SSML
        emotion: Emotion for SSML generation

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return False, "google-genai not installed. Run: pip install google-genai"

    # Get API key
    try:
        api_key = get_gemini_key()
    except FileNotFoundError as e:
        return False, str(e)

    # Initialize client
    client = genai.Client(api_key=api_key)

    # Enhance text with SSML if requested
    if use_ssml:
        enhanced_text = generate_ssml(text, emotion)
    else:
        enhanced_text = text

    # Retry loop with exponential backoff
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            # Apply rate limiting before each request
            _rate_limit_wait()

            # Generate audio
            response = client.models.generate_content(
                model=model,
                contents=enhanced_text,
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

            # Extract audio data
            if not response.candidates:
                return False, "No audio generated - empty response"

            audio_data = response.candidates[0].content.parts[0].inline_data.data

            if not audio_data:
                return False, "No audio data in response"

            # Write to WAV file first (Gemini outputs PCM)
            wav_path = output_path.replace(".mp3", ".wav")
            wave_file_write(wav_path, audio_data)

            # Convert to MP3
            if not convert_wav_to_mp3(wav_path, output_path):
                return False, "Failed to convert WAV to MP3"

            return True, None

        except Exception as e:
            error_str = str(e)
            last_error = error_str

            # Check if it's a rate limit error
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                # Extract retry delay if provided
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
                # Non-rate-limit error, don't retry
                return False, f"Gemini TTS error: {error_str}"

    return False, f"Max retries exceeded. Last error: {last_error}"


def process_segment(args: Tuple) -> Tuple[int, bool, float, Optional[str]]:
    """Process a single segment (for concurrent execution)"""
    idx, segment, audio_path, voice, model, use_ssml = args

    # Check cache
    if os.path.exists(audio_path):
        duration = get_duration(audio_path)
        return idx, True, duration, "cached"

    text = segment["text"]
    emotion = segment.get("emotion", "energetic")

    success, error = generate_audio_gemini(
        text=text,
        output_path=audio_path,
        voice=voice,
        model=model,
        use_ssml=use_ssml,
        emotion=emotion,
    )

    if success:
        duration = get_duration(audio_path)
        return idx, True, duration, None
    else:
        return idx, False, 0, error


def concatenate_audio(audio_files: list, output_path: str) -> bool:
    """Concatenate all audio segments into final podcast"""
    # Create file list for ffmpeg
    list_file = output_path.replace(".mp3", "_list.txt")
    with open(list_file, "w") as f:
        for audio_file in audio_files:
            f.write(f"file '{audio_file}'\n")

    # Concatenate with ffmpeg
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_file,
        "-c:a",
        "libmp3lame",
        "-b:a",
        "256k",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up list file
    if os.path.exists(list_file):
        os.remove(list_file)

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate podcast audio using Google Gemini TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
GENERATION MODES:

  Single Request (default, RECOMMENDED):
    Generates entire podcast in ONE TTS request for consistent voice.
    Prevents the "different people talking" issue.

  Legacy Segment Mode (--legacy):
    Generates each segment separately then concatenates.
    May result in inconsistent voice characteristics.

EXAMPLES:
  # Generate podcast (single request, consistent voice)
  python3 src/gemini_podcast_audio_generator.py --project my-podcast

  # Use Pro model for higher quality
  python3 src/gemini_podcast_audio_generator.py --project my-podcast --model pro

  # Preview transcript before generating
  python3 src/gemini_podcast_audio_generator.py --project my-podcast --preview
""",
    )
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument(
        "--model",
        choices=["flash", "pro"],
        default="flash",
        help="Gemini model: flash (free) or pro (paid, higher quality)",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Voice name (default: {DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy segment-by-segment generation (may cause voice inconsistency)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview transcript and voice profile without generating audio",
    )
    parser.add_argument(
        "--list-voices", action="store_true", help="List available voices and exit"
    )
    args = parser.parse_args()

    # List voices and exit
    if args.list_voices:
        print("Available Gemini TTS Voices:")
        print("-" * 40)
        for key, name in GEMINI_VOICES.items():
            print(f"  {name}")
        print(f"\nDefault: {DEFAULT_VOICE}")
        sys.exit(0)

    # Setup paths
    project_dir = get_project_dir(args.project)
    output_dir = f"{project_dir}/output"
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # Load script
    with open(script_file) as f:
        script = json.load(f)

    # Select model
    model = GEMINI_MODEL_PRO if args.model == "pro" else GEMINI_MODEL_FLASH
    voice = args.voice
    segments = script.get("segments", [])

    # Build transcript for display
    transcript = build_podcast_transcript(script)
    word_count = len(transcript.split())
    estimated_duration = word_count / 150  # ~150 words per minute

    print("=" * 60)
    print(f"Gemini Podcast Audio Generator")
    print("=" * 60)
    print(f"Project: {args.project}")
    print(f"Model: {args.model.upper()} ({model})")
    print(f"Voice: {voice}")
    print(f"Segments: {len(segments)}")
    print(f"Words: {word_count:,}")
    print(f"Estimated duration: {estimated_duration:.1f} min")
    print(
        f"Mode: {'Legacy (segment-by-segment)' if args.legacy else 'Single Request (consistent voice)'}"
    )
    print("=" * 60)

    # Preview mode
    if args.preview:
        print("\n" + "=" * 60)
        print("VOICE PROFILE")
        print("=" * 60)
        print(PODCAST_VOICE_PROFILE.strip())
        print("\n" + "=" * 60)
        print("TRANSCRIPT PREVIEW (first 500 chars)")
        print("=" * 60)
        print(transcript[:500] + ("..." if len(transcript) > 500 else ""))
        print("\n" + "=" * 60)
        print("[PREVIEW MODE] No audio generated.")
        sys.exit(0)

    output_path = f"{output_dir}/final.mp3"

    # =================================================================
    # SINGLE REQUEST MODE (default, recommended)
    # =================================================================
    if not args.legacy:
        print("\nGenerating entire podcast in single request...")
        print("(This ensures consistent voice throughout)")

        success, error = generate_full_podcast_audio(
            script=script,
            output_path=output_path,
            voice=voice,
            model=model,
        )

        if success:
            duration = get_duration(output_path)
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"\n{'=' * 60}")
            print("SUCCESS!")
            print(f"Output: {output_path}")
            print(f"Duration: {duration:.1f}s ({duration / 60:.1f} min)")
            print(f"Size: {file_size:.1f} MB")
            print(f"{'=' * 60}")
        else:
            print(f"\nFailed: {error}")
            sys.exit(1)

    # =================================================================
    # LEGACY MODE (segment-by-segment, kept for compatibility)
    # =================================================================
    else:
        print("\nWARNING: Legacy mode may produce inconsistent voice characteristics!")
        print("Consider using default single-request mode instead.\n")

        audio_dir = f"{project_dir}/audio"
        os.makedirs(audio_dir, exist_ok=True)

        # Process segments sequentially
        for i, segment in enumerate(segments):
            audio_path = f"{audio_dir}/segment_{i:02d}.mp3"
            context = segment.get("context", "Segment")[:30]

            # Skip if cached
            if os.path.exists(audio_path):
                duration = get_duration(audio_path)
                print(f"[{i + 1}/{len(segments)}] Cached ({duration:.1f}s) - {context}")
                continue

            print(
                f"[{i + 1}/{len(segments)}] Generating - {context}...",
                end=" ",
                flush=True,
            )

            success, error = generate_audio_gemini(
                text=segment["text"],
                output_path=audio_path,
                voice=voice,
                model=model,
                use_ssml=True,
                emotion=segment.get("emotion", "energetic"),
            )

            if success:
                duration = get_duration(audio_path)
                print(f"Done ({duration:.1f}s)")
            else:
                print(f"Failed: {error}")
                sys.exit(1)

        # Concatenate all segments
        print(f"\nConcatenating {len(segments)} segments...")
        audio_files = [f"{audio_dir}/segment_{i:02d}.mp3" for i in range(len(segments))]

        if concatenate_audio(audio_files, output_path):
            duration = get_duration(output_path)
            print(f"\nSuccess! Output: {output_path}")
            print(f"Duration: {duration:.1f}s ({duration / 60:.1f} min)")
        else:
            print("Error: Failed to concatenate segments")
            sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()
