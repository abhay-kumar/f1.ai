#!/usr/bin/env python3
"""
YouTube Uploader - Uploads shorts to YouTube with auto-generated metadata
Uses YouTube Data API v3 with OAuth 2.0
"""

import argparse
import json
import os
import pickle
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir
from channels import channel_cred, load_channel_from_script

# YouTube API imports
try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# YouTube API config
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # Required for posting comments
]
DEFAULT_PRIVACY = "public"  # Default to public for Shorts


def get_authenticated_service(channel):
    """Authenticate and return YouTube API service"""
    client_secrets_file = channel_cred(channel, channel["creds"]["youtube_client_secrets"])
    token_file = channel_cred(channel, channel["creds"]["youtube_token"])

    credentials = None

    # Load saved credentials
    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            credentials = pickle.load(token)

    # Refresh or get new credentials
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(client_secrets_file):
                print(f"Error: YouTube credentials not found at {client_secrets_file}")
                print("\nSetup instructions:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a project and enable YouTube Data API v3")
                print("3. Create OAuth 2.0 credentials (Desktop app)")
                print(
                    f"4. Download and save as: {client_secrets_file}"
                )
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, SCOPES
            )
            credentials = flow.run_local_server(port=0)

        # Save credentials
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, "wb") as token:
            pickle.dump(credentials, token)

    return build("youtube", "v3", credentials=credentials)


def generate_metadata_from_script(script):
    """Generate YouTube title, description, and tags from script.json"""
    channel = load_channel_from_script(script)

    base_title = script.get("title", "Short")
    # Add #Shorts to title to help YouTube classify as Short
    title = f"{base_title} #Shorts"
    segments = script.get("segments", [])

    # Extract all text for description
    full_text = " ".join([seg["text"] for seg in segments])

    # Build description with disclaimer
    description_lines = [
        full_text[:300] + "..." if len(full_text) > 300 else full_text,
        "",
        channel["shorts_hashtags"],
        "",
        channel["disclaimer_shorts"],
        "",
        channel["created_with"],
    ]
    description = "\n".join(description_lines)

    # Extract tags from content (drivers, teams mentioned)
    tags = list(channel["base_tags"]) + ["Shorts"]

    # Also include any tags from script.json itself
    script_tags = script.get("tags", [])
    tags.extend(script_tags)

    # Add driver/team/topic tags based on mentions
    full_text_lower = full_text.lower()

    for keyword, tag_list in channel["driver_tags"].items():
        if keyword in full_text_lower:
            tags.extend(tag_list)

    for keyword, tag_list in channel["team_tags"].items():
        if keyword in full_text_lower:
            tags.extend(tag_list)

    for keyword, tag_list in channel["topic_tags"].items():
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


def post_comment(youtube, video_id, comment_text):
    """Post a top-level comment on a YouTube video"""
    try:
        body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": comment_text,
                    }
                },
            }
        }

        response = youtube.commentThreads().insert(
            part="snippet", body=body
        ).execute()

        comment_id = response["snippet"]["topLevelComment"]["id"]
        return comment_id

    except Exception as e:
        print(f"Comment posting failed: {e}")
        return None


def upload_video(youtube, video_path, metadata, category_id, privacy="private"):
    """Upload video to YouTube"""
    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024,  # 1MB chunks
        resumable=True,
        mimetype="video/mp4",
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()), body=body, media_body=media
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
    parser.add_argument(
        "--privacy",
        default=DEFAULT_PRIVACY,
        choices=["public", "unlisted", "private"],
        help="Video privacy setting",
    )
    parser.add_argument("--title", help="Override auto-generated title")
    parser.add_argument(
        "--main-video",
        help="URL of the full-length video to link in a pinned comment",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show metadata without uploading"
    )
    args = parser.parse_args()

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

    # Load script and generate metadata
    with open(script_path) as f:
        script = json.load(f)

    channel = load_channel_from_script(script)
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
    print(f"Size: {os.path.getsize(video_path) / (1024 * 1024):.1f}MB")

    if args.dry_run:
        print("\n[Dry run - no upload performed]")
        return

    print("\n" + "-" * 60)

    # Authenticate and upload
    youtube = get_authenticated_service(channel)
    if not youtube:
        sys.exit(1)

    response = upload_video(youtube, video_path, metadata, channel["category_id"], args.privacy)

    video_id = response.get("id")
    print(f"\n{'=' * 60}")
    print(f"SUCCESS! Video uploaded")
    print(f"URL: https://youtube.com/shorts/{video_id}")
    print(f"{'=' * 60}")

    # Post comment with main video link if provided
    comment_id = None
    main_video_url = args.main_video or script.get("main_video_url")
    if main_video_url:
        print(f"\nPosting comment with full video link...")
        comment_text = f"👉 Watch the full breakdown here: {main_video_url}"
        comment_id = post_comment(youtube, video_id, comment_text)
        if comment_id:
            print(f"Comment posted! Pin it from YouTube Studio for max visibility.")
        else:
            print(f"Comment posting failed — add it manually.")

    # Save upload info to project
    upload_info = {
        "video_id": video_id,
        "url": f"https://youtube.com/shorts/{video_id}",
        "title": metadata["title"],
        "privacy": args.privacy,
        "upload_status": "uploaded",
    }
    if comment_id:
        upload_info["comment_id"] = comment_id
        upload_info["main_video_url"] = main_video_url

    with open(f"{project_dir}/upload_info.json", "w") as f:
        json.dump(upload_info, f, indent=2)


if __name__ == "__main__":
    main()
