# Create Long-Form Video

Create a professional F1 long-form video (4-6 minutes, 16:9 horizontal, up to 4K resolution) based on user's prompt.

**Quality-first process**: Script goes through iterative self-review before any production. See `.claude/prd-longform.json` for full acceptance criteria.

## User Input

**Synopsis** (required): $ARGUMENTS

## Instructions

You are creating a **long-form horizontal video** (16:9, 4-6 minutes) for YouTube standard format consumption.

> Script writing guidelines: see **f1-scriptwriting** skill
> Footage sourcing rules: see **f1-footage-sourcing** skill
> Quality criteria: see **.claude/prd-longform.json** for acceptance criteria and anti-patterns

### Key Principles (from channel analytics)
- **4-6 minutes MAX** — Channel has 274 subs. Viewers won't commit to 17+ minutes from an unknown channel. Earn longer durations with a bigger audience.
- **Every minute must earn its place** — If a segment doesn't move the story forward, cut it. No padding.
- **Hook must work as a standalone Short** — The first 15 seconds should stop a scroll. If the hook isn't compelling enough for Shorts, it's not compelling enough for long-form.
- **Curiosity gap titles** — "The Man With More F1 Races Than Any Driver" (12K views) >>> "F1 Testing Recap" (7 views)
- **Tags are mandatory** — Previous long-form videos shipped with ZERO tags. Include 15+ relevant tags.

### Key Differences from Shorts
- **Format**: 16:9 horizontal (3840x2160 4K or 1920x1080 HD)
- **Duration**: 4-6 minutes (HARD LIMIT — not 10, not 15, not 20)
- **Depth**: Story-driven with narrative tension, not an information dump
- **References**: Every claim must have a source citation
- **Script Approval**: User must approve script BEFORE any processing

### Project Structure
```
projects/{name}/
├── script.json      # Video script with segments + references
├── audio/           # Generated voiceovers (cached)
├── footage/         # Downloaded source clips + graphics
├── previews/        # Frame previews for verification
├── temp/            # Intermediate files
└── output/          # Final video (final.mp4)
```

---

## Visual Content Strategy

Long-form videos use a **YouTube-first visual approach**: YouTube clips for on-track action, stock images with Ken Burns effects for portraits/stills, quote overlays for speaker quotes, and AI-generated graphics for abstract concepts.

### Shot Source Types

| Type | Use Case | Field |
|------|----------|-------|
| `youtube_clip` | Races, overtakes, celebrations | `footage_query` + `footage_start` |
| `image` | People, historical, technical | `image_query` + `ken_burns` |
| `quote_overlay` | Speaker quotes | Auto-detected or `speaker_name` + `quote_text` |
| `veo3_video` | Abstract concepts (fuel, wind tunnels) | `footage_query` |
| `graphic` | AI-generated diagrams | `graphic_description` |

### Transition Preferences
- `cross_dissolve` (0.5s): Default between related shots
- `wipe_left` (0.3s): Topic changes, forward progression
- `fade_to_black` (0.3s): Section transitions
- `cut`: Fast-paced action sequences
- `whip_pan` (0.2s): Energetic transitions, comparisons

### Shot List Example
```json
{ "id": 5, "section": "rising_action",
  "text": "But Mercedes saw an opportunity. Their engine division in Brixworth had been working on a radical new architecture.",
  "shots": [
    { "label": "Mercedes factory", "text_cue": "But Mercedes saw an opportunity.", "source_type": "image", "image_query": "Mercedes F1 Brixworth factory", "ken_burns": "zoom_out", "transition_in": "fade_to_black" },
    { "label": "Engine assembly", "text_cue": "Their engine division in Brixworth had been working on a radical new architecture.", "source_type": "youtube_clip", "footage_query": "Mercedes F1 power unit 2026", "footage_start": 20, "transition_in": "cross_dissolve" }
] }
```
Ken Burns: `zoom_in`, `zoom_out`, `pan_left`, `pan_right`, `zoom_pan_right` — auto-varied per segment.

---

## Workflow

### Phase 1: Topic Validation

1. **Understand the Prompt**: Identify main topic, emotional core, unique angle, narrative arc
2. **Validate Topic Depth**: Before writing a single word, answer these:
   - Does this story have a protagonist, conflict, and resolution? (Not just "here are some facts about X")
   - Can this genuinely fill 4-6 minutes without padding? If not, make it a Short instead.
   - Does this relate to themes proven by Shorts analytics? (driver drama, untold stories, surprising facts)
   - What's the "why should I keep watching?" through-line for every minute?
