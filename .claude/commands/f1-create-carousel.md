# Create Instagram Carousel

Create an Instagram carousel (multi-image post) from a link, raw content, or both.

## User Input

**Content** (required): $ARGUMENTS

The input can be:
- A Reddit URL (e.g., `https://www.reddit.com/r/formula1/comments/...`)
- A web article URL
- Raw text describing the topic
- A combination of link + additional context

## Instructions

You are creating a professional Instagram carousel — a set of 1080x1080 square slide images that get uploaded as a single swipeable post. Carousels currently outperform Reels for engagement on Instagram.

**Output:** 5-10 JPEG slides in `projects/{name}/output/slide_01.jpg` through `slide_NN.jpg`
**Upload:** Manual (user uploads via Instagram app)

### Project Structure
```
projects/{name}/
├── script.json     # Carousel script (format: "carousel")
├── images/         # Source images (backgrounds, portraits)
└── output/         # Generated slides (slide_01.jpg, slide_02.jpg, ...)
```

### Workflow

#### Phase 1: Content Sourcing

1. **If input contains a Reddit URL**: Fetch the full thread using `python3 src/reddit_fetcher.py --post URL`. Extract:
   - OP's post title, body, and any images/media
   - Top 20-30 comments for community insights, quotes, stats
   - All media URLs (images, GIFs, videos) — these are gold for `content_image` slides
   
   If `reddit_fetcher.py` fails, fall back to: `curl -s -L -A "Mozilla/5.0" "URL.json?limit=50&sort=top" -o /tmp/reddit_thread.json`
   
   **Do NOT use WebFetch for Reddit** — it blocks all requests.

2. **If input contains a non-Reddit URL**: Use WebSearch to research the topic and gather facts, stats, and quotes.

3. **If input is raw text**: Use it as the topic. Optionally use WebSearch to find supporting facts, statistics, and quotes to enrich the content.

4. **Always**: Fact-check key claims via WebSearch. Carousels with wrong facts destroy credibility.

#### Phase 2: Script Creation

Analyze the sourced content and determine the best carousel format:

**Carousel Formats:**
- **Listicle** ("5 things about...", "Top 7...") — Most common, high engagement
- **Story/Timeline** (chronological events) — Good for historical content
- **Stat Breakdown** (numbers + context) — Great for data-heavy topics
- **Hot Take/Debate** (opinion + evidence) — Good for controversial Reddit threads
- **Explainer** (concept breakdown) — Good for technical/regulation topics

**Script Guidelines:**
- **Cover slide is everything** — It must be a hook that compels swiping. Use a bold question, surprising claim, or big number. Think: "What would make someone stop scrolling?"
- **4-8 content slides** — Aim for 6-7 total (including cover + auto-appended CTA)
- **Each slide: max 30 words** — Instagram is visual-first. If you need more text, split into two slides
- **Every slide must stand alone** — Users can screenshot or save individual slides
- **Build momentum** — Each slide should make them want to swipe to the next
- **End strong** — The last content slide before CTA should have the biggest revelation or most impactful stat

**Slide Types Available:**

| Type | When to Use | Key Fields |
|------|-------------|------------|
| `cover` | Always first | `headline`, `subheadline`, optional `background_image` |
| `content` | Standard fact/point | `number`, `heading`, `body`, optional `background_image` |
| `content_stat` | Big number callout | `stat` (e.g., "350kW"), `label` |
| `content_quote` | Direct quotes | `quote`, `speaker`, `role`, optional `speaker_image` |
| `content_image` | Image-forward slide | `heading`, `background_image` (required) |

**Do NOT include a CTA slide** — the generator auto-appends one with the F1 Burnouts logo + Follow/Like/Share.

**Theme Selection:**
- The generator auto-detects theme from team/driver mentions in content
- Override with `"theme": "ferrari"` in script.json if needed
- Available themes: `ferrari`, `redbull`, `mercedes`, `mclaren`, `aston_martin`, `alpine`, `williams`, `haas`, `cadillac`, `audi`, `dramatic`, `gold`, `breaking`, `stats`
- Use `breaking` for urgent news, `stats` for data-heavy content, `dramatic` for general/multi-team content, `gold` for awards/records

