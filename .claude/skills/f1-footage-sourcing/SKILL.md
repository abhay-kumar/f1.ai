---
name: f1-footage-sourcing
description: Use whenever sourcing, downloading, validating, or troubleshooting footage for any F1 Burnouts video — auto-trigger when footage, yt-dlp, Gemini validation, Reddit media, image sourcing, preview extraction, or footage_start is mentioned.
---

# F1 Footage Sourcing

## Source Priority

**Always follow this order when sourcing visuals:**

1. **Reddit media (FIRST)** — Current, event-specific, matches the story exactly
2. **Official F1 YouTube channel (SECOND)** — Clean, high quality, consistent
3. **Official team/manufacturer channels** — For technical topics, CGI animations
4. **Google Images (THIRD)** — Good for portraits, team principals; returns older-season cars
5. **Pexels/Unsplash (LAST RESORT)** — Generic stock photos

### Why Reddit First
Reddit posts almost always contain images, GIFs, or video clips purpose-made for the story. YouTube compilation videos are unreliable (wrong timestamps, wrong teams, burned-in graphics). Google Images return old-season cars. Reddit media is current, relevant, and matches exactly.

### Why Official F1 Channel
Fan channels (e.g., USA SportsLine, Saile Racing) often have screen recordings with visible cursors, news anchors, or low-quality re-uploads. Official FORMULA 1 channel footage is consistently clean and high quality.

---

## Reddit Media

### URL Patterns
- Images: `https://i.redd.it/xxxxx.jpg` or `https://preview.redd.it/xxxxx.jpg`
- GIFs (served as MP4): `https://preview.redd.it/xxxxx.gif?format=mp4&s=xxxxx`
- Videos: `https://v.redd.it/xxxxx` or `https://packaged-media.redd.it/xxxxx`

### Reddit Media Gotchas
- **URL truncation**: `reddit_fetcher.py` truncates the `s=` hash parameter in `preview.redd.it` URLs, causing 403 errors. Fix: fetch the post JSON directly with `curl -s -L -H "User-Agent: Mozilla/5.0" "https://www.reddit.com/r/formula1/comments/{id}/.json"` and extract full URLs with `html.unescape()`
- **Reddit images saved as .mp4 crash the single-shot path**: Rename to `.jpg` and use `source_type: "image"`, or split into a multi-shot segment
- **Reddit GIFs fail in assembler**: 480x270 `preview.redd.it` GIFs cause "Shot failed, skipping". Convert before assembly: `ffmpeg -i input.gif -movflags faststart -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2,fps=30" output.mp4`. Prefer `v.redd.it` or `i.redd.it` over `preview.redd.it` GIFs
- **Reddit videos with on-screen text**: Add `"no_text": true` to the segment when using Reddit videos with built-in text/graphics overlays — otherwise our text overlay clashes
- **Short Reddit clips**: When shorter than shot duration, the assembler holds the last frame (natural for 1-2s). For longer holds, split into video + image shots

---

## Gemini Vision Validation

### MANDATORY — Never Skip
Never deliver a video without running Gemini Flash validation on every image shot and every video clip at its `footage_start` timestamp. Google Images returns wrong people ~20% of the time. YouTube clips land on wrong content ~30% of the time.

### Team-Specific Prompts Are Required
**NEVER** ask vague questions like "Is this an F1 car on track?" — that matches ANY team's car.

**DO ask:**
```
"What SPECIFIC F1 team's car is shown? Look at livery colors, sponsor logos, and team branding.
Expected: [Team Name] car ([color description], [key sponsor]).
Is this EXACTLY the expected team? Answer MATCH or MISMATCH."
```

**Examples:**
- "Is this a Racing Bulls car (dark blue/navy with Cash App branding)?" NOT "Is this an F1 car?"
- "Is this Christian Horner specifically?" NOT "Is this a person at a press conference?"
- "Is this Albert Park Melbourne circuit?" NOT "Is this an F1 circuit?"

### Why This Matters
YouTube compilation videos ("First Look At Every 2026 Car") cycle through ALL teams. At `footage_start: 20` you get whichever team appears at that timestamp — usually wrong. Always verify the SPECIFIC team at the SPECIFIC timestamp.

