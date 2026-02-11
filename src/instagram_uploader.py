#!/usr/bin/env python3
"""
Instagram Uploader - Uploads shorts as Instagram Reels with auto-generated metadata
Uses instagrapi library for direct file upload via Instagram's private API
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    INSTAGRAM_CREDENTIALS_FILE,
    INSTAGRAM_SESSION_FILE,
    get_project_dir,
)

try:
    from instagrapi import Client
    from instagrapi.mixins.challenge import ChallengeChoice
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install instagrapi")
    sys.exit(1)

# Instagram caption limit
MAX_CAPTION_LENGTH = 2200

# F1 Fan Content Disclaimer (shorter version for Instagram)
F1_FAN_DISCLAIMER = (
    "This is unofficial fan content — not affiliated with Formula 1, FIA, or FOM. "
    "Created for commentary and entertainment."
)


def get_credentials():
    """Load Instagram credentials from file (username on line 1, password on line 2)"""
    if not os.path.exists(INSTAGRAM_CREDENTIALS_FILE):
        return None
    with open(INSTAGRAM_CREDENTIALS_FILE) as f:
        lines = f.read().strip().split("\n")
        if len(lines) >= 2:
            return {"username": lines[0].strip(), "password": lines[1].strip()}
    return None


_pending_challenge_code = None


def challenge_code_handler(username, choice):
    """Handle Instagram challenge verification"""
    if choice == ChallengeChoice.SMS:
        print(
            f"\nInstagram sent a verification code via SMS to the number on file for @{username}"
        )
    elif choice == ChallengeChoice.EMAIL:
        print(
            f"\nInstagram sent a verification code via email to the address on file for @{username}"
        )
    else:
        print(f"\nInstagram requires verification for @{username}")

    if _pending_challenge_code:
        print(f"Using provided verification code.")
        return _pending_challenge_code

    code = input("Enter the verification code: ").strip()
    return code


def get_authenticated_client():
    """Authenticate and return an instagrapi Client with session persistence"""
    credentials = get_credentials()
    if not credentials:
        print(f"Error: Instagram credentials not found at {INSTAGRAM_CREDENTIALS_FILE}")
        print("\nSetup instructions:")
        print("1. Create the file: shared/creds/instagram")
        print("2. Line 1: your Instagram username")
        print("3. Line 2: your Instagram password")
        return None

    cl = Client()
    cl.challenge_code_handler = challenge_code_handler

    # Try to reuse existing session
    if os.path.exists(INSTAGRAM_SESSION_FILE):
        try:
            cl.load_settings(INSTAGRAM_SESSION_FILE)
            cl.login(credentials["username"], credentials["password"])
            cl.get_timeline_feed()  # Validate session is alive
            print("Logged in with saved session.")
            return cl
        except Exception:
            print("Saved session expired, logging in fresh...")

    # Fresh login
    try:
        cl.login(credentials["username"], credentials["password"])
    except Exception as e:
        error_msg = str(e)
        if "challenge_required" in error_msg:
            print("Instagram requires verification. Attempting challenge resolution...")
            try:
                cl.challenge_resolve(cl.last_json)
                print("Challenge resolved!")
            except Exception as ce:
                print(f"Challenge resolution failed: {ce}")
                return None
        else:
            print(f"Instagram login failed: {e}")
            return None

    # Save session for reuse
    os.makedirs(os.path.dirname(INSTAGRAM_SESSION_FILE), exist_ok=True)
    cl.dump_settings(INSTAGRAM_SESSION_FILE)
    print("Logged in and session saved.")
    return cl


def generate_caption_from_script(script):
    """Generate Instagram caption from script.json"""
    base_title = script.get("title", "F1 Short")
    segments = script.get("segments", [])
    full_text = " ".join([seg["text"] for seg in segments])

    # Summary (first 300 chars of script text)
    summary = full_text[:300] + "..." if len(full_text) > 300 else full_text

    # Extract driver/team hashtags
    hashtags = ["#F1", "#Formula1", "#Reels", "#FormulaOne", "#Racing"]

    driver_hashtags = {
        "vettel": "#Vettel",
        "webber": "#Webber",
        "norris": "#LandoNorris",
        "piastri": "#Piastri",
        "verstappen": "#Verstappen",
        "hamilton": "#LewisHamilton",
        "leclerc": "#Leclerc",
        "alonso": "#Alonso",
    }

    team_hashtags = {
        "red bull": "#RedBull",
        "mclaren": "#McLaren",
        "ferrari": "#Ferrari",
        "mercedes": "#Mercedes",
        "aston martin": "#AstonMartin",
        "alpine": "#Alpine",
        "williams": "#Williams",
        "haas": "#Haas",
    }

    full_text_lower = full_text.lower()

    for keyword, tag in driver_hashtags.items():
        if keyword in full_text_lower:
            hashtags.append(tag)

    for keyword, tag in team_hashtags.items():
        if keyword in full_text_lower:
            hashtags.append(tag)

    # Deduplicate
    seen = set()
    unique_hashtags = []
    for tag in hashtags:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            unique_hashtags.append(tag)

    hashtag_line = " ".join(unique_hashtags)

    # Build caption
    caption_parts = [
        base_title,
        "",
        summary,
        "",
        hashtag_line,
        "",
        F1_FAN_DISCLAIMER,
    ]
    caption = "\n".join(caption_parts)

    # Trim to Instagram limit
    if len(caption) > MAX_CAPTION_LENGTH:
        caption = caption[: MAX_CAPTION_LENGTH - 3] + "..."

    return caption


def upload_reel(client, video_path, caption):
    """Upload video as an Instagram Reel, resolving challenges if needed"""
    print("Uploading Reel", end="", flush=True)
    try:
        media = client.clip_upload(Path(video_path), caption)
    except Exception as e:
        if "challenge_required" in str(e):
            print("\nUpload triggered a challenge. Resolving...")
            client.challenge_resolve(client.last_json)
            print("Challenge resolved. Retrying upload...")
            media = client.clip_upload(Path(video_path), caption)
        else:
            raise
    print(" Done!")
    return media


def main():
    parser = argparse.ArgumentParser(description="Upload F1 short as Instagram Reel")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--caption", help="Override auto-generated caption")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show metadata without uploading"
    )
    parser.add_argument(
        "--verification-code",
        help="Instagram verification code for challenge resolution",
    )
    args = parser.parse_args()

    global _pending_challenge_code
    if args.verification_code:
        _pending_challenge_code = args.verification_code

    project_dir = get_project_dir(args.project)
    video_path = f"{project_dir}/output/final.mp4"
    script_path = f"{project_dir}/script.json"

    # Validate files exist
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        print(
            f"Run video assembly first: python3 src/video_assembler.py --project {args.project}"
        )
        sys.exit(1)

    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        sys.exit(1)

    # Load script and generate caption
    with open(script_path) as f:
        script = json.load(f)

    caption = args.caption if args.caption else generate_caption_from_script(script)

    # Display metadata
    print("=" * 60)
    print(f"Instagram Reel Upload - Project: {args.project}")
    print("=" * 60)
    print(f"\nCaption:\n{caption}")
    print(f"\nVideo: {video_path}")
    print(f"Size: {os.path.getsize(video_path) / (1024 * 1024):.1f}MB")

    if args.dry_run:
        print("\n[Dry run - no upload performed]")
        return

    print("\n" + "-" * 60)

    # Authenticate and upload
    client = get_authenticated_client()
    if not client:
        sys.exit(1)

    media = upload_reel(client, video_path, caption)

    media_id = media.pk
    media_code = media.code
    instagram_url = f"https://www.instagram.com/reel/{media_code}/"

    print(f"\n{'=' * 60}")
    print("SUCCESS! Reel uploaded")
    print(f"URL: {instagram_url}")
    print(f"{'=' * 60}")

    # Save/update upload info
    upload_info_path = f"{project_dir}/upload_info.json"
    upload_info = {}
    if os.path.exists(upload_info_path):
        with open(upload_info_path) as f:
            upload_info = json.load(f)

    upload_info["instagram_media_id"] = str(media_id)
    upload_info["instagram_url"] = instagram_url
    upload_info["instagram_code"] = media_code

    with open(upload_info_path, "w") as f:
        json.dump(upload_info, f, indent=2)


if __name__ == "__main__":
    main()
