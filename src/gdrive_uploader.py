#!/usr/bin/env python3
"""
Google Drive Uploader - Uploads project folders to Google Drive
Uses Google Drive API v3 with OAuth 2.0

Recreates the local folder structure in Google Drive, uploading all files.
"""

import argparse
import mimetypes
import os
import pickle
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import SHARED_DIR
from channels import channel_cred, load_channel

# Google Drive API imports
try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# Google Drive API config
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
# GDrive token is shared (not per-channel) since it's for archival
TOKEN_FILE = f"{SHARED_DIR}/creds/gdrive_token.pickle"

DRIVE_FOLDER_NAME = "iti.ai"


def get_authenticated_service(channel_id: str = None):
    """Authenticate and return Google Drive API service."""
    ch = load_channel(channel_id)
    client_secrets = channel_cred(ch, ch["creds"]["youtube_client_secrets"])

    credentials = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(client_secrets):
                print(f"Error: OAuth credentials not found at {client_secrets}")
                print("\nThis uses the same OAuth client as YouTube upload.")
                print("Setup instructions:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Enable the Google Drive API for your project")
                print("3. Use the same OAuth 2.0 credentials as YouTube")
                print(f"4. Ensure file exists at: {client_secrets}")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets, SCOPES
            )
            credentials = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)

    return build("drive", "v3", credentials=credentials)


def find_folder(service, folder_name, parent_id=None):
    """Find a folder by name in Google Drive. Returns folder ID or None."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            pageSize=10,
        )
        .execute()
    )

    files = results.get("files", [])
    return files[0]["id"] if files else None


def create_folder(service, folder_name, parent_id=None):
    """Create a folder in Google Drive. Returns folder ID."""
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def find_or_create_folder(service, folder_name, parent_id=None):
    """Find an existing folder or create a new one. Returns folder ID."""
    folder_id = find_folder(service, folder_name, parent_id)
    if folder_id:
        return folder_id
    return create_folder(service, folder_name, parent_id)


def upload_file(service, file_path, folder_id):
    """Upload a single file to a Google Drive folder. Returns file ID."""
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "application/octet-stream"

    metadata = {
        "name": file_name,
        "parents": [folder_id],
    }

    media = MediaFileUpload(
        file_path,
        mimetype=mime_type,
        resumable=True,
        chunksize=50 * 1024 * 1024,  # 50MB chunks
    )

    size_str = (
        f"{file_size / (1024 * 1024):.1f} MB"
        if file_size > 1024 * 1024
        else f"{file_size / 1024:.1f} KB"
    )
    print(f"    {file_name} ({size_str})")

    request = service.files().create(body=metadata, media_body=media, fields="id,name")

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status and file_size > 10 * 1024 * 1024:  # Show progress for files > 10MB
            pct = int(status.progress() * 100)
            print(f"      Progress: {pct}%", end="\r")

    return response["id"]


def upload_folder(service, local_path, parent_folder_id):
    """Recursively upload a local folder to Google Drive. Returns (files_uploaded, bytes_uploaded)."""
    folder_name = os.path.basename(local_path)
    drive_folder_id = find_or_create_folder(service, folder_name, parent_folder_id)

    files_uploaded = 0
    bytes_uploaded = 0

    for item in sorted(os.listdir(local_path)):
        item_path = os.path.join(local_path, item)

        if os.path.isfile(item_path):
            upload_file(service, item_path, drive_folder_id)
            files_uploaded += 1
            bytes_uploaded += os.path.getsize(item_path)
        elif os.path.isdir(item_path):
            sub_files, sub_bytes = upload_folder(service, item_path, drive_folder_id)
            files_uploaded += sub_files
            bytes_uploaded += sub_bytes

    return files_uploaded, bytes_uploaded


def get_folder_size(path):
    """Get total size of a directory in bytes."""
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total


def main():
    parser = argparse.ArgumentParser(
        description="Upload project folders to Google Drive"
    )
    parser.add_argument("folders", nargs="+", help="Project folders to upload")
    parser.add_argument(
        "--folder",
        default=DRIVE_FOLDER_NAME,
        help=f"Google Drive destination folder (default: {DRIVE_FOLDER_NAME})",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete local folders after successful upload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without uploading",
    )
    args = parser.parse_args()

    # Validate folders exist
    project_folders = []
    for f in args.folders:
        path = Path(f)
        if not path.exists():
            print(f"Warning: Not found: {f}, skipping")
            continue
        if not path.is_dir():
            print(f"Warning: Not a directory: {f}, skipping")
            continue
        project_folders.append(path)

    if not project_folders:
        print("Error: No valid folders to upload")
        sys.exit(1)

    print(f"\nFolders to upload ({len(project_folders)}):")
    total_size = 0
    for pf in project_folders:
        size = get_folder_size(pf)
        total_size += size
        file_count = sum(1 for _ in pf.rglob("*") if _.is_file())
        print(f"  {pf.name} ({size / (1024 * 1024):.1f} MB, {file_count} files)")
    print(f"  Total: {total_size / (1024 * 1024):.1f} MB")
    print(f"  Destination: Google Drive / {args.folder}")

    if args.dry_run:
        print("\nDry run - nothing uploaded.")
        return

    # Authenticate
    print("\nAuthenticating with Google Drive...")
    service = get_authenticated_service()
    if not service:
        sys.exit(1)

    # Find or create root destination folder
    root_folder_id = find_or_create_folder(service, args.folder)
    print(f"Destination folder '{args.folder}' ready")

    # Upload each project folder
    print(f"\nUploading {len(project_folders)} project(s)...\n")
    uploaded = []
    failed = []

    for i, pf in enumerate(project_folders, 1):
        print(f"[{i}/{len(project_folders)}] {pf.name}:")
        try:
            files_uploaded, bytes_uploaded = upload_folder(
                service, str(pf), root_folder_id
            )
            uploaded.append((pf, files_uploaded, bytes_uploaded))
            print(
                f"  Done ({files_uploaded} files, {bytes_uploaded / (1024 * 1024):.1f} MB)\n"
            )
        except Exception as e:
            print(f"  FAILED: {e}\n")
            failed.append((pf, str(e)))

    # Delete local folders if requested
    deleted = []
    if args.delete and uploaded:
        print("Deleting local folders...")
        for pf, _, _ in uploaded:
            try:
                shutil.rmtree(pf)
                deleted.append(pf)
                print(f"  Deleted: {pf.name}")
            except Exception as e:
                print(f"  Failed to delete {pf.name}: {e}")

    # Summary
    total_files = sum(f for _, f, _ in uploaded)
    total_bytes = sum(b for _, _, b in uploaded)
    print(f"\n{'=' * 50}")
    print("Upload Summary")
    print(f"{'=' * 50}")
    print(f"  Projects uploaded: {len(uploaded)}/{len(project_folders)}")
    print(f"  Total files: {total_files}")
    print(f"  Total size: {total_bytes / (1024 * 1024):.1f} MB")
    if failed:
        print(f"  Failed: {len(failed)}")
        for pf, err in failed:
            print(f"    - {pf.name}: {err}")
    if deleted:
        print(f"  Deleted locally: {len(deleted)}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
