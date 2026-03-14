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
from src.config import SHARED_DIR, get_project_dir

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
CLIENT_SECRETS_FILE = f"{SHARED_DIR}/creds/youtube_client_secrets.json"
TOKEN_FILE = f"{SHARED_DIR}/creds/youtube_token.pickle"

# Shorts-specific settings
SHORTS_CATEGORY_ID = "17"  # Sports category
DEFAULT_PRIVACY = "public"  # Default to public for Shorts

# F1 Fan Content Disclaimer (per F1 guidelines)
F1_FAN_DISCLAIMER = """
───────────────────────────────────────────────────────────
DISCLAIMER: This video is unofficial fan content and is not
associated with, endorsed by, or affiliated with Formula 1,
FIA, or Formula One Management (FOM). All F1-related trademarks
and imagery are property of their respective owners. Created
for commentary and entertainment under fair use principles.

For official F1 content: https://www.formula1.com
───────────────────────────────────────────────────────────
"""


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
                print(
                    "4. Download and save as: shared/creds/youtube_client_secrets.json"
                )
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
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

    # Build description with disclaimer
    description_lines = [
        full_text[:300] + "..." if len(full_text) > 300 else full_text,
        "",
        "#F1 #Formula1 #Shorts",
        "",
        F1_FAN_DISCLAIMER,
        "",
        "Created with F1.ai",
    ]
    description = "\n".join(description_lines)

    # Extract tags from content (drivers, teams mentioned)
    tags = ["F1", "Formula1", "Shorts", "Formula 1", "Racing", "Motorsport", "Grand Prix"]

    # Also include any tags from script.json itself
    script_tags = script.get("tags", [])
    tags.extend(script_tags)

    # Add driver/team tags based on mentions
    driver_tags = {
        "verstappen": ["Verstappen", "Max Verstappen", "Red Bull"],
        "hamilton": ["Hamilton", "Lewis Hamilton"],
        "leclerc": ["Leclerc", "Charles Leclerc", "Ferrari"],
        "norris": ["Norris", "Lando Norris", "McLaren"],
        "sainz": ["Sainz", "Carlos Sainz"],
        "alonso": ["Alonso", "Fernando Alonso", "Aston Martin"],
        "piastri": ["Piastri", "Oscar Piastri"],
        "russell": ["Russell", "George Russell"],
        "vettel": ["Vettel", "Sebastian Vettel"],
        "schumacher": ["Schumacher", "Michael Schumacher"],
        "senna": ["Senna", "Ayrton Senna"],
        "prost": ["Prost", "Alain Prost"],
        "webber": ["Webber", "Mark Webber"],
        "ricciardo": ["Ricciardo", "Daniel Ricciardo"],
        "raikkonen": ["Raikkonen", "Kimi Raikkonen"],
        "bottas": ["Bottas", "Valtteri Bottas"],
        "perez": ["Perez", "Sergio Perez"],
        "ocon": ["Ocon", "Esteban Ocon"],
        "hulkenberg": ["Hulkenberg", "Nico Hulkenberg"],
        "antonelli": ["Antonelli", "Kimi Antonelli"],
        "hadjar": ["Hadjar", "Isack Hadjar"],
        "newey": ["Adrian Newey", "Newey"],
        "horner": ["Christian Horner", "Horner"],
        "toto": ["Toto Wolff", "Wolff"],
        "vasseur": ["Fred Vasseur", "Vasseur"],
        "lauda": ["Lauda", "Niki Lauda"],
        "brabham": ["Brabham", "Jack Brabham"],
        "andretti": ["Andretti", "Mario Andretti"],
        "maylander": ["Maylander", "Bernd Maylander", "Safety Car"],
    }

    team_tags = {
        "red bull": ["Red Bull", "Red Bull Racing", "Red Bull F1"],
        "mclaren": ["McLaren", "McLaren F1 Team"],
        "ferrari": ["Ferrari", "Scuderia Ferrari"],
        "mercedes": ["Mercedes", "Mercedes AMG"],
        "aston martin": ["Aston Martin", "Aston Martin F1"],
        "williams": ["Williams", "Williams Racing"],
        "alpine": ["Alpine", "Alpine F1"],
        "haas": ["Haas", "Haas F1"],
        "cadillac": ["Cadillac", "Cadillac F1"],
        "audi": ["Audi", "Audi F1"],
        "racing bulls": ["Racing Bulls"],
    }

    # Topic tags
    topic_tags = {
        "champion": ["World Championship", "F1 Champion"],
        "race win": ["Race Winner", "Victory"],
        "pole position": ["Pole Position", "Qualifying"],
        "rivalry": ["F1 Rivalry", "Racing Rivalry"],
        "history": ["F1 History", "Racing History"],
        "legend": ["F1 Legend", "Racing Legend"],
        "debut": ["F1 Debut", "Rookie"],
        "retirement": ["F1 Retirement"],
        "safety": ["F1 Safety", "Safety Car"],
        "testing": ["F1 Testing", "Pre-Season"],
        "regulation": ["F1 Regulations", "F1 Rules"],
        "crash": ["F1 Crash", "Incident"],
        "overtake": ["Overtake", "Overtaking"],
        "pit stop": ["Pit Stop", "Strategy"],
        "2026": ["F1 2026", "2026 Season"],
    }

    full_text_lower = full_text.lower()

    for keyword, tag_list in driver_tags.items():
        if keyword in full_text_lower:
            tags.extend(tag_list)

    for keyword, tag_list in team_tags.items():
        if keyword in full_text_lower:
            tags.extend(tag_list)

    for keyword, tag_list in topic_tags.items():
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
    youtube = get_authenticated_service()
    if not youtube:
        sys.exit(1)

    response = upload_video(youtube, video_path, metadata, args.privacy)

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