**Create the project and write script.json:**
```bash
mkdir -p projects/{name}/output
```

Write `script.json` with this format:
```json
{
  "title": "Carousel Title",
  "format": "carousel",
  "theme": "auto-detected or manual",
  "source_url": "original URL if applicable",
  "slides": [
    {
      "type": "cover",
      "headline": "Bold Hook That Demands Swiping",
      "subheadline": "Swipe to find out"
    },
    {
      "type": "content",
      "number": 1,
      "heading": "First Point",
      "body": "Supporting detail in 1-2 short sentences."
    }
  ]
}
```

#### Phase 3: Review Checkpoint

**STOP and present the slide plan to the user.** Show:
1. Carousel title and theme
2. Numbered list of all slides with type and content summary
3. Note which slides have background images
4. Total slide count (including auto-appended CTA)

Wait for user approval before proceeding. The user may want to:
- Reorder slides
- Change the angle/hook
- Add or remove slides
- Switch theme
- Add specific images

#### Phase 4: Image Sourcing

For slides that reference images:

1. **Reddit-sourced images**: If the content came from Reddit and media URLs were extracted, download them:
   ```bash
   curl -L -o projects/{name}/images/slide_img_NN.jpg "URL"
   ```
   Update `background_image` in script.json to point to the downloaded file.

2. **Speaker portraits** (`content_quote` slides): Search for the person's photo:
   - F1 Fandom Wiki has team principal photos
   - Wikipedia for high-profile figures
   - Download and save to `projects/{name}/images/`
   - Note: Fandom serves WebP despite .jpg URLs — convert with: `ffmpeg -y -i input.webp output.jpg`

3. **Auto-sourced by generator**: The carousel generator auto-sources background images via Google Images for all slides that don't have a `background_image` set. This runs automatically — no manual image sourcing needed for most carousels. Use `--no-images` to skip auto-sourcing for offline/fast iteration.

4. **No image needed**: `content`, `content_stat`, and `content_quote` (without portrait) work great without images. Don't force images where they're not needed.

5. **Never use Pexels for carousel backgrounds** — Pexels returns generic stock photos that are semantically similar but contextually wrong (e.g. a random party for "McLaren's Civil War"). Google Images returns actual F1/topic-specific photos. The carousel generator uses Google Images exclusively.

#### Phase 5: Generate Slides

```bash
# Generate all slides (auto-sources background images via Google Images)
python3 src/carousel_generator.py --project {name}

# Preview plan without generating
python3 src/carousel_generator.py --project {name} --list

# Regenerate a single slide after editing script.json
python3 src/carousel_generator.py --project {name} --slide 3

# Override theme
python3 src/carousel_generator.py --project {name} --theme breaking

# Skip auto image sourcing (solid backgrounds only)
python3 src/carousel_generator.py --project {name} --no-images
```

After generation, **validate all background images with Gemini Vision** before presenting to the user:

```bash
python3 -c "
from src.gemini_vision_validator import validate_shot
# For each slide's source image:
is_match, confidence, reason = validate_shot(
    'projects/{name}/images/bg_slide_NN.jpg',
    'Expected content description',
    'search query used'
)
print(f'Slide N: {\"MATCH\" if is_match else \"MISMATCH\"} ({confidence:.2f}) - {reason}')
"
```

For any MISMATCH images:
1. Re-source with a more targeted Google Images query
2. Replace the image in `images/`
3. Regenerate just that slide with `--slide N`
4. Re-validate the new image

Only present slides to the user once all images pass validation.

If slides need revision:
- Edit the specific slide in `script.json`
- Re-run with `--slide N` to regenerate just that slide
- For theme changes, re-run without `--slide` to regenerate all

#### Phase 6: Caption & Delivery

Generate an Instagram caption for the carousel:

**Caption Format:**
```
{Hook line that matches the cover slide}

{1-2 sentence summary of the content}

{Optional: credit source if from Reddit/article}

Follow @f1burnouts for daily F1 content

#F1 #Formula1 #F1Burnouts #{relevant team/driver hashtags}
```

**Caption Guidelines:**
- First line is critical — it shows in the feed preview
- Keep total caption under 200 words
- 5-10 relevant hashtags (mix of popular + niche)
- Include the source credit if content came from a specific Reddit thread or article
- End with a CTA that matches the carousel's CTA slide

