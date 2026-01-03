#!/usr/bin/env python3
"""
YouTube Uploader (Long-form) - Uploads standard videos to YouTube with references
Uses YouTube Data API v3 with OAuth 2.0

Features:
- Standard YouTube video format (not Shorts)
- Auto-generated description with references
- Source citations in description
- Timestamped chapters support
- Higher quality upload settings
"""
import os
import sys
import json
import argparse
import pickle
from pathlib import Path
from typing import Dict, List, Optional

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
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # Required for captions
    "https://www.googleapis.com/auth/youtube"  # Required for thumbnail upload
]
CLIENT_SECRETS_FILE = f"{SHARED_DIR}/creds/youtube_client_secrets.json"
TOKEN_FILE = f"{SHARED_DIR}/creds/youtube_token.pickle"

# Long-form video settings
VIDEO_CATEGORY_ID = "17"  # Sports category
DEFAULT_PRIVACY = "public"


def get_authenticated_service():
    """Authenticate and return YouTube API service"""
    credentials = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            credentials = pickle.load(token)

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

        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)

    return build("youtube", "v3", credentials=credentials)


def format_references_for_description(script: Dict) -> str:
    """Format references into a clean description section"""
    lines = []

    # Gather all unique sources
    sources = {}

    # From references_summary
    for ref in script.get("references_summary", []):
        source_name = ref.get("source", "Unknown")
        if source_name not in sources:
            sources[source_name] = ref.get("url", "")

    # From segment references
    for segment in script.get("segments", []):
        for ref in segment.get("references", []):
            source_name = ref.get("source", "Unknown")
            if source_name not in sources:
                sources[source_name] = ref.get("url", "")

    if not sources:
        return ""

    lines.append("\n📚 SOURCES & REFERENCES")
    lines.append("─" * 30)

    for i, (source, url) in enumerate(sources.items(), 1):
        if url:
            lines.append(f"• {source}")
            lines.append(f"  {url}")
        else:
            lines.append(f"• {source}")

    lines.append("")
    lines.append("All facts have been verified against official sources.")

    return "\n".join(lines)


def generate_chapters(script: Dict) -> str:
    """Generate YouTube chapters from segments with sections"""
    segments = script.get("segments", [])

    if not segments:
        return ""

    # Group segments by section
    sections = {}
    current_time = 0

    for segment in segments:
        section = segment.get("section", "content")

        # Estimate duration (using ~20 seconds per segment as rough estimate)
        # In practice, you'd calculate from actual audio durations
        segment_duration = segment.get("duration", 20)

        if section not in sections:
            sections[section] = {
                "start_time": current_time,
                "name": section.replace("_", " ").title()
            }

        current_time += segment_duration

    if len(sections) < 3:
        return ""  # Not enough sections for meaningful chapters

    lines = ["\n⏱️ CHAPTERS"]
    lines.append("─" * 30)

    for section, data in sections.items():
        minutes = int(data["start_time"] // 60)
        seconds = int(data["start_time"] % 60)
        lines.append(f"{minutes:02d}:{seconds:02d} - {data['name']}")

    return "\n".join(lines)


def generate_metadata_from_script(script: Dict) -> Dict:
    """Generate YouTube title, description, and tags from script.json"""
    base_title = script.get("title", "F1 Video")
    # No #Shorts suffix for long-form
    title = base_title

    segments = script.get("segments", [])

    # Build description
    # 1. Opening summary (first 2-3 segment texts)
    opening_texts = [seg["text"] for seg in segments[:3]]
    summary = " ".join(opening_texts)
    if len(summary) > 400:
        summary = summary[:400] + "..."

    # 2. References section
    references_section = format_references_for_description(script)

    # 3. Chapters (if sections are defined)
    chapters_section = generate_chapters(script)

    # 4. Build full description
    description_parts = [
        summary,
        "",
        "─" * 40,
        "",
        "🏎️ ABOUT THIS VIDEO",
        "An in-depth look at Formula 1 history, statistics, and stories.",
        "All facts are verified against official sources.",
    ]

    if chapters_section:
        description_parts.append(chapters_section)

    if references_section:
        description_parts.append(references_section)

    description_parts.extend([
        "",
        "─" * 40,
        "",
        "#F1 #Formula1 #Racing #Motorsport",
        "",
        "Created with F1.ai - Automated F1 video production",
    ])

    description = "\n".join(description_parts)

    # Extract tags
    tags = ["F1", "Formula1", "Formula 1", "Racing", "Motorsport", "Grand Prix"]

    # Driver/team detection
    full_text = " ".join([seg.get("text", "") for seg in segments]).lower()

    driver_tags = {
        "verstappen": ["Verstappen", "Max Verstappen", "Red Bull"],
        "hamilton": ["Hamilton", "Lewis Hamilton", "Mercedes"],
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
    }

    team_tags = {
        "red bull": ["Red Bull Racing", "Red Bull F1"],
        "mclaren": ["McLaren", "McLaren F1 Team"],
        "ferrari": ["Ferrari", "Scuderia Ferrari"],
        "mercedes": ["Mercedes", "Mercedes AMG"],
        "aston martin": ["Aston Martin F1"],
        "williams": ["Williams Racing"],
        "alpine": ["Alpine F1"],
    }

    for keyword, tag_list in driver_tags.items():
        if keyword in full_text:
            tags.extend(tag_list)

    for keyword, tag_list in team_tags.items():
        if keyword in full_text:
            tags.extend(tag_list)

    # Add topic-specific tags
    topic_tags = {
        "champion": ["World Championship", "F1 Champion"],
        "race win": ["Race Winner", "Victory"],
        "pole position": ["Pole Position", "Qualifying"],
        "rivalry": ["F1 Rivalry", "Racing Rivalry"],
        "history": ["F1 History", "Racing History"],
        "legend": ["F1 Legend", "Racing Legend"],
        "debut": ["F1 Debut", "Rookie"],
        "retirement": ["F1 Retirement"],
    }

    for keyword, tag_list in topic_tags.items():
        if keyword in full_text:
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
        "tags": unique_tags[:30],
    }


