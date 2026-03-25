# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iti.ai is a multi-channel automated pipeline for creating content across YouTube channels. Each channel has its own branding, themes, knowledge base, and credentials. The pipeline infrastructure is shared; channel-specific data lives in `channels/<id>.py`.

**Active channels:**
- **f1** — F1 Burnouts (Formula 1 content)
- **history** — (planned)
- **science** — (planned)
- **food** — (planned)

It supports five content formats:

1. **Shorts** (60-second vertical videos, 9:16) - Quick, engaging content for mobile
2. **Long-form** (4-6 minute horizontal videos, 16:9, up to 4K) - In-depth story-driven content with references
3. **Podcasts** (~20-minute audio episodes) - Engaging monologue-style content for RSS.com/Spotify
4. **Animated videos** (Remotion) - Programmatic React animations synced to voiceover for technical explainers
5. **Carousels** (Instagram multi-image posts, 1080x1080) - Professional swipeable slide decks for Instagram

**Video formats** orchestrate: script creation → fact checking → voiceover generation (Gemini TTS / ElevenLabs) → footage acquisition (yt-dlp) → video assembly (FFmpeg with GPU acceleration) → YouTube + Instagram upload.

**Animated video format** orchestrates: script creation → TTS generation → VTT transcript parsing → Remotion animation composition → frame-by-frame rendering → video output.

**Podcast format** orchestrates: script creation → single-request TTS generation (Gemini) → music mixing (intro/outro) → RSS.com upload.

**Carousel format** orchestrates: content sourcing (Reddit/web/text) → script creation → image sourcing → HTML/CSS slide rendering (Playwright) → manual Instagram upload.

## Multi-Channel Architecture

### Channel Config System (`channels/`)

Each channel has a Python config file exporting a `CHANNEL` dict with all channel-specific data:

```
channels/
  __init__.py      # load_channel(), channel_asset(), channel_cred() helpers
  f1.py            # F1 Burnouts — colors, entities, themes, knowledge base, upload metadata
  history.py       # (planned)
  science.py       # (planned)
  food.py          # (planned)
```

**Channel resolution order:**
1. `script.json["channel"]` field (stored with each project)
2. `ITI_CHANNEL` environment variable
3. Default: `"f1"`

**Key helpers:**
- `load_channel(channel_id)` — load config by ID
- `load_channel_from_script(script)` — load from script.json's "channel" field
- `channel_asset(channel, relative_path)` — resolve asset path under `shared/channels/<id>/`
- `channel_cred(channel, filename)` — resolve credential path under `shared/creds/<id>/`

### Asset Organization

```
shared/
  channels/
    f1/                      # Per-channel branded assets
      assets/logo/           # logo.png, logo2.mp4
      assets/daily-news/     # intro.mp4, outro.mp4, etc.
      audio/                 # intro_voiceover.mp3, outro_longform.mp3
      fonts/                 # Formula1-Bold.ttf, TitilliumWeb-Black.ttf
      music/                 # background.mp3, f1_cinematic_rock.mp3
    history/                 # (planned)
      assets/, fonts/, music/
  sfx/                       # Shared across all channels (whoosh, swoosh, etc.)
  creds/
    f1/                      # Per-channel platform credentials
      youtube_client_secrets.json
      youtube_token.pickle
      instagram, rss_com
    elevenlabs               # Shared API keys
    google_ai, pexels, openai
```

## Skill Files (Format-Specific Guides)

All format-specific commands, script.json formats, lessons, and pipeline instructions are in the skill files:

- `/f1-create-short` — Shorts pipeline (9:16 vertical, up to 2:40). Includes shot list reference, footage validation.
- `/f1-create-video` — Long-form pipeline (16:9, 4-6min) + Animated video (Remotion). Includes storytelling guide, reference system.
- `/f1-create-podcast` — Podcast pipeline (~20min audio). Includes host persona, SSML, chunked TTS, music mixing.
- `/f1-create-carousel` — Instagram carousel pipeline (1080x1080). Includes themes, slide types, meme compositing.
- `/f1-daily-news` — Daily F1 news update shorts. Includes hook pattern, shared assets, Reddit-first media sourcing.
- `/f1-find-content` — Reddit trend discovery
- `/f1-upload-short` — YouTube Shorts + Instagram upload
- `/f1-upload-video` — YouTube long-form upload with auto-generated thumbnail
- `/f1-upload-podcast` — RSS.com podcast upload
- `/f1-upload-carousel` — Instagram carousel upload
- `/f1-channel-review` — YouTube analytics review and content strategy recommendations
- `/f1-archive` — Project cleanup + Google Drive
- `/f1-release` — Git release workflow

