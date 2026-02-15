# Create Short Video

Create an F1 short video based on user's prompt. This command handles the entire pipeline from script to final video.

## User Input

**Synopsis** (required): $ARGUMENTS

The synopsis is the topic/story idea for the short video. This argument is mandatory.

## Instructions

You are creating a short-form vertical video (9:16) for mobile consumption.

**Duration:** YouTube Shorts support up to 3 minutes (since October 2024). However, aim for **2:30-2:40 max** to avoid edge-case classification issues. Ask the user for their target duration upfront (60s, 90s, 2 min, etc.).

### Project Structure
```
f1.ai/
├── projects/           # Each short gets its own folder
│   └── {project-name}/
│       ├── script.json     # Video script with segments
│       ├── audio/          # Generated voiceovers (cached)
│       ├── footage/        # Downloaded source clips
│       ├── temp/           # Intermediate files
│       └── output/         # Final video
├── shared/
│   ├── music/              # Reusable background music
│   └── creds/              # API keys
├── src/                    # Core modules
│   ├── audio_generator.py
│   ├── footage_downloader.py
│   ├── video_assembler.py
│   └── preview_extractor.py
└── .claude/commands/
```

### Workflow

1. **Gather All Requirements First**: Before writing ANY script, ask the user:
   - What specific story beats / topics must be covered?
   - Target duration (60s, 90s, 2 min, etc.)?
   - Any specific moments, people, or events to highlight?
   
   This prevents multiple rounds of script revision. Get all content requirements in a single pass.

2. **Research** (if needed): Search web for facts, quotes, sources
3. **Create Script**: Generate `script.json` with segments containing:
   - `text`: Voiceover text (keep each segment to 1-2 sentences; if text exceeds 8 wrapped lines, the assembler auto-splits into two timed parts at a natural break point, but shorter segments are always better for short-form)
   - `context`: Segment purpose
   - `footage_query`: YouTube search query (for single-shot segments)
   - `footage_start`: Timestamp in source video (verify with previews!)
   - `shots`: (optional) Array of shots for multi-visual segments -- see Shot List section below

4. **REVIEW CHECKPOINT**: Present the script to the user for review before proceeding:
   - Display the complete script with all segments
   - Show title, segment texts, and footage queries
   - **STOP and wait for user approval** before continuing
   - User may request changes to the script before proceeding
   - Only continue to step 5 after **explicit user approval**
   - Aim to get approval in ONE round by gathering all requirements in step 1

5. **Download Footage**: Use yt-dlp to find and download clips
6. **Verify Footage via `--list`**: CRITICAL - After downloading, run `--list` to check the actual YouTube video titles match the intended content. Fan channels often have screen recordings or wrong content.
7. **Fix Mismatched Footage**: If a title doesn't match:
   - Prefer official F1 channel footage over fan channels
   - For team-specific footage, download a broad official video (e.g., shakedown highlights) and use subtitle search to find the right timestamp:
     ```bash
     yt-dlp --write-auto-sub --sub-lang en --skip-download --sub-format vtt -o /tmp/subs "https://youtube.com/watch?v=VIDEO_ID"
     grep -i "team name" /tmp/subs*.vtt
     ```
   - Delete old previews (`rm previews/segNN_*.jpg`) before re-extracting
8. **Ensure `footage` key in script.json**: After downloading, every segment MUST have a `footage` field (e.g., `"footage": "segment_00.mp4"`). The downloader doesn't always add this for all segments. Verify and manually add any missing ones before assembly.
9. **Extract Previews**: Generate thumbnail frames and visually verify:
   - Footage matches the narrative (not wrong era/drivers)
   - Timestamp shows the actual moment needed
   - Update `footage_start` based on visual verification

10. **Generate Audio**: Use Gemini TTS with Alnilam voice (caches to avoid re-generation)
11. **Assemble Video**: Run video assembler with:
    - Consistent 30fps (avoids timestamp issues)
    - Blur-pad effect (no cropping)
    - Background music mixed at 15%
    - GPU encoding (VideoToolbox)

12. **USER REVIEW CHECKPOINT (MANDATORY)**: Present the output video to the user for review BEFORE uploading:
    - Tell the user to review `projects/{name}/output/final.mp4`
    - **STOP and wait for user confirmation** that the video looks good
    - Fix any issues (footage swaps, sync problems) before uploading
    - **NEVER upload without explicit user approval of the final video**

13. **Verify Final Output**: Check that:
    - Video and audio durations match
    - Video plays correctly throughout
    - Content syncs with narration

### Critical Lessons Learned

1. **Always prefer official F1 channel footage** - Fan channels often have screen recordings with cursors, news anchors, or low-quality re-uploads
2. **Use `--list` after downloading to verify titles** - Catches mismatches instantly without opening preview images
3. **Use subtitle search for team-specific timestamps** - Download subtitles with `yt-dlp --write-auto-sub` and grep for team/driver names instead of scanning preview frames
4. **Delete old previews before re-extracting** - Preview images are cached; stale images will show after footage replacement
5. **Force consistent framerate (30fps)** - Mixed framerates cause audio/video desync
6. **Use `split` filter in FFmpeg** - Can't consume same stream twice without splitting
7. **Re-encode during concat** - Stream copy causes timestamp corruption with mixed sources
8. **Cache audio files** - Don't regenerate voiceovers during video editing iterations
9. **Check video/audio stream durations** - They must match in final output
10. **Clear audio cache when script structure changes** - If you merge, remove, or reorder segments, the cached audio files will have wrong text for the new segment numbering. Always `rm audio/*.mp3` and regenerate fresh when the script structure (number of segments or their order) changes. Only reuse cache when making footage-only changes.
11. **YouTube Shorts max is 3 minutes** (since Oct 2024) - but aim for 2:30-2:40 to avoid edge cases. Videos at exactly 180s may not classify as Shorts.

