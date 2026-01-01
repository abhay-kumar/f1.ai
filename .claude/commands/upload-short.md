# Upload F1 Short to YouTube

Upload a completed F1 short video to YouTube with auto-generated metadata.

## Input
Project name: $ARGUMENTS

## Instructions

1. **Validate the project exists** and has a completed video:
   - Check `projects/{project}/output/final.mp4` exists
   - Check `projects/{project}/script.json` exists

2. **Preview the upload metadata** by running:
   ```bash
   python3 src/youtube_uploader.py --project {project} --dry-run
   ```

3. **Show the user** the auto-generated:
   - Title (from script.json)
   - Description (summary + hashtags)
   - Tags (drivers/teams mentioned)

4. **Ask the user** to confirm or modify:
   - Title override (optional)

5. **Upload the video** (always public by default):
   ```bash
   python3 src/youtube_uploader.py --project {project}
   ```
   Or with custom title:
   ```bash
   python3 src/youtube_uploader.py --project {project} --title "Custom Title #Shorts"
   ```

   Note: Title automatically includes #Shorts to ensure YouTube classifies it as a Short.

6. **Report the result**:
   - Show the YouTube URL
   - Confirm upload_info.json was saved

## First-time Setup

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
/upload-short stolen-crown
```

This will:
1. Read the script from `projects/stolen-crown/script.json`
2. Generate title: "The Stolen Crown"
3. Generate description with story summary
4. Auto-tag: F1, Vettel, Webber, Norris, McLaren, Red Bull, etc.
5. Ask for confirmation
6. Upload and return the YouTube Shorts URL
