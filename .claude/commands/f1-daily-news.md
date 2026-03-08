# F1 Daily News Update

Create a daily F1 news update video (16:9 horizontal) by finding trending stories from the past 24 hours and assembling them into a news-style video.

## Instructions

You are creating a daily F1 news update video (16:9 long-form format). This command orchestrates the full workflow:
1. Find trending F1 stories from Reddit (past 24 hours)
2. Get user confirmation on which stories to include
3. Create a news-style video with all selected stories

### Phase 1: Find Trending Stories

First, fetch trending posts directly from Reddit using the API:
```bash
python3 src/reddit_fetcher.py --top day --limit 30
```

This returns posts with scores, titles, permalinks, and **extracted media URLs** (images, GIFs, videos) — all available for use in the video.

Then use `/f1-find-content day` to analyze these posts and generate video ideas.

This will:
- Use the Reddit API data to identify popular discussions from the past 24 hours
- Extract media URLs from each post for footage sourcing
- Filter out duplicate ideas already in `shared/reddit_ideas.json`
- Present a ranked list of newsworthy stories with their Reddit media

After reviewing the ideas from `/f1-find-content day`:

1. **Filter Out Previously Reported Stories**: Before presenting the list to the user, cross-reference every discovered story against `shared/reddit_ideas.json`:
   - Remove any story that matches an existing entry with `"status": "used"` (same topic, team, person, or event — match semantically, not just by exact ID)
   - Also remove stories that are minor updates to previously used stories (e.g., if "Aston Martin 4 seconds off" was used yesterday, "Aston Martin still 4 seconds off" is not fresh news)
   - Only present **genuinely fresh stories** that have NOT been covered in any previous daily news episode
   - If a story is a significant escalation or new development of a previously covered topic, it IS fresh (e.g., "Skinner resigns" is fresh even if "Red Bull staff purge" was covered before)

2. **CHECKPOINT - User Selection**: 
   - Present ONLY the fresh, unreported stories to the user
   - Clearly label how many stories were filtered out (e.g., "Filtered out 4 previously reported stories")
   - Ask user which stories to include (by number or ID)
   - Recommend 6-8 stories for a ~60-90 second video (16:9 horizontal format)
   - Wait for explicit confirmation before proceeding

### Phase 2: Create News Script

Once user confirms story selection, create the daily news script:

1. **Project Setup**: 
   - Create project folder: `projects/f1-daily-news-{date}` (e.g., `f1-daily-news-jan23`)
   - Use today's date in the folder name

2. **Script Structure**: Generate `script.json` with this news format:
   ```json
   {
     "title": "F1 Daily News - [Full Date]",
     "duration_target": 60,
     "segments": [
       {
         "id": 1,
         "text": "[Biggest story hook - punchy, attention-grabbing, 1-2 sentences]",
         "context": "Hook - [story description], biggest story of the day",
         "visual": "[Specific visual for the hook story]",
         "footage_query": "[search query]",
         "footage_start": 5
       },
       {
         "id": 2,
         "text": "Here's what happened in F1 in the last 24 hours.",
         "context": "Brand moment - show logo with zoom-in, quick transition to news",
         "visual": "F1 Burnouts logo centered on screen with fast zoom-in effect and swoosh SFX",
         "footage": "segment_01.mp4"
       },
       // ... news segments (one per story, 1-2 sentences each) ...
       // The first news segment CONTINUES the hook story with more detail
       // Each news segment should have a lower_third_title for the on-screen graphic
       {
         "id": 3,
         "text": "...",
         "context": "Hadjar breakout performance at Red Bull",
         "lower_third_title": "HADJAR QUALIFIES P3",
         ...
       },
       {
         "id": N,
         "text": "That's your daily news. Like, subscribe, and drop your thoughts in the comments. See you tomorrow!",
         "context": "Outro - CTA",
         "visual": "High-speed F1 racing action montage, multiple cars battling on track",
         "footage_query": "F1 racing action montage",
         "footage_start": 25
       }
     ]
   }
   ```