**Skills** (auto-triggered by topic, shared across commands):
- `f1-scriptwriting` — Hook patterns, segment structure, pacing rules, one-entity-one-shot
- `f1-footage-sourcing` — Source priority, Reddit media, Gemini validation, QA checklist
- `f1-podcast-voice` — Host persona, emotion markers, monologue style

## Architecture

**Pipeline Flow:**
```
script.json → fact_check → audio/*.mp3 → footage/*.mp4 → previews/*.jpg → output/final.mp4 → YouTube
```

**Core Modules (`src/`):**
- `config.py` - Generic pipeline settings (frame rates, concurrency, video specs). Channel-specific data is in `channels/`.
- `fact_checker.py` - Script validation with channel knowledge base, web search, and reference validation
- `audio_generator.py` - Gemini TTS (default, free) / ElevenLabs TTS with caching and concurrent processing
- `gemini_podcast_audio_generator.py` - Podcast: Single-request TTS with channel voice profile
- `podcast_music_mixer.py` - Podcast: Intro/outro music mixing with FFmpeg
- `reddit_fetcher.py` - Reddit OAuth2 API: fetch posts + extract media (images, GIFs, videos, galleries)
- `footage_downloader.py` - yt-dlp YouTube search/download with concurrent downloads, 4K support, per-shot downloads, Reddit media priority
- `shot_assembler.py` - Shared shot list logic: timing calculation, clip creation, transition stitching (used by both assemblers)
- `stock_image_fetcher.py` - Pexels/Unsplash API for stock photos, Google Images for person portraits
- `google_image_search.py` - Playwright-based Google Images scraper + Google-for-YouTube search
- `gemini_vision_validator.py` - Gemini Flash vision validation for footage accuracy (thumbnail + file validation)
- `image_video_assembler.py` - Long-form: YouTube-first visual routing with color grading, transition SFX, animated intro, context-aware music, SRT caption generation
- `color_grader.py` - FFmpeg color grading presets (B&W, vintage, cinematic, warm, cool)
- `intro_generator.py` - Animated logo intro with engine rev + swoosh SFX (channel-aware)
- `thumbnail_generator.py` - Auto-generated viral thumbnails with channel team colors
- `veo3_generator.py` - Google Veo3 AI video generation for abstract concepts
- `download_footage.sh` - Sequential footage downloader in isolated subprocesses (fallback for hangs/memory leaks)
- `video_assembler.py` - Shorts: 9:16 vertical FFmpeg composition with GPU acceleration
- `video_assembler_longform.py` - Long-form: 16:9 horizontal with YouTube footage (legacy)
- `carousel_generator.py` - Carousel: HTML/CSS slide rendering via Playwright, channel themes
- `youtube_uploader.py` - Shorts: OAuth upload with channel tags/disclaimer
- `instagram_uploader.py` - Shorts: Instagram Reels upload via instagrapi
- `youtube_uploader_longform.py` - Long-form: Standard video upload with references in description
- `youtube_analytics.py` - Channel analytics: view counts, retention, format performance comparison
- `gdrive_uploader.py` - Google Drive upload for project archival

**Project Structure (Video):**
```
projects/{name}/
├── script.json      # Segments with text, shots array, footage_query, footage_start, channel
├── audio/           # Generated voiceovers (segment_00.mp3, ...)
├── footage/         # Downloaded clips (segment_00.mp4, segment_00_shot_01.mp4, ...)
├── previews/        # Frame extractions for QA (seg00_shot00_t000.jpg, ...)
├── output/          # Final video (final.mp4)
└── upload_info.json # YouTube + Instagram URLs after upload
```

