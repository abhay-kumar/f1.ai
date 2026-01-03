# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

F1.ai is an automated pipeline for creating F1-themed YouTube videos. It supports two formats:

1. **Shorts** (60-second vertical videos, 9:16) - Quick, engaging content for mobile
2. **Long-form** (~10-minute horizontal videos, 16:9, up to 4K) - In-depth content with references

Both formats orchestrate: script creation → fact checking → voiceover generation (ElevenLabs) → footage acquisition (yt-dlp) → video assembly (FFmpeg with GPU acceleration) → YouTube upload.

## Common Commands

### Shared Commands (Both Formats)

```bash
# Fact-check script content
python3 src/fact_checker.py --project {name}
python3 src/fact_checker.py --project {name} --web-search --api-key YOUR_KEY
python3 src/fact_checker.py --project {name} --validate-refs  # Check reference coverage (long-form)
python3 src/fact_checker.py --project {name} --suggest-refs --web-search  # Get source suggestions

# Generate voiceovers (concurrent by default)
python3 src/audio_generator.py --project {name}
python3 src/audio_generator.py --project {name} --sequential  # disable concurrency

# Download footage (concurrent by default)
python3 src/footage_downloader.py --project {name}
python3 src/footage_downloader.py --project {name} --workers 5  # custom concurrency
python3 src/footage_downloader.py --project {name} --sequential  # disable concurrency

# Download footage for specific segment with custom query
python3 src/footage_downloader.py --project {name} --segment 0 --query "F1 race highlights"

# Check footage status
python3 src/footage_downloader.py --project {name} --list

# Extract preview frames (concurrent by default)
python3 src/preview_extractor.py --project {name}
```

### Shorts Commands (9:16 Vertical)

```bash
# Assemble short video (1080x1920)
python3 src/video_assembler.py --project {name}
python3 src/video_assembler.py --project {name} --encoder nvenc  # NVIDIA GPU
python3 src/video_assembler.py --project {name} --encoder cpu    # CPU fallback

# Upload short to YouTube
python3 src/youtube_uploader.py --project {name} --dry-run      # Preview metadata
python3 src/youtube_uploader.py --project {name}                 # Upload
```

### Long-Form Commands (16:9 Horizontal, 4K/HD)

```bash
# Assemble long-form video (4K: 3840x2160 or HD: 1920x1080)
python3 src/video_assembler_longform.py --project {name}                    # 4K default
python3 src/video_assembler_longform.py --project {name} --resolution hd    # 1080p
python3 src/video_assembler_longform.py --project {name} --encoder hevc     # HEVC codec
python3 src/video_assembler_longform.py --project {name} --no-credits       # Skip end credits
python3 src/video_assembler_longform.py --project {name} --workers 8        # Custom concurrency

# Upload long-form video to YouTube (includes references in description)
python3 src/youtube_uploader_longform.py --project {name} --dry-run  # Preview metadata
python3 src/youtube_uploader_longform.py --project {name}             # Upload
```

## Architecture

**Pipeline Flow:**
```
script.json → fact_check → audio/*.mp3 → footage/*.mp4 → previews/*.jpg → output/final.mp4 → YouTube
```

**Core Modules (`src/`):**
- `config.py` - Centralized settings, API keys, F1 team colors, video specs (shorts + long-form)
- `fact_checker.py` - Script validation with knowledge base, web search, and **reference validation**
- `audio_generator.py` - ElevenLabs TTS with caching and **concurrent processing**
- `footage_downloader.py` - yt-dlp YouTube search/download with **concurrent downloads**
- `preview_extractor.py` - Frame extraction with **concurrent processing**
- `video_assembler.py` - Shorts: 9:16 vertical FFmpeg composition with GPU acceleration
- `video_assembler_longform.py` - Long-form: 16:9 horizontal, 4K/HD with **end credits**
- `youtube_uploader.py` - Shorts: OAuth upload with #Shorts hashtag
- `youtube_uploader_longform.py` - Long-form: Standard video upload with **references in description**

**Project Structure:**
```
projects/{name}/
├── script.json      # Segments with text, footage_query, footage_start
├── audio/           # Generated voiceovers (segment_00.mp3, ...)
├── footage/         # Downloaded clips (segment_00.mp4, ...)
├── previews/        # Frame extractions for QA
├── output/          # Final video (final.mp4)
└── upload_info.json # YouTube video ID and URL after upload
```