3. **Script Guidelines**:
   - **Hook segment (segment 0)**: The video opens with the BIGGEST story of the day, delivered as a punchy attention-grabber. NO generic "Welcome to F1 Daily News" intro. The hook should make the viewer stop scrolling — a bold claim, a shocking quote, or a dramatic development. Example: "Max Verstappen just dropped a bombshell. He says we are close to the end of his Formula One career." The hook needs its own footage (NOT shared assets — download specific footage for the hook story).
   - **Logo segment (segment 1)**: Always follows the hook. Pre-built assets, never regenerate.
   - **First news segment (segment 2)**: Should CONTINUE the hook story with more details/context. This creates a satisfying payoff for the hook.
   - **Remaining segments**: Cover the other stories, one per segment.
   - **`lower_third_title`**: A short, punchy title for the on-screen lower-third graphic (e.g., `"RUSSELL TAKES POLE"`, `"HADJAR QUALIFIES P3"`). The assembler auto-generates from `context` if omitted, but explicit titles look better. Do NOT add `lower_third_title` to segment 0 (hook) or segment 1 (logo) — they are skipped automatically.
   - **Shot pacing (3-4 shots per story)**: Each news segment should have 3-4 shots at 2-3 seconds each for professional pacing. Use the `shots` array with varied shot types:
     - **Pattern: portrait → action → detail** (e.g., driver headshot → car on track → data graphic)
     - Use `cross_dissolve` between related shots, `cut` for dramatic changes
     - Single-image segments (no `shots` array) are acceptable for short stories but look less polished
   - **`visual` (storyboard)**: Describe what the viewer should SEE on screen for each segment. This is NOT a search query — it describes the intended visual scene. Be specific about:
     - Subject: which car, driver, team, or object
     - Shot type: aerial, onboard, pit lane, close-up, wide shot, trackside
     - Setting: which track, factory, desert, rain, night
     - Example: "Close-up of the McLaren MCL-40 papaya livery in Bahrain pit lane"
     - Example: "Aerial shot of Bahrain circuit with multiple F1 cars on track, desert setting"
     - Keep to 1-2 sentences per segment
   - Keep each news item to 1-2 crisp sentences. If text wraps to 8+ lines, the assembler auto-splits into two timed parts at a natural break point — part 1 shows first, then gets replaced by part 2. Still prefer shorter segments when possible.
   - Use present tense for immediacy ("Ferrari reveals...", "Hamilton admits...")
   - Include specific details (names, numbers, quotes)
   - Transition naturally between stories
   - Total target: ~60-90 seconds
   - Use the `shots` array for segments covering multiple topics (see `/f1-create-video` Shot List section for full reference)

4. **CHECKPOINT - Script Review**:
   - Present the complete script to user
   - Show all segments with text and footage queries
   - **STOP and wait for user approval**
   - Make any requested changes before proceeding

### News Writing Style

- **Crisp and punchy**: No filler words, every word counts
- **Active voice**: "Ferrari reveals" not "It was revealed by Ferrari"
- **Specific details**: Include names, numbers, dates
- **Natural flow**: Stories should transition smoothly
- **Variety**: Mix team news, driver news, technical updates, controversies
- **NEVER use the word "Quote"**: When including quotes, integrate them naturally into the narration. Instead of "Quote: 'I'll never forget this'", write "In his words: I'll never forget this" or simply state the quote directly as part of the narrative.

#### Example News Segment

**Good**: "Lewis Hamilton finally drove a Ferrari at Fiorano today. The SF-26 marks his first competitive laps in red, with Ferrari finishing the car just one day before launch."

**Bad**: "So there's been some exciting news from Ferrari today. Lewis Hamilton, who as you know moved from Mercedes, has finally had the chance to drive the new car."

### Reusable Elements

The **logo** and **outro** segments are consistent across all daily news videos:
- Logo (segment 1): "Here's what happened in F1 in the last 24 hours." — Pre-built audio + video, never regenerate.
- Outro: "That's your daily news. Like, subscribe, and drop your thoughts in the comments. See you tomorrow!" — **Rendered dynamically by Remotion** (animated CTA card with logo, like/subscribe/comment icons). No pre-built footage needed.

The **hook** (segment 0) is unique every episode — always the biggest story, with custom footage. This builds brand recognition while keeping the opening fresh and scroll-stopping.

### Shared Assets

Pre-downloaded footage and audio for consistent elements is stored in `shared/assets/daily-news/`:
- `logo_with_f1sound.mp3` - Pre-mixed logo segment audio: TTS "Here's what happened in F1 in the last twenty-four hours" + f1sound whoosh (2x speed, overlapped 1s with voice ending). Duration: 3.6s
- `logo_zoom_16x9.mp4` - Pre-rendered 16:9 logo zoom-in video (logo.mp4 at 2.22x speed, 1920x1080, no audio track). Duration: 3.6s
- `logo_zoom.mp4` - Legacy 9:16 version (1080x1920) for shorts use
- `logo_voice.mp3` - Clean TTS voice only (no SFX), for remixing if needed. Duration: 2.58s
- `f1sound_2x.mp3` - f1sound.mp3 0-4s at 2x speed, standalone whoosh clip. Duration: 2.0s
- `logo.jpg` - Source logo image for regenerating zoom video if needed

