# Upload F1 Long-Form Video to YouTube

Upload a completed F1 long-form video to YouTube with auto-generated metadata, references in description, captions, and **auto-generated viral thumbnail**.

## Input
Project name: $ARGUMENTS

## Instructions

1. **Validate the project exists** and has required files:
   - Check `projects/{project}/output/final.mp4` exists
   - Check `projects/{project}/script.json` exists
   - Check `projects/{project}/output/captions.srt` exists (optional but recommended)

2. **Generate thumbnail if not exists**:
   If `projects/{project}/output/thumbnail.jpg` doesn't exist, generate one:
   ```bash
   python3 src/thumbnail_generator.py --project {project}
   ```
   This auto-generates a viral-style thumbnail with:
   - Eye-catching text from the video title
   - F1 team colors based on content
   - High-contrast overlay for readability
   - Channel branding

3. **Preview the upload metadata** by running:
   ```bash
   python3 src/youtube_uploader_longform.py --project {project} --dry-run
   ```

4. **Show the user** the auto-generated:
   - Title (from script.json title field)
   - Description preview (summary + references section)
   - Tags (drivers/teams/topics mentioned)
   - References count (sources cited in description)
   - Captions status (whether SRT file will be uploaded)
   - Thumbnail status (auto-generated or custom)
   - Video file size

5. **Ask the user** to confirm or modify:
   - Title override (optional)
   - Privacy setting (public/unlisted/private - default is public)
   - Thumbnail text override (optional)

6. **Upload the video** (public by default):
   ```bash
   python3 src/youtube_uploader_longform.py --project {project}
   ```
   Or with custom title:
   ```bash
   python3 src/youtube_uploader_longform.py --project {project} --title "Custom Title"
   ```
   Or with different privacy:
   ```bash
   python3 src/youtube_uploader_longform.py --project {project} --privacy unlisted
   ```

7. **Report the result**:
   - Show the YouTube URL
   - Confirm captions were uploaded (if available)
   - Confirm thumbnail was uploaded
   - Confirm upload_info.json was saved

## Thumbnail Generation

The thumbnail generator (`src/thumbnail_generator.py`) creates viral-style thumbnails automatically:

### Auto-Generated Features
- **Smart text extraction**: Pulls catchy phrases from video title
- **Team color detection**: Uses Ferrari red, Red Bull blue, Mercedes teal based on content
- **High contrast overlay**: Dark gradient for text readability
- **Bold typography**: F1-style fonts for brand consistency
- **Channel branding**: Small "F1 BURNOUTS" watermark

### Thumbnail Commands
```bash
# Auto-generate thumbnail (uses script title and auto-detects colors)
python3 src/thumbnail_generator.py --project {project}

# Custom text override
python3 src/thumbnail_generator.py --project {project} --text "FUEL WAR"

# Force specific color scheme
python3 src/thumbnail_generator.py --project {project} --color ferrari
python3 src/thumbnail_generator.py --project {project} --color redbull
python3 src/thumbnail_generator.py --project {project} --color mercedes
python3 src/thumbnail_generator.py --project {project} --color dramatic
python3 src/thumbnail_generator.py --project {project} --color gold
```

### Color Schemes Available
| Scheme | Background | Text | Accent | Best For |
|--------|------------|------|--------|----------|
| `ferrari` | Red (#E8002D) | White | Gold | Ferrari content |
| `redbull` | Blue (#1E41FF) | White | Red | Red Bull content |
| `mercedes` | Teal (#00D2BE) | Black | White | Mercedes content |
| `mclaren` | Orange (#FF8700) | Black | White | McLaren content |
| `dramatic` | Black | White | Red | Controversy, drama |
| `gold` | Dark gray | Gold | White | Championships, legends |
| `default` | Red | White | Gold | General F1 content |

### Viral Thumbnail Best Practices
- **Keep text SHORT**: 2-4 words maximum (e.g., "FUEL WAR", "REVOLUTION", "2026")
- **Use power words**: SHOCKING, REVEALED, SECRET, EPIC, INSANE, BRUTAL
- **High contrast**: Dark backgrounds with bright text
- **Faces work**: If relevant, frames with driver faces get more clicks
- **Avoid clutter**: Clean, simple designs outperform busy thumbnails

## What Gets Uploaded

### Video
- Full 16:9 horizontal video (4K or HD)
- Includes outro with channel branding and CTA

### Description (Auto-Generated)
- Opening summary from first 2-3 script segments
- "ABOUT THIS VIDEO" section
- Chapters (if sections are defined in script)
- **References section** with all cited sources and URLs
- Hashtags: #F1 #Formula1 #Racing #Motorsport

### Tags (Auto-Detected)
- Base tags: F1, Formula1, Racing, Motorsport, Grand Prix
- Driver tags (detected from script): Verstappen, Hamilton, Leclerc, etc.
- Team tags (detected from script): Red Bull, Ferrari, Mercedes, etc.
- Topic tags: World Championship, F1 History, etc.

### Captions
- Uploads `captions.srt` file if present in output folder
- Allows viewers to toggle closed captions on YouTube

### Thumbnail
- **Auto-generated** if not present using `thumbnail_generator.py`
- Size: 1280x720 pixels (16:9 aspect ratio)
- Format: JPEG
- Includes: Bold text, team colors, gradient overlay, branding

## First-time Setup

If YouTube credentials are not configured, guide the user:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable **YouTube Data API v3**
3. Go to Credentials > Create Credentials > OAuth 2.0 Client ID
4. Select "Desktop app" as application type
5. Download the JSON file
6. Save it as: `shared/creds/youtube_client_secrets.json`

First upload will open a browser for Google sign-in to grant YouTube access.

**Note**: The first time you upload after adding caption/thumbnail support, you may need to re-authenticate to grant the additional permissions:
- `youtube.force-ssl` - Required for caption uploads
- `youtube` - Required for thumbnail uploads

To re-authenticate, delete the token file: `rm shared/creds/youtube_token.pickle`

## Example Usage

```
/upload-video sustainable-fuels-2026
```

This will:
1. Read the script from `projects/sustainable-fuels-2026/script.json`
2. **Generate viral thumbnail** with text like "FUEL REVOLUTION" and appropriate colors
3. Generate title: "F1 2026: The Sustainable Fuel Revolution" (or similar)
4. Generate description with:
   - Video summary
   - Chapters (if defined)
   - All source references with URLs
5. Auto-tag: F1, Ferrari, Mercedes, Aramco, Shell, Sustainable Fuel, etc.
6. Detect captions file at `output/captions.srt`
7. Ask for confirmation
8. Upload video, captions, and thumbnail
9. Return the YouTube URL

## Differences from /upload-short

| Feature | /upload-short | /upload-video |
|---------|---------------|---------------|
| Format | 9:16 Vertical | 16:9 Horizontal |
| Duration | ~60 seconds | ~10+ minutes |
| Title suffix | Adds #Shorts | No suffix |
| Description | Summary only | Summary + References + Chapters |
| Captions | Not supported | SRT upload supported |
| Thumbnail | Not supported | **Auto-generated viral thumbnail** |
| References | Not included | Full citations in description |
| Privacy default | public | public |

## Output Files

After successful upload:
- `projects/{project}/output/thumbnail.jpg` - Generated thumbnail
- `projects/{project}/upload_info.json` - Contains:
  ```json
  {
    "video_id": "abc123xyz",
    "url": "https://youtube.com/watch?v=abc123xyz",
    "title": "Video Title",
    "privacy": "public",
    "format": "longform",
    "references_count": 12,
    "captions_uploaded": true,
    "thumbnail_uploaded": true
  }
  ```