3. If the topic fails validation, propose alternatives or suggest making it a Short instead.

### Phase 2: Research & Script Creation (with Self-Review Loop)

4. **Research**: Search web for facts, quotes, statistics. **Record sources for every claim.**
5. **Create Script**: Generate `script.json`:
   ```json
   { "title": "Video Title", "format": "longform", "resolution": "4k", "duration_target": 300,
     "tags": ["F1", "Formula 1", "Driver Name", "Team Name", "Topic Keywords", "...15+ tags"],
     "segments": [
       { "id": 1, "section": "cold_open", "text": "The hook...", "context": "Dramatic opening",
         "shots": [ ... ],
         "references": [{ "claim": "Specific claim", "source": "Source Name", "url": "https://...", "date": "2024-01-15" }]
       }
     ],
     "references_summary": [{ "source": "F1 Official", "url": "https://f1.com/...", "claims_supported": [1, 3, 5] }]
   }
   ```

6. **SELF-REVIEW LOOP (up to 3 iterations)** — Before showing to user, validate script against these criteria:
   - [ ] **HOOK TEST**: First 15 seconds would stop a scroll if posted as a Short
   - [ ] **TENSION TEST**: Every 60 seconds has a question, conflict, or revelation
   - [ ] **PADDING TEST**: Every segment moves the story forward (if not, cut it)
   - [ ] **DURATION TEST**: Word count is 600-900 words (4-6 min at ~150 wpm)
   - [ ] **SEGMENT TEST**: No segment exceeds 80 words / ~30 seconds
   - [ ] **SHOT PACING TEST**: No single static image on screen for >6 seconds. If a segment has only 1 image shot and >15 words of narration, split into multiple shots (one per entity mentioned, or mix image + video)
   - [ ] **VARIETY TEST**: Uses at least 3 section types (cold_open, rising_action, climax, etc.)
   - [ ] **CTA TEST**: Final segment includes subscribe/follow CTA
   - [ ] **TAG TEST**: `tags` array has 15+ specific tags (driver names, teams, topics)
   - [ ] **REFERENCE TEST**: Every factual claim has a source
   - [ ] **TITLE TEST**: Uses curiosity gap pattern, under 60 chars
   If ANY check fails, rewrite the failing sections and re-check. Do NOT present to user until all pass.

7. **Fact Check Script**:
   ```bash
   python3 src/fact_checker.py --project {name} --web-search
   ```

### Phase 3: Script Review (MANDATORY CHECKPOINT)

8. **STOP AND WAIT FOR USER APPROVAL** — Present the complete script showing: title, duration, segment count, visual mix, cold open text, story structure, sources, AND the self-review checklist results. **DO NOT PROCEED** until user explicitly approves.

### Phase 4: Asset Generation

9. **Generate Audio**:
   ```bash
   python3 src/audio_generator.py --project {name}
   ```

10. **Download Footage & Images** (REQUIRED for multi-shot scripts):
    ```bash
    python3 src/footage_downloader.py --project {name} --google-search --validate
    python3 src/footage_downloader.py --project {name} --list  # Check status
    python3 src/footage_downloader.py --project {name} --segment N --shot M --query "alt search"  # Re-download
    ```

11. **Assemble Video**:
    ```bash
    python3 src/image_video_assembler.py --project {name}
    python3 src/image_video_assembler.py --project {name} --resolution hd   # Faster 1080p
    python3 src/image_video_assembler.py --project {name} --no-music        # Skip music
    python3 src/image_video_assembler.py --project {name} --analyze         # Dry run
    ```

    **Topic cards & lower thirds — narrative vs news:**
    - **Narrative/story-driven videos** (predictions, explainers, deep dives): Use `--no-topic-cards --no-lower-thirds`. The `context` field contains internal script notes ("dramatic hook", "quick elimination") that are meaningless to viewers. Narrative videos flow continuously and don't need chapter breaks.
    - **News/multi-story videos** (daily news, weekly roundups): Keep topic cards and lower thirds ON. Each segment covers a distinct story, and context fields should be actual headlines.
    - If a narrative video genuinely needs chapter labels, add an explicit `topic_label` field per segment instead of reusing internal `context` notes.

    **Intro**: Uses `shared/channels/f1/assets/logo/logo2.mp4` (F1 car burnout + logo reveal), sped up to match voiceover duration, placed AFTER the cold_open segment so the hook plays first.

    **Footage quality rules:**
    - Use `source_type: image` for buildings, facilities, headquarters — YouTube clips for these return irrelevant results (tunnels, promos with burned-in text)
    - Portraits: verify orientation/crop, use `ken_burns: zoom_out` on tight portraits (zoom_in = over-zoom)
    - Reject YouTube clips with burned-in text overlays from documentaries/promos