**Outro is NOT a shared asset** — it's rendered dynamically by the Remotion `Outro` composition during assembly. The assembler auto-detects segments with "outro" or "cta" in their context and renders the animated CTA card. No footage file needed for the outro segment.

Only the **logo segment** assets should be copied to each new project. The logo segment (segment_01) should NEVER be recreated from scratch — always use the pre-built assets.

### Media Sourcing Priority (Reddit-First Approach)

**CRITICAL**: Reddit media is ALWAYS the first choice for daily news visuals. These stories come from Reddit — the original posts almost always contain images, GIFs, or video clips that are purpose-made for the story. YouTube compilation videos are unreliable (wrong timestamps, wrong teams, burned-in graphics). Google Images return old-season cars. Reddit media is current, relevant, and matches the story exactly.

**During Phase 1 (Story Discovery)**, the Reddit fetcher (`python3 src/reddit_fetcher.py --top day --limit 30`) automatically extracts all media URLs from each post. Media URLs are included in the output and should be stored in `shared/reddit_ideas.json` with each story idea.

Common Reddit media URL patterns (extracted automatically by the fetcher):
  - Images: `https://i.redd.it/xxxxx.jpg` or `https://preview.redd.it/xxxxx.jpg`
  - GIFs (served as MP4): `https://preview.redd.it/xxxxx.gif?format=mp4&s=xxxxx`
  - Videos: `https://v.redd.it/xxxxx` or `https://packaged-media.redd.it/xxxxx`

For any story where the fetcher didn't find media (e.g., text-only discussion posts), you can fetch the specific post for more detail:
```bash
python3 src/reddit_fetcher.py --post "https://reddit.com/r/formula1/comments/..."
```

**RACE DAY RULE**: When covering a specific race (qualifying, sprint, or race day), footage MUST be from THAT event — not generic driver portraits, pre-season testing, or prior-year clips. Viewers notice immediately when visuals don't match the event. For race recaps:
1. Download the official "Race Highlights | 2026 [Race Name] Grand Prix" video from the F1 YouTube channel
2. Download the "Drivers React After The Race" video for interview clips
3. Extract clips at specific timestamps for each story (e.g., race start at t=30, VSC pit stop at t=270, podium at t=470)
4. Use these race-specific clips for ALL YouTube-sourced shots. Never fall back to testing footage or old races.

**Priority order for ALL visual assets:**

1. **Reddit media (FIRST PRIORITY — use for every story if available)**:
   - GIFs/short clips from Reddit posts are IDEAL for daily news: they're current and show exactly the moment being discussed
   - Reddit GIFs served as MP4 (`preview.redd.it/xxx.gif?format=mp4`) are perfect short clips (3-10s)
   - Reddit videos (`v.redd.it`, `packaged-media.redd.it`) are higher quality but may need trimming
   - Reddit images (`i.redd.it`) work great for Ken Burns shots
   - Download commands:
     - GIF/MP4: `curl -L -o footage/segment_XX_shot_YY.mp4 "https://preview.redd.it/xxx.gif?format=mp4&s=xxx"`
     - Video: `yt-dlp -o footage/segment_XX.mp4 "https://v.redd.it/xxx"` or `yt-dlp -o footage/segment_XX.mp4 "https://packaged-media.redd.it/xxx"`
     - Image: `curl -L -o footage/segment_XX_shot_YY.jpg "https://i.redd.it/xxx.jpg"`
   - **When a Reddit clip is shorter than the shot duration**: The assembler will hold on the last frame. This looks natural for 1-2s. For longer holds, split into two shots — video first, then image.
   - **When a Reddit clip is 9:16 vertical**: The long-form assembler will handle it with letterboxing/blurred background. Set `footage_start: 0` to play from the beginning.

2. **Official F1 channel footage (SECOND PRIORITY)**: Only if Reddit has no usable media:
   - Use `footage_query` to search official FORMULA 1 YouTube channel
   - Prefer recent testing/race footage from the official channel
   - **WARNING**: YouTube compilation videos are unreliable — `footage_start` timestamps often land on wrong teams/content. Always verify with preview frames.

