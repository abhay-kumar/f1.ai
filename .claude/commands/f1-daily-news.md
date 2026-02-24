# F1 Daily News Update

Create a daily F1 news update short video by finding trending stories from the past 24 hours and assembling them into a news-style video.

## Instructions

You are creating a daily F1 news update short video. This command orchestrates the full workflow:
1. Find trending F1 stories from Reddit (past 24 hours)
2. Get user confirmation on which stories to include
3. Create a news-style short video with all selected stories

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
   - Recommend 6-8 stories for a ~60-90 second video
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
   - Use the `shots` array for segments covering multiple topics (see `/f1-create-short` Shot List section for full reference)

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
- Outro: "That's your daily news. Like, subscribe, and drop your thoughts in the comments. See you tomorrow!"

The **hook** (segment 0) is unique every episode — always the biggest story, with custom footage. This builds brand recognition while keeping the opening fresh and scroll-stopping.

### Shared Assets

Pre-downloaded footage and audio for consistent elements is stored in `shared/assets/daily-news/`:
- `outro.mp4` - F1 racing action montage for the outro segment
- `logo_with_f1sound.mp3` - Pre-mixed logo segment audio: TTS "Here's what happened in F1 in the last twenty-four hours" + f1sound whoosh (2x speed, overlapped 1s with voice ending). Duration: 3.6s
- `logo_zoom.mp4` - Pre-rendered logo zoom-in video (fast zoom, `zoom+0.008`, no audio track). Duration: 3.6s
- `logo_voice.mp3` - Clean TTS voice only (no SFX), for remixing if needed. Duration: 2.58s
- `f1sound_2x.mp3` - f1sound.mp3 0-4s at 2x speed, standalone whoosh clip. Duration: 2.0s
- `logo.jpg` - Source logo image for regenerating zoom video if needed

These assets should be copied to each new project's footage/audio folders to avoid redundant downloads, TTS generation, and audio mixing. The logo segment (segment_01) should NEVER be recreated from scratch — always use the pre-built assets.

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

**Priority order for ALL visual assets:**

1. **Reddit media (FIRST PRIORITY — use for every story if available)**:
   - GIFs/short clips from Reddit posts are IDEAL for shorts: they're vertical-friendly, current, and show exactly the moment being discussed
   - Reddit GIFs served as MP4 (`preview.redd.it/xxx.gif?format=mp4`) are perfect short clips (3-10s)
   - Reddit videos (`v.redd.it`, `packaged-media.redd.it`) are higher quality but may need trimming
   - Reddit images (`i.redd.it`) work great for Ken Burns shots
   - Download commands:
     - GIF/MP4: `curl -L -o footage/segment_XX_shot_YY.mp4 "https://preview.redd.it/xxx.gif?format=mp4&s=xxx"`
     - Video: `yt-dlp -o footage/segment_XX.mp4 "https://v.redd.it/xxx"` or `yt-dlp -o footage/segment_XX.mp4 "https://packaged-media.redd.it/xxx"`
     - Image: `curl -L -o footage/segment_XX_shot_YY.jpg "https://i.redd.it/xxx.jpg"`
   - **When a Reddit clip is shorter than the shot duration**: The assembler will hold on the last frame. This looks natural for 1-2s. For longer holds, split into two shots — video first, then image.
   - **When a Reddit clip is 9:16 vertical**: Perfect — no blurred-background letterboxing needed. Set `footage_start: 0` to play from the beginning.

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

**Follow the `/f1-create-short` pipeline from step 5 (Download Footage) through step 14 (Verify Final Output)**, with these daily-news-specific overrides:

1. **Before downloading footage**, copy shared logo/outro assets:
   ```bash
   cp shared/assets/daily-news/logo_zoom.mp4 projects/f1-daily-news-{date}/footage/segment_01.mp4
   cp shared/assets/daily-news/logo_with_f1sound.mp3 projects/f1-daily-news-{date}/audio/segment_01.mp3
   cp shared/assets/daily-news/outro.mp4 projects/f1-daily-news-{date}/footage/segment_{outro_index}.mp4
   ```
   **Segment 0 (hook) needs its own footage** — do NOT copy shared assets for it. The hook is unique every episode with story-specific visuals.
   The footage downloader will skip segments that already have footage files. The audio generator will skip segments that already have audio files. The logo segment (segment_01) is fully pre-built — no TTS generation or SFX mixing needed.

2. **Set `footage` field** for ALL segments in script.json at creation time (e.g., `"footage": "segment_00.mp4"`). Pre-copied assets (intro/outro) especially need this since the footage_downloader only adds it for segments it downloads.

3. **Duration target is fixed** at 60-90 seconds (not user-chosen like in general shorts).

5. **Always use `--segment-transition cut --no-music` when assembling**:
   ```bash
   python3 src/video_assembler.py --project f1-daily-news-{date} --segment-transition cut --no-music
   ```
   - `--segment-transition cut`: The default `cross_dissolve` transition causes progressive audio-video drift: each 0.3s xfade overlap shortens the video track but not the audio, so by segment 7-8 the voiceover is ~2 seconds ahead of the visuals. Hard cuts eliminate this drift and better suit the punchy news format.
   - `--no-music`: Background music at even 4% volume competes with the f1sound whoosh in the logo segment. Daily news format is punchy enough without background music.

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

### Phase 4: Post-Production

#### Update Reddit Ideas

After creating the video, update `shared/reddit_ideas.json`:
- Add any new story ideas discovered during research
- Mark used stories with `"status": "used"` and `"used_date"`

### Output

Final video: `projects/f1-daily-news-{date}/output/final.mp4`
- Format: 1080x1920 (9:16 vertical)
- Duration: ~60-90 seconds
- Style: Fast-paced news update

