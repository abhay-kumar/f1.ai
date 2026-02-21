# F1 Reddit Idea

Create an F1 short video from a specific Reddit post. Reads the original post and all comments, distills the most compelling angle into a 60-second script, then produces and optionally uploads the video.

## Parameters

- `$ARGUMENTS` - A Reddit URL (e.g., `https://www.reddit.com/r/formula1/comments/...`). Required.

## Instructions

You are creating an F1 short video inspired by a specific Reddit thread. This command handles the full pipeline: reading the thread → extracting the best angle → script creation → video production → upload.

### Phase 1: Read the Reddit Thread

1. **Fetch the Reddit post**: Use `python3 src/reddit_fetcher.py --post URL` to fetch the post and comments via Reddit OAuth2 API. If reddit_fetcher is unavailable, fall back to fetching the JSON via curl: `curl -s -L -A "Mozilla/5.0" "URL.json?limit=50&sort=top" -o /tmp/reddit_thread.json` then parse with Python. **Do NOT use WebFetch** — Reddit blocks all WebFetch requests.

2. **Extract key information**:
   - **OP's post**: Title, full text/body, any links or images referenced
   - **Top comments**: Read the top 20-30 comments (sorted by best/top), including reply chains
   - **Community sentiment**: What's the prevailing opinion? Is there a strong debate? Any surprising takes?
   - **Key facts/claims**: Specific stats, quotes, dates, or events mentioned
   - **Emotional hooks**: What made this post popular? Drama, humor, nostalgia, controversy?

3. **Collect Reddit images and media**: Extract ALL image/video URLs from the thread — both OP's post and comments. Reddit JSON contains these in `preview.images`, `url`, or inline markdown links. Common patterns:
   - `preview.redd.it/...` — Reddit-hosted images
   - `i.redd.it/...` — Direct image uploads
   - `v.redd.it/...` — Reddit-hosted video
   - `streamable.com/...`, `streamja.com/...` — Video clips
   - Imgur, Twitter/X media links
   
   **Build an image inventory** with each image's:
   - URL
   - Context (which comment/post it came from)
   - What it shows (description)
   - Relevance to potential video angles
   
   These Reddit-sourced images are **gold** — they're the actual visuals the community was reacting to, making the video feel authentic and connected to the discussion. They also save significant time vs. searching for footage externally.

4. **Summarize the thread**: Present a brief summary to yourself covering:
   - What the post is about
   - The most interesting angles from the comments
   - Key facts and claims that could be verified
   - The emotional tone of the discussion
   - **Available images/media from the thread** (list them)

### Phase 2: Find the Best Video Angle

Not every aspect of a Reddit thread makes a good 60-second video. Evaluate the thread and select the **single most compelling angle**:

**Angle Selection Criteria:**
- **Specific over general**: "Hamilton's engineer left 4 weeks before the season" beats "Ferrari has staffing issues"
- **Emotional hook**: Does it make you go "wait, what?" or "no way!" in the first 5 seconds?
- **Visual potential**: Can you find footage/images to illustrate this? (F1 cars, driver reactions, team footage)
- **Self-contained**: Can the story be told in 60 seconds without requiring deep background knowledge?
- **Engagement bait**: Would this make someone stop scrolling? Would they comment?

**Angle Sources (in priority order):**
1. The OP's core claim/story itself (if it's specific and dramatic enough)
2. A surprising fact or stat buried in the comments that most people missed
3. A strong contrarian take from a highly-upvoted comment
4. A historical parallel drawn by a commenter ("This is just like when Senna...")
5. A combination of OP's story + the community's reaction to it

### Phase 3: Script Creation

1. **Research & fact-check**: Use WebSearch to verify key claims from the thread. Reddit comments can be wrong — verify dates, stats, quotes, and records before scripting.

2. **Create project folder**: `projects/{project-name}/` where `{project-name}` is a short slug derived from the angle (e.g., `hamilton-engineer-exodus`, `verstappen-exit-clause`)

3. **Generate `script.json`**: Follow the standard shorts format with these Reddit-specific guidelines:

   **Script Structure for Reddit-sourced content:**
   - **Hook (segment 1)**: The most shocking/surprising element. Lead with the "wait, what?" moment.
   - **Context (segments 2-3)**: Brief background so viewers understand why this matters.
   - **The meat (segments 3-5)**: Key details, facts, or the story arc.
   - **Payoff (segment 5-6)**: The twist, consequence, or open question that makes viewers want to comment.
   - **CTA (final segment)**: "What do you think? Drop your take in the comments."

   **Writing style:**
   - Credit Reddit naturally when appropriate: "F1 fans on Reddit spotted something interesting..." or "A viral Reddit thread revealed..."
   - Don't say "Reddit users" — say "F1 fans" or "the F1 community"
   - Use the community's best insights but write them in your own voice
   - If a specific commenter made the key insight, don't credit them by username

   **Target duration:** Ask the user for their preferred duration (60s, 90s, 2 min). Default to 60s if not specified.