3. **Google Images (THIRD PRIORITY)**: Last resort:
   - Use `--google-search` flag with the footage downloader
   - Good for driver portraits, team principal photos
   - Returns older-season cars — acceptable for portraits, not ideal for on-track action

When writing `script.json`, include a `reddit_media_url` field in each segment or shot where Reddit media is available:
```json
{
  "reddit_media_url": "https://preview.redd.it/xxx.gif?format=mp4&s=xxx",
  "reddit_media_type": "video"
}
```
Or for images:
```json
{
  "reddit_media_url": "https://i.redd.it/abc123.jpg",
  "reddit_media_type": "image"
}
```

The footage downloader **automatically handles Reddit media** when `reddit_media_url` is present in script.json segments/shots. It downloads Reddit media first (highest priority), then falls back to YouTube/Google/Pexels for any segments without Reddit media. No manual `curl` downloads needed.

Just run:
```bash
python3 src/footage_downloader.py --project {name} --google-search
```

**Tips for finding Reddit media:**
- r/formula1 posts with testing footage often have v.redd.it clips of 10-30 seconds
- Image posts frequently have high-res photos from official team social media
- GIF posts (preview.redd.it with `?format=mp4`) are 3-10s clips perfect for shots
- Check top comments for additional media links (streamable, imgur, Twitter clips)
- Cross-posted content from r/F1Technical often has close-up technical photos
- Reddit galleries: download the most relevant image from the gallery

### Phase 3: Video Production

**Follow the `/f1-create-video` pipeline from Phase 3 (Asset Generation)**, with these daily-news-specific overrides:

1. **Before downloading footage**, copy shared logo assets:
   ```bash
   cp shared/assets/daily-news/logo_zoom_16x9.mp4 projects/f1-daily-news-{date}/footage/segment_01.mp4
   cp shared/assets/daily-news/logo_with_f1sound.mp3 projects/f1-daily-news-{date}/audio/segment_01.mp3
   ```
   **Segment 0 (hook) needs its own footage** — do NOT copy shared assets for it. The hook is unique every episode with story-specific visuals.
   **Outro does NOT need footage** — the assembler auto-renders a Remotion CTA card for the outro segment. Do not copy `outro.mp4`.
   The footage downloader will skip segments that already have footage files. The audio generator will skip segments that already have audio files. The logo segment (segment_01) is fully pre-built — no TTS generation or SFX mixing needed.

2. **Set `footage` field** for ALL segments in script.json at creation time (e.g., `"footage": "segment_00.mp4"`). Pre-copied assets (intro/outro) especially need this since the footage_downloader only adds it for segments it downloads.

3. **Duration target is fixed** at 60-90 seconds (not user-chosen like in general shorts).

5. **Always use `--resolution hd --no-music --no-intro --no-sfx --no-credits` when assembling**:
   ```bash
   python3 src/image_video_assembler.py --project f1-daily-news-{date} --resolution hd --no-music --no-intro --no-sfx --no-credits
   ```
   - `--resolution hd`: Daily news doesn't need 4K. HD (1920x1080) is much faster, especially for Ken Burns zoompan on images. 4K zoompan can hang for minutes per image.
   - `--no-intro`: Daily news has its own logo segment (segment_01), skip the long-form animated intro.
   - `--no-sfx`: No transition SFX between segments — the logo segment has its own f1sound whoosh.
   - `--no-credits`: No end credits overlay — daily news has its own outro segment.
   - `--no-music`: Background music competes with the f1sound whoosh in the logo segment. Daily news format is punchy enough without background music.