**Final Delivery:**
Present to the user:
1. All slide file paths (`projects/{name}/output/slide_*.jpg`)
2. The generated caption text
3. Reminder: Upload manually via Instagram app → New Post → Select multiple images in order

### Writing Guidelines for Carousel Content

- **Be bold, not safe** — Carousels that play it safe get scrolled past
- **Use contrast** — "Everyone thinks X, but actually Y"
- **Numbers perform** — "3 reasons", "The $50M mistake", "In just 17 days"
- **Questions hook** — "Why did Ferrari do this?" compels swiping for the answer
- **Keep it scannable** — No walls of text. Each slide: one idea, one takeaway
- **Build curiosity** — Each slide should leave them wanting the next one
- **Credit your sources** — "According to [source]" builds trust
- **Avoid clickbait without payoff** — The content must deliver on the cover slide's promise
- **Use `\n` for vertical lists** — Steps, bullet points, numbered lists in `body` text should use `\n` for line breaks, not inline sentences
- **Max 10 slides** — Instagram limit. Plan for 8 content + 1 cover + 1 auto-CTA = 10

### Image Sourcing Lessons

1. **Always set `image_query` on every slide** — The auto-derived queries from heading/body text often produce terrible results (e.g., heading "2025 Had Everything" becomes query "2025 Everything" which returns abstract art). Always add an explicit `image_query` field to every slide in script.json with a specific, descriptive search query like "Norris Piastri McLaren F1 2025 battle".

2. **Validate all images with Gemini Vision after generation** — Don't rely on visual inspection alone. Run `gemini_vision_validator.py` on every `images/bg_slide_*.jpg` to programmatically verify contextual relevance. This catches subtle mismatches (wrong era, wrong team, generic stock photos). Target 100% MATCH rate before presenting to user.

3. **Use action-specific image queries, not topic summaries** — "McLaren team orders controversy" finds relevant on-track photos. "McLaren's Civil War Was Barely Shown" (the heading) finds irrelevant results. The `image_query` should describe what you want to SEE, not the editorial point being made.

4. **Don't source portraits for fictional/non-person speakers** — "Netflix Narrator" is not a real person. Google will return random people. Only use speaker portraits for real, identifiable people (team principals, drivers, journalists).

5. **Run the generator with `/usr/bin/env -i`** — Playwright has asyncio event loop conflicts when run from certain environments (e.g., Claude Code's Bash tool). Always use: `/usr/bin/env -i HOME="$HOME" PATH="$PATH" TERM="$TERM" python3 src/carousel_generator.py --project {name}` for a clean subprocess.

6. **Re-source individually, not in bulk** — When an image fails validation, download a replacement with a more targeted query, swap just that file in `images/`, and regenerate with `--slide N`. Don't regenerate all slides — it's slow and risks breaking slides that were already good.

7. **Prefer on-track/action shots over portraits** — For content slides about driver rivalries or race incidents, on-track racing photos are more visually compelling than posed portraits and pass Gemini validation more reliably.

### Meme Slides

For real internet memes (not just comparison infographics), do NOT use the `content_meme` slide type. Instead:

1. **Download the raw template** from imgflip: `curl -sL -o images/template.jpg "https://i.imgflip.com/{TEMPLATE_ID}.jpg"`
   - Common templates: `2za3u1` (They're the same picture), `2wifqv` (Spider-Man pointing)
2. **Source images** via `search_google_images()` from `src/google_image_search.py` — Reddit preview URLs often block direct downloads
3. **Detect blank zones** programmatically: downscale template to PPM, flood-fill white regions (R>210,G>210,B>210), find bounding boxes, apply 12% margin for safe zone
4. **Composite with FFmpeg**: overlay images into detected zones, add only label text (NOT meme caption text — the template already has it)
5. **Resize to 1080x1080**: `scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:white`
6. **Save as slide_NN.jpg** — replace the placeholder slide in the output folder

**Memegen.link API** (`https://api.memegen.link`) works for text-only memes (free, no auth). Template IDs: `same`, `db`, `spiderman`. But its image overlay feature is unreliable — use FFmpeg compositing for image-in-template memes.
