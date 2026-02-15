# F1 Daily News Update

Create a daily F1 news update short video by finding trending stories from the past 24 hours and assembling them into a news-style video.

## Instructions

You are creating a daily F1 news update short video. This command orchestrates the full workflow:
1. Find trending F1 stories from Reddit (past 24 hours)
2. Get user confirmation on which stories to include
3. Create a news-style short video with all selected stories

### Phase 1: Find Trending Stories

Use `/f1-find-content day` to discover trending F1 stories from the past 24 hours.

This will:
- Search Reddit's r/formula1 for popular discussions from the past 24 hours
- Filter out duplicate ideas already in `shared/reddit_ideas.json`
- Present a ranked list of newsworthy stories

After reviewing the ideas from `/f1-find-content day`:

1. **CHECKPOINT - User Selection**: 
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

### Phase 3: Video Production

**Follow the `/f1-create-short` pipeline from step 5 (Download Footage) through step 13 (Verify Final Output)**, with these daily-news-specific overrides:

1. **Before downloading footage**, copy shared intro/outro assets:
   ```bash
   cp shared/assets/daily-news/intro.mp4 projects/f1-daily-news-{date}/footage/segment_00.mp4
   cp shared/assets/daily-news/outro.mp4 projects/f1-daily-news-{date}/footage/segment_{outro_index}.mp4
   ```
   The footage downloader will skip segments that already have footage files.

2. **Set `footage` field** for ALL segments in script.json at creation time (e.g., `"footage": "segment_00.mp4"`). Pre-copied assets (intro/outro) especially need this since the footage_downloader only adds it for segments it downloads.

3. **Duration target is fixed** at 60-90 seconds (not user-chosen like in general shorts).

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