4. **Shot list examples for daily news** -- when using multi-shot segments, common patterns include:

   **Person + team story:**
   ```json
   {
     "text": "Ferrari has ruled out protesting Mercedes' engine. Fred Vasseur says the team wants clear regulations, not courtroom battles.",
     "context": "Ferrari rules out engine protest",
     "shots": [
       {
         "label": "Vasseur portrait",
         "text_cue": "Ferrari has ruled out protesting Mercedes' engine. Fred Vasseur says",
         "source_type": "image",
         "image_query": "Fred Vasseur Ferrari F1 team principal",
         "ken_burns": "zoom_in",
         "transition_in": "cut"
       },
       {
         "label": "Ferrari on track",
         "text_cue": "the team wants clear regulations, not courtroom battles.",
         "source_type": "youtube_clip",
         "footage_query": "Ferrari SF-26 2026 Bahrain testing on track",
         "footage_start": 30,
         "transition_in": "cross_dissolve"
       }
     ]
   }
   ```

   **Multi-topic segment:**
   ```json
   {
     "text": "Former F1 star Heinz-Harald Frentzen has a plan to fix the 2026 regulations. His proposal: bigger retractable wings and manual-only energy recovery controlled entirely by the driver.",
     "context": "Frentzen fix proposal",
     "shots": [
       {
         "label": "Frentzen portrait",
         "text_cue": "Former F1 star Heinz-Harald Frentzen has a plan",
         "source_type": "image",
         "image_query": "Heinz-Harald Frentzen F1 driver",
         "ken_burns": "zoom_in",
         "transition_in": "cut"
       },
       {
         "label": "2026 active aero wings",
         "text_cue": "to fix the 2026 regulations. His proposal: bigger retractable wings",
         "source_type": "youtube_clip",
         "footage_query": "F1 2026 active aerodynamics wings DRS",
         "footage_start": 10,
         "transition_in": "wipe_left"
       },
       {
         "label": "Driver cockpit controls",
         "text_cue": "and manual-only energy recovery controlled entirely by the driver.",
         "source_type": "youtube_clip",
         "footage_query": "F1 cockpit steering wheel onboard 2026",
         "footage_start": 5,
         "transition_in": "cross_dissolve"
       }
     ]
   }
   ```

   Simple segments (intro/outro) don't need shots -- just use `footage_query` as normal.

### Phase 3.5: Mandatory Footage Review (NEVER SKIP)

**This step is MANDATORY before delivering the final video.** Do NOT skip it even if the assembler succeeds.

After footage download completes and BEFORE final assembly:

1. **Run Gemini vision validation on ALL image shots**:
   ```python
   # For each image shot (segment_XX_shot_YY.jpg), validate with Gemini Flash:
   # "Identify the person/subject. Expected: [description]. Answer MATCH or MISMATCH."
   ```
   Check every portrait, team photo, and image shot against its expected subject. Google Images frequently returns wrong people — especially for less-famous figures (team principals, former drivers, actors).

2. **Validate video clips at their `footage_start` timestamps** — be STRICT about team identity:
   ```bash
   # Extract a frame at the footage_start timestamp and validate:
   ffmpeg -y -ss {footage_start} -i footage/segment_XX_shot_YY.mp4 -frames:v 1 -q:v 2 /tmp/check.jpg
   ```
   **CRITICAL: Use team-specific validation prompts.** Do NOT ask vague questions like "is this an F1 car on track?" — that matches ANY team's car. Instead ask:
   ```
   "What SPECIFIC F1 team's car is shown? Look at livery colors, sponsor logos, and team branding.
   Expected: [Team Name] car ([color description], [key sponsor]).
   Is this EXACTLY the expected team? Answer MATCH or MISMATCH."
   ```
   Examples of strict prompts:
   - "Is this a Racing Bulls car (dark blue/navy with Cash App branding)?" NOT "Is this an F1 car?"
   - "Is this Christian Horner specifically?" NOT "Is this a person at a press conference?"
   - "Is this Albert Park Melbourne circuit?" NOT "Is this an F1 circuit?"

   YouTube compilation videos (e.g., "First Look At Every 2026 Car") cycle through ALL teams — at `footage_start: 20` you might get McLaren when you wanted Racing Bulls. Always verify the SPECIFIC team at the SPECIFIC timestamp.

3. **Fix any mismatches BEFORE assembly**:
   - For wrong images: delete the file, re-download with a more specific query, re-validate
   - For wrong video timestamps: scan multiple timestamps (every 20s) to find correct content, update `footage_start` in script.json
   - For wrong team in compilation video: delete the file, re-download with a driver-specific or team-specific query (e.g., "Yuki Tsunoda Racing Bulls onboard" instead of "Racing Bulls 2026 on track")
   - For fundamentally wrong video clips: delete and re-download with a better `footage_query`

4. **Detect PNG files saved as .jpg** (causes zoompan to hang):
   ```bash
   file footage/*.jpg | grep PNG
   ```
   Convert any PNG-as-JPG files: `ffmpeg -y -i input.png -q:v 2 output.jpg`

5. **Re-assemble only after ALL footage passes validation**:
   ```bash
   rm -f projects/{name}/output/final.mp4 projects/{name}/output/segment_*.mp4
   python3 src/image_video_assembler.py --project {name} --resolution hd --no-music --no-intro --no-sfx --no-credits
   ```

