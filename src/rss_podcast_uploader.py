#!/usr/bin/env python3
"""
RSS.com Podcast Uploader - Automates podcast episode uploads using Playwright

Since RSS.com API is only available on Network plans, this script uses
browser automation to upload episodes through their web dashboard.

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    python3 src/rss_podcast_uploader.py --project <project-name>
    python3 src/rss_podcast_uploader.py --project <project-name> --episode 1
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import SHARED_DIR, get_project_dir
from channels import channel_cred, load_channel_from_script

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not installed. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)

# RSS.com configuration
RSS_LOGIN_URL = "https://dashboard.rss.com/auth/sign-in"


def get_credentials(creds_file: str):
    """Load RSS.com credentials from file"""
    if os.path.exists(creds_file):
        with open(creds_file) as f:
            lines = f.read().strip().split("\n")
            if len(lines) >= 2:
                return {"email": lines[0], "password": lines[1]}
    return None


def generate_episode_description(script: dict) -> str:
    """Generate episode description from script"""
    segments = script.get("segments", [])

    # Get first segment text for summary
    first_text = segments[0].get("text", "") if segments else ""
    summary = first_text[:300] + "..." if len(first_text) > 300 else first_text

    # Build description
    lines = [summary, ""]

    # Add topics from segment contexts
    contexts = [seg.get("context", "") for seg in segments if seg.get("context")]
    if contexts:
        lines.append("Topics covered:")
        for ctx in contexts[:10]:
            if ctx and ctx.lower() not in [
                "intro",
                "outro",
                "segment",
                "intro hook",
                "sign off",
                "closing",
            ]:
                lines.append(f"- {ctx}")
        lines.append("")

    # Add timestamps
    lines.append("Timestamps:")
    current_time = 0
    words_per_second = 150 / 60

    for i, segment in enumerate(segments):
        context = segment.get("context", f"Segment {i + 1}")
        text = segment.get("text", "")

        minutes = int(current_time // 60)
        seconds = int(current_time % 60)
        lines.append(f"{minutes:02d}:{seconds:02d} - {context}")

        word_count = len(text.split())
        current_time += word_count / words_per_second

    # Channel-specific tagline and hashtags are added by the caller

    return "\n".join(lines)


def upload_episode(
    project_name: str,
    episode_num: int = None,
    title_override: str = None,
    dry_run: bool = False,
):
    """Upload podcast episode to RSS.com using Playwright"""

    project_dir = get_project_dir(project_name)
    audio_path = f"{project_dir}/output/final.mp3"
    script_path = f"{project_dir}/script.json"

    # Validate files exist
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        sys.exit(1)

    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        sys.exit(1)

    # Load script
    with open(script_path) as f:
        script = json.load(f)

    channel = load_channel_from_script(script)
    podcast_config = channel.get("podcast", {})
    show_name = podcast_config.get("show_name", "Podcast")

    # Generate metadata
    base_title = script.get("title", f"{show_name} Episode")
    prefix = f"{show_name}:"
    if base_title.lower().startswith(prefix.lower()):
        base_title = base_title[len(prefix):].strip()

    if title_override:
        title = title_override
    elif episode_num:
        title = f"Ep. {episode_num}: {base_title}"
    else:
        title = base_title

    description = generate_episode_description(script)
    # Append channel-specific tagline and hashtags
    tagline = podcast_config.get("tagline", "")
    hashtags = podcast_config.get("hashtags", "")
    if tagline or hashtags:
        description += f"\n\n---\n{tagline}\n\n{hashtags}"

    # Get file size
    file_size = os.path.getsize(audio_path) / (1024 * 1024)

    print("=" * 60)
    print("RSS.com Podcast Uploader")
    print("=" * 60)
    print(f"Project: {project_name}")
    print(f"Title: {title}")
    print(f"Audio: {audio_path} ({file_size:.1f}MB)")
    print(f"Episode #: {episode_num or 'Not specified'}")
    print("-" * 60)
    print("Description preview:")
    desc_preview = description[:400] + "..." if len(description) > 400 else description
    print(desc_preview)
    print("=" * 60)

    if dry_run:
        print("\n[DRY RUN - No upload performed]")
        return

    # Get credentials
    rss_creds_file = channel_cred(channel, channel["creds"]["rss_com"])
    credentials = get_credentials(rss_creds_file)
    if not credentials:
        print("Error: No credentials found at", rss_creds_file)
        sys.exit(1)

    print("\nLaunching browser...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        try:
            # Step 1: Always go to login page first
            print("Navigating to login page...")
            page.goto(RSS_LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)

            # Step 2: Fill credentials and login (use type() for reliability)
            print("Entering credentials...")
            page.locator("input#username").click()
            time.sleep(0.3)
            page.locator("input#username").type(credentials["email"], delay=50)
            time.sleep(0.5)
            page.locator("input#password").click()
            time.sleep(0.3)
            page.locator("input#password").type(credentials["password"], delay=50)
            time.sleep(0.5)

            print("Submitting login...")
            page.keyboard.press("Enter")
            time.sleep(8)
            print(f"Logged in. Current URL: {page.url}")

            # Step 3: Navigate to podcast page and click New Episode
            rss_dashboard = podcast_config.get("rss_dashboard_url", "https://dashboard.rss.com/podcasts/")
            print(f"Navigating to podcast page ({rss_dashboard})...")
            page.goto(
                rss_dashboard,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            time.sleep(3)

            print("Clicking '+ New Episode' button...")
            page.click(
                'button:has-text("New Episode"), a:has-text("New Episode"), [class*="new-episode"]'
            )
            time.sleep(3)
            print(f"On page: {page.url}")

            # Step 4: Upload audio file (file input is hidden, set directly)
            print("\nUploading audio file...")
            file_input = page.locator('input[type="file"][accept*="audio"]')
            file_input.set_input_files(audio_path)
            print(f"Audio file selected: {audio_path}")
            print("Waiting for upload to complete...")
            # Wait for upload progress to finish (check for audio player or progress)
            time.sleep(60)  # Wait up to 60 seconds for upload

            # Step 5: Fill title
            print("\nFilling title...")
            page.fill("input#title", title)
            print(f"Title set: {title}")
            time.sleep(1)

            # Step 6: Fill description (look for rich text editor)
            print("\nFilling description...")
            try:
                # RSS.com likely uses a rich text editor like ProseMirror or similar
                desc_editor = page.locator(
                    '.ProseMirror, [contenteditable="true"]'
                ).first
                if desc_editor.is_visible(timeout=3000):
                    desc_editor.click()
                    page.keyboard.type(description)
                    print("Description filled!")
            except Exception as e:
                print(f"Description editor not found: {e}")
            time.sleep(1)

            # Step 7: Set season and episode number
            print("\nSetting season number...")
            page.fill("input#seasonNumber", "1")
            print("Season number set: 1")

            if episode_num:
                print("Setting episode number...")
                page.fill("input#episodeNumber", str(episode_num))
                print(f"Episode number set: {episode_num}")
            time.sleep(1)

            # Step 8: Add keywords
            print("\nAdding keywords...")
            keywords = podcast_config.get("keywords", ["Podcast"])
            try:
                # Look for keywords input or button to expand keywords section
                keyword_section = page.locator(
                    'button:has-text("EPISODE KEYWORDS")'
                ).first
                if keyword_section.is_visible(timeout=2000):
                    keyword_section.click()
                    time.sleep(1)

                keyword_input = page.locator(
                    'input[placeholder*="keyword" i], input[name*="keyword" i], input[id*="keyword" i]'
                ).first
                if keyword_input.is_visible(timeout=3000):
                    for kw in keywords:
                        keyword_input.fill(kw)
                        keyword_input.press("Enter")
                        time.sleep(0.3)
                    print(f"Keywords added: {', '.join(keywords)}")
            except Exception as e:
                print(f"Could not add keywords: {e}")
            time.sleep(1)

            # Step 9: Upload cover art
            cover_art_path = f"{project_dir}/output/cover_art.jpg"
            if os.path.exists(cover_art_path):
                print(f"\nUploading cover art: {cover_art_path}")
                try:
                    image_input = page.locator('input[type="file"][accept*="image"]')
                    image_input.set_input_files(cover_art_path)
                    print("Cover art uploaded!")
                    time.sleep(3)
                except Exception as e:
                    print(f"Could not upload cover art: {e}")
            else:
                print(f"\nNo cover art found at {cover_art_path}")

            print("\n" + "=" * 60)
            print("BROWSER IS OPEN")
            print("=" * 60)
            print("\nPlease complete the following in the browser:")
            print("  1. Verify/upload the audio file if needed")
            print("  2. Review title and description")
            print("  3. Click 'Publish' or 'Save' when ready")
            print(f"\nAudio file: {audio_path}")
            print("\nThe browser will stay open for 10 minutes.")
            print("Close the browser window when done, or wait for timeout.")
            print("=" * 60)

            # Keep browser open for manual completion
            time.sleep(600)  # 10 minutes

        except Exception as e:
            print(f"\nError: {e}")
            print("\nBrowser will stay open for manual intervention (5 min)...")
            time.sleep(300)

        finally:
            browser.close()
            print("\nBrowser closed.")


def main():
    parser = argparse.ArgumentParser(
        description="Upload podcast episode to RSS.com using browser automation"
    )
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--episode", type=int, help="Episode number")
    parser.add_argument("--title", help="Override episode title")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show metadata without uploading"
    )

    args = parser.parse_args()

    upload_episode(
        project_name=args.project,
        episode_num=args.episode,
        title_override=args.title,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