4. **Prioritize Reddit-sourced visuals**: When building shots for each segment, **always check the image inventory first** before falling back to YouTube/stock searches:
   
   **Visual source priority order:**
   1. **Reddit thread images** — Photos, screenshots, memes posted in the thread. Download these directly into `footage/` and reference them as `image` source_type shots. These are the most authentic visuals since viewers may recognize them from the original discussion.
   2. **Reddit thread video/clips** — Any video links shared in the thread (streamable, v.redd.it, etc.)
   3. **YouTube clips** — Fall back to YouTube search only for segments where no Reddit image exists
   4. **Stock images** — Last resort for generic establishing shots
   
   **How to use Reddit images in script.json:**
   ```json
   {
     "label": "Vettel's red pass photo from Reddit",
     "text_cue": "It says World Champion on it",
     "source_type": "image",
     "reddit_image_url": "https://preview.redd.it/rswsvsg85yjg1.jpeg?width=1080&format=pjpg&auto=webp",
     "image_query": "Sebastian Vettel F1 world champion red pass",
     "ken_burns": "zoom_in",
     "transition_in": "cut"
   }
   ```
   
   Download Reddit images during the footage phase:
   ```bash
   curl -L -o projects/{name}/footage/segment_XX_shot_YY.jpg "REDDIT_IMAGE_URL"
   ```
   
   **Why this matters:**
   - Authenticity: The video feels connected to the viral discussion
   - Speed: No need to search/validate footage for shots where Reddit already provided the perfect image
   - Uniqueness: These images won't appear in other F1 YouTube shorts — they came from the community

5. **Use multi-shot segments** where appropriate — if a segment mentions multiple teams/drivers, break it into shots (see `/f1-create-short` Shot List section for reference).

6. **CHECKPOINT - Script Review**:
   - Present the complete script to the user
   - Show the Reddit thread summary and chosen angle
   - Explain why this angle was selected
   - **STOP and wait for user approval** before proceeding

### Phase 4: Video Production

**Follow the `/f1-create-short` pipeline from step 5 (Download Footage) through step 14 (Verify Final Output)**, including:

1. Download footage with `--google-search --validate` for accuracy
2. Verify footage with `--list` and preview extraction
3. Run Gemini vision validation on all footage
4. Generate audio with Gemini TTS (Alnilam voice)
5. Assemble video **without background music** and with **word-by-word captions**: `python3 src/video_assembler.py --project {name} --no-music --word-by-word`
6. Use `--segment-transition cut` for news-style content, `cross_dissolve` only for cinematic/emotional stories with few segments
7. **USER REVIEW CHECKPOINT**: Present output video, wait for approval

### Phase 5: Post-Production

1. **Update Reddit Ideas Tracker**: Add the idea to `shared/reddit_ideas.json`:
   ```json
   {
     "id": "slug-from-project-name",
     "title": "Video Title",
     "synopsis": "Brief description",
     "reddit_source": "Original Reddit thread title",
     "reddit_url": "Full URL of the Reddit post",
     "proposed_date": "YYYY-MM-DD",
     "status": "used",
     "used_date": "YYYY-MM-DD"
   }
   ```

2. **Suggest upload**: After the video is created, suggest:
   ```
   /f1-upload-short {project-name}
   ```
   to upload to YouTube and Instagram.

### Reddit Idea Shorts Lessons

1. **Progressive reveal captions (karaoke style)** — Reddit idea shorts use `--word-by-word` mode which shows a progressive word-by-word reveal within each sentence. Words accumulate on screen as the narrator speaks: "Did" → "Did you" → "Did you know" → ... When the sentence ends, it clears and the next sentence starts building. This matches the MrBeast/Hormozi caption style. Text is positioned at the bottom of screen. This is only for reddit idea shorts — not for `/f1-create-short` or `/f1-daily-news`.

