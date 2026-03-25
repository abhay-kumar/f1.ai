# F1 Daily News Update

Create a daily F1 news update SHORT (9:16 vertical, max 90 seconds) by finding trending stories from the past 24 hours.

**CRITICAL: Daily news MUST be a Short (9:16 vertical, under 90s). Analytics show daily news as Shorts averages ~1,500 views vs ~46 views as long-form. NEVER create daily news as 16:9 horizontal.**

## Instructions

> Script writing guidelines: see **f1-scriptwriting** skill
> Footage sourcing rules: see **f1-footage-sourcing** skill

### Phase 1: Find Trending Stories

```bash
python3 src/reddit_fetcher.py --top day --limit 30
```

Then use `/f1-find-content day` to analyze posts and generate video ideas.

1. **Filter Out Previously Reported Stories**: Cross-reference against `shared/reddit_ideas.json`. Remove stories with `"status": "used"` (match semantically). Only present **genuinely fresh stories**.
2. **CHECKPOINT - User Selection**: Present fresh stories. Recommend **3-5 stories** for a ~60-90s Short. Wait for explicit confirmation.

### Phase 2: Create News Script

1. **Project Setup**: `projects/f1-daily-news-{date}/` (e.g., `f1-daily-news-jan23`)

2. **Script Structure**:
   ```json
   {
     "title": "F1 Daily News - [Full Date] #Shorts",
     "format": "short",
     "duration_target": 75,
     "segments": [
       { "id": 0, "text": "[Biggest story hook — bold, dramatic, scroll-stopping]", "context": "Hook - biggest story", "footage_query": "...", "footage_start": 5 },
       { "id": 1, "text": "Here's what happened in F1 in the last twenty-four hours.", "context": "Brand moment - logo zoom", "footage": "segment_01.mp4" },
       { "id": 2, "text": "[Continue hook story with details]", "context": "Story 1 details", "footage_query": "..." },
       { "id": 3, "text": "[Story 2 - 1-2 sentences]", "context": "Story 2", "footage_query": "..." },
       { "id": 4, "text": "[Story 3 - 1-2 sentences]", "context": "Story 3", "footage_query": "..." },
       { "id": "N", "text": "Follow F1 Burnouts for your daily F1 fix. Drop your take in the comments.", "context": "Outro - CTA", "footage": "segment_{N:02d}.mp4", "footage_start": 0 }
     ]
   }
   ```

3. **Duration Rules (STRICT)**:
   - **Target: 60-75 seconds** (absolute max 90s)
   - **3-5 news stories** max — pick the biggest, skip the rest
   - **1-2 sentences per story** — be ruthless, cut filler
   - If a day has huge news (race results, major controversy), focus on 2-3 stories with more detail
   - Slow news days: 3 stories at 60s is fine

4. **Script Guidelines**:
   - **Hook (segment 0)**: Biggest story as scroll-stopping hook. Bold claim, shocking quote, or dramatic development. Needs its own footage.
   - **Logo (segment 1)**: Pre-built 9:16 assets, never regenerate.
   - **First news segment (segment 2)**: CONTINUES the hook story with more details.
   - Keep each story to 1-2 sentences. Every word must earn its place.
   - Use present tense, specific details, natural transitions between stories.
   - **Mandatory CTA in final segment**: "Follow F1 Burnouts for your daily F1 fix" (or variation). NEVER skip the subscribe/follow CTA.
   - Include `reddit_media_url` and `reddit_media_type` where Reddit media is available.

5. **CHECKPOINT - Script Review**: Present complete script with estimated duration. **STOP and wait for approval.**

### Shared Assets

