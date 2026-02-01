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

### Phase 2: Create News Video

Once user confirms story selection, create the daily news video:

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
         "footage_query": "F1 2026 cars grid formation",
         "footage_start": 10
       },
       // ... news segments (one per story, 1-2 sentences each) ...
       {
         "id": N,
         "text": "That's your F1 Daily News. Subscribe, hit the bell, and drop a comment with your thoughts. See you tomorrow!",
         "context": "Outro - CTA for subscribe/like/comment (reusable)",
         "footage_query": "F1 racing action montage",
         "footage_start": 25
       }
     ]
   }
   ```

3. **Script Guidelines**:
   - **Intro date format**: Use only month and day (e.g., "February first"), do NOT include the weekday (no "Saturday", "Monday", etc.)
   - Keep each news item to 1-2 crisp sentences. If text wraps to 8+ lines, the assembler auto-splits into two timed parts at a natural break point — part 1 shows first, then gets replaced by part 2. Still prefer shorter segments when possible.
   - Use present tense for immediacy ("Ferrari reveals...", "Hamilton admits...")
   - Include specific details (names, numbers, quotes)
   - Transition naturally between stories
   - Total target: ~60-90 seconds

4. **CHECKPOINT - Script Review**:
   - Present the complete script to user
   - Show all segments with text and footage queries
   - **STOP and wait for user approval**
   - Make any requested changes before proceeding

5. **Video Production Pipeline**:
   ```bash
   # Generate voiceovers with Gemini TTS
   python3 src/audio_generator.py --project f1-daily-news-{date}
   
   # Copy reusable intro and outro footage (DO THIS BEFORE downloading other footage)
   cp shared/assets/daily-news/intro.mp4 projects/f1-daily-news-{date}/footage/segment_00.mp4
   cp shared/assets/daily-news/outro.mp4 projects/f1-daily-news-{date}/footage/segment_{outro_index}.mp4
   
   # Download footage for all segments EXCEPT intro (segment_00) and outro (they're pre-copied)
   python3 src/footage_downloader.py --project f1-daily-news-{date}
   
   # Verify downloaded footage titles match intended content
   python3 src/footage_downloader.py --project f1-daily-news-{date} --list
   
   # If any segment has wrong footage, retry (auto-downloads top result):
   python3 src/footage_downloader.py --project f1-daily-news-{date} --segment {id} --query "alternative search"
   
   # Or preview candidates first without downloading:
   python3 src/footage_downloader.py --project f1-daily-news-{date} --segment {id} --query "alternative search" --dry-run
   
   # Extract preview frames
   python3 src/preview_extractor.py --project f1-daily-news-{date}
   
   # Assemble final video
   python3 src/video_assembler.py --project f1-daily-news-{date}
   ```
   
   **IMPORTANT**: The outro footage is stored at `shared/assets/daily-news/outro.mp4` and should be copied to the project's footage folder as the last segment BEFORE running the footage downloader. This ensures consistency across all daily news videos and avoids unnecessary downloads.

6. **Footage Verification**:
   - Run `--list` first to check downloaded video titles match each news story
   - Prefer official F1 channel footage over fan channels (fan channels often have screen recordings or news anchors)
   - For team-specific footage, use subtitle search on broad official videos:
     ```bash
     yt-dlp --write-auto-sub --sub-lang en --skip-download --sub-format vtt -o /tmp/subs "URL"
     grep -i "team name" /tmp/subs*.vtt
     ```
   - **Add 1-2 seconds buffer to subtitle timestamps** - Video visuals often lag behind narration. If subtitles mention "Cadillac" at 240s, the visual may still show the previous team. Use 241-242s instead.
   - Delete old previews (`rm previews/segNN_*.jpg`) before re-extracting after footage replacement
   - Update `footage_start` timestamps as needed
   - **Iterate quickly**: Update timestamp in script.json → run video_assembler.py → review → repeat until correct

7. **Final Output**:
   - Verify video/audio sync
   - Report final video location and specs

### News Writing Style

- **Crisp and punchy**: No filler words, every word counts
- **Active voice**: "Ferrari reveals" not "It was revealed by Ferrari"
- **Specific details**: Include names, numbers, dates
- **Natural flow**: Stories should transition smoothly
- **Variety**: Mix team news, driver news, technical updates, controversies
- **NEVER use the word "Quote"**: When including quotes, integrate them naturally into the narration. Instead of "Quote: 'I'll never forget this'", write "In his words: I'll never forget this" or simply state the quote directly as part of the narrative.

### Example News Segment

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

**IMPORTANT**: After copying intro/outro assets, ensure their segments in script.json have the `footage` field set (e.g., `"footage": "segment_00.mp4"`). The footage_downloader only adds this field for segments it downloads, not for pre-copied files. Missing `footage` fields will cause video_assembler.py to fail with `KeyError: 'footage'`.

### Composite Segments (Image + Video)

When a story benefits from showing both a static image AND real footage (e.g., Antonov plane photo + Aston Martin on track):

1. **Create assets folder**: `mkdir -p projects/{project}/assets`
2. **Save the image** to `projects/{project}/assets/`
3. **Download source video** (e.g., official F1 shakedown) to `projects/{project}/assets/`
4. **Find timestamp** using subtitle search:
   ```bash
   yt-dlp --write-auto-sub --sub-lang en --skip-download --sub-format vtt -o /tmp/subs "VIDEO_URL"
   grep -i "team name" /tmp/subs*.vtt
   ```
5. **Create composite** using FFmpeg with blurred background:
   ```bash
   # Image part (2-4 seconds with Ken Burns zoom)
   ffmpeg -y -loop 1 -i assets/image.jpg -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.002,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=60:s=1080x1920:fps=30" -t 2 -c:v h264_videotoolbox -pix_fmt yuv420p -r 30 /tmp/image_part.mp4
   
   # Video part with BLURRED BACKGROUND (not black bars or stretched)
   ffmpeg -y -ss {timestamp} -i assets/source_video.mp4 -t 12 -filter_complex "
   [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:20[bg];
   [0:v]scale=1080:-2[fg];
   [bg][fg]overlay=(W-w)/2:(H-h)/2
   " -c:v h264_videotoolbox -pix_fmt yuv420p -r 30 -an /tmp/video_part.mp4
   
   # Concatenate
   echo "file '/tmp/image_part.mp4'" > /tmp/concat.txt
   echo "file '/tmp/video_part.mp4'" >> /tmp/concat.txt
   ffmpeg -y -f concat -safe 0 -i /tmp/concat.txt -c copy footage/segment_XX.mp4
   ```

**Key rules for composite segments:**
- **Image duration**: 2-4 seconds (shorter for supporting visuals, longer for key images)
- **Video duration**: Create 2-3 seconds LONGER than needed to avoid freeze at end
- **Blurred background**: Use the filter above - NOT black bars or stretched video
- **Update script.json**: Set `footage_start: 0` since composite starts from beginning

### Troubleshooting

#### yt-dlp 403 Errors (HD Downloads Fail)
YouTube requires PO Token authentication for HD formats. Install the required plugins:
```bash
pip install -U yt-dlp
pip install yt-dlp-get-pot bgutil-ytdlp-pot-provider
```

#### Video Shows Wrong Team
Subtitle timestamps don't always match visuals. Add 1-2 seconds buffer:
- If subtitles say "Cadillac" at 240s, try 241s or 242s
- Iterate: update script.json → run video_assembler.py → review → adjust

#### KeyError: 'footage'
Ensure all segments (including intro/outro) have the `footage` field in script.json.

### Update Reddit Ideas

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