### Thumbnail vs footage_start
`gemini_vision_validator.py --project` validates YouTube **thumbnails**, which may not represent content at `footage_start`. When validation fails but content might be correct at the right timestamp:
```bash
ffmpeg -y -ss {footage_start} -i footage/segment_XX.mp4 -vframes 1 -q:v 2 /tmp/check.jpg
python3 src/gemini_vision_validator.py --file /tmp/check.jpg --expected "description" --query "search terms"
```

---

## Team Color Validation

### Hex Reference Table
| Team | Primary Color | Key Visual |
|------|--------------|------------|
| Ferrari | Red (168,66,49) | Prancing horse, Shell sponsor |
| Red Bull | Dark blue (42,44,66) | Red bull logo, Oracle sponsor |
| Mercedes | Silver/teal (77,89,93) | Three-pointed star, Petronas teal |
| McLaren | Papaya (255,135,0) | Papaya orange, black accents |
| Aston Martin | Dark green (34,153,113) | British racing green, AMR logo |
| Alpine | Blue (35,56,81) | French blue, BWT pink accents |
| Racing Bulls | Dark blue/navy | Cash App branding |

### Programmatic Color Analysis
```bash
ffmpeg -y -ss {timestamp} -i footage/segment_XX.mp4 -vframes 1 -q:v 2 /tmp/check.jpg
magick /tmp/check.jpg -resize 100x100 -colors 5 -unique-colors -format '%c' histogram:info:-
```

---

## footage_start Consistency

The `footage_start` field exists at BOTH the top-level segment AND inside each `shots[]` entry. The assembler uses the top-level value for single-shot segments.

**Rules:**
- When replacing footage files (especially with pre-trimmed clips), update BOTH levels
- Mismatched values cause wrong video duration (e.g., 5s video for 25s audio = cut-off voiceover)
- **Best practice**: Pre-trim all clips with FFmpeg and set ALL `footage_start` to 0:
  ```bash
  ffmpeg -y -ss TIMESTAMP -i source.mp4 -t DURATION -c:v h264_videotoolbox -r 30 -an output.mp4
  ```
  This makes validation simpler since frame 0 of each clip is the intended content.

---

## File Format Issues

### PNG-as-JPG Detection
Reddit and Google Images sometimes serve PNG files despite `.jpg` URLs. This causes FFmpeg's zoompan filter to hang for minutes per image (vs <1s for actual JPEG).
```bash
file footage/*.jpg 2>/dev/null | grep PNG
# Convert: ffmpeg -y -i input.png -q:v 2 output.jpg
```

### WebP-as-JPG
F1 official site (`media.formula1.com`) and F1 Fandom Wiki serve WebP format despite `.jpg` URLs. Convert with:
```bash
ffmpeg -y -i input.jpg -q:v 2 output.jpg
```

### Fandom Wiki Images Are Unusable
F1 Fandom Wiki serves WebP format at only 300px wide — far too small for 1920x1080 video. Use Google Images via `--google-search` flag instead.

### 50fps Source Footage
Official F1 broadcast footage is often 50fps (PAL). Mixed with 30fps assembler segments, concat produces mismatched durations (video shorter than audio = black frames at end). Always force `-r 30` on all clips. Check with:
```bash
ffprobe -select_streams v:0 -show_entries stream=r_frame_rate footage/segment_XX.mp4
```

### Force 30fps Always
Mixed framerates cause audio/video desync. The assembler enforces 30fps but always verify source footage.

---

## Download & Cache

- **Delete footage before re-downloading**: `yt-dlp` skips download if a file exists at the output path. Always `rm` the old file first
- **Delete ALL footage when rewriting a script**: The downloader caches by filename (`segment_XX_shot_YY.jpg`). After rewriting/reordering, old files at same paths are treated as valid cached footage — showing wrong content
- **Delete old previews before re-extracting**: Preview images are cached. After replacing footage, delete old previews (`rm previews/segNN_*.jpg`) before running preview_extractor
- **`footage` key must exist for ALL segments**: Set the `footage` field in script.json at creation time (e.g., `"footage": "segment_00.mp4"`). The downloader doesn't always add this for all segments
- **yt-dlp can hang indefinitely**: Use `--socket-timeout 20`. If the Python downloader hangs, fall back to `bash src/download_footage.sh {name}` which runs each download in an isolated subprocess
- **Adding shots mid-array shifts all filenames**: When inserting new shots between existing ones, ALL downstream shots' filenames shift (shot_01 → shot_02, etc.). You MUST rename existing footage files AND update `footage` paths in script.json for every affected shot. Failure to do this causes wrong images on wrong narration or missing footage.