Copy branded assets before downloading footage:
```bash
# Logo intro (segment 1) — logo2.mp4 is the F1 car burnout + logo reveal animation (16:9, 8s, has its own audio)
# IMPORTANT: Speed up logo2.mp4 to match the segment 1 audio duration so the FULL animation plays.
# The raw logo2.mp4 is 8s but segment audio is ~3.6s — without speedup the animation gets cut off midway.
AUDIO_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 projects/f1-daily-news-{date}/audio/segment_01.mp3)
VIDEO_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 shared/channels/f1/assets/logo/logo2.mp4)
PTS=$(python3 -c "print(f'{$AUDIO_DUR / $VIDEO_DUR:.4f}')")
ffmpeg -y -i shared/channels/f1/assets/logo/logo2.mp4 \
  -filter_complex "[0:v]setpts=${PTS}*PTS,fps=30,format=yuv420p[v]" \
  -map "[v]" -an -c:v h264_videotoolbox -pix_fmt yuv420p \
  projects/f1-daily-news-{date}/footage/segment_01.mp4
cp shared/channels/f1/assets/daily-news/logo_with_f1sound.mp3 projects/f1-daily-news-{date}/audio/segment_01.mp3
# CTA outro (last segment) — outro_cta.mp4 is the "F1 BURNOUTS / LIKE • SUBSCRIBE • BELL" card
cp shared/channels/f1/assets/daily-news/outro_cta.mp4 projects/f1-daily-news-{date}/footage/segment_{N:02d}.mp4
```
The assembler handles 16:9 → 9:16 vertical crop with blurred background automatically.
Segment 0 (hook) needs its own footage. The CTA/outro segment always uses outro_cta.mp4 (the assembler auto-copies it if missing, but copy it explicitly to avoid wasted YouTube searches).
**NEVER use logo_zoom.mp4 for intro or outro** — it is an old asset. Always use logo2.mp4 (intro, sped up) and outro_cta.mp4 (outro).

### Media Sourcing Priority

Reddit media is ALWAYS the first choice — see **f1-footage-sourcing** skill for full priority order and download commands.
```bash
python3 src/footage_downloader.py --project {name} --google-search --validate
```

### Phase 2.5: Official Source Videos (MANDATORY for Race Day)

If covering a specific race weekend, download official F1 videos BEFORE creating footage:
```bash
yt-dlp -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" \
  "ytsearch1:Race Highlights | 2026 [Race Name] Grand Prix" \
  -o "projects/f1-daily-news-{date}/footage/race_highlights.mp4"
```
Pre-cut clips from verified timestamps. Set `footage_start: 0` for pre-trimmed clips.

### Phase 3: Video Production

Follow `/f1-create-short` pipeline Phase 3 (NOT `/f1-create-video`):

1. **Generate audio**: `python3 src/audio_generator.py --project f1-daily-news-{date}`
2. **Assemble as vertical Short** (hard cuts are the default for `"format": "short"`):
   ```bash
   python3 src/video_assembler.py --project f1-daily-news-{date}
   ```
   The assembler auto-detects `"format": "short"` and uses hard cuts (no cross-dissolve). This prevents the A/V sync drift that cross-dissolve causes. It also auto-copies the logo to CTA segments missing footage.
3. **Duration check**: Final video MUST be under 180s (YouTube Shorts limit). Target 60-90s. The assembler prints an A/V sync warning if video and audio durations diverge by more than 1s.

### Phase 3.5: Mandatory Footage Review (NEVER SKIP)

1. Run Gemini vision validation on ALL footage.
2. Validate video clips at `footage_start` timestamps.
3. Fix any mismatches BEFORE assembly.

### Phase 3.75: Post-Assembly Validation (NEVER SKIP)

1. **A/V sync check** — the assembler prints a warning if video/audio durations diverge by >1s. If you see this warning, check transition type and footage durations.
2. **Duration sanity check** — must be under 180s, ideally 60-90s.
3. **Hook segment check** — extract frame at t=2s and verify hook footage is correct (not logo or wrong driver).
4. **CTA segment check** — extract frame at last 5s and verify logo is showing.
5. Fix any issues and re-assemble before delivery.

### Phase 4: Post-Production

Update `shared/reddit_ideas.json`: add new ideas, mark used stories with `"status": "used"` and `"used_date"`.

### Pipeline-Specific Notes
- Pronunciation vs spelling: fix phonetic spelling in `text` back to correct spelling before assembly
- Daily news Shorts do NOT use lower thirds, topic cards, intro, or credits
- Keep it fast-paced: cut, cut, cut. No slow transitions.

### Output

Final video: `projects/f1-daily-news-{date}/output/final.mp4` — 1080x1920 (9:16 vertical), 60-90s, 30fps, voiceover + background music.

### Next Step
After video is created, suggest `/f1-upload-short` to upload to YouTube as a Short (NOT `/f1-upload-video`).