### Next Step

After the video is created, suggest:
```
/f1-upload-short
```
to upload to YouTube with appropriate daily news metadata.

### Daily News Lessons

1. **Hook pattern, not generic intro** — Segment 0 is always the biggest story of the day as a scroll-stopping hook, NOT a generic "Welcome to F1 Daily News" intro. The logo segment (segment 1) follows the hook, then segment 2 continues the hook story with more detail. This creates a satisfying payoff and keeps viewers watching.

2. **Reddit videos with on-screen text need `no_text: true`** — When using Reddit videos that have their own text/graphics overlays (comparison videos, infographics, data visualizations), add `"no_text": true` to the segment. Otherwise our text overlay clashes with the video's built-in text and becomes unreadable.

3. **Person portraits: photos beat YouTube clips** — For team principals, former drivers, and personnel (e.g., Damon Hill, Jenson Button, Claire Williams), use `source_type: "image"` with Google Images search (`--google-search` flag). YouTube clips of these people are either old race footage or interview clips that don't match the news context. Ken Burns zoom on a good portrait looks professional and clean.

4. **Fandom Wiki images are unusable** — F1 Fandom Wiki serves WebP format (despite .jpg URLs) at only 300px wide. Far too small for 1080x1920 shorts. Use Google Images via the footage downloader's `--google-search` flag instead.

5. **Ferrari footage needs specific channel/driver queries** — Generic queries like "Ferrari SF-26 sidepod close up" return Barcelona Highlights compilations that land on non-Ferrari content at the given timestamp. Use the official Ferrari channel (e.g., "SF-26 Fires Up") or F1 channel with driver-specific queries (e.g., "Charles Leclerc Sets The Fastest Lap Pre-Season Testing").

6. **YouTube search picks wrong year — add context** — Queries for "Leclerc fastest lap Bahrain 2026" return 2022 Bahrain pole laps because yt-dlp relevance scoring doesn't distinguish years well. Always include extra context like "Pre-Season Testing", "Day 2", or the specific video series name to disambiguate from older seasons.

7. **Pronunciation vs spelling in script.json** — The `text` field is used for BOTH audio generation AND text overlay. If you respell a name for pronunciation (e.g., "Laurent" → "Lorahn"), the misspelling will appear on screen. Fix: use phonetic spelling for audio generation, then restore correct spelling before video assembly. Cached MP3s won't regenerate as long as the files exist.

8. **Blurred background aspect ratio fix** — The common `scale=1080:-2` for foreground in 9:16 frame causes stretching on some sources. For 16:9 (1920x1080) sources, explicitly use `scale=1080:608` to maintain correct aspect ratio.

9. **Skip jittery interview cuts** — Interview footage from YouTube often has abrupt transitions at clip boundaries. Always preview the first 1-2 seconds and add offset to skip any jitter (e.g., start at 525s instead of 524s).

10. **Use official team/manufacturer videos for technical topics** — For power unit, engine, or technical regulation topics, use official team channels (Mercedes "Road to 2026", Honda PU Launch) or the official F1 channel's explainer videos. Clean CGI animations work better than on-track footage for technical concepts.

11. **Instagram challenge_required** — Instagram may trigger security challenges on upload. The user needs to approve login from the Instagram app before retrying.

12. **Image shots use upper-zone layout** — Image shots in shorts are automatically fitted into the top 1270px of the 1080x1920 frame. The blurred background fills the full frame, and text renders below the image with no overlap. `no_text` flags are never needed on image shots.

13. **Reddit media URLs get truncated by the fetcher** — `reddit_fetcher.py` output truncates the `s=` hash parameter in `preview.redd.it` URLs, causing 403 errors. Fix: fetch the post JSON directly with `curl -s -L -H "User-Agent: Mozilla/5.0" "https://www.reddit.com/r/formula1/comments/{id}/.json"` and extract full URLs with `html.unescape()`. `i.redd.it` URLs work fine.

14. **Reddit images saved as .mp4 crash the single-shot path** — If a Reddit image gets saved with a `.mp4` extension, the single-shot path uses `trim=start=...` which produces zero video frames from a still image. Fix: rename to `.jpg` and use `source_type: "image"`, or split into a multi-shot segment.

15. **Always QA footage content, not just existence** — The footage downloader often returns plausible but wrong content. Use `--list` after download to check video titles. Color signatures: Red (168,66,49) = Ferrari, Orange (255,128,0) = McLaren, Dark green (34,153,113) = Aston Martin, Dark blue (42,44,66) = Red Bull.

16. **Text overlay uses team colors, not white** — The shorts assembler renders text in team-specific colors (e.g., Ferrari red `#E8002D`, McLaren orange `#FF8000`). Text also has a black shadow at +3px offset.

17. **Never mix SFX into TTS and treat it as the original** — Always keep a clean `_clean.mp3` backup of TTS immediately after generation, before any audio mixing. The audio generator caches by file existence — if you overwrite `segment_XX.mp3` with a mixed version, it's treated as "cached" on next run.

18. **f1sound.mp3 is an engine recording, not a clean whoosh** — The file at `shared/audio/f1sound.mp3` (6s, stereo) has: 0-1.1s rev-up, 1.1-2.0s peak, 2.0-3.4s Doppler tail, 3.4s+ silence. Use 0-4s at `atempo=2.0` to compress into a single perceived whoosh.

19. **Overlap f1sound with voice ending for smooth transitions** — Start f1sound 1s before voice ends using `adelay=(voice_duration - 1.0) * 1000` with `amix duration=longest`. This creates a smooth crossfade instead of an abrupt voice→SFX cut.