def upload_captions(youtube, video_id: str, caption_path: str,
                    language: str = "en", name: str = "English") -> bool:
    """Upload captions/subtitles to a YouTube video"""
    if not os.path.exists(caption_path):
        print(f"Caption file not found: {caption_path}")
        return False

    try:
        body = {
            "snippet": {
                "videoId": video_id,
                "language": language,
                "name": name,
                "isDraft": False
            }
        }

        media = MediaFileUpload(
            caption_path,
            mimetype="application/x-subrip",  # SRT format
            resumable=True
        )

        request = youtube.captions().insert(
            part="snippet",
            body=body,
            media_body=media
        )

        response = request.execute()
        return response is not None

    except Exception as e:
        print(f"Caption upload failed: {e}")
        return False


def upload_thumbnail(youtube, video_id: str, thumbnail_path: str) -> bool:
    """Upload custom thumbnail to a YouTube video.

    Supported formats: JPEG, PNG, GIF, BMP
    Recommended size: 1280x720 (16:9 aspect ratio)
    Max file size: 2MB
    """
    if not os.path.exists(thumbnail_path):
        print(f"Thumbnail file not found: {thumbnail_path}")
        return False

    # Determine MIME type from extension
    ext = os.path.splitext(thumbnail_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp'
    }
    mime_type = mime_types.get(ext, 'image/jpeg')

    try:
        media = MediaFileUpload(
            thumbnail_path,
            mimetype=mime_type,
            resumable=True
        )

        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=media
        )

        response = request.execute()
        return response is not None

    except Exception as e:
        print(f"Thumbnail upload failed: {e}")
        return False


def upload_video(youtube, video_path: str, metadata: Dict,
                 privacy: str = "private") -> Optional[Dict]:
    """Upload video to YouTube"""
    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": VIDEO_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        }
    }

    # Calculate file size for progress
    file_size = os.path.getsize(video_path)
    size_mb = file_size / (1024 * 1024)

    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024 * 5,  # 5MB chunks for large files
        resumable=True,
        mimetype="video/mp4"
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    print(f"Uploading {size_mb:.1f}MB...", end="", flush=True)
    response = None
    last_progress = 0

    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            if progress > last_progress + 5:  # Update every 5%
                print(f"\rUploading... {progress}% ({size_mb * progress / 100:.1f}/{size_mb:.1f}MB)", end="", flush=True)
                last_progress = progress

    print(f"\rUploading... Done! ({size_mb:.1f}MB)                    ")
    return response


