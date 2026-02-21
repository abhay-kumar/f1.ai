# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

F1.ai is an automated pipeline for creating F1-themed content. It supports five formats:

1. **Shorts** (60-second vertical videos, 9:16) - Quick, engaging content for mobile
2. **Long-form** (~10-minute horizontal videos, 16:9, up to 4K) - In-depth content with references
3. **Podcasts** (~20-minute audio episodes) - Engaging monologue-style content for RSS.com/Spotify
4. **Animated videos** (Remotion) - Programmatic React animations synced to voiceover for technical explainers
5. **Carousels** (Instagram multi-image posts, 1080x1080) - Professional swipeable slide decks for Instagram

**Video formats** orchestrate: script creation → fact checking → voiceover generation (Gemini TTS / ElevenLabs) → footage acquisition (yt-dlp) → video assembly (FFmpeg with GPU acceleration) → YouTube + Instagram upload.

**Animated video format** orchestrates: script creation → TTS generation → VTT transcript parsing → Remotion animation composition → frame-by-frame rendering → video output.

**Podcast format** orchestrates: script creation → single-request TTS generation (Gemini) → music mixing (intro/outro) → RSS.com upload.

**Carousel format** orchestrates: content sourcing (Reddit/web/text) → script creation → image sourcing → HTML/CSS slide rendering (Playwright) → manual Instagram upload.

## Common Commands

### Shared Commands (Both Formats)

```bash
# Fact-check script content
python3 src/fact_checker.py --project {name}
python3 src/fact_checker.py --project {name} --web-search --api-key YOUR_KEY
python3 src/fact_checker.py --project {name} --validate-refs  # Check reference coverage (long-form)
python3 src/fact_checker.py --project {name} --suggest-refs --web-search  # Get source suggestions

# Generate voiceovers (Gemini TTS by default, free)
python3 src/audio_generator.py --project {name}
python3 src/audio_generator.py --project {name} --engine elevenlabs  # paid fallback
python3 src/audio_generator.py --project {name} --voice Charon       # different Gemini voice
python3 src/audio_generator.py --project {name} --sequential         # disable concurrency

# Download footage (concurrent by default)
python3 src/footage_downloader.py --project {name}
python3 src/footage_downloader.py --project {name} --4k          # 4K resolution (2160p)
python3 src/footage_downloader.py --project {name} --workers 5   # custom concurrency
python3 src/footage_downloader.py --project {name} --sequential  # disable concurrency
python3 src/footage_downloader.py --project {name} --google-search              # Use Google for better search results
python3 src/footage_downloader.py --project {name} --validate                   # Validate footage with Gemini vision
python3 src/footage_downloader.py --project {name} --google-search --validate   # Both (recommended for accuracy)

# Download footage for specific segment (auto-downloads top result)
python3 src/footage_downloader.py --project {name} --segment 0 --query "F1 race highlights"

# Download footage for a specific shot within a segment
python3 src/footage_downloader.py --project {name} --segment 0 --shot 2 --query "Mercedes F1 power unit"

# Preview candidates without downloading
python3 src/footage_downloader.py --project {name} --segment 0 --query "F1 race highlights" --dry-run

# Check footage status (shows per-shot status for multi-shot segments)
python3 src/footage_downloader.py --project {name} --list

# Download footage sequentially in isolated subprocesses (fallback when Python downloader hangs)
bash src/download_footage.sh {name}                    # All segments with footage_query
bash src/download_footage.sh {name} "0 1 3 6 8"       # Specific segments only

# Extract preview frames (concurrent by default)
python3 src/preview_extractor.py --project {name}

# Fetch trending Reddit posts with media (for content discovery)
python3 src/reddit_fetcher.py --top day --limit 25           # Top posts from past 24 hours
python3 src/reddit_fetcher.py --top week --limit 25          # Top posts from past week
python3 src/reddit_fetcher.py --hot --limit 10               # Currently trending
python3 src/reddit_fetcher.py --top day --media-only         # Only posts with media
python3 src/reddit_fetcher.py --post "https://reddit.com/r/formula1/comments/..."  # Specific post
python3 src/reddit_fetcher.py --test                         # Test connectivity (no API key needed)
```

### Shorts Commands (9:16 Vertical)

```bash
# Assemble short video (1080x1920)
python3 src/video_assembler.py --project {name}
python3 src/video_assembler.py --project {name} --encoder nvenc  # NVIDIA GPU
python3 src/video_assembler.py --project {name} --encoder cpu    # CPU fallback

# Upload short to YouTube + Instagram
python3 src/youtube_uploader.py --project {name} --dry-run      # Preview metadata
python3 src/youtube_uploader.py --project {name}                 # Upload to YouTube
python3 src/instagram_uploader.py --project {name} --dry-run    # Preview caption
python3 src/instagram_uploader.py --project {name}               # Upload to Instagram
```

### Long-Form Commands (16:9 Horizontal, 4K/HD)