**External Dependencies:**
- ffmpeg/ffprobe (video processing)
- yt-dlp (YouTube download)
- ElevenLabs API (TTS)
- YouTube Data API v3 (upload)
- SerpAPI (fact checking web search, optional)

## Critical Technical Notes

1. **Always verify footage with previews** - YouTube search often returns incorrect videos; run preview_extractor and visually check before assembly
2. **30fps is mandatory** - Mixed framerates cause audio/video desync; video_assembler enforces this
3. **FFmpeg split filter required** - Cannot consume the same stream twice in filter graphs
4. **Re-encode during concat** - Stream copy corrupts timestamps with mixed source formats
5. **Cache awareness** - Audio files are cached; delete segment MP3 to regenerate
6. **Duration validation** - Assembly verifies video/audio durations match within 1 second

## Performance Features

### Concurrency
All pipeline stages support concurrent processing by default:
- **Audio generation**: 4 concurrent API calls (ElevenLabs rate-limit friendly)
- **Footage download**: 3 concurrent downloads (YouTube respectful)
- **Video assembly**: CPU core count workers for parallel segment encoding
- **Preview extraction**: 4 concurrent frame extractions

Use `--sequential` flag on any command to disable concurrency for debugging.
Use `--workers N` to customize the concurrency level.

### GPU Acceleration
Video encoding automatically detects and uses GPU acceleration:
- **macOS**: VideoToolbox (Metal) - `h264_videotoolbox`
- **Linux/Windows with NVIDIA**: NVENC (CUDA) - `h264_nvenc`
- **Fallback**: CPU encoding with libx264

Force a specific encoder with `--encoder [auto|videotoolbox|nvenc|cpu]`

## Quality Assurance Features

### Fact Checking (`fact_checker.py`)
Validates F1 script content against:
- Built-in F1 knowledge base (champions, teams, records, famous moments)
- Optional web search verification (requires SerpAPI key)

```bash
python3 src/fact_checker.py --project {name} --strict  # Exit non-zero if unverified claims
```

## script.json Format

### Shorts Format (Basic)

```json
{
  "title": "Video Title",
  "duration_target": 60,
  "segments": [
    {
      "id": 1,
      "text": "Voiceover narration text",
      "context": "Editorial note (not rendered)",
      "footage_query": "YouTube search terms",
      "footage_start": 55,
      "footage": "segment_00.mp4"
    }
  ]
}
```

### Long-Form Format (With References)

```json
{
  "title": "The Rise of Max Verstappen",
  "format": "longform",
  "resolution": "4k",
  "duration_target": 600,
  "segments": [
    {
      "id": 1,
      "section": "intro",
      "text": "At just seventeen years old, Max Verstappen became the youngest driver ever to compete in Formula One.",
      "context": "Opening hook",
      "footage_query": "Verstappen F1 debut 2015",
      "footage_start": 45,
      "references": [
        {
          "claim": "Youngest driver ever to compete in F1 at seventeen",
          "source": "Formula 1 Official",
          "url": "https://www.formula1.com/en/drivers/max-verstappen.html",
          "date": "2024-01-15"
        }
      ]
    }
  ],
  "references_summary": [
    {
      "source": "Formula 1 Official",
      "url": "https://www.formula1.com",
      "claims_supported": [1, 3, 5]
    }
  ]
}
```

**Key Fields:**
- `footage_start`: Timestamp (seconds) in source footage to begin extraction
- `section`: Organize segments (intro, main, conclusion) - used for YouTube chapters
- `references`: Sources for factual claims - displayed in end credits and description
- `references_summary`: Consolidated source list for the entire video

## Long-Form Video Features

- **4K/HD Resolution**: 3840x2160 or 1920x1080, 16:9 horizontal
- **Higher Bitrate**: 20Mbps (4K) or 12Mbps (HD) for quality
- **End Credits**: Auto-generated with sources/references
- **Reference Tracking**: Every factual claim should have a source
- **YouTube Chapters**: Generated from section names
- **Description with Sources**: All references included in upload