def main():
    parser = argparse.ArgumentParser(description="Upload F1 long-form video to YouTube")
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
    captions_path = f"{project_dir}/output/captions.srt"

    # Check for thumbnail (supports multiple formats)
    thumbnail_path = None
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        candidate = f"{project_dir}/output/thumbnail{ext}"
        if os.path.exists(candidate):
            thumbnail_path = candidate
            break

    # Validate files exist
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        print(f"Run video assembly first: python3 src/video_assembler_longform.py --project {args.project}")
        sys.exit(1)

    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        sys.exit(1)

    has_captions = os.path.exists(captions_path)
    has_thumbnail = thumbnail_path is not None

    # Load script and generate metadata
    with open(script_path) as f:
        script = json.load(f)

    metadata = generate_metadata_from_script(script)

    # Override title if provided
    if args.title:
        metadata["title"] = args.title

    # Get file info
    file_size = os.path.getsize(video_path) / (1024 * 1024)

    # Count references
    ref_count = len(script.get("references_summary", []))
    for seg in script.get("segments", []):
        ref_count += len(seg.get("references", []))

    # Display metadata
    print("=" * 70)
    print(f"YouTube Upload (Long-form) - Project: {args.project}")
    print("=" * 70)
    print(f"\n📺 TITLE:")
    print(f"   {metadata['title']}")
    print(f"\n📝 DESCRIPTION:")
    print("-" * 50)
    # Show truncated description
    desc_preview = metadata['description'][:800]
    if len(metadata['description']) > 800:
        desc_preview += "\n... [truncated]"
    print(desc_preview)
    print("-" * 50)
    print(f"\n🏷️  TAGS ({len(metadata['tags'])}):")
    print(f"   {', '.join(metadata['tags'][:15])}...")
    print(f"\n📚 REFERENCES: {ref_count} sources cited")
    print(f"📝 CAPTIONS: {'Yes - ' + captions_path if has_captions else 'No captions file found'}")
    print(f"🖼️  THUMBNAIL: {'Yes - ' + thumbnail_path if has_thumbnail else 'No thumbnail found (place thumbnail.jpg/png in output/)'}")
    print(f"\n🔒 PRIVACY: {args.privacy}")
    print(f"📁 VIDEO: {video_path}")
    print(f"📦 SIZE: {file_size:.1f}MB")

    if args.dry_run:
        print("\n" + "=" * 70)
        print("[DRY RUN - No upload performed]")
        print("=" * 70)
        return

    print("\n" + "-" * 70)
    confirm = input("Proceed with upload? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Upload cancelled.")
        return

    print()

    # Authenticate and upload
    youtube = get_authenticated_service()
    if not youtube:
        sys.exit(1)

    response = upload_video(youtube, video_path, metadata, args.privacy)

    if response:
        video_id = response.get("id")
        print(f"\n{'=' * 70}")
        print(f"✅ SUCCESS! Video uploaded")
        print(f"🔗 URL: https://youtube.com/watch?v={video_id}")

        # Upload captions if available
        captions_uploaded = False
        if has_captions:
            print(f"\n📝 Uploading captions...")
            captions_uploaded = upload_captions(youtube, video_id, captions_path)
            if captions_uploaded:
                print("✅ Captions uploaded successfully")
            else:
                print("⚠️  Caption upload failed (video is still uploaded)")

        # Upload thumbnail if available
        thumbnail_uploaded = False
        if has_thumbnail:
            print(f"\n🖼️  Uploading thumbnail...")
            thumbnail_uploaded = upload_thumbnail(youtube, video_id, thumbnail_path)
            if thumbnail_uploaded:
                print("✅ Thumbnail uploaded successfully")
            else:
                print("⚠️  Thumbnail upload failed (video is still uploaded)")

        print(f"{'=' * 70}")

        # Save upload info
        upload_info = {
            "video_id": video_id,
            "url": f"https://youtube.com/watch?v={video_id}",
            "title": metadata["title"],
            "privacy": args.privacy,
            "format": "longform",
            "references_count": ref_count,
            "captions_uploaded": captions_uploaded,
            "thumbnail_uploaded": thumbnail_uploaded,
        }

        with open(f"{project_dir}/upload_info.json", "w") as f:
            json.dump(upload_info, f, indent=2)

        print(f"\nUpload info saved to: {project_dir}/upload_info.json")
    else:
        print("\n❌ Upload failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
