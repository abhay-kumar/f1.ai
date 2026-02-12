# Upload Podcast to RSS.com

Generate all the content needed to manually upload a podcast episode to RSS.com.

## Input

**Project name** (required): $ARGUMENTS

The project name is the folder name under `projects/` containing the podcast to upload.

## Instructions

1. **Validate the project exists** and has required files:
   - Check `projects/{project}/output/final.mp3` exists
   - Check `projects/{project}/script.json` exists

2. **Get episode number** from the tracker at `shared/podcast_episodes.json`:
   - Read `next_episode` for the episode number
   - After upload content is generated, update the tracker: increment `next_episode` and append the new episode to the `episodes` array

3. **Generate cover art** if it doesn't exist:
   ```bash
   python3 src/podcast_cover_generator.py --project {project} --episode {episode_num} --title "{short_title}"
   ```

4. **Read the script.json** and extract:
   - Title
   - Host information
   - All segments with text, context, and emotion

4. **Generate the RSS.com upload content** in this format:

---

### Episode Details

**Title:** `{title}` (clean, without "F1 Burnouts:" prefix if present)

**Season Number:** `1`

**Episode Number:** `{from shared/podcast_episodes.json next_episode}`

**Episode Type:** `Full`

---

### Description

Generate a description with:
- Opening hook (first 1-2 sentences from segment 1)
- "Topics covered:" section (list relevant segment contexts, skip generic ones like "intro", "outro", "closing")
- "Timestamps:" section (calculate from word count, ~150 words/minute)
- Footer with podcast tagline and hashtags

Format:
```
{Opening text from first segment, ~300 chars}

Topics covered:
- {topic 1}
- {topic 2}
...

Timestamps:
00:00 - {context 1}
00:22 - {context 2}
...

---
F1 Burnouts - Your weekly dose of Formula 1 passion, engineering deep-dives, and honest takes.

#F1 #Formula1 #Podcast #Motorsport #Racing
```

---

### Keywords

Generate relevant keywords based on script content:
- Always include: F1, Formula 1, Podcast, Motorsport, Racing, F1 Burnouts
- Add topic-specific keywords detected from script (e.g., Sustainable Fuel, E-fuels, 2026)
- Add team names mentioned (Ferrari, McLaren, Red Bull, Mercedes, etc.)
- Add driver names mentioned (Verstappen, Hamilton, Alonso, etc.)
- Add technical terms (Carbon Capture, Fischer-Tropsch, etc.)

List each keyword on a separate line for easy copy-paste.

---

### Files to Upload

Provide absolute paths:
```
Audio file:
/Users/abhaykumar/Documents/f1.ai/projects/{project}/output/final.mp3

Cover art:
/Users/abhaykumar/Documents/f1.ai/projects/{project}/output/cover_art.jpg
```

---

## Timestamp Calculation

Calculate timestamps based on word count:
- Speech rate: ~150 words per minute (2.5 words/second)
- For each segment, calculate duration: `word_count / 2.5`
- Accumulate time for each subsequent segment
- Format as `MM:SS`

## Example Output

For a project called `sustainable-fuels-podcast`:

```
## Episode Details

**Title:** The Synthetic Fuel Revolution - How F1 is Making Fuel from Thin Air

**Season Number:** 1

**Episode Number:** 1

**Episode Type:** Full

---

## Description

Welcome back to F1 Burnouts! I'm your host, and today we're going somewhere special. We're talking about sustainable fuel - and what F1 is doing in 2026 is genuinely one of the coolest things in the sport's history...

Topics covered:
- The 2026 sustainable fuel mandate
- How e-fuels work
- Carbon capture technology
- Team fuel partnerships
- Racing implications

Timestamps:
00:00 - Intro hook
00:22 - Topic intro
00:46 - The mandate
...

---
F1 Burnouts - Your weekly dose of Formula 1 passion, engineering deep-dives, and honest takes.

#F1 #Formula1 #Podcast #Motorsport #Racing

---

## Keywords

F1
Formula 1
Podcast
Motorsport
Racing
Sustainable Fuel
E-fuels
2026
F1 Burnouts
Aramco
Shell
Ferrari
McLaren

---

## Files to Upload

Audio file:
/Users/abhaykumar/Documents/f1.ai/projects/sustainable-fuels-podcast/output/final.mp3

Cover art:
/Users/abhaykumar/Documents/f1.ai/projects/sustainable-fuels-podcast/output/cover_art.jpg
```

---

### Transcript

Generate a WebVTT format transcript from the script segments:

1. **Format**: WebVTT (.vtt) with timestamps
2. **Clean the text**: Remove any `[emotion]` markers like `[excited]`, `[sarcastic]`, etc.
3. **Calculate timestamps**: Use word count (~2.5 words/second) to estimate segment timing
4. **Save to file**: `projects/{project}/output/transcript.vtt`

**VTT Format**:
```
WEBVTT

00:00:00.000 --> 00:00:22.000
Welcome back to F1 Burnouts! I'm your host, and today we're going somewhere special...

00:00:22.000 --> 00:00:45.000
We're talking about fuel. Sustainable fuel. And before you click away thinking this is going to be some boring chemistry lecture, stay with me...

00:00:45.000 --> 00:01:05.000
So here's the deal. From 2026, every single car on the grid will run on one hundred percent sustainable fuel...
```

**Timestamp calculation**:
- Speech rate: ~150 words per minute (2.5 words/second)
- For each segment: `duration = word_count / 2.5`
- Accumulate start times for each subsequent segment
- Format: `HH:MM:SS.mmm`

---

## Files to Upload (Updated)

Provide absolute paths for all three files:
```
Audio file:
/Users/abhaykumar/Documents/f1.ai/projects/{project}/output/final.mp3

Cover art:
/Users/abhaykumar/Documents/f1.ai/projects/{project}/output/cover_art.jpg

Transcript:
/Users/abhaykumar/Documents/f1.ai/projects/{project}/output/transcript.vtt
```

---

## Notes

- RSS.com requires video/audio files, MP3 is accepted directly
- Cover art should be square (the generator creates 3000x3000)
- Cover art uses the official F1 font (Formula1-Bold) for episode number and title
- Episode number and title are displayed in large, bold text for visibility
- Keep keywords to ~15-20 max for best results
- Description can be long - RSS.com supports detailed show notes
- Transcript must be in WebVTT format (.vtt) with proper timestamps