### API Keys Location
- Gemini: `shared/creds/google_ai` (free at https://aistudio.google.com/apikey)
- ElevenLabs (fallback): `shared/creds/elevenlabs`

### Voice Settings
- Engine: Google Gemini TTS (free)
- Voice: Alnilam (Male, friendly, clean American voice)
- Model: gemini-2.5-flash-preview-tts

### Commands to Use
```bash
# Generate audio with Gemini TTS (run once, caches results)
python3 src/audio_generator.py --project {name}

# Or use ElevenLabs as fallback
# python3 src/audio_generator.py --project {name} --engine elevenlabs

# Download all footage
python3 src/footage_downloader.py --project {name}

# Verify downloaded footage titles
python3 src/footage_downloader.py --project {name} --list

# Re-download a specific segment (auto-downloads top result)
python3 src/footage_downloader.py --project {name} --segment {id} --query "search terms"

# Preview candidates without downloading
python3 src/footage_downloader.py --project {name} --segment {id} --query "search terms" --dry-run

# Download specific YouTube video by URL
python3 src/footage_downloader.py --project {name} --segment {id} --url "https://youtube.com/watch?v=VIDEO_ID"

# Extract preview frames
python3 src/preview_extractor.py --project {name}

# Assemble final video
python3 src/video_assembler.py --project {name}
```

### Shot List (Multi-Visual Segments)

For segments that mention multiple entities, topics, or people, break the visuals into a `shots` array. This creates immersive, fast-paced visuals where the screen changes to match what's being narrated.

**When to create shots:**
- Segment mentions 2+ different teams, drivers, or people
- Segment covers a before/after or timeline
- Segment includes a quote from someone (show their face, then the action)
- Segment is longer than ~5 seconds

**How to create shots:**
1. Read the segment text -- identify distinct visual beats
2. For each beat, create a shot with a `text_cue` (exact substring of the text)
3. Choose the right `source_type`: `youtube_clip` for action, `image` for people/stills, `quote_overlay` for quotes
4. Choose a `transition_in`: `cut` (default), `cross_dissolve` (smooth), `wipe_left` (topic change), `whip_pan` (energetic)
5. Ensure text_cues cover all the text contiguously

**Example:**
```json
{
  "text": "Alpine switched from Renault engines despite backlash from Enstone to Mercedes for 2026 and looks quick.",
  "context": "Alpine engine switch",
  "shots": [
    {
      "label": "Alpine on track",
      "text_cue": "Alpine switched from Renault engines",
      "source_type": "youtube_clip",
      "footage_query": "Alpine A525 Renault F1 2025",
      "footage_start": 30,
      "transition_in": "cut"
    },
    {
      "label": "Enstone factory",
      "text_cue": "despite backlash from Enstone",
      "source_type": "image",
      "image_query": "Enstone F1 factory Alpine",
      "ken_burns": "zoom_in",
      "transition_in": "cross_dissolve"
    },
    {
      "label": "Mercedes power unit",
      "text_cue": "to Mercedes for 2026",
      "source_type": "youtube_clip",
      "footage_query": "Mercedes F1 power unit 2026",
      "footage_start": 15,
      "transition_in": "wipe_left"
    },
    {
      "label": "New Alpine testing",
      "text_cue": "and looks quick.",
      "source_type": "youtube_clip",
      "footage_query": "Alpine 2026 Bahrain testing",
      "footage_start": 45,
      "transition_in": "cut"
    }
  ]
}
```

**Footage download for multi-shot segments:**
```bash
# Downloads all shots automatically (images from Pexels, clips from YouTube)
python3 src/footage_downloader.py --project {name}

# Re-download a specific shot
python3 src/footage_downloader.py --project {name} --segment 2 --shot 1 --query "new search"

# Check per-shot download status
python3 src/footage_downloader.py --project {name} --list
```

**Simple segments still work without shots** -- if a segment only needs one visual, just use `footage_query` as before.

### Video Features
- **Blur-pad effect**: Full footage shown centered, blurred version as background (no cropping)
- **Text captions**: Team-colored text always at the bottom (auto-wrapped). If text exceeds 8 lines, it is automatically split into two timed parts at a natural break point (period, comma, semicolon) — part 1 shows first, then gets replaced by part 2
- **Background music**: Epic cinematic track mixed at 15% volume
- **GPU encoding**: VideoToolbox for fast processing

### Output
Final video: `projects/{name}/output/final.mp4`
- Format: 1080x1920 (9:16 vertical)
- Duration: Up to ~2:40 (must stay under 3 minutes for YouTube Shorts)
- Framerate: 30fps
- Audio: Voiceover + background music
- Captions: Auto-generated from script text

### Next Step
After the video is created, suggest the user run `/f1-upload-short` to upload to YouTube.