```bash
# RECOMMENDED: Advanced visual assembler with YouTube-first approach
python3 src/image_video_assembler.py --project {name}                     # 4K default
python3 src/image_video_assembler.py --project {name} --resolution hd     # 1080p output
python3 src/image_video_assembler.py --project {name} --veo3              # Enable Veo3 AI video
python3 src/image_video_assembler.py --project {name} --analyze           # Preview visual routing
python3 src/image_video_assembler.py --project {name} --no-music          # Skip background music
python3 src/image_video_assembler.py --project {name} --no-sfx            # Skip transition SFX
python3 src/image_video_assembler.py --project {name} --no-intro          # Skip animated logo intro

# Visual types (automatically routed based on script content):
# - youtube_clip: YouTube footage as primary visual source (YouTube-first approach)
# - f1_image: High-quality F1 photos from Pexels/Unsplash with Ken Burns effects (fallback)
# - quote_overlay: Speaker image + quote text
# - veo3_video: AI-generated video for abstract concepts (requires --veo3 flag)
#
# Post-processing features (automatic):
# - Color grading: B&W, vintage, cinematic, warm, cool (auto-detected from script context)
# - Transition SFX: Swoosh sounds between segments
# - Animated intro: Logo animation with engine rev SFX
# - Context-aware music: Dynamic volume based on segment mood

# Alternative: Footage-based assembly (downloads YouTube videos)
python3 src/video_assembler_longform.py --project {name}                    # 4K default
python3 src/video_assembler_longform.py --project {name} --resolution hd    # 1080p
python3 src/video_assembler_longform.py --project {name} --with-text        # Add burned-in captions

# Upload long-form video to YouTube (includes references in description)
python3 src/youtube_uploader_longform.py --project {name} --dry-run  # Preview metadata
python3 src/youtube_uploader_longform.py --project {name}             # Upload
```

### Animated Video Commands (Remotion)

```bash
# Setup: Clone shared template into project
cp -r shared/remotion-template projects/{name}/video
cd projects/{name}/video && npm install

# Concatenate audio chunks for Remotion
ffmpeg -f concat -safe 0 -i <(for f in ../audio/chunk_*.mp3; do echo "file '$(cd .. && pwd)/audio/$(basename $f)'"; done) -c:a libmp3lame -b:a 256k public/audio.mp3

# Preview in browser (Remotion Studio)
npm run dev

# Quick preview render (first 3 seconds)
npm run preview

# Full HD render (1920x1080, ~15min for 17min video)
npm run render
# Or with explicit options:
npx remotion render F1Video --output output/final.mp4 --codec h264 --concurrency 4 --video-bitrate 12M

# Background render (won't block terminal)
nohup npx remotion render F1Video --output output/final.mp4 --codec h264 --concurrency 4 > /tmp/render.log 2>&1 &
tail -f /tmp/render.log

# 4K render
npm run build:4k
```

**Key files to customize per project:**
- `src/data/segments.ts` — Segment timing from VTT transcript, animation type mapping
- `src/components/SegmentRenderer.tsx` — Animation router (which component for which segment)
- `src/animations/*.tsx` — Animation components (15+ reusable, or create new ones)

**See `shared/remotion-template/REMOTION_GUIDE.md` for full documentation.**

### Podcast Commands (Audio Only)

```bash
# Generate podcast audio (RECOMMENDED: chunked mode prevents voice degradation)
python3 src/gemini_podcast_audio_generator.py --project {name} --chunked
python3 src/gemini_podcast_audio_generator.py --project {name} --chunked --voice Kore  # Different voice
python3 src/gemini_podcast_audio_generator.py --project {name} --chunked --model pro   # Pro model (paid)
python3 src/gemini_podcast_audio_generator.py --project {name} --preview  # Preview transcript

# Add intro/outro music (always use --output to write directly to final.mp3)
python3 src/podcast_music_mixer.py --project {name} \
  --music shared/music/podcast_default.mp3 \
  --documentary \
  --output projects/{name}/output/final.mp3

# Preview music placement without processing
python3 src/podcast_music_mixer.py --project {name} --dry-run
```

### Carousel Commands (Instagram Multi-Image Posts)

```bash
# Generate carousel slides (1080x1080 JPEG)
python3 src/carousel_generator.py --project {name}
python3 src/carousel_generator.py --project {name} --theme ferrari    # Override theme
python3 src/carousel_generator.py --project {name} --slide 3          # Regenerate single slide
python3 src/carousel_generator.py --project {name} --list             # Preview slide plan
```

## Architecture

**Pipeline Flow:**
```
script.json → fact_check → audio/*.mp3 → footage/*.mp4 → previews/*.jpg → output/final.mp4 → YouTube
```