**Common validation failures:**
- Google Images returns a random woman instead of a male team principal
- YouTube paddock arrival video starts with a building/flag shot before drivers appear (need to offset `footage_start` by 30-40s)
- YouTube compilation videos ("all 2026 cars") show the WRONG team at the given timestamp — always use team/driver-specific queries
- Generic F1 search returns footage of wrong team's car
- Actor/celebrity images return circuit photos instead of the person

### Phase 3.75: Post-Assembly Validation (NEVER SKIP)

**This step is MANDATORY after every assembly, BEFORE delivering the video to the user.** A successful assembler exit code does NOT mean the video is correct.

1. **Duration sanity check**: Compare `final.mp4` total duration against the sum of all audio file durations + topic card time (~1.5s per topic card). They should be within 5%.
   ```bash
   ffprobe -v error -show_entries format=duration -of csv=p=0 projects/{name}/output/final.mp4
   # Compare against: sum of all audio/*.mp3 durations + (num_topic_cards × 1.5)
   ```

2. **Hook segment check (CRITICAL)**: The hook is the most important segment — if it's broken, the whole video feels broken. Extract the first 15s of the final video audio and verify the hook voiceover plays completely without cutting off:
   ```bash
   ffmpeg -y -i projects/{name}/output/final.mp4 -t 15 -q:a 2 /tmp/hook_check.mp3
   # Listen or check duration against audio/segment_00.mp3 duration
   ```

3. **Segment-by-segment duration check**: Parse the assembler log for each segment's reported video duration. Compare against each segment's audio file duration. Flag any segment where video duration is <80% of audio duration — that means footage is too short and audio will be cut off or video will freeze.
   ```bash
   # For each segment, compare:
   ffprobe -v error -show_entries format=duration -of csv=p=0 audio/segment_XX.mp3
   # Against the segment's video clip duration in output/segment_XX.mp4
   ```

4. **`footage_start` consistency check**: Verify that top-level `footage_start` and shot-level `footage_start` values are consistent. When footage files are replaced (e.g., pre-trimmed clips), BOTH levels must be updated. The assembler uses the top-level value for single-shot segments.
   ```bash
   # Check script.json for any segment where top-level footage_start != 0
   # but shots[0].footage_start == 0 (or vice versa) — this is a mismatch
   python3 -c "
   import json
   with open('projects/{name}/script.json') as f: script = json.load(f)
   for seg in script['segments']:
       top = seg.get('footage_start', 0)
       shots = seg.get('shots', [])
       if shots and shots[0].get('footage_start', 0) != top:
           print(f'MISMATCH segment {seg[\"id\"]}: top={top}, shot[0]={shots[0].get(\"footage_start\", 0)}')
   "
   ```

5. **Fix any issues BEFORE delivery**: If any check fails, fix the root cause and re-assemble:
   ```bash
   rm -f projects/{name}/output/final.mp4 projects/{name}/output/segment_*.mp4
   python3 src/image_video_assembler.py --project {name} --resolution hd --no-music --no-intro --no-sfx --no-credits
   ```

### Phase 4: Post-Production

#### Update Reddit Ideas

After creating the video, update `shared/reddit_ideas.json`:
- Add any new story ideas discovered during research
- Mark used stories with `"status": "used"` and `"used_date"`

### Output

Final video: `projects/f1-daily-news-{date}/output/final.mp4`
- Format: 1920x1080 (16:9 horizontal)
- Duration: ~60-90 seconds
- Style: Fast-paced news update

### Next Step

After the video is created, suggest:
```
/f1-upload-video
```
to upload to YouTube with appropriate daily news metadata.

### Daily News Lessons

1. **Hook pattern, not generic intro** — Segment 0 is always the biggest story of the day as a scroll-stopping hook, NOT a generic "Welcome to F1 Daily News" intro. The logo segment (segment 1) follows the hook, then segment 2 continues the hook story with more detail. This creates a satisfying payoff and keeps viewers watching.

2. **Reddit videos with on-screen text need `no_text: true`** — When using Reddit videos that have their own text/graphics overlays (comparison videos, infographics, data visualizations), add `"no_text": true` to the segment. Otherwise our text overlay clashes with the video's built-in text and becomes unreadable.

3. **Person portraits: photos beat YouTube clips** — For team principals, former drivers, and personnel (e.g., Damon Hill, Jenson Button, Claire Williams), use `source_type: "image"` with Google Images search (`--google-search` flag). YouTube clips of these people are either old race footage or interview clips that don't match the news context. Ken Burns zoom on a good portrait looks professional and clean.