---

## YouTube Search Pitfalls

### Keyword Search Returns Wrong Teams
`ytsearch1:` frequently returns completely wrong content (e.g., McLaren when Red Bull was requested). Mitigations:
1. Use `--google-search` flag for better results
2. Search for specific YouTube URLs from official channels
3. Download broad compilation videos and use subtitle search to find the right timestamp

### Compilation Video Timestamp Problem
Compilation videos ("all 2026 cars") show different teams at different timestamps. The bulk downloader may download the same compilation for two segments. The downloader warns about duplicates — always verify with subtitle search.

### Wrong Year Results
Queries for "Leclerc fastest lap Bahrain 2026" return 2022 Bahrain pole laps. Always include extra context: "Pre-Season Testing", "Day 2", or the specific video series name.

### Ferrari Needs Specific Queries
Generic queries like "Ferrari SF-26 sidepod close up" return Barcelona Highlights compilations. Use the official Ferrari channel or F1 channel with driver-specific queries (e.g., "Charles Leclerc Sets The Fastest Lap Pre-Season Testing").

### Race Day: NEVER Use Generic Search
Generic YouTube searches return compilations with mixed content (~70% wrong). ALWAYS download official Race Highlights + Drivers React videos and pre-cut clips from verified timestamps.

---

## Timestamp Finding

### Subtitle Search Method
```bash
yt-dlp --write-auto-sub --sub-lang en --skip-download --sub-format vtt -o /tmp/subs "https://youtube.com/watch?v=VIDEO_ID"
grep -i "team name" /tmp/subs*.vtt
```
Add 1-2 seconds buffer — video content often doesn't match narration exactly. When subtitles mention a team at timestamp X, the visual may still show the previous team for 1-2s.

### Skip Jittery Interview Cuts
Interview footage from YouTube often has abrupt transitions at clip boundaries. Preview the first 1-2 seconds and add offset to skip jitter (e.g., start at 525s instead of 524s).

---

## Image vs Video Shots

### Portraits: Photos Beat YouTube Clips
For team principals, former drivers, and personnel (Damon Hill, Jenson Button, Claire Williams), use `source_type: "image"` with Google Images search. YouTube clips of these people are either old race footage or interview clips that don't match the news context. Ken Burns zoom on a good portrait looks professional and clean.

### Avoid Footage with Text Overlays
YouTube clips with burned-in text (titles, lower thirds, commentary text) cause visual confusion when captions are displayed on top. Prefer `source_type: "image"` when clean footage isn't available.

### Person Identity in Queries
Searching for "Lance Stroll Lawrence Stroll" returns Lance (the driver), not Lawrence (the owner/dad). Always match the query to the specific person. For non-drivers (team owners, ex-champions), images are far more accurate than YouTube search.

### Official Team Videos for Technical Topics
For power unit, engine, or technical regulation topics, use official team channels (Mercedes "Road to 2026", Honda PU Launch) or the F1 channel's explainer videos. Clean CGI animations work better than on-track footage for technical concepts.

---

## QA Checklist

- [ ] Every footage file validated with Gemini vision (not just existence check)
- [ ] Team-specific validation prompts used (not generic)
- [ ] `footage_start` consistent at both top-level and shot-level
- [ ] No PNG-as-JPG files (`file footage/*.jpg | grep PNG`)
- [ ] No stale previews from previous downloads
- [ ] All segments have `footage` key in script.json
- [ ] Reddit media URLs are complete (not truncated)
- [ ] Race day footage is from official highlights (not generic search)
- [ ] **No static image holds > 6 seconds** — check each segment's shot count vs narration duration. If a segment has only 1 image shot and >15 words of narration (~6s), it needs more shots
- [ ] **No failed shots in assembler log** — grep output for "Shot N failed" or "skipping". A failed shot means fewer visuals than planned, causing remaining shots to stretch and potentially freeze. Re-download failed shots and reassemble before delivery.