**Core Modules (`src/`):**
- `config.py` - Centralized settings, API keys, F1 team colors, video specs (shorts + long-form)
- `fact_checker.py` - Script validation with knowledge base, web search, and **reference validation**
- `audio_generator.py` - Gemini TTS (default, free) / ElevenLabs TTS with caching and **concurrent processing**
- `gemini_podcast_audio_generator.py` - **Podcast**: Single-request TTS for voice consistency
- `podcast_music_mixer.py` - **Podcast**: Intro/outro music mixing with FFmpeg
- `reddit_fetcher.py` - Reddit OAuth2 API: fetch r/formula1 posts + extract media (images, GIFs, videos, galleries)
- `footage_downloader.py` - yt-dlp YouTube search/download with **concurrent downloads**, 4K support, per-shot downloads, **Reddit media priority**
- `shot_assembler.py` - Shared shot list logic: timing calculation, clip creation, transition stitching (used by both assemblers)
- `stock_image_fetcher.py` - Pexels/Unsplash API for stock photos, Google Images for person portraits
- `google_image_search.py` - Playwright-based Google Images scraper + Google-for-YouTube search
- `gemini_vision_validator.py` - Gemini Flash vision validation for footage accuracy (thumbnail + file validation)
- `image_video_assembler.py` - **Long-form**: YouTube-first visual routing with color grading, transition SFX, animated intro, context-aware music
- `color_grader.py` - FFmpeg color grading presets (B&W, vintage, cinematic, warm, cool)
- `intro_generator.py` - Animated logo intro with engine rev + swoosh SFX
- `veo3_generator.py` - Google Veo3 AI video generation for abstract concepts
- `download_footage.sh` - Sequential footage downloader in isolated subprocesses (fallback for hangs/memory leaks)
- `video_assembler.py` - Shorts: 9:16 vertical FFmpeg composition with GPU acceleration
- `video_assembler_longform.py` - Long-form: 16:9 horizontal with YouTube footage (legacy)
- `carousel_generator.py` - **Carousel**: HTML/CSS slide rendering via Playwright, 14 themes, 6 slide types
- `youtube_uploader.py` - Shorts: OAuth upload with #Shorts hashtag
- `instagram_uploader.py` - Shorts: Instagram Reels upload via instagrapi
- `youtube_uploader_longform.py` - Long-form: Standard video upload with **references in description**

**Project Structure (Video):**
```
projects/{name}/
├── script.json      # Segments with text, shots array, footage_query, footage_start
├── audio/           # Generated voiceovers (segment_00.mp3, ...)
├── footage/         # Downloaded clips (segment_00.mp4, segment_00_shot_01.mp4, ...)
├── previews/        # Frame extractions for QA (seg00_shot00_t000.jpg, ...)
├── output/          # Final video (final.mp4)
└── upload_info.json # YouTube + Instagram URLs after upload
```

**Project Structure (Podcast):**
```
projects/{name}/
├── script.json           # Segments with text, context, emotion
└── output/
    ├── final.mp3         # Final podcast with intro/outro music
    ├── cover_art.jpg     # Podcast cover (1400x1400 or 3000x3000)
    └── transcript.vtt    # WebVTT transcript for RSS.com
```

**Project Structure (Animated Video - Remotion):**
```
projects/{name}/
├── script.json      # Segments with text, context, emotion
├── audio/           # Generated voiceovers (chunk_000.mp3, ...)
├── output/
│   ├── transcript.vtt  # VTT timestamps (used for segment timing)
│   └── final.mp3       # Podcast output (if dual-format)
└── video/           # Remotion project (cloned from shared/remotion-template)
    ├── public/
    │   └── audio.mp3   # Concatenated audio for video
    ├── src/
    │   ├── data/segments.ts      # Segment timing + animation mapping
    │   ├── components/           # Background, SubtitleBar, Transitions, SegmentRenderer
    │   └── animations/           # 15+ animation components
    └── output/
        └── final.mp4             # Rendered video
```

**Project Structure (Carousel):**
```
projects/{name}/
├── script.json      # Slides with type, content, theme (format: "carousel")
├── images/          # Source images (backgrounds, portraits)
└── output/
    ├── slide_01.jpg  # Cover slide (1080x1080)
    ├── slide_02.jpg  # Content slides...
    └── slide_NN.jpg  # CTA slide (auto-appended, always last)
```

**Remotion Shared Template (`shared/remotion-template/`):**
- Reusable scaffold for any animated F1 video
- Clone into project with `cp -r shared/remotion-template projects/{name}/video`
- Contains 15+ animation components, team colors, background system
- See `shared/remotion-template/REMOTION_GUIDE.md` for full docs

**External Dependencies:**
- ffmpeg/ffprobe (video processing)
- yt-dlp (YouTube download - for shorts) + PO Token plugins (see below)
- Google Gemini TTS API (free tier, `pip install google-genai`)
- ElevenLabs API (TTS, paid fallback)
- Pexels API (stock images - for long-form)
- Unsplash API (fallback stock images - optional)
- YouTube Data API v3 (upload)
- instagrapi (Instagram Reels upload, `pip install instagrapi`)
- SerpAPI (fact checking web search, optional)
- OpenAI API (DALL-E graphics - optional)
- Playwright (`pip install playwright && playwright install chromium` - Google search scraping for `--google-search`)
- Google Gemini Flash vision (free tier via `google-genai` - footage validation for `--validate`)
- Reddit public .json endpoints (no API key, ~10 RPM unauthenticated)
- Remotion (`npm install remotion @remotion/cli` - animated video rendering)
- Node.js (required for Remotion)

## Critical Technical Notes

