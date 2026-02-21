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
         "text": "Welcome to F1 Daily News, your sixty-second briefing on everything Formula One. It's [month] [day]. Here's what you need to know.",
         "context": "Intro - establish daily news format",
         "visual": "F1 2026 cars lined up on the grid or driving in formation, wide shot",
         "footage_query": "F1 2026 cars grid formation",
         "footage_start": 10
       },
       // ... news segments (one per story, 1-2 sentences each) ...
       {
         "id": N,
         "text": "That's your F1 Daily News. Subscribe, hit the bell, and drop a comment with your thoughts. See you tomorrow!",
         "context": "Outro - CTA for subscribe/like/comment (reusable)",
         "visual": "High-speed F1 racing action montage, multiple cars battling on track",
         "footage_query": "F1 racing action montage",
         "footage_start": 25
       }
     ]
   }
   ```

3. **Script Guidelines**:
   - **Intro date format**: Use only month and day (e.g., "February first"), do NOT include the weekday (no "Saturday", "Monday", etc.)
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

The **intro** and **outro** segments are designed to be consistent across all daily news videos:
- Intro: "Welcome to F1 Daily News, your sixty-second briefing..."
- Outro: "That's your F1 Daily News. Subscribe, hit the bell..."

This builds brand recognition and viewer expectations.

### Shared Assets

Pre-downloaded footage for consistent elements is stored in `shared/assets/daily-news/`:
- `intro.mp4` - F1 cars/grid footage for the intro segment (segment_00)
- `outro.mp4` - F1 racing action montage for the outro segment

These assets should be copied to each new project's footage folder to avoid redundant downloads and ensure visual consistency across episodes.

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

1. **Before downloading footage**, copy shared intro/outro assets:
   ```bash
   cp shared/assets/daily-news/intro.mp4 projects/f1-daily-news-{date}/footage/segment_00.mp4
   cp shared/assets/daily-news/outro.mp4 projects/f1-daily-news-{date}/footage/segment_{outro_index}.mp4
   ```
   The footage downloader will skip segments that already have footage files.

2. **Set `footage` field** for ALL segments in script.json at creation time (e.g., `"footage": "segment_00.mp4"`). Pre-copied assets (intro/outro) especially need this since the footage_downloader only adds it for segments it downloads.

3. **Duration target is fixed** at 60-90 seconds (not user-chosen like in general shorts).

5. **Always use `--segment-transition cut` when assembling**:
   ```bash
   python3 src/video_assembler.py --project f1-daily-news-{date} --segment-transition cut
   ```
   The default `cross_dissolve` transition causes progressive audio-video drift: each 0.3s xfade overlap shortens the video track but not the audio, so by segment 7-8 the voiceover is ~2 seconds ahead of the visuals. Hard cuts eliminate this drift and better suit the punchy news format.

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