4. **Fandom Wiki images are unusable** — F1 Fandom Wiki serves WebP format (despite .jpg URLs) at only 300px wide. Far too small for 1920x1080 video. Use Google Images via the footage downloader's `--google-search` flag instead.

5. **Ferrari footage needs specific channel/driver queries** — Generic queries like "Ferrari SF-26 sidepod close up" return Barcelona Highlights compilations that land on non-Ferrari content at the given timestamp. Use the official Ferrari channel (e.g., "SF-26 Fires Up") or F1 channel with driver-specific queries (e.g., "Charles Leclerc Sets The Fastest Lap Pre-Season Testing").

6. **YouTube search picks wrong year — add context** — Queries for "Leclerc fastest lap Bahrain 2026" return 2022 Bahrain pole laps because yt-dlp relevance scoring doesn't distinguish years well. Always include extra context like "Pre-Season Testing", "Day 2", or the specific video series name to disambiguate from older seasons.

7. **Pronunciation vs spelling in script.json** — The `text` field is used for BOTH audio generation AND text overlay. If you respell a name for pronunciation (e.g., "Laurent" → "Lorahn"), the misspelling will appear on screen. Fix: use phonetic spelling for audio generation, then restore correct spelling before video assembly. Cached MP3s won't regenerate as long as the files exist.

8. **16:9 format means no blurred backgrounds needed** — Since daily news now uses 16:9 horizontal format, most footage plays natively without letterboxing. Vertical (9:16) Reddit clips will be handled automatically by the long-form assembler.

9. **Skip jittery interview cuts** — Interview footage from YouTube often has abrupt transitions at clip boundaries. Always preview the first 1-2 seconds and add offset to skip any jitter (e.g., start at 525s instead of 524s).

10. **Use official team/manufacturer videos for technical topics** — For power unit, engine, or technical regulation topics, use official team channels (Mercedes "Road to 2026", Honda PU Launch) or the official F1 channel's explainer videos. Clean CGI animations work better than on-track footage for technical concepts.

11. **Instagram challenge_required** — Instagram may trigger security challenges on upload. The user needs to approve login from the Instagram app before retrying.

12. **Image shots use Ken Burns in 16:9** — Image shots in the long-form assembler get Ken Burns zoom/pan effects automatically. The assembler scales images to fill the 1920x1080 frame. No `no_text` flags needed since long-form doesn't burn in text overlays.

13. **Reddit media URLs get truncated by the fetcher** — `reddit_fetcher.py` output truncates the `s=` hash parameter in `preview.redd.it` URLs, causing 403 errors. Fix: fetch the post JSON directly with `curl -s -L -H "User-Agent: Mozilla/5.0" "https://www.reddit.com/r/formula1/comments/{id}/.json"` and extract full URLs with `html.unescape()`. `i.redd.it` URLs work fine.

14. **Reddit images saved as .mp4 crash the single-shot path** — If a Reddit image gets saved with a `.mp4` extension, the single-shot path uses `trim=start=...` which produces zero video frames from a still image. Fix: rename to `.jpg` and use `source_type: "image"`, or split into a multi-shot segment.

15. **Always QA footage content, not just existence** — The footage downloader often returns plausible but wrong content. Use `--list` after download to check video titles. Color signatures: Red (168,66,49) = Ferrari, Orange (255,128,0) = McLaren, Dark green (34,153,113) = Aston Martin, Dark blue (42,44,66) = Red Bull.

16. **Long-form uses SRT captions, not burned-in text** — Unlike the shorts assembler, the long-form assembler (`image_video_assembler.py`) does NOT burn text overlays into the video. Captions are generated as separate SRT files for YouTube's caption system. This is standard for long-form YouTube content.

17. **Never mix SFX into TTS and treat it as the original** — Always keep a clean `_clean.mp3` backup of TTS immediately after generation, before any audio mixing. The audio generator caches by file existence — if you overwrite `segment_XX.mp3` with a mixed version, it's treated as "cached" on next run.

18. **f1sound.mp3 is an engine recording, not a clean whoosh** — The file at `shared/audio/f1sound.mp3` (6s, stereo) has: 0-1.1s rev-up, 1.1-2.0s peak, 2.0-3.4s Doppler tail, 3.4s+ silence. Use 0-4s at `atempo=2.0` to compress into a single perceived whoosh.

