# Upload F1 Carousel to Instagram

Generate all the content needed to manually upload an Instagram carousel post.

## Input

**Project name** (required): $ARGUMENTS

The project name is the folder name under `projects/` containing the carousel to upload.

## Instructions

1. **Validate the project exists** and has required files:
   - Check `projects/{project}/script.json` exists and has `"format": "carousel"`
   - Check `projects/{project}/output/slide_*.jpg` files exist
   - Count the slides and verify order (slide_01.jpg through slide_NN.jpg, no gaps)
   - If slides are missing, tell the user to run: `python3 src/carousel_generator.py --project {project}`

2. **Read script.json** and extract:
   - Title
   - Theme
   - Source URL (if any)
   - All slide types, headings, and content
   - Number of slides (including auto-appended CTA)

3. **Verify slide images**:
   - Confirm all slides are 1080x1080 (use `identify` or `ffprobe`)
   - Report any dimension mismatches
   - List file sizes

4. **Generate Instagram caption**:

   The caption should follow this structure:

   ```
   {Hook line — bold, attention-grabbing, matches the cover slide}

   {1-2 sentence summary of the carousel content. What will they learn by swiping?}

   {If sourced from Reddit/article: "Inspired by a viral r/formula1 thread" or similar credit — do NOT link directly, Instagram doesn't support clickable links in captions}

   Follow @f1burnouts for daily F1 content

   #F1 #Formula1 #F1Burnouts #{3-7 relevant hashtags based on content}
   ```

   **Caption guidelines:**
   - First line is critical — it shows in the feed preview before "...more"
   - Keep total caption under 150 words (carousels get engagement from visuals, not caption walls)
   - 5-10 hashtags total (mix popular + niche)
   - Include team/driver hashtags if relevant (e.g., #AstonMartin #Alonso #Honda)
   - Match the tone of the carousel (sarcastic carousel = witty caption)
   - End with a CTA before hashtags

5. **Generate alt text** for accessibility:
   - One line per slide describing the visual content
   - Instagram allows alt text per image — provide it for each slide
   - Keep each alt text under 100 characters

6. **Present the upload package** to the user:

   ```
   ## Carousel Upload Package

   **Project:** {project}
   **Slides:** {count} images
   **Theme:** {theme}

   ### Files (in order)

   1. {absolute_path}/output/slide_01.jpg ({size}KB) — Cover
   2. {absolute_path}/output/slide_02.jpg ({size}KB) — {slide type/summary}
   ...
   N. {absolute_path}/output/slide_NN.jpg ({size}KB) — CTA

   ### Caption

   {generated caption text — ready to copy-paste}

   ### Alt Text (per slide)

   Slide 1: {alt text}
   Slide 2: {alt text}
   ...

   ### Upload Instructions

   1. Open Instagram app
   2. Tap + (New Post)
   3. Tap "Select Multiple" (overlapping squares icon)
   4. Select all {count} images IN ORDER (slide_01 first, slide_NN last)
   5. Skip filters (slides are already styled)
   6. Paste the caption above
   7. Add alt text per image (Settings > Write Alt Text on each)
   8. Set location to "Formula 1" (optional, helps discovery)
   9. Share!
   ```

7. **Ask if the user wants any changes** to the caption or alt text before they upload.

## Notes

- Instagram carousels support up to 10 images (enforced by the generator)
- All slides must be square (1080x1080) — the generator ensures this
- JPEG quality 95 keeps file sizes reasonable while looking crisp on mobile
- Instagram compresses images on upload — the high source quality compensates for this
- Carousel posts cannot be scheduled natively — use Meta Business Suite for scheduling
- Best posting times for F1 content: race weekends, testing days, major news drops
