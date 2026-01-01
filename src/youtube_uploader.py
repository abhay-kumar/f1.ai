#!/usr/bin/env python3
"""
YouTube Uploader - Uploads shorts to YouTube with auto-generated metadata
Uses YouTube Data API v3 with OAuth 2.0
"""
import os
import sys
import json
import argparse
import pickle
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir, SHARED_DIR

# YouTube API imports
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# YouTube API config
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = f"{SHARED_DIR}/creds/youtube_client_secrets.json"
TOKEN_FILE = f"{SHARED_DIR}/creds/youtube_token.pickle"

# Shorts-specific settings
SHORTS_CATEGORY_ID = "17"  # Sports category
DEFAULT_PRIVACY = "public"  # Default to public for Shorts


def get_authenticated_service():
    """Authenticate and return YouTube API service"""
    credentials = None

    # Load saved credentials
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            credentials = pickle.load(token)

    # Refresh or get new credentials
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"Error: YouTube credentials not found at {CLIENT_SECRETS_FILE}")
                print("\nSetup instructions:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a project and enable YouTube Data API v3")
                print("3. Create OAuth 2.0 credentials (Desktop app)")
                print("4. Download and save as: shared/creds/youtube_client_secrets.json")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)

        # Save credentials
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)

    return build("youtube", "v3", credentials=credentials)


def generate_metadata_from_script(script):
    """Generate YouTube title, description, and tags from script.json"""
    base_title = script.get("title", "F1 Short")
    # Add #Shorts to title to help YouTube classify as Short
    title = f"{base_title} #Shorts"
    segments = script.get("segments", [])

    # Extract all text for description
    full_text = " ".join([seg["text"] for seg in segments])

    # Build description
    description_lines = [
        full_text[:300] + "..." if len(full_text) > 300 else full_text,
        "",
        "#F1 #Formula1 #Shorts",
        "",
        "---",
        "Created with F1.ai"
    ]
    description = "\n".join(description_lines)

    # Extract tags from content (drivers, teams mentioned)
    tags = ["F1", "Formula1", "Shorts", "Formula 1", "Racing"]

    # Add driver/team tags based on mentions
    driver_tags = {
        "vettel": ["Vettel", "Sebastian Vettel"],
        "webber": ["Webber", "Mark Webber"],
        "norris": ["Norris", "Lando Norris"],
        "piastri": ["Piastri", "Oscar Piastri"],
        "verstappen": ["Verstappen", "Max Verstappen"],
        "hamilton": ["Hamilton", "Lewis Hamilton"],
        "leclerc": ["Leclerc", "Charles Leclerc"],
        "alonso": ["Alonso", "Fernando Alonso"],
    }

    team_tags = {
        "red bull": ["Red Bull", "Red Bull Racing"],
        "mclaren": ["McLaren", "McLaren F1"],
        "ferrari": ["Ferrari", "Scuderia Ferrari"],
        "mercedes": ["Mercedes", "Mercedes AMG"],
    }

    full_text_lower = full_text.lower()

    for keyword, tag_list in driver_tags.items():
        if keyword in full_text_lower:
            tags.extend(tag_list)

    for keyword, tag_list in team_tags.items():
        if keyword in full_text_lower:
            tags.extend(tag_list)

    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            unique_tags.append(tag)

    return {
        "title": title,
        "description": description,
        "tags": unique_tags[:30],  # YouTube limit is 500 chars total, ~30 tags safe
    }


def upload_video(youtube, video_path, metadata, privacy="private"):
    """Upload video to YouTube"""
    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": SHORTS_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024,  # 1MB chunks
        resumable=True,
        mimetype="video/mp4"
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    print("Uploading", end="", flush=True)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"\rUploading... {progress}%", end="", flush=True)

    print(f"\rUploading... Done!")
    return response


def main():
    parser = argparse.ArgumentParser(description="Upload F1 short to YouTube")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--privacy", default=DEFAULT_PRIVACY,
                        choices=["public", "unlisted", "private"],
                        help="Video privacy setting")
    parser.add_argument("--title", help="Override auto-generated title")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show metadata without uploading")
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    video_path = f"{project_dir}/output/final.mp4"
    script_path = f"{project_dir}/script.json"

    # Validate files exist
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        print(f"Run video assembly first: python3 src/video_assembler.py --project {args.project}")
        sys.exit(1)

    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        sys.exit(1)

    # Load script and generate metadata
    with open(script_path) as f:
        script = json.load(f)

    metadata = generate_metadata_from_script(script)

    # Override title if provided
    if args.title:
        metadata["title"] = args.title

    # Display metadata
    print("=" * 60)
    print(f"YouTube Upload - Project: {args.project}")
    print("=" * 60)
    print(f"\nTitle: {metadata['title']}")
    print(f"\nDescription:\n{metadata['description']}")
    print(f"\nTags: {', '.join(metadata['tags'][:10])}...")
    print(f"\nPrivacy: {args.privacy}")
    print(f"Video: {video_path}")
    print(f"Size: {os.path.getsize(video_path) / (1024*1024):.1f}MB")

    if args.dry_run:
        print("\n[Dry run - no upload performed]")
        return

    print("\n" + "-" * 60)

    # Authenticate and upload
    youtube = get_authenticated_service()
    if not youtube:
        sys.exit(1)

    response = upload_video(youtube, video_path, metadata, args.privacy)

    video_id = response.get("id")
    print(f"\n{'=' * 60}")
    print(f"SUCCESS! Video uploaded")
    print(f"URL: https://youtube.com/shorts/{video_id}")
    print(f"{'=' * 60}")

    # Save upload info to project
    upload_info = {
        "video_id": video_id,
        "url": f"https://youtube.com/shorts/{video_id}",
        "title": metadata["title"],
        "privacy": args.privacy,
    }

    with open(f"{project_dir}/upload_info.json", "w") as f:
        json.dump(upload_info, f, indent=2)


if __name__ == "__main__":
    main()
