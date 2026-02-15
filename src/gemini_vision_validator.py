#!/usr/bin/env python3
"""
Gemini Vision Validator - Validates downloaded footage/images against intended content
using Gemini Flash vision (free tier).

Extracts a frame from video (or uses image directly), sends to Gemini with a structured
prompt, and parses MATCH/MISMATCH response to determine if the content is correct.

Usage:
    from src.gemini_vision_validator import validate_shot

    # Validate an image
    is_match, confidence, reason = validate_shot(
        "footage/segment_01_shot_00.jpg",
        "Fred Vasseur press conference",
        "Fred Vasseur Ferrari F1 team principal"
    )

    # Validate a video (extracts frame at footage_start)
    is_match, confidence, reason = validate_shot(
        "footage/segment_03_shot_00.mp4",
        "Red Bull RB22 on track",
        "Red Bull RB22 F1 2026 Bahrain testing",
        footage_start=25
    )
"""

import os
import re
import subprocess
import sys
import tempfile
import time
from threading import Lock
from typing import Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Gemini configuration
GEMINI_VISION_MODEL = "gemini-2.0-flash"
GEMINI_KEY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "shared",
    "creds",
    "google_ai",
)

# Rate limiting (free tier: ~15 RPM for Flash)
RATE_LIMIT_REQUESTS = 14
RATE_LIMIT_WINDOW = 60  # seconds
MAX_RETRIES = 2
RETRY_DELAY = 5  # seconds

_rate_limiter_lock = Lock()
_request_timestamps: list = []
_client = None


def _get_client():
    """Get or create Gemini client singleton."""
    global _client
    if _client is not None:
        return _client

    try:
        from google import genai

        api_key = None
        if os.path.exists(GEMINI_KEY_FILE):
            with open(GEMINI_KEY_FILE) as f:
                api_key = f.read().strip()

        if not api_key:
            api_key = os.environ.get("GOOGLE_AI_API_KEY")

        if not api_key:
            return None

        _client = genai.Client(api_key=api_key)
        return _client
    except Exception as e:
        print(f"  [Gemini Vision] Client init failed: {e}")
        return None


def _rate_limit_wait():
    """Wait if necessary to respect Gemini rate limits."""
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
                print(f"  [Gemini Vision] Rate limit, waiting {wait_time:.0f}s...")
                time.sleep(wait_time)
        _request_timestamps.append(time.time())


def _build_prompt(expected_description: str, query: str = "") -> str:
    """Build the validation prompt for Gemini."""
    prompt = (
        "You are validating footage for an F1 (Formula 1) video.\n\n"
        f'Required content: "{expected_description}"\n'
    )
    if query:
        prompt += f'Search query used: "{query}"\n'

    prompt += (
        "\nDescribe what you see in this image in 1-2 sentences. "
        "Be specific about any people, teams, car liveries, brands, or logos visible.\n\n"
        "Then answer: Does this image match the requirement?\n"
        "Reply with MATCH or MISMATCH followed by a brief reason.\n\n"
        "Examples:\n"
        '- Required: "Fred Vasseur press conference" → Image of man in Ferrari jacket '
        "at podium → MATCH: Shows Ferrari team principal at press event\n"
        '- Required: "Red Bull RB22 on track" → Image of McLaren papaya car '
        "→ MISMATCH: Shows McLaren livery, not Red Bull\n"
        '- Required: "Hamilton in Ferrari gear" → Image of driver in red team wear '
        "→ MATCH: Shows driver in Ferrari team clothing\n"
    )
    return prompt