1. **Always verify footage with previews** - YouTube search often returns incorrect videos; run preview_extractor and visually check before assembly
2. **30fps is mandatory** - Mixed framerates cause audio/video desync; video_assembler enforces this
3. **FFmpeg split filter required** - Cannot consume the same stream twice in filter graphs
4. **Re-encode during concat** - Stream copy corrupts timestamps with mixed source formats
5. **Cache awareness** - Audio files are cached; delete segment MP3 to regenerate
6. **Duration validation** - Assembly verifies video/audio durations match within 1 second

## Footage Sourcing Lessons

1. **Always prefer official F1 channel** - Fan channels (e.g., USA SportsLine, Saile Racing) often have screen recordings with visible cursors, news anchors, or low-quality re-uploads. Official FORMULA 1 channel footage is consistently clean and high quality.
2. **Use broad official videos + transcript search for specific teams** - Searching for a specific team's car launch often returns fan re-uploads. Instead, download a broad official video (e.g., "2026 F1 Barcelona Shakedown highlights") and use `yt-dlp --write-auto-sub` to extract subtitles, then grep for the team name to find the exact timestamp.
3. **Subtitle-based timestamp finding**:
   ```bash
   # Download subtitles and find where a team/driver appears
   yt-dlp --write-auto-sub --sub-lang en --skip-download --sub-format vtt -o /tmp/subs "https://youtube.com/watch?v=VIDEO_ID"
   grep -i "alpine" /tmp/subs*.vtt  # Shows timestamps where "alpine" is mentioned
   ```
4. **Add 1-2 seconds buffer to subtitle timestamps** - Video content often doesn't match narration exactly. When subtitles mention a team at timestamp X, the visual may still show the previous team for 1-2 seconds. Always add a small buffer (e.g., use 242s instead of 240s) to ensure the correct team is visible when the segment starts.
5. **Delete previews before re-extracting** - Preview images are cached. After replacing footage, delete old previews (`rm previews/segNN_*.jpg`) before running preview_extractor, otherwise stale images will be shown.
6. **Delete footage before re-downloading** - `yt-dlp` may skip download if a file already exists at the output path. Always `rm` the old file first when re-downloading a segment.
7. **Use `--list` to verify downloads** - After bulk download, run `--list` to see the actual YouTube video titles. This catches mismatches instantly without needing to open preview images (e.g., "Scuderia Ferrari SF-26" when you wanted Alpine).
8. **Ensure all segments have `footage` key** - Set the `footage` field for ALL segments in script.json at creation time (e.g., `"footage": "segment_00.mp4"`). The assembler will fallback to the convention `segment_{idx:02d}.mp4` if missing, but setting it explicitly is best practice. The footage_downloader now also sets this field for cached segments.
9. **Compilation videos often serve wrong content for multiple segments** - The bulk downloader may download the same YouTube compilation (e.g., "Day 2 Highlights") for two different segments. The downloader now warns about duplicates. When this happens, one segment will have correct content at the right timestamp, but the other may have NO relevant content at all. Always verify with subtitle search, especially when `--list` shows the same title for multiple segments.
10. **Use ImageMagick color analysis to verify team footage programmatically** - When preview JPGs can't be visually inspected, extract a frame and analyze dominant colors:
    ```bash
    ffmpeg -y -ss {timestamp} -i footage/segment_XX.mp4 -vframes 1 -q:v 2 /tmp/check.jpg
    magick /tmp/check.jpg -resize 100x100 -colors 5 -unique-colors -format '%c' histogram:info:-
    # Red (168,66,49) = Ferrari, Dark blue (42,44,66) = Red Bull,
    # Silver/teal (77,89,93) = Mercedes, Green (26,46,36) = Aston Martin,
    # Blue (35,56,81) = Alpine, Papaya (255,135,0) = McLaren
    ```

## Footage Validation (`--google-search --validate`)

The footage downloader supports Google-powered search and Gemini Flash vision validation to improve footage accuracy. Without these flags, yt-dlp `ytsearch` keyword matching and Pexels stock photos often return wrong content (0% accuracy on daily news shorts).

### How It Works

1. **`--google-search`**: Uses Playwright headless Chromium to scrape Google Images (for `image` shots) and Google `site:youtube.com` search (for `youtube_clip` shots) before falling back to Pexels/ytsearch. Google results are significantly more accurate for specific people, teams, and events.

2. **`--validate`**: Before downloading a video, validates each candidate's YouTube thumbnail with Gemini Flash vision. Only downloads the full video for the first thumbnail that passes validation. For images, downloads and validates each candidate directly. Forces sequential mode (Gemini rate limits).

### Validation Flow
```
Image shots:  Google Images → download each → Gemini validate → accept/reject → Pexels fallback
Video shots:  Google YouTube → ytsearch → validate thumbnails → download winner
All fail:     Download best-confidence candidate as "unverified"
```

### Performance
- Without flags: ~45s (concurrent)
- `--google-search` only: ~60s (adds Playwright scraping)
- `--google-search --validate`: ~3-5min (adds Gemini calls, sequential mode, but thumbnail validation avoids unnecessary video downloads)

