# Upload F1 Short to YouTube & Instagram

Upload a completed F1 short video to YouTube and Instagram with auto-generated metadata.

## Input

**Project name** (required): $ARGUMENTS

The project name is the folder name under `projects/` containing the video to upload. This argument is mandatory.

## Instructions

1. **Validate the project exists** and has a completed video:
   - Check `projects/{project}/output/final.mp4` exists
   - Check `projects/{project}/script.json` exists

2. **Preview the upload metadata** by running:
   ```bash
   python3 src/youtube_uploader.py --project {project} --dry-run
   python3 src/instagram_uploader.py --project {project} --dry-run
   ```

3. **Show the user** the auto-generated:
   - YouTube: Title (from script.json), Description (summary + hashtags), Tags (drivers/teams mentioned)
   - Instagram: Caption (summary + hashtags + disclaimer)

4. **Ask the user** to confirm or modify:
   - Title override (optional)

5. **Upload to YouTube** (always public by default):
   ```bash
   python3 src/youtube_uploader.py --project {project}
   ```
   Or with custom title:
   ```bash
   python3 src/youtube_uploader.py --project {project} --title "Custom Title #Shorts"
   ```

   Note: Title automatically includes #Shorts to ensure YouTube classifies it as a Short.

6. **Instagram (manual upload)**:
   - Generate and display the Instagram caption (summary + hashtags + disclaimer) for the user to copy
   - Do NOT run `instagram_uploader.py` or attempt any programmatic upload
   - Do NOT generate or display a thumbnail image
   - Simply present the caption text so the user can paste it when uploading manually via the Instagram app

7. **Report the result**:
   - Show the YouTube Shorts URL
   - Show the Instagram caption for manual upload
   - Confirm upload_info.json was saved with the YouTube URL

## First-time Setup

### YouTube
If YouTube credentials are not configured, guide the user:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable **YouTube Data API v3**
3. Go to Credentials > Create Credentials > OAuth 2.0 Client ID
4. Select "Desktop app" as application type
5. Download the JSON file
6. Save it as: `shared/creds/youtube_client_secrets.json`

First upload will open a browser for Google sign-in to grant YouTube access.

## Example Usage

```
/f1-upload-short stolen-crown
```

This will:
1. Read the script from `projects/stolen-crown/script.json`
2. Generate YouTube title: "The Stolen Crown #Shorts"
3. Generate YouTube description with story summary
4. Generate Instagram caption with hashtags
5. Auto-tag: F1, Vettel, Webber, Norris, McLaren, Red Bull, etc.
6. Ask for confirmation
7. Upload to YouTube and return the YouTube Shorts URL
8. Display the Instagram caption for manual upload