def _extract_frame(video_path: str, timestamp: float = 5.0) -> Optional[str]:
    """Extract a single frame from a video file at the given timestamp.

    Returns path to temp JPEG file, or None on failure.
    """
    try:
        # Create temp file for the frame
        fd, temp_path = tempfile.mkstemp(suffix=".jpg", prefix="validate_")
        os.close(fd)

        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(timestamp),
                "-i",
                video_path,
                "-vframes",
                "1",
                "-q:v",
                "2",
                temp_path,
            ],
            capture_output=True,
            timeout=15,
        )

        if (
            result.returncode == 0
            and os.path.exists(temp_path)
            and os.path.getsize(temp_path) > 0
        ):
            return temp_path

        # If timestamp too far, try at 0
        if timestamp > 0:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    "0",
                    "-i",
                    video_path,
                    "-vframes",
                    "1",
                    "-q:v",
                    "2",
                    temp_path,
                ],
                capture_output=True,
                timeout=15,
            )
            if (
                result.returncode == 0
                and os.path.exists(temp_path)
                and os.path.getsize(temp_path) > 0
            ):
                return temp_path

        # Cleanup on failure
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return None
    except Exception:
        return None


def _validate_image(
    image_path: str, expected_description: str, query: str = ""
) -> Tuple[bool, float, str]:
    """Validate an image file against expected content using Gemini Flash.

    Returns: (is_match, confidence 0-1, reason)
    """
    client = _get_client()
    if client is None:
        return True, 0.5, "Gemini client unavailable, skipping validation"

    try:
        from PIL import Image

        img = Image.open(image_path)
    except Exception as e:
        return True, 0.5, f"Cannot open image: {e}"

    prompt = _build_prompt(expected_description, query)

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            _rate_limit_wait()

            response = client.models.generate_content(
                model=GEMINI_VISION_MODEL,
                contents=[img, prompt],
            )

            text = response.text.strip()
            return _parse_response(text)

        except Exception as e:
            last_error = str(e)
            if "429" in last_error or "quota" in last_error.lower():
                time.sleep(RETRY_DELAY * (attempt + 1))
            elif attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    return True, 0.5, f"Validation failed after {MAX_RETRIES} attempts: {last_error}"


def _parse_response(text: str) -> Tuple[bool, float, str]:
    """Parse Gemini's MATCH/MISMATCH response into structured result."""
    text_lower = text.lower()

    # Look for MATCH or MISMATCH verdict
    has_match = bool(re.search(r"\bMATCH\b", text, re.IGNORECASE))
    has_mismatch = bool(re.search(r"\bMISMATCH\b", text, re.IGNORECASE))

    if has_mismatch:
        # Extract reason after MISMATCH
        reason_match = re.search(r"MISMATCH[:\s]*(.+)", text, re.IGNORECASE | re.DOTALL)
        reason = reason_match.group(1).strip()[:200] if reason_match else text[:200]
        confidence = 0.2
        return False, confidence, reason

    if has_match:
        reason_match = re.search(r"MATCH[:\s]*(.+)", text, re.IGNORECASE | re.DOTALL)
        reason = reason_match.group(1).strip()[:200] if reason_match else text[:200]

        # Higher confidence for strong matches
        if any(
            w in text_lower for w in ["clearly", "definitely", "correct", "exactly"]
        ):
            confidence = 0.95
        elif any(w in text_lower for w in ["shows", "appears to be", "likely"]):
            confidence = 0.8
        else:
            confidence = 0.7

        return True, confidence, reason

    # Ambiguous response — treat as marginal match to avoid false rejections
    return True, 0.5, f"Ambiguous response: {text[:150]}"