2. **Yellow + black double border on text** — The caption style uses two stacked FFmpeg `drawtext` layers: a wider yellow border (borderw=6, #FFD700) underneath, and a narrower black border (borderw=3) on top, both with white font fill. Font size is 64px to fit accumulating text.

3. **Sentence-based clearing** — Text is split at sentence boundaries (.!?) and also at commas/semicolons for long sentences (>8 words). Each sentence group builds up word by word, then clears completely when the next sentence begins. This keeps the screen readable while maintaining the progressive reveal rhythm.

4. **Avoid footage with text overlays** — YouTube clips with burned-in text (titles, lower thirds, commentary text) cause visual confusion when our own word-by-word captions are displayed on top. Prefer `source_type: "image"` shots (photos, stock images) over YouTube clips that contain text. When using YouTube clips, validate that the clip at `footage_start` doesn't have prominent text on screen. If no clean footage exists, use an image instead.

5. **Prefer images over YouTube clips for reddit idea shorts** — Images (photos, portraits) with Ken Burns effects are cleaner, faster to source, and avoid text-overlay conflicts. Use `source_type: "image"` as the default for most shots. Only use `youtube_clip` when you specifically need motion footage (on-track action, celebrations). Google Image search via `search_google_images()` is more reliable than the footage downloader for finding specific people/topics.

6. **Verify person identity in footage queries** — Searching for "Lance Stroll Lawrence Stroll" returns Lance (the driver), not Lawrence (the owner/dad). Always match the query to the specific person mentioned in the script. When the script references a non-driver (team owner, ex-champion, etc.), use images — they're far more accurate for specific people than YouTube search.

7. **F1 official site serves WebP as .jpg** — Images from `media.formula1.com` and F1 Fandom Wiki are WebP format despite having `.jpg` in the URL. Always convert with `ffmpeg -y -i input.jpg -q:v 2 output.jpg` before using in the assembler.

8. **No background music for reddit idea shorts** — Use `--no-music` flag. The progressive reveal captions + narration are enough. Music competes with the intimate, story-driven tone of reddit idea content.

9. **Always read the actual Reddit thread BEFORE scripting** — Do NOT reconstruct the topic from web search articles. Web articles cover related topics but miss the specific question, community debate, and top-voted answers that make the thread unique. The OP's exact framing and the community's ranked responses ARE the content. Scripting from web searches alone leads to a generic explainer instead of a Reddit-inspired short.

10. **Use top Reddit comments as the script backbone** — The community has already surfaced, debated, and ranked the best answers. Map high-upvote comments directly to script segments. A comment with 2,000 upvotes that says "it's basically traction control" is a better script beat than any angle you'll find from web research.

11. **Hook with the problem, then tease the solution** — Start with the F1 problem or controversy ("F1 2026 cars have a huge problem with race starts"), THEN pivot to the surprising comparison or answer. Problem-first hooks grab attention better than leading with context. The viewer needs to feel the problem before they care about the answer.

12. **Delete ALL footage files when rewriting a script** — The downloader caches by filename (`segment_XX_shot_YY.jpg`). When script segments are reordered or rewritten, old files at the same paths are falsely treated as valid cached footage (e.g., Jean Todt's portrait appearing during a "battery energy" segment). Always `rm footage/segment_*` before redownloading after any script rewrite that changes segment order or content.

13. **WebFetch cannot access Reddit** — Reddit blocks all WebFetch/web scraping attempts across `www.reddit.com`, `old.reddit.com`, and `api.reddit.com`. Use `reddit_fetcher.py --post URL` (OAuth2 API) or fall back to `curl` with browser User-Agent to fetch the `.json` endpoint.

### Tips for Reddit Thread Analysis

- **Sort by controversial** (mentally): The best video angles often come from divisive opinions, not consensus
- **Look for "Actually..." comments**: Corrections to the OP often contain the real story
- **Buried replies matter**: Sometimes the best insight is a reply to a reply with 50 upvotes, not the top comment with 2000
- **Cross-reference with news**: If a Reddit thread discusses a news article, read the original source too — Reddit titles often editorialize
- **Timing matters**: If the post is > 1 week old, check if there have been new developments since

### Example

```
/f1-reddit-idea https://www.reddit.com/r/formula1/comments/abc123/hamilton_still_doesnt_have_a_race_engineer
```

This would:
1. Fetch the thread about Hamilton's missing race engineer
2. Read OP's concerns and top comments (maybe someone found out the engineer went to Cadillac)
3. Select the angle: "Hamilton's support team is falling apart before the season even starts"
4. Fact-check the claims (verify engineer departures, dates, destinations)
5. Create a punchy 60-second script
6. Produce the video following the standard shorts pipeline
7. Suggest `/f1-upload-short` when done