### Standalone Validation
```bash
# Validate a single file against expected content
python3 src/gemini_vision_validator.py --file path/to/file.mp4 --expected "Red Bull RB22 on track" --query "Red Bull F1 2026"

# Validate all shots in a project
python3 src/gemini_vision_validator.py --project {name}
```

### Known Limitations
- Google regular search triggers CAPTCHAs frequently; Google Images works more reliably
- YouTube thumbnails don't always represent video content at `footage_start` timestamp
- Gemini free tier is 15 RPM — validation adds ~4s per candidate
- Niche queries (specific car models, technical concepts) often fail all candidates

## Daily News Shorts Lessons

1. **Pronunciation vs spelling in script.json** - The `text` field is used for BOTH audio generation AND text overlay. If you respell a name for pronunciation (e.g., "Laurent" → "Lorahn"), the misspelling will appear on screen. Instead, fix pronunciation in the `text` field, generate the audio with the phonetic spelling, then restore the correct spelling before video assembly. The cached MP3s won't regenerate as long as the files exist.
2. **Shot lists for visual storytelling** - When a segment covers multiple topics (e.g., a person + a concept), use the `shots` array in script.json to define multiple visual beats per segment. Each shot maps to a `text_cue` substring and gets its own footage/image. The assembler handles timing and transitions automatically. See "Shot List (Multi-Visual Segments)" in the script.json format section.
3. **Blurred background aspect ratio fix** - The common `scale=1080:-2` for foreground in 9:16 frame causes stretching on some sources. For 16:9 (1920x1080) sources, explicitly use `scale=1080:608` to maintain correct aspect ratio instead of relying on `-2` auto-calculation.
4. **Skip jittery interview cuts** - Interview footage from YouTube often has abrupt transitions at clip boundaries. Always preview the first 1-2 seconds of interview clips and add offset to skip any jitter (e.g., start at 525s instead of 524s).
5. **Use official team/manufacturer videos for technical topics** - For power unit, engine, or technical regulation topics, use official team channels (Mercedes "Road to 2026", Honda PU Launch) or the official F1 channel's explainer videos. These have clean CGI animations and diagrams that work much better than on-track footage for technical concepts.
6. **Photo sourcing for F1 personnel** - F1 Fandom Wiki has photos of team principals and senior staff. Wikipedia has photos of high-profile figures (e.g., Horner). Behind-the-scenes personnel (HR directors, junior engineers) often have no publicly available photos.
7. **Fandom Wiki images are WebP** - Despite `.jpg` URLs, Fandom serves WebP format. Convert with FFmpeg after download.
8. **Instagram challenge_required** - Instagram may trigger security challenges on upload. The user needs to approve login from the Instagram app before retrying.

## Shorts: 16:9 Video in 9:16 Frame (Blurred Background)

When using horizontal (16:9) footage in vertical (9:16) shorts, use a **blurred background** instead of black bars or stretching:

```bash
# FFmpeg filter for blurred background effect (like typical YouTube Shorts)
ffmpeg -y -ss {start} -i source.mp4 -t {duration} -filter_complex "
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:20[bg];
[0:v]scale=1080:608[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2
" -c:v h264_videotoolbox -pix_fmt yuv420p -r 30 -an output.mp4
```

**How it works:**
1. Creates a blurred, scaled-up version of the video as background (`[bg]`)
2. Scales the original video to fit width (`[fg]`)
3. Overlays the sharp video centered on the blurred background