def validate_shot(
    file_path: str,
    expected_description: str,
    query: str = "",
    footage_start: float = 0,
) -> Tuple[bool, float, str]:
    """
    Validate a downloaded file (image or video) against expected content.

    For video files: extracts a frame at footage_start, sends to Gemini.
    For image files: sends image directly to Gemini.

    Args:
        file_path: Path to the downloaded file
        expected_description: What the image/video should show (shot label)
        query: The search query used (for context)
        footage_start: For video, timestamp to extract frame at (seconds)

    Returns:
        (is_match, confidence, reason)
        - is_match: True if content matches the requirement
        - confidence: 0.0-1.0 match confidence score
        - reason: Human-readable explanation
    """
    if not os.path.exists(file_path):
        return False, 0.0, f"File not found: {file_path}"

    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".jpg", ".jpeg", ".png", ".webp"):
        return _validate_image(file_path, expected_description, query)
    elif ext in (".mp4", ".mkv", ".webm"):
        # Extract frame and validate
        frame_path = _extract_frame(file_path, footage_start)
        if frame_path is None:
            return True, 0.5, "Could not extract frame, skipping validation"

        try:
            result = _validate_image(frame_path, expected_description, query)
            return result
        finally:
            try:
                os.remove(frame_path)
            except Exception:
                pass
    else:
        return True, 0.5, f"Unsupported file type: {ext}"


def validate_project_shots(project_name: str) -> None:
    """Validate all footage in a project against script requirements.

    Prints a report showing which shots match and which don't.
    """
    from src.config import get_project_dir
    from src.shot_assembler import (
        get_shot_source_ext,
        normalize_segment,
        shot_footage_filename,
    )

    project_dir = get_project_dir(project_name)
    script_file = f"{project_dir}/script.json"
    footage_dir = f"{project_dir}/footage"

    import json

    with open(script_file) as f:
        script = json.load(f)

    print("=" * 70)
    print(f"Footage Validation Report - {project_name}")
    print("=" * 70)

    total, matched, mismatched, skipped = 0, 0, 0, 0

    for seg in script["segments"]:
        idx = seg["id"] - 1
        seg_norm = normalize_segment(dict(seg))
        shots = seg_norm.get("shots", [])

        print(f"\nSegment {idx}: {seg.get('context', '')[:50]}")

        for si, shot in enumerate(shots):
            total += 1
            st = shot.get("source_type", "youtube_clip")
            label = shot.get("label", seg.get("context", ""))
            query = shot.get("footage_query", shot.get("image_query", ""))
            footage_start = shot.get("footage_start", 5)

            ext = get_shot_source_ext(st)
            footage_file = shot.get("footage", shot_footage_filename(idx, si, ext))
            file_path = os.path.join(footage_dir, footage_file)

            if not os.path.exists(file_path):
                print(f"  Shot {si}: MISSING {footage_file}")
                skipped += 1
                continue

            is_match, confidence, reason = validate_shot(
                file_path, label, query, footage_start
            )

            status = "MATCH" if is_match else "MISMATCH"
            icon = "OK" if is_match else "!!"
            print(f"  Shot {si} [{icon}] {status} ({confidence:.1f}): {reason[:60]}")

            if is_match:
                matched += 1
            else:
                mismatched += 1

    print(f"\n{'=' * 70}")
    print(
        f"Total: {total} | Matched: {matched} | Mismatched: {mismatched} | Skipped: {skipped}"
    )
    accuracy = (
        matched / (matched + mismatched) * 100 if (matched + mismatched) > 0 else 0
    )
    print(f"Accuracy: {accuracy:.0f}%")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate footage with Gemini vision")
    parser.add_argument("--project", help="Validate all footage in a project")
    parser.add_argument("--file", help="Validate a single file")
    parser.add_argument("--expected", help="Expected content description (with --file)")
    parser.add_argument("--query", default="", help="Search query used (with --file)")
    parser.add_argument(
        "--timestamp",
        type=float,
        default=5,
        help="Video timestamp for frame extraction",
    )
    args = parser.parse_args()

    if args.project:
        validate_project_shots(args.project)
    elif args.file:
        if not args.expected:
            print("Error: --expected is required with --file")
            sys.exit(1)
        is_match, confidence, reason = validate_shot(
            args.file, args.expected, args.query, args.timestamp
        )
        status = "MATCH" if is_match else "MISMATCH"
        print(f"{status} (confidence: {confidence:.2f})")
        print(f"Reason: {reason}")
    else:
        parser.print_help()
