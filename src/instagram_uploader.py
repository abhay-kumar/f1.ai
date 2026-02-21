#!/usr/bin/env python3
"""
Instagram Uploader - Uploads shorts as Instagram Reels with auto-generated metadata
Uses instagrapi library for direct file upload via Instagram's private API
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    INSTAGRAM_CREDENTIALS_FILE,
    INSTAGRAM_SESSION_FILE,
    get_project_dir,
)

try:
    from instagrapi import Client
    from instagrapi.exceptions import ChallengeRequired
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

# Modern device settings — Instagram blocks old app versions with "unsupported_version"
DEVICE_SETTINGS = {
    "app_version": "417.0.0.54.77",
    "android_version": 34,
    "android_release": "14.0",
    "dpi": "480dpi",
    "resolution": "1080x2400",
    "manufacturer": "Google",
    "device": "husky",
    "model": "Pixel 8 Pro",
    "cpu": "tensor",
    "version_code": "578940096",
}


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


def handle_exception(client, e):
    """Custom exception handler for instagrapi Client.

    This replaces the default handler which calls challenge_resolve() and crashes
    when Instagram returns unsupported_version or empty JSON responses.
    For ChallengeRequired, we attempt the simple private API path first,
    then fall back to re-raising so the caller can handle it.
    """
    if isinstance(e, ChallengeRequired):
        last_json = client.last_json or {}
        challenge = last_json.get("challenge", {})
        challenge_url = challenge.get("api_path", "")
        step_name = last_json.get("step_name", "")

        # Check for unsupported_version — can't resolve, must update app version
        if "unsupported_version" in challenge.get("url", ""):
            raise ChallengeRequired(
                f"Instagram blocked this app version. "
                f"Update DEVICE_SETTINGS in instagram_uploader.py"
            )

        # Try simple challenge (delta_login_review = "was this you?")
        if challenge_url and step_name in ("delta_login_review", ""):
            try:
                client.challenge_resolve_simple(challenge_url)
                return  # resolved, private_request will retry
            except Exception:
                pass

        # Re-raise so the caller can handle it (prompt for code, etc.)
        raise
    else:
        raise e


def _create_client():
    """Create a properly configured instagrapi Client."""
    cl = Client()
    cl.challenge_code_handler = challenge_code_handler
    cl.handle_exception = handle_exception
    cl.set_device(DEVICE_SETTINGS)
    cl.set_locale("en_US")
    cl.set_timezone_offset(19800)  # IST (UTC+5:30)
    cl.delay_range = [1, 3]
    return cl


def get_authenticated_client(delete_session=False):
    """Authenticate and return an instagrapi Client with session persistence"""
    credentials = get_credentials()
    if not credentials:
        print(f"Error: Instagram credentials not found at {INSTAGRAM_CREDENTIALS_FILE}")
        print("\nSetup instructions:")
        print("1. Create the file: shared/creds/instagram")
        print("2. Line 1: your Instagram username")
        print("3. Line 2: your Instagram password")
        return None

    # Delete stale session if requested
    if delete_session and os.path.exists(INSTAGRAM_SESSION_FILE):
        os.remove(INSTAGRAM_SESSION_FILE)
        print("Deleted stale session file. Starting fresh.")

    cl = _create_client()

    # Try to reuse existing session
    if os.path.exists(INSTAGRAM_SESSION_FILE):
        try:
            cl.load_settings(INSTAGRAM_SESSION_FILE)
            # Override device settings from saved session with modern version
            cl.set_device(DEVICE_SETTINGS)
            cl.login(credentials["username"], credentials["password"])
            cl.get_timeline_feed()  # Validate session is alive
            print("Logged in with saved session.")
            return cl
        except Exception:
            print("Saved session expired, deleting and logging in fresh...")
            try:
                os.remove(INSTAGRAM_SESSION_FILE)
            except OSError:
                pass

    # Fresh login with new client to avoid stale UUIDs
    cl = _create_client()

    try:
        cl.login(credentials["username"], credentials["password"])
    except ChallengeRequired:
        print("Instagram requires verification during login...")
        if not _try_resolve_challenge(cl):
            return None
    except Exception as e:
        print(f"Instagram login failed: {e}")
        return None

    # Warmup: establish the session with a lightweight request
    try:
        cl.account_info()
    except Exception:
        pass  # Non-critical, proceed anyway

    # Save session for reuse
    os.makedirs(os.path.dirname(INSTAGRAM_SESSION_FILE), exist_ok=True)
    cl.dump_settings(INSTAGRAM_SESSION_FILE)
    print("Logged in and session saved.")
    return cl


def _try_resolve_challenge(cl):
    """Attempt to resolve an Instagram challenge via private API then contact form.
    Returns True if resolved, False otherwise."""
    last_json = cl.last_json or {}

    # Try the simple/private API path first (handles "was this you?" / delta_login_review)
    try:
        if last_json.get("challenge", {}).get("api_path"):
            challenge_url = last_json["challenge"]["api_path"]
            step_name = last_json.get("step_name", "")
            if step_name in ("delta_login_review", ""):
                print("Attempting automatic challenge approval (was this you?)...")
                cl.challenge_resolve_simple(challenge_url)
                print("Challenge resolved automatically!")
                return True
    except Exception:
        pass  # Fall through to contact form

    # Try the contact form path (sends SMS/email code)
    try:
        print("Attempting challenge resolution (may send SMS/email code)...")
        cl.challenge_resolve(last_json)
        print("Challenge resolved!")
        return True
    except Exception as e:
        print(f"Challenge resolution failed: {e}")
        print("\nTo fix this:")
        print("  1. Log into Instagram on your phone and approve any security prompts")
        print("  2. Wait 10 minutes, then retry with: --delete-session")
        return False


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


def upload_reel(client, video_path, caption, max_retries=2):
    """Upload video as an Instagram Reel, resolving challenges if needed"""
    for attempt in range(1, max_retries + 1):
        print(
            f"Uploading Reel (attempt {attempt}/{max_retries})...", end="", flush=True
        )
        try:
            media = client.clip_upload(Path(video_path), caption)
            print(" Done!")
            return media
        except ChallengeRequired:
            print(f"\nUpload triggered a challenge on attempt {attempt}.")
            if attempt >= max_retries:
                print("Max retries reached.")
                print("\nTo fix this:")
                print(
                    "  1. Log into Instagram on your phone and approve any security prompts"
                )
                print("  2. Wait 10 minutes, then retry with: --delete-session")
                raise
            if _try_resolve_challenge(client):
                # Save updated session after challenge resolution
                try:
                    os.makedirs(os.path.dirname(INSTAGRAM_SESSION_FILE), exist_ok=True)
                    client.dump_settings(INSTAGRAM_SESSION_FILE)
                except Exception:
                    pass
                print("Waiting 10 seconds before retry...")
                time.sleep(10)
                continue
            else:
                raise
        except Exception as e:
            if "challenge_required" in str(e):
                print(f"\nUpload triggered a challenge on attempt {attempt}.")
                if attempt >= max_retries:
                    print("Max retries reached.")
                    print("\nTo fix this:")
                    print(
                        "  1. Log into Instagram on your phone and approve any security prompts"
                    )
                    print("  2. Wait 10 minutes, then retry with: --delete-session")
                    raise
                if _try_resolve_challenge(client):
                    try:
                        os.makedirs(
                            os.path.dirname(INSTAGRAM_SESSION_FILE), exist_ok=True
                        )
                        client.dump_settings(INSTAGRAM_SESSION_FILE)
                    except Exception:
                        pass
                    print("Waiting 10 seconds before retry...")
                    time.sleep(10)
                    continue
                else:
                    raise
            raise


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
    parser.add_argument(
        "--delete-session",
        action="store_true",
        help="Delete saved session and login fresh (fixes recurring challenges)",
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
    client = get_authenticated_client(delete_session=args.delete_session)
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
