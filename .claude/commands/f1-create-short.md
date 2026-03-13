# Create Short Video

Create an F1 short video based on user's prompt. Handles the entire pipeline from script to final video.

## User Input

**Synopsis** (required): $ARGUMENTS

## Instructions

You are creating a short-form vertical video (9:16) for mobile consumption.

> Script writing guidelines: see **f1-scriptwriting** skill
> Footage sourcing rules: see **f1-footage-sourcing** skill

**Duration:** YouTube Shorts support up to 3 minutes (since Oct 2024). Aim for **2:30-2:40 max**. Ask the user for target duration upfront.

### Project Structure
```
projects/{name}/
├── script.json     # Video script with segments
├── audio/          # Generated voiceovers (cached)
├── footage/        # Downloaded source clips
├── temp/           # Intermediate files
└── output/         # Final video (final.mp4)
```

### Workflow

1. **Gather All Requirements First**: Before writing ANY script, ask: story beats, target duration, specific moments/people/events. Get all content requirements in a single pass.
2. **Research** (if needed): Search web for facts, quotes, sources
3. **Create Script**: Generate `script.json` with segments containing `text`, `context`, `footage_query`, `footage_start`, and optional `shots` array for multi-visual segments
4. **REVIEW CHECKPOINT**: Present complete script. **STOP and wait for user approval.** Aim for approval in ONE round.
5. **Download Footage**: `python3 src/footage_downloader.py --project {name} --google-search --validate`
6. **Verify Footage**: `python3 src/footage_downloader.py --project {name} --list` — check titles match intended content
7. **Fix Mismatched Footage**: Re-download with better queries, use subtitle search for timestamps
8. **Ensure `footage` key in script.json**: Every segment MUST have a `footage` field
9. **Extract & Verify Previews**: `python3 src/preview_extractor.py --project {name}` — visually verify footage matches narrative
10. **Validate Footage (MANDATORY)**: Run Gemini vision validation on ALL footage:
    ```bash
    python3 src/gemini_vision_validator.py --project {name}
    ```
    Every segment must pass with high confidence. Fix and re-validate until all pass. **Do NOT proceed until all footage is validated.**
11. **Generate Audio**: `python3 src/audio_generator.py --project {name}`
12. **Assemble Video**: `python3 src/video_assembler.py --project {name}`
13. **Post-Assembly Validation (NEVER SKIP)**:
    - Duration sanity check: `ffprobe -v error -show_entries format=duration -of csv=p=0 projects/{name}/output/final.mp4`
    - First segment check: verify opening voiceover plays completely
    - Segment duration check: video ≥ 80% of audio for each segment
    - **Static image hold check**: No single image on screen >6s. If a segment has 1 image shot and >15 words, add more shots.
    - **Failed shot check**: Grep assembler output for "Shot N failed" or "skipping". Re-download and reassemble — do NOT deliver with failed shots.
    - `footage_start` consistency: top-level matches shots[]
    - Fix any issues before proceeding
14. **USER REVIEW CHECKPOINT (MANDATORY)**: Present output video. **STOP and wait for user confirmation.** Fix any issues before uploading. **NEVER upload without explicit approval.**
15. **Verify Final Output**: Video/audio durations match, content syncs with narration

### Assembly Notes
- Cross-dissolve between segments causes audio-video drift (~0.3s per boundary). Use `--segment-transition cut` for news-style shorts. Only use `cross_dissolve` for cinematic shorts with 3-4 segments.
- Clear audio cache (`rm audio/*.mp3`) when script structure changes (merge, remove, reorder segments). Only reuse cache for footage-only changes.

### Shot List (Multi-Visual Segments)

For segments mentioning multiple entities, break visuals into a `shots` array:

```json
{
  "text": "Alpine switched from Renault engines despite backlash from Enstone to Mercedes for 2026.",
  "context": "Alpine engine switch",
  "shots": [
    { "label": "Alpine on track", "text_cue": "Alpine switched from Renault engines", "source_type": "youtube_clip", "footage_query": "Alpine A525 Renault F1 2025", "footage_start": 30, "transition_in": "cut" },
    { "label": "Enstone factory", "text_cue": "despite backlash from Enstone", "source_type": "image", "image_query": "Enstone F1 factory Alpine", "ken_burns": "zoom_in", "transition_in": "cross_dissolve" },
    { "label": "Mercedes PU", "text_cue": "to Mercedes for 2026", "source_type": "youtube_clip", "footage_query": "Mercedes F1 power unit 2026", "footage_start": 15, "transition_in": "wipe_left" }
  ]
}
```

### Shot Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | yes | Human-readable shot description |
| `text_cue` | string | yes | Exact substring of segment `text` |
| `source_type` | enum | yes | `youtube_clip`, `image`, `quote_overlay`, `veo3_video`, `graphic` |
| `footage_query` | string | for youtube_clip | YouTube search query |
| `footage_start` | int | no | Start timestamp in source video (seconds) |
| `image_query` | string | for image | Stock image search query |
| `ken_burns` | enum | no | `zoom_in`, `zoom_out`, `pan_left`, `pan_right` |
| `transition_in` | enum | no | `cut`, `cross_dissolve`, `wipe_left`, `whip_pan`, `fade_to_black`, etc. |
| `color_grade` | enum | no | `bw`, `vintage`, `cinematic`, `warm`, `cool`, `none` |

Timing is proportional to `text_cue` character position. Min shot duration: 1.5s. Footage naming: `segment_XX_shot_YY.mp4` (shot 0 uses `segment_XX.mp4`).

### script.json Key Fields
- `visual`: Scene description for storyboard review
- `footage_start`: Timestamp (seconds) in source footage
- `footage`: Downloaded filename (e.g., `segment_00.mp4`)
- `shots`: Array of shot objects for multi-visual segments
- `reddit_media_url` / `reddit_media_type`: Direct Reddit media
- `no_text`: Set `true` to suppress text overlay

### Commands
```bash
python3 src/audio_generator.py --project {name}                              # Generate audio
python3 src/footage_downloader.py --project {name} --google-search --validate # Download footage
python3 src/footage_downloader.py --project {name} --list                     # Verify titles
python3 src/footage_downloader.py --project {name} --segment {id} --query "X" # Re-download
python3 src/preview_extractor.py --project {name}                             # Extract previews
python3 src/video_assembler.py --project {name}                               # Assemble video
```

### Voice & API Keys
- Engine: Gemini TTS (free) | Voice: Alnilam | Model: gemini-2.5-flash-preview-tts
- Gemini: `shared/creds/google_ai` | ElevenLabs (fallback): `shared/creds/elevenlabs`

### Output
Final video: `projects/{name}/output/final.mp4` — 1080x1920 (9:16), up to ~2:40, 30fps, voiceover + background music, auto-generated captions.

### Next Step
After video is created, suggest `/f1-upload-short` to upload to YouTube.
