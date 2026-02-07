# F1 Archive

Clean up intermediate files from project folders, upload to Google Drive, and delete locally after successful upload.

## Input

**Project names** (optional): $ARGUMENTS

- If provided, only archive the specified projects (space-separated or comma-separated)
- If not provided, list all project folders in `projects/` and ask the user which ones to archive

## Prerequisites

The Google Drive API must be enabled in the same Google Cloud project used for YouTube uploads:

1. Go to https://console.cloud.google.com/
2. Select the project used for YouTube Data API
3. Enable **Google Drive API**
4. The same `youtube_client_secrets.json` is reused for authentication

On first run, a browser window will open for OAuth consent. The token is saved to `shared/creds/gdrive_token.pickle`.

## Instructions

### 1. Identify Project Folders

List all folders in the `projects/` directory:

```bash
ls -d projects/*/
```

If arguments were provided, validate that each folder exists (check for `projects/{name}/`). If any don't exist, warn and skip.

If no arguments were provided, display the list of project folders with sizes and ask the user which ones to archive. Accept:
- `all` to archive everything
- Space or comma-separated project names
- A pattern like `f1-daily-news-*`

If no project folders exist, inform the user there's nothing to archive.

### 2. Clean Intermediate Files

Before uploading, remove intermediate build artifacts to reduce upload size. For each project, delete everything except `script.json`, `upload_info.json`, and `output/`:

```bash
# Remove intermediate directories
rm -rf "projects/{name}/audio"
rm -rf "projects/{name}/footage"
rm -rf "projects/{name}/previews"
rm -rf "projects/{name}/temp"

# Remove any other files/directories that aren't preserved
find "projects/{name}" -maxdepth 1 ! -name "script.json" ! -name "upload_info.json" ! -name "output" ! -name "$(basename projects/{name})" -exec rm -rf {} +
```

Report the space freed by cleanup for each project.

### 3. Show Summary Before Uploading

For each project to be archived, show:
- Project name
- Size before cleanup
- Size after cleanup (what will be uploaded)
- Number of files remaining

Total upload size. Ask the user to confirm before proceeding.

### 4. Upload to Google Drive

Use the uploader script with the `--delete` flag to upload and clean up:

```bash
python3 src/gdrive_uploader.py projects/{name1} projects/{name2} --delete
```

The script will:
- Authenticate with Google Drive (browser popup on first run)
- Find or create the `f1.ai` folder in Google Drive
- Create a subfolder for each project, mirroring the local structure
- Upload all files within each project folder
- Delete local project folders after successful upload

### 5. Dry Run Option

If the user asks for a dry run or preview:

```bash
python3 src/gdrive_uploader.py projects/{name} --dry-run
```

This skips the cleanup step and only previews what would be uploaded.

### 6. Report Summary

Display:
- Number of projects archived
- Space freed by cleanup (intermediate files removed)
- Total files uploaded
- Total data uploaded to Google Drive
- Number of local folders deleted
- Any failures

## Example Usage

```
/f1-archive                                    # Interactive - asks which projects
/f1-archive f1-daily-news-jan23               # Archive specific project
/f1-archive f1-daily-news-jan23 f1-daily-news-jan24  # Multiple
```

## Error Handling

- **No project folders found**: Inform user there's nothing to archive
- **Cleanup fails**: Warn but continue with upload of remaining files
- **No output/ directory**: Warn that project has no final output but still archive if user confirms
- **Authentication fails**: Show setup instructions for Google Drive API
- **Upload fails**: Report error, do NOT delete the local folder
- **Partial failure**: Report which succeeded and which failed