**Project Structure (Podcast):**
```
projects/{name}/
├── script.json           # Segments with text, context, emotion, channel
└── output/
    ├── final.mp3         # Final podcast with intro/outro music
    ├── cover_art.jpg     # Podcast cover (1400x1400 or 3000x3000)
    └── transcript.vtt    # WebVTT transcript for RSS.com
```

**Project Structure (Carousel):**
```
projects/{name}/
├── script.json      # Slides with type, content, theme, channel (format: "carousel")
├── images/          # Source images (backgrounds, portraits)
└── output/
    ├── slide_01.jpg  # Cover slide (1080x1080)
    ├── slide_02.jpg  # Content slides...
    └── slide_NN.jpg  # CTA slide (auto-appended, always last)
```

**External Dependencies:**
- ffmpeg/ffprobe (video processing)
- yt-dlp (YouTube download) + PO Token plugins (see below)
- Google Gemini TTS API (free tier, `pip install google-genai`)
- ElevenLabs API (TTS, paid fallback)
- Pexels API (stock images - for long-form)
- Unsplash API (fallback stock images - optional)
- YouTube Data API v3 (upload)
- instagrapi (Instagram Reels upload, `pip install instagrapi`)
- SerpAPI (fact checking web search, optional)
- OpenAI API (DALL-E graphics - optional)
- Playwright (`pip install playwright && playwright install chromium` - Google search scraping)
- Google Gemini Flash vision (free tier via `google-genai` - footage validation)
- Remotion (`npm install remotion @remotion/cli` - animated video rendering)
- Node.js (required for Remotion)
- Google Drive API (project archival, same GCP project as YouTube)

## Critical Technical Notes

1. **Always verify footage with previews** - YouTube search often returns incorrect videos; run preview_extractor and visually check before assembly
2. **30fps is mandatory** - Mixed framerates cause audio/video desync; video_assembler enforces this
3. **FFmpeg split filter required** - Cannot consume the same stream twice in filter graphs
4. **Re-encode during concat** - Stream copy corrupts timestamps with mixed source formats
5. **Cache awareness** - Audio files are cached; delete segment MP3 to regenerate
6. **Duration validation** - Assembly verifies video/audio durations match within 1 second
7. **Static image max 6s** - No single image shot should hold >6s; >8s causes freeze frames. Split into multiple shots (one per entity). Runtime warning in shot_assembler.
8. **SRT captions sync** - Caption generator accounts for intro video offset after cold_open. Captions are split into 8-14 word chunks, not full paragraphs.
9. **Logo thumbnails** - AI generators cannot render real logos. For multi-brand topics, use hybrid approach: Imagen for background + FFmpeg overlay of transparent PNG logos.
10. **Channel field in script.json** - Every script.json must include `"channel": "<id>"` so pipeline modules load the correct channel config.

## Shorts: 16:9 Video in 9:16 Frame (Blurred Background)

When using horizontal (16:9) footage in vertical (9:16) shorts, use a **blurred background** instead of black bars or stretching:

```bash
ffmpeg -y -ss {start} -i source.mp4 -t {duration} -filter_complex "
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:20[bg];
[0:v]scale=1080:608[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2
" -c:v h264_videotoolbox -pix_fmt yuv420p -r 30 -an output.mp4
```

**Important:** Always create footage 2-3 seconds longer than the audio duration to avoid freeze at the end of segments.

## Performance Features

### Concurrency
All pipeline stages support concurrent processing by default:
- **Audio generation**: 4 concurrent API calls
- **Footage download**: 3 concurrent downloads
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

Store shared API keys in `shared/creds/`:
- `elevenlabs` - ElevenLabs TTS API key
- `pexels` - Pexels stock image API (free at https://www.pexels.com/api/)
- `unsplash` - Unsplash fallback (free at https://unsplash.com/developers)
- `openai` - OpenAI for DALL-E graphics (optional)
- `google_ai` - Google AI API key for Gemini TTS + Veo3 video generation

Store per-channel credentials in `shared/creds/<channel_id>/`:
- `youtube_client_secrets.json` - YouTube OAuth credentials
- `youtube_token.pickle` - YouTube OAuth token (auto-generated)
- `instagram` - Instagram credentials (username on line 1, password on line 2)
- `rss_com` - RSS.com credentials (email on line 1, password on line 2)