### Phase 5: Post-Assembly Validation (NEVER SKIP)

12. **Validate before delivery** (see f1-footage-sourcing skill for detailed checks):
    ```bash
    ffprobe -v error -show_entries format=duration -of csv=p=0 projects/{name}/output/final.mp4
    ```
    - **Duration HARD CHECK**: Must be 4-6 minutes. If outside this range, investigate why and fix.
    - First segment check (hook voiceover plays completely)
    - Segment-by-segment duration check (video ≥ 80% of audio for each)
    - **Static image hold check**: No single image on screen >6s. For each segment, estimate narration duration from word count (~150 wpm) and verify enough shots exist. Flag any segment with 1 image shot and >15 words.
    - **Failed shot check**: Grep assembler output for "Shot N failed" or "skipping". Failed shots cause remaining shots to stretch and freeze. Re-download failed shots and reassemble — do NOT deliver with failed shots.
    - `footage_start` consistency (top-level matches shots[])
    - PNG-as-JPG detection: `file footage/*.jpg 2>/dev/null | grep PNG`
    - Fix any issues and re-assemble before delivery

### Phase 6: Upload

13. **Upload to YouTube**:
    ```bash
    python3 src/youtube_uploader_longform.py --project {name} --dry-run  # Preview — verify tags are present!
    python3 src/youtube_uploader_longform.py --project {name}            # Upload
    ```
    **CRITICAL**: Verify the dry-run shows 15+ tags. Previous long-form uploads had ZERO tags which killed discoverability.

    **Thumbnail**: For multi-brand topics (team predictions, manufacturer comparisons), use the hybrid logo composite approach described in `/f1-upload-video` instead of `thumbnail_generator.py`. AI generators cannot render real logos — use Imagen for backgrounds only, overlay real transparent PNG logos with FFmpeg.

---

## Output

Final video: `projects/{name}/output/final.mp4`
- Format: 3840x2160 (4K) or 1920x1080 (HD), 16:9 horizontal, 30fps
- Bitrate: 20Mbps (4K) / 12Mbps (HD)
- Audio: Voiceover + subtle background music (5% volume or less)
- **No burned-in captions** — generate separate `.srt` for YouTube CC
- **Outro**: Reusable 19s outro at `shared/channels/f1/audio/outro_longform.mp3` (DO NOT regenerate)

---

## Animated Video (Remotion)

For technical explainers, use Remotion for programmatic React animations synced to voiceover.

```bash
cp -r shared/remotion-template projects/{name}/video
cd projects/{name}/video && npm install
# Concatenate audio for Remotion
ffmpeg -f concat -safe 0 -i <(for f in ../audio/chunk_*.mp3; do echo "file '$(cd .. && pwd)/audio/$(basename $f)'"; done) -c:a libmp3lame -b:a 256k public/audio.mp3
npm run dev       # Preview in browser
npm run preview   # Quick 3s render
npm run render    # Full HD render
npm run build:4k  # 4K render
```

Key files: `src/data/segments.ts` (timing from VTT), `src/components/SegmentRenderer.tsx` (animation router), `src/animations/*.tsx` (reusable components). See `shared/remotion-template/REMOTION_GUIDE.md` for full docs.

---

## Voice & API Keys
- Voice: Jarnathan (c6SfcYrb2t09NHXiT80T), eleven_multilingual_v2
- ElevenLabs: `shared/creds/elevenlabs` | YouTube: `shared/creds/youtube_client_secrets.json`
- Pexels: `shared/creds/pexels` | OpenAI: `shared/creds/openai` | SerpAPI: `SERPAPI_KEY` env var

### Next Step
After video is created, suggest `/f1-upload-video` to upload to YouTube.