19. **Overlap f1sound with voice ending for smooth transitions** — Start f1sound 1s before voice ends using `adelay=(voice_duration - 1.0) * 1000` with `amix duration=longest`. This creates a smooth crossfade instead of an abrupt voice→SFX cut.

20. **Gemini vision review is MANDATORY, not optional** — Never deliver a video without running Gemini Flash validation on every image shot and every video clip at its `footage_start` timestamp. Google Images returns wrong people ~20% of the time (e.g., a random woman instead of Christian Horner). YouTube clips land on wrong content ~30% of the time (e.g., a Bahrain building instead of Verstappen walking). The footage downloader checking file existence is NOT enough — you must verify the CONTENT matches the narrative. Fix all mismatches before assembly.

21. **Validation prompts must be team-specific, not generic** — When validating footage with Gemini, ask "Is this SPECIFICALLY a Racing Bulls car (dark blue/navy with Cash App)?" not "Is this an F1 car on track?" The latter matches ANY team's car and will pass a McLaren when you needed Racing Bulls. YouTube compilation videos ("First Look At Every 2026 Car") cycle through all teams — at `footage_start: 20` you get whichever team appears at that timestamp, which is usually wrong. Use driver-specific or team-specific `footage_query` values (e.g., "Yuki Tsunoda Racing Bulls onboard" not "Racing Bulls 2026 on track").

22. **Lower thirds and topic cards are ON by default** — The assembler automatically adds team-colored lower-third overlays (story title + "F1 BURNOUTS" branding) to news segments, and topic transition cards between stories. Segments 0 (hook) and 1 (logo) are skipped. Use `--no-lower-thirds` or `--no-topic-cards` to disable. Add `lower_third_title` to script.json for custom titles; otherwise auto-generated from `context`.

23. **Single-image segments with `footage` pointing to .jpg work correctly** — The assembler detects image extensions (.jpg, .jpeg, .png, .webp) in the `footage` field and routes to `create_image_clip()` with Ken Burns effect instead of `process_video_clip()`. Without this, images produced zero video frames and caused the video to freeze.

24. **PNG files saved as .jpg cause zoompan to hang** — Reddit and Google Images sometimes serve PNG despite .jpg URLs. Detect with `file footage/*.jpg | grep PNG` and convert with `ffmpeg -y -i input.png -q:v 2 output.jpg`. Always use `--resolution hd` for daily news (4K zoompan is extremely slow).

25. **Outro is Remotion-rendered, not footage** — The assembler auto-detects segments with "outro" or "cta" in context and renders a Remotion CTA card (logo + like/subscribe/comment + accent lines + "SEE YOU TOMORROW"). No need to copy `shared/assets/daily-news/outro.mp4` to projects. Falls back to footage if Remotion fails.

26. **50fps source footage breaks concat** — Official F1 broadcast footage is often 50fps (PAL). Mixed with 30fps assembler segments, concat demuxer produces mismatched video/audio durations (video stream shorter than audio = black frames at end). The `process_video_clip()` function now forces `-r 30` on all clips. If you encounter missing video at the end of a video, check `ffprobe -select_streams v:0 -show_entries stream=r_frame_rate` on the source.

27. **Topic card duration 1.5s, not 0.8s** — `TOPIC_CARD_DURATION` in config.py was increased from 0.8s to 1.5s. At 0.8s the character-stagger reveal text was unreadable. 1.5s gives enough time to read the title.

28. **Topic cards have swoosh SFX** — `create_topic_card()` now mixes `shared/sfx/whoosh_clean.mp3` into the topic card audio using `apad` + `aresample=24000`. This gives an audible transition cue.

29. **Thumbnail: use dramatic footage frame, not auto-generator** — The `thumbnail_generator.py` auto-picks a frame from the video which is often boring. Better approach: manually select the most dramatic footage image (crash, close-up, action) and build thumbnail with FFmpeg: `scale=1280:720` + `eq=brightness=-0.08:contrast=1.3` + `drawbox` dark overlay + bold `drawtext` in white + team color + "F1 DAILY NEWS" branding. Thumbnails can be replaced after upload via `youtube.thumbnails().set()`.

30. **Logo intro uses logo.mp4 at 2.22x speed** — The logo animation source (`shared/assets/logo/logo.mp4`, 8s, 1280x720) is sped up with `setpts=PTS/2.22` to fill the 3.6s audio slot smoothly. Previous 4x speed felt like a frozen pause at the end. No tpad/hold needed at 2.22x.