**Important:** Always create footage 2-3 seconds longer than the audio duration to avoid freeze at the end of segments.

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
      "visual": "Scene description for storyboard review and footage search guidance",
      "footage_query": "YouTube search terms",
      "footage_start": 55,
      "footage": "segment_00.mp4"
    }
  ]
}
```

### Shorts Format (With Shot List)

```json
{
  "title": "Video Title",
  "duration_target": 60,
  "segments": [
    {
      "id": 1,
      "text": "Alpine switched from Renault engines despite backlash from Enstone to Mercedes for 2026 and looks quick.",
      "context": "Alpine engine switch story",
      "shots": [
        {
          "label": "Alpine on track with Renault PU",
          "text_cue": "Alpine switched from Renault engines",
          "source_type": "youtube_clip",
          "footage_query": "Alpine A525 Renault engine 2025 F1",
          "footage_start": 30,
          "transition_in": "cut"
        },
        {
          "label": "Enstone factory/protests",
          "text_cue": "despite backlash from Enstone",
          "source_type": "image",
          "image_query": "Enstone F1 factory Alpine",
          "ken_burns": "zoom_in",
          "transition_in": "cross_dissolve"
        },
        {
          "label": "Mercedes PU deal",
          "text_cue": "to Mercedes for 2026",
          "source_type": "youtube_clip",
          "footage_query": "Mercedes F1 power unit 2026",
          "footage_start": 15,
          "transition_in": "wipe_left"
        },
        {
          "label": "New Alpine car testing",
          "text_cue": "and looks quick",
          "source_type": "youtube_clip",
          "footage_query": "Alpine 2026 testing fast lap",
          "footage_start": 45,
          "transition_in": "cut"
        }
      ]
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
- `visual`: Scene description for storyboard review and footage search guidance (optional)
- `footage_start`: Timestamp (seconds) in source footage to begin extraction
- `section`: Organize segments (intro, main, conclusion) - used for YouTube chapters
- `references`: Sources for factual claims - displayed in end credits and description
- `references_summary`: Consolidated source list for the entire video
- `color_grade`: Override auto-detected grade (`bw`, `vintage`, `cinematic`, `warm`, `cool`, `none`)
- `music_mood`: Override music volume (`uplifting`, `atmospheric`, `default`)
- `transition_sfx`: Override transition sound (`swoosh`, `fade`)
- `shots`: Array of shot objects for multi-visual segments (see Shot List below)
- `reddit_media_url`: Direct URL to Reddit media (image, GIF-as-MP4, or video). Downloaded first by footage_downloader.
- `reddit_media_type`: Type of Reddit media: `"image"`, `"video"`, or `"gif"`

### Shot List (Multi-Visual Segments)

Each segment can contain a `shots` array to break narration into multiple visual beats. If `shots` is absent, existing fields (`footage_query`, `footage`, `footage_start`) are treated as a single implicit shot -- zero changes needed for existing scripts.

**Shot Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | yes | Human-readable shot description for storyboard review |
| `text_cue` | string | yes | Exact substring of segment `text` this shot covers (used for proportional timing) |
| `source_type` | enum | yes | `youtube_clip`, `image`, `quote_overlay`, `veo3_video`, `remotion_animation`, `graphic` |
| `footage_query` | string | for youtube_clip | YouTube search query |
| `footage_start` | int | no | Start timestamp in source video (seconds) |
| `footage` | string | no | Downloaded filename. Convention: `segment_XX_shot_YY.mp4`. Set by downloader. |
| `image_query` | string | for image | Stock image search query (Pexels/Unsplash) |
| `ken_burns` | enum | no | `zoom_in`, `zoom_out`, `pan_left`, `pan_right`. Default: random. |
| `transition_in` | enum | no | How to enter this shot. Default: `cut`. |
| `transition_duration` | float | no | Override default transition duration (seconds) |
| `color_grade` | enum | no | Per-shot: `bw`, `vintage`, `cinematic`, `warm`, `cool`, `none` |
| `speaker_name` | string | for quote_overlay | Speaker name |
| `quote_text` | string | for quote_overlay | Quote text |
| `veo3_prompt` | string | for veo3_video | Veo3 generation prompt |
| `animation_type` | string | for remotion_animation | Remotion component name |
| `duration_weight` | float | no | Override proportional timing |

**Available Transitions:**

| Name | FFmpeg xfade | Default Duration | When to Use |
|------|-------------|-----------------|-------------|
| `cut` | (none) | 0s | Default. Most shot changes. |
| `cross_dissolve` | `fade` | 0.4s | Between related shots, topic continuity |
| `wipe_left` | `wipeleft` | 0.3s | Topic changes, forward progression |
| `wipe_right` | `wiperight` | 0.3s | Flashbacks, reversals |
| `whip_pan` | `smoothleft` | 0.2s | Fast-paced, energetic transitions |
| `fade_to_black` | `fadeblack` | 0.3s | Section endings, dramatic pauses |
| `slide_left` | `slideleft` | 0.3s | Comparisons, before/after |
| `circle_open` | `circleopen` | 0.4s | Reveals, dramatic openings |
| `circle_close` | `circleclose` | 0.4s | Scene endings, closings |

**Timing:** Shot timing is proportional to `text_cue` character position within segment `text`. Speech rate is roughly proportional to character count, and the human eye tolerates +/- 0.5s of visual-audio misalignment. Minimum shot duration: 1.5s (shorts), 2.0s (long-form).

**Footage naming:** Multi-shot footage uses `segment_XX_shot_YY.mp4` (or `.jpg` for images). The first shot (index 0) uses the legacy `segment_XX.mp4` name for backwards compatibility.

**Guidelines:**
- Aim for 2-4 shots per segment (shorts), 3-6 shots per segment (long-form)
- Ensure `text_cue` values cover all of the segment's `text` without gaps
- Use `cut` for most transitions; reserve dissolves/wipes for topic changes or dramatic moments
- Use `image` source_type for less-known people, factory exteriors, or when no YouTube footage exists
- Use `quote_overlay` when directly quoting a person
- Use `veo3_video` or `remotion_animation` for abstract/scientific concepts

### Podcast Format

```json
{
  "title": "F1 Burnouts: The Fuel Revolution",
  "format": "podcast",
  "duration_target": 1200,
  "tts_engine": "gemini",
  "voice": "Charon",
  "host": {
    "name": "Host",
    "description": "The host of F1 Burnouts - engineering expert and F1 historian"
  },
  "segments": [
    {
      "id": 1,
      "text": "Welcome back to F1 Burnouts! Today we're diving into...",
      "context": "Intro hook",
      "emotion": "energetic"
    },
    {
      "id": 2,
      "text": "[sarcastic] And in news that shocked absolutely no one...",
      "context": "Main topic",
      "emotion": "humorous"
    }
  ]
}
```

**Key Fields:**
- `emotion`: Segment mood (energetic, intrigued, contemplative, humorous, sarcastic, heartfelt, serious, passionate)
- `context`: Editorial note for organization (not spoken)
- Inline emotion markers: `[excited]`, `[sarcastic]`, `[whispering]`, `[laughing]`, etc.

### Carousel Format

```json
{
  "title": "5 Things About Ferrari's 2026 Car",
  "format": "carousel",
  "theme": "ferrari",
  "source_url": "https://reddit.com/r/formula1/comments/...",
  "slides": [
    {
      "type": "cover",
      "headline": "5 Things You Didn't Know About Ferrari's 2026 Car",
      "subheadline": "Swipe to find out"
    },
    {
      "type": "content",
      "number": 1,
      "heading": "The Engine is Revolutionary",
      "body": "Ferrari's new power unit delivers 350kW of electrical power."
    },
    {
      "type": "content_stat",
      "stat": "350kW",
      "label": "Electrical power output — 3x more than 2025"
    },
    {
      "type": "content_quote",
      "quote": "This is the most ambitious project in Ferrari's history.",
      "speaker": "Fred Vasseur",
      "role": "Ferrari Team Principal"
    },
    {
      "type": "content_image",
      "heading": "The SF-26 on track at Fiorano",
      "background_image": "images/fiorano.jpg"
    }
  ]
}
```

**Key Fields:**
- `type`: Slide type — `cover`, `content`, `content_stat`, `content_quote`, `content_image`
- `theme`: Auto-detected from content or manual — 10 F1 teams + `dramatic`, `gold`, `breaking`, `stats`
- CTA slide is auto-appended by the generator (not in script.json)
- `background_image`: URL or local path — downloaded to `images/` automatically
- `speaker_image`: Portrait URL for quote slides (optional)

## Carousel Lessons

1. **Use `\n` for vertical lists in body text** — Steps, numbered lists, and bullet points should use newline characters in the `body` field. The generator converts `\n` to `<br>` for proper vertical layout. A wall of "Step 1: ... Step 2: ... Step 3: ..." reads terribly on Instagram — each step needs its own line.
2. **Memes should use real meme templates, not infographic slides** — The `content_meme` slide type generates clean comparison panels, but for actual internet memes (e.g., "They're the same picture" Pam), use the real template image and composite with FFmpeg. Users expect the authentic meme format, not a branded version.
3. **Meme template compositing workflow** — Download the raw template from imgflip (e.g., `https://i.imgflip.com/2za3u1.jpg`), programmatically detect white/blank zones using flood fill on a downscaled PPM, then overlay images into those zones with FFmpeg. Do NOT add text that the template already contains — inspect the raw template first.
4. **Memegen.link API** (`https://api.memegen.link`) is free, no auth, and supports text-only memes well. Template IDs: `same` (They're the same picture), `db` (Distracted Boyfriend), `spiderman` (Spider-Man pointing). But its `style[]` overlay feature places images too small — use FFmpeg compositing for image-in-template memes instead.
5. **Reddit images often block direct download** — `external-preview.redd.it` URLs return HTML instead of images when downloaded with curl. Use Google Images search (`search_google_images()`) as a reliable alternative for sourcing F1 car/person photos.
6. **Keep slides under 30 words** — Instagram is visual-first. If body text is getting long, split into two slides or use a `content_stat` slide to pull out the key number.
7. **The CTA slide is auto-appended** — Never include it in script.json. The generator always adds it as the last slide with the F1 Burnouts logo + Follow/Like/Share.
8. **Max 10 slides on Instagram** — Plan for 8 content slides + 1 cover + 1 auto-CTA = 10 total (the Instagram maximum).

## Long-Form Video Features

- **Stock Image Approach**: Uses Pexels/Unsplash photos instead of YouTube footage
- **Ken Burns Effects**: zoom_in, zoom_out, pan_left, pan_right for engaging motion
- **Quote Overlays**: Auto-detects quotes and displays with speaker images
- **4K/HD Resolution**: 3840x2160 or 1920x1080, 16:9 horizontal
- **Higher Bitrate**: 20Mbps (4K) or 12Mbps (HD) for quality
- **End Credits**: Auto-generated with sources/references
- **Image Attributions**: Auto-generated file with stock photo credits
- **No Text Overlay**: Clean footage with separate SRT for YouTube captions
- **Reference Tracking**: Every factual claim should have a source
- **YouTube Chapters**: Generated from section names
- **Description with Sources**: All references included in upload

## Podcast Features

- **Chunked TTS Generation**: Use `--chunked` mode to split content into ~250-word chunks (~60-90 seconds each) - prevents voice degradation on long podcasts
- **Voice Profile**: Character traits, performance style, and director's notes maintain personality
- **Documentary Music Mode**: Clean voice content with music only at intro (12s) and outro (10s)
- **Loudness Normalization**: Output normalized to -16 LUFS for podcast standards
- **WebVTT Transcripts**: Auto-generated for RSS.com upload
- **Available Voices**: Charon (default), Kore, Puck, Zephyr, Enceladus, Aoede
- **Emotion Markers**: Inline `[excited]`, `[sarcastic]`, `[whispering]` for expressive delivery
- **SSML Enhancement**: Auto-applied pauses, emphasis, and prosody via `ssml_generator.py`

### Gemini TTS Voice Degradation Fix

**Problem**: Gemini TTS voice quality degrades after ~4 minutes of continuous generation (becomes raspy, strained, "throat infection" effect).

**Solution**: Use `--chunked` mode which splits content into ~250-word chunks:
```bash
# RECOMMENDED for podcasts > 5 minutes
python3 src/gemini_podcast_audio_generator.py --project {name} --chunked

# Then add music
python3 src/podcast_music_mixer.py --project {name} --music shared/music/podcast_default.mp3 --documentary --output projects/{name}/output/final.mp3
```

**Why it works**: Each TTS request stays short enough (~60-90 seconds) to maintain consistent voice quality throughout. SSML is preserved within each chunk.

**Avoid**: Single-request mode (`--legacy` or default) for podcasts longer than ~5 minutes.

### Gemini TTS Ad-Lib Fix

**Problem**: Gemini TTS sometimes generates extra speech beyond the script text in the last chunk (e.g., an improvised sign-off or repeated content). This results in unwanted voiceover during the outro music.

**Detection**: After generating audio, check the last chunk for suspicious trailing content:
```bash
# Look for a gap followed by extra speech at the end of the last chunk
ffmpeg -i projects/{name}/audio/chunk_NNN.mp3 -af "silencedetect=noise=-28dB:d=0.3" -f null - 2>&1 | grep silence | tail -5
```
If there's a silence gap in the last ~15s followed by more speech, Gemini ad-libbed.

**Fix**: Trim the last chunk at the silence gap before the ad-lib:
```bash
ffmpeg -y -i projects/{name}/audio/chunk_NNN.mp3 -t {cut_point} -c:a libmp3lame -b:a 256k projects/{name}/audio/chunk_NNN.mp3
```
Then re-run the audio generator (it will use cached chunks) and the music mixer.

**Alternative**: Delete the last chunk and re-run the generator. Gemini doesn't always ad-lib — regenerating often produces a clean take.

### Local TTS Alternative (Qwen3)

Qwen3-TTS 1.7B with MLX is available for local generation but produces more robotic output:
- No SSML support - uses `instruct` parameter for emotion control
- Good for sleep/meditation content, not ideal for energetic podcasts
- Use `src/qwen_podcast_audio_generator.py` if needed

### Podcast Music

Default track: `shared/music/podcast_default.mp3` (symlink to `f1_invincible.mp3`)

Music placement:
- **Intro**: 0-12s at 80% volume, fades as voice starts
- **Content**: Pure voice, no background music
- **Outro**: Last 10s, music swells from 25% to 70% after voice ends

## yt-dlp Setup (Required for HD Downloads)

YouTube requires PO Token authentication for HD formats (720p+). Without these plugins, downloads fail with 403 errors.

**Required installation:**
```bash
pip install -U yt-dlp
pip install yt-dlp-get-pot bgutil-ytdlp-pot-provider
```

**Symptoms of missing plugins:**
- Downloads fail with "HTTP Error 403: Forbidden"
- Warning about "SABR streaming" in yt-dlp output
- Only 360p format available instead of HD

**Verification:**
```bash
yt-dlp --version  # Should be 2026.x or later
pip list | grep yt-dlp  # Should show yt-dlp, yt-dlp-get-pot, bgutil-ytdlp-pot-provider
```

## API Keys Setup

Store API keys in `shared/creds/`:
- `elevenlabs` - ElevenLabs TTS API key
- `pexels` - Pexels stock image API (free at https://www.pexels.com/api/)
- `unsplash` - Unsplash fallback (free at https://unsplash.com/developers)
- `openai` - OpenAI for DALL-E graphics (optional)
- `google_ai` - Google AI API key for Veo3 video generation (optional)
- `instagram` - Instagram credentials (username on line 1, password on line 2)
- `youtube_client_secrets.json` - YouTube OAuth credentials

### Veo3 Setup (Optional - AI Video Generation)

Veo3 generates cinematic AI videos for abstract concepts (fuel production, chemistry, etc.):

1. **Install library**: `pip install google-genai`
2. **Get API key**: Visit https://aistudio.google.com/apikey
3. **Save key**: `echo "YOUR_KEY" > shared/creds/google_ai`
4. **Enable**: Use `--veo3` flag with image_video_assembler.py

**Pricing** (as of 2025):
- Veo 3 Fast: $0.15/second (~$1.20 per 8s clip)
- Veo 3 Standard: $0.40/second (~$3.20 per 8s clip)

**When Veo3 is used**:
- Abstract concepts without specific F1 imagery (fuel chemistry, carbon capture, etc.)
- Technical visualizations (wind tunnel, molecular processes)
- When other visual sources fail to find relevant content
