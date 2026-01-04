# Create Long-Form Video

Create a professional F1 long-form video (~10 minutes, 16:9 horizontal, up to 4K resolution) based on user's prompt. This command handles the entire pipeline from research to final video.

## User Input
$ARGUMENTS

## Instructions

You are creating a **long-form horizontal video** (16:9, ~10 minutes) for YouTube standard format consumption. This is NOT a short or vertical video.

### Key Differences from Shorts
- **Format**: 16:9 horizontal (3840x2160 4K or 1920x1080 HD)
- **Duration**: ~10 minutes (adjustable based on content)
- **Depth**: In-depth coverage with multiple sections
- **References**: Every claim must have a source citation
- **Script Approval**: User must approve script BEFORE any processing

### Project Structure
```
f1.ai/
├── projects/           # Each video gets its own folder
│   └── {project-name}/
│       ├── script.json     # Video script with segments + references
│       ├── audio/          # Generated voiceovers (cached)
│       ├── footage/        # Downloaded source clips + graphics
│       ├── previews/       # Frame previews for verification
│       ├── temp/           # Intermediate files
│       └── output/         # Final video (final.mp4)
├── shared/
│   ├── music/              # Reusable background music
│   ├── graphics/           # Reusable illustrations, charts, diagrams
│   └── creds/              # API keys
├── src/                    # Core modules
│   ├── audio_generator.py
│   ├── footage_downloader.py
│   ├── video_assembler_longform.py  # 16:9 horizontal assembler
│   ├── youtube_uploader_longform.py # Long-form uploader with references
│   ├── preview_extractor.py
│   └── fact_checker.py
└── .claude/commands/
```

---

## SCRIPTWRITING BEST PRACTICES

### The Golden Rules of Engaging Content

#### 1. Hook First, Context Second
- **First 10 seconds are critical** - Open with intrigue, not background
- Start with a provocative question, surprising fact, or dramatic moment
- Save the "In this video, we'll explore..." for AFTER the hook

**BAD Opening:**
> "Lewis Hamilton is one of the greatest Formula One drivers of all time. In this video, we'll look at his career."

**GOOD Opening:**
> "Forty-four. That's the number Lewis Hamilton saw when he looked at his championship standings after Abu Dhabi 2021. Not first. Second. And in that moment, everything changed."

#### 2. Create Narrative Tension
- Every great video has conflict, stakes, or mystery
- Ask questions that demand answers
- Create "open loops" - introduce ideas that pay off later
- Use phrases like: "But what nobody expected was..." / "That's when everything fell apart..."

#### 3. Show, Don't Just Tell
- Instead of stating facts, paint scenes
- Use sensory details: sounds, sights, atmosphere
- Transport the viewer to the moment

**TELLING:**
> "Senna and Prost had a famous rivalry in 1989."

**SHOWING:**
> "The gravel flew. Metal scraped against metal. As Senna climbed out of his McLaren at Suzuka, he locked eyes with Prost across the runoff area. Neither man blinked. The 1989 championship had just exploded."

#### 4. Vary Pacing and Rhythm
- Alternate between fast, punchy segments and slower, reflective ones
- Short sentences create urgency. They punch. They hit.
- Longer, flowing sentences allow the viewer to breathe and absorb the weight of what you're describing, building anticipation for what comes next.
- Use strategic pauses (segment breaks) for dramatic effect

#### 5. The "So What?" Test
Every segment must answer: "Why should the viewer care?"
- Connect facts to emotions
- Relate historical events to present-day implications
- Show how this affects drivers, teams, or the sport

### Content Structure for Maximum Engagement

#### The 10-Minute Formula

```
[0:00-0:30]   COLD OPEN - The hook, no context needed
[0:30-1:30]   SETUP - What we're exploring and why it matters
[1:30-4:00]   ACT 1 - The beginning/origin of the story
[4:00-4:30]   TRANSITION - Pivot point, things are about to change
[4:30-7:00]   ACT 2 - The conflict/development/main action
[7:00-7:30]   TRANSITION - The turning point
[7:30-9:00]   ACT 3 - Resolution/climax/aftermath
[9:00-9:45]   REFLECTION - What it means, legacy, impact
[9:45-10:00]  CLOSE - Call to action, tease future content
```

#### Section Types and Their Purpose

| Section | Purpose | Tone | Length |
|---------|---------|------|--------|
| `cold_open` | Hook viewer instantly | Dramatic, intriguing | 15-30s |
| `intro` | Establish topic and stakes | Confident, inviting | 30-60s |
| `origin` | Background, how it began | Narrative, scene-setting | 60-90s |
| `rising_action` | Building tension/conflict | Escalating, engaging | 90-120s |
| `climax` | Peak moment, main event | Intense, vivid | 60-90s |
| `aftermath` | Immediate consequences | Reflective, impactful | 45-60s |
| `analysis` | Expert insight, deeper meaning | Thoughtful, authoritative | 60-90s |
| `legacy` | Long-term impact, relevance | Contemplative, connecting | 45-60s |
| `conclusion` | Wrap up, final thoughts | Satisfying, memorable | 30-45s |

### Writing Techniques for Intrigue

#### The Curiosity Gap
Introduce information that creates a gap between what viewers know and what they want to know:
- "There's one race that Ferrari wishes everyone would forget."
- "Only three people know what really happened in that meeting."

#### Foreshadowing
Plant seeds that pay off later:
- "Little did Verstappen know, this decision would haunt him for years."
- "Remember that corner. It becomes important later."

#### Parallel Structure
Connect past and present, or compare two stories:
- "In 1976, Lauda walked through fire. In 2019, another driver faced a different kind of inferno."

#### The Rule of Three
Group information in threes for rhythm and memorability:
- "He was fast. He was fearless. He was seventeen years old."

### Avoiding Repetitive Content

**REPETITION TO AVOID:**
- Restating the same fact in different words
- Summarizing what you just said
- Repeating the thesis in every section
- Using the same transition phrases

**REPETITION THAT WORKS:**
- Key phrases for emphasis ("And once again, Red Bull...")
- Callback references to earlier points
- Thematic echoes that tie the narrative together
- Repeating a word for stylistic impact ("Champion. Champion of Britain. Champion of the world.")

### Intuitive Storytelling

Make complex topics accessible:
- Use analogies viewers can relate to
- Build from simple to complex
- Define jargon when first used (but briefly)
- Use concrete examples, not abstract concepts

**ABSTRACT:**
> "The aerodynamic regulations significantly impacted downforce generation."

**INTUITIVE:**
> "Imagine pressing your hand out a car window at highway speed. Now imagine doing that at 200 miles per hour. That's the force these new rules just took away from the cars."

---

## VISUAL CONTENT STRATEGY

### CRITICAL: Footage Selection Rules for Long-Form Videos

**MUST AVOID - These will ruin the video:**
1. **No talking heads**: Never use footage where someone is speaking directly to camera (interviews, vlogs, commentary). This confuses viewers who expect to hear that person.
2. **No heavy text/subtitles**: Avoid footage with burned-in subtitles, lower thirds, or text overlays. These clash with our narrative.
3. **No vertical/short-form content**: Never use 9:16 vertical videos or TikTok/Shorts content. Only use 16:9 horizontal footage.
4. **No mismatched content**: The visual MUST relate to what the voiceover is discussing. Generic F1 footage is better than unrelated content.

**PREFER - These work well:**
1. **B-roll footage**: Race action, pit stops, car details, circuit aerials, paddock scenes without people talking
2. **Official highlight reels**: Race highlights, onboard cameras, slow-motion shots
3. **Technical footage**: Engine close-ups, factory shots, car components (without narration)
4. **Historical footage**: Archive clips relevant to the topic
5. **Stock footage**: Generic relevant visuals (fuel production, chemistry labs, factories)

**Search Query Best Practices:**
```
GOOD: "F1 pit stop refueling b-roll"
BAD:  "F1 pit stop interview"

GOOD: "Mercedes F1 factory tour no commentary"
BAD:  "Mercedes F1 explained video"

GOOD: "synthetic fuel production plant footage"
BAD:  "synthetic fuel documentary"
```

### When Stock Footage Isn't Available

Not all moments have fair-use footage. For these situations, use alternative visuals:

#### 1. Motion Graphics & Illustrations
Use for:
- Technical explanations (aerodynamics, engine components)
- Data visualization (lap times, championship points)
- Timeline sequences
- Comparison charts

Mark in script.json:
```json
{
  "footage_type": "graphic",
  "footage_query": "GRAPHIC: Championship points progression 2021",
  "graphic_description": "Animated line chart showing Verstappen vs Hamilton points through the 2021 season, with key races highlighted"
}
```

#### 2. Map Animations
Use for:
- Circuit walkthroughs
- Incident reconstructions
- Geographic context (driver origins, race locations)

```json
{
  "footage_type": "graphic",
  "footage_query": "GRAPHIC: Silverstone circuit layout with crash location",
  "graphic_description": "Top-down circuit map with animated car positions showing the 2021 Hamilton-Verstappen collision at Copse"
}
```

#### 3. Still Images with Ken Burns Effect (Pan & Zoom)
The Ken Burns effect transforms static images into dynamic visuals through slow pan and zoom movements. This is a proven documentary technique used by professionals.

Use for:
- Historical moments without video footage
- Driver portraits during biographical sections
- Newspaper headlines, magazine covers, documents
- Team photos, podium celebrations
- Circuit aerial views
- Car technical photos

**Motion Types:**
| Motion | Best For | Example |
|--------|----------|---------|
| `slow_zoom_in` | Building intensity, focusing on detail | Driver's face before race start |
| `slow_zoom_out` | Revealing context, showing scale | Crowd at a historic race |
| `pan_left` | Following action, timeline progression | Car evolution over years |
| `pan_right` | Transition, moving forward in story | From past to present |
| `pan_up` | Revealing, dramatic reveal | From car to driver standing |
| `pan_down` | Grounding, settling into scene | From sky to circuit |
| `zoom_in_pan` | Dynamic focus | Zooming into newspaper headline |
| `ken_burns_combo` | Complex movement | Slow zoom while panning |

```json
{
  "footage_type": "image",
  "footage_query": "IMAGE: Historic photo 1976 Lauda crash aftermath",
  "image_motion": "slow_zoom_in",
  "image_duration": 8,
  "image_source": "Getty Images / Fair Use",
  "motion_notes": "Start wide on the burning car, slowly zoom to focus on marshals responding"
}
```

**Image Quality Requirements:**
- Minimum resolution: 1920x1080 (HD) or 3840x2160 (4K)
- Higher resolution allows more zoom range without quality loss
- Horizontal images work best for 16:9 format
- For vertical images, use pan movements instead of zoom

**Sourcing Fair-Use Images:**
- Wikimedia Commons (public domain, CC licenses)
- Official F1/FIA press photos (editorial use)
- Team official media galleries
- Historical archives (with attribution)
- Creative Commons licensed photos

#### 4. Text Cards
Use for:
- Quotes (with attribution)
- Key statistics
- Date/location stamps
- Chapter transitions

```json
{
  "footage_type": "text_card",
  "footage_query": "TEXT: Niki Lauda quote about fear",
  "text_content": "\"Fear is stupid. So are regrets.\" — Niki Lauda",
  "style": "quote_card"
}
```

#### 5. Screen Recordings
Use for:
- Social media reactions
- Telemetry data
- Timing screens
- Official statements/press releases

### Footage Type Reference

| Type | Use Case | footage_type | Motion Options | Example |
|------|----------|--------------|----------------|---------|
| Video | Race footage, interviews | `video` | N/A | Standard YouTube search |
| Graphic | Charts, diagrams, animations | `graphic` | Animated | Technical explanations |
| Image | Photos, stills with motion | `image` | `slow_zoom_in`, `slow_zoom_out`, `pan_left`, `pan_right`, `pan_up`, `pan_down`, `ken_burns_combo` | Historical moments |
| Text Card | Quotes, stats, titles | `text_card` | `fade`, `slide_up` | Driver quotes |
| Map | Circuit layouts, geography | `map` | `animated`, `highlight` | Incident reconstruction |
| Screen | Telemetry, social media | `screen` | `scroll`, `zoom` | Data visualization |

### Visual Pacing Guidelines

Mix visual types to maintain viewer engagement:

| Video Duration | Recommended Mix |
|----------------|-----------------|
| 0-2 min | 70% video, 20% images, 10% graphics |
| 2-5 min | 60% video, 25% images, 15% graphics/text |
| 5-10 min | 50% video, 30% images, 20% graphics/text |

**Tips for Visual Variety:**
- Never use the same visual type for more than 3 consecutive segments
- Use graphics/text cards as "breathing room" between intense video sequences
- Ken Burns images work well for reflective, emotional moments
- Save video footage for action-heavy segments (races, overtakes, crashes)
- Use text cards to emphasize key quotes or statistics

---

## Workflow

### Phase 1: Research & Script Creation

1. **Understand the Prompt**: Analyze what story/narrative the user wants
   - Identify the main topic (driver profile, race analysis, history, etc.)
   - Determine the emotional core: What should viewers FEEL?
   - Find the unique angle: What's the fresh perspective?
   - Plan the narrative arc: Beginning → Conflict → Resolution

2. **Research**: Search web for facts, quotes, statistics, sources
   - Use web search to gather accurate information
   - **CRITICAL**: Record sources for every factual claim
   - Look for lesser-known details that add depth
   - Find direct quotes from drivers, team principals, journalists
   - Verify statistics and dates from official sources

3. **Create Script**: Generate `script.json` with comprehensive segments:
   ```json
   {
     "title": "Video Title",
     "format": "longform",
     "resolution": "4k",
     "duration_target": 600,
     "segments": [
       {
         "id": 1,
         "section": "cold_open",
         "text": "The hook that grabs attention immediately...",
         "context": "Dramatic opening - the climactic moment",
         "footage_type": "video",
         "footage_query": "YouTube search terms",
         "footage_start": 0,
         "references": [
           {
             "claim": "The specific claim being made",
             "source": "Source Name",
             "url": "https://source-url.com/article",
             "date": "2024-01-15"
           }
         ]
       },
       {
         "id": 2,
         "section": "intro",
         "text": "Establishing context after the hook...",
         "context": "Set up the story we're telling",
         "footage_type": "graphic",
         "footage_query": "GRAPHIC: Timeline of key events",
         "graphic_description": "Animated timeline showing the major milestones"
       }
     ],
     "references_summary": [
       {
         "source": "F1 Official",
         "url": "https://f1.com/...",
         "claims_supported": [1, 3, 5]
       }
     ]
   }
   ```

4. **Fact Check Script**: Run fact checker on created script
   ```bash
   python3 src/fact_checker.py --project {name} --web-search
   ```
   - Verify all claims have supporting sources
   - Flag any disputed or unverified claims
   - Do NOT proceed until all claims are verified or acknowledged

### Phase 2: Script Review (MANDATORY CHECKPOINT)

5. **REVIEW CHECKPOINT - STOP AND WAIT FOR USER APPROVAL**

   Present the complete script to the user:

   ---

   **📺 VIDEO SCRIPT REVIEW**

   **Title**: {title}
   **Duration**: ~{duration_target/60} minutes
   **Segments**: {number of segments}
   **Visual Mix**: {X} video clips, {Y} graphics, {Z} text cards

   ---

   **🎬 COLD OPEN**
   > {First segment text - the hook}

   **📖 STORY STRUCTURE**

   For each section, show:
   - Section name and purpose
   - Key narrative beats
   - Visual approach (video/graphic/image)

   **📚 SOURCES** ({count} references)
   List primary sources being cited.

   ---

   **Ask the user:**
   "Please review this script. I can:
   1. ✅ Proceed with video creation
   2. ✏️ Revise specific sections
   3. 🔍 Add more depth to a topic
   4. 🎯 Adjust the angle/focus
   5. 🔄 Start fresh with a different approach"

   **DO NOT PROCEED** until user explicitly approves.

### Phase 3: Asset Generation

6. **Generate Audio**: Use ElevenLabs API
   ```bash
   python3 src/audio_generator.py --project {name}
   ```

7. **Download/Create Visuals**:
   ```bash
   # For video footage
   python3 src/footage_downloader.py --project {name}

   # For graphics - manually create or use generation tools
   # Place in projects/{name}/footage/ with matching filenames
   ```

8. **Extract Previews**: Generate preview frames
   ```bash
   python3 src/preview_extractor.py --project {name}
   ```

9. **Verify All Assets**: CRITICAL
   - Check video footage matches narrative context
   - Verify graphics are clear and accurate
   - Ensure all segments have appropriate visuals

### Phase 4: Video Assembly

10. **Assemble Video**:
    ```bash
    python3 src/video_assembler_longform.py --project {name}
    ```

11. **Quality Check**:
    - Video/audio sync throughout
    - Graphics render correctly
    - Pacing feels right
    - End credits display properly

### Phase 5: Upload (Optional)

12. **Upload to YouTube**:
    ```bash
    python3 src/youtube_uploader_longform.py --project {name} --dry-run  # Preview
    python3 src/youtube_uploader_longform.py --project {name}            # Upload
    ```

---

## Segment Guidelines

### Text Length & Pacing

| Segment Type | Words | Duration | Sentences |
|--------------|-------|----------|-----------|
| Hook/Punch | 25-40 | 10-15s | 2-3 short |
| Standard | 50-70 | 20-25s | 3-5 mixed |
| Reflective | 60-80 | 25-30s | 3-4 flowing |
| Technical | 40-60 | 15-20s | 2-4 clear |

### Sentence Variety

Mix these patterns:
- **Punchy**: "He won. Again." (2-4 words)
- **Standard**: "The championship battle continued into the final race." (8-12 words)
- **Flowing**: "As the lights went out in Abu Dhabi, both drivers knew that everything they had worked for across twenty-one grueling races came down to this single moment." (25+ words)

### Transition Phrases

**Avoid overusing:**
- "Now let's talk about..."
- "Moving on to..."
- "Next, we'll look at..."

**Use instead:**
- Scene shifts: "Three thousand miles away..." / "Meanwhile, in Maranello..."
- Time jumps: "Fast forward to 2019." / "Rewind to his first race."
- Contrast: "But the data told a different story." / "Yet something felt wrong."
- Consequence: "The implications were immediate." / "What followed changed everything."

---

## Reference Requirements

**Every factual claim must have a source:**
- Driver statistics → F1 official records
- Historical events → Contemporary news reports
- Quotes → Direct source with date
- Technical details → Official team/F1 communications

**References format in script.json:**
```json
{
  "references": [
    {
      "claim": "Hamilton has 104 race wins",
      "source": "Formula 1 Official Statistics",
      "url": "https://www.formula1.com/en/results.html",
      "date": "2024-12-01"
    }
  ]
}
```

---

## Commands Reference

```bash
# Fact-check with web search
python3 src/fact_checker.py --project {name} --web-search

# Validate references coverage
python3 src/fact_checker.py --project {name} --validate-refs

# Generate audio (cached)
python3 src/audio_generator.py --project {name}

# Download all footage
python3 src/footage_downloader.py --project {name}

# Download specific segment with custom query
python3 src/footage_downloader.py --project {name} --segment {id} --query "search terms"

# Extract previews
python3 src/preview_extractor.py --project {name}

# Assemble 4K video
python3 src/video_assembler_longform.py --project {name} --resolution 4k

# Assemble HD video (faster)
python3 src/video_assembler_longform.py --project {name} --resolution hd

# Preview upload metadata
python3 src/youtube_uploader_longform.py --project {name} --dry-run

# Upload to YouTube
python3 src/youtube_uploader_longform.py --project {name}
```

---

## Output

Final video: `projects/{name}/output/final.mp4`
- Format: 3840x2160 (4K) or 1920x1080 (HD), 16:9 horizontal
- Duration: ~10 minutes + 19s outro (as specified)
- Framerate: 30fps
- Bitrate: 20Mbps (4K) / 12Mbps (HD)
- Audio: Voiceover + subtle ambient/motorsport background music (5% volume or less)
- **No burned-in captions**: Generate separate `.srt` or `.vtt` file for YouTube CC upload
- **Outro**: Reusable 19-second outro with voiceover (like/subscribe CTA) + 5-sec credits overlay

### Outro Audio (Reusable)
The outro audio is pre-generated and stored at `shared/audio/outro_longform.mp3` (~19 seconds).
This saves ElevenLabs credits and ensures consistent branding across all videos.

**Outro sequence:**
1. **0-5 seconds**: "Sources & References in Description" text overlay
2. **5-19 seconds**: Channel branding (F1 BURNOUTS) + CTA text while outro voiceover plays

**Outro voiceover content** (DO NOT regenerate - reuse the existing file):
> "If you enjoyed this pit stop through F1 history, smash that like button harder than a late braking move into turn one. Subscribe and hit the bell—because unlike a safety car restart, you don't want to miss what's coming next. Until then, keep the rubber on the track and the passion in your heart. F1 Burnouts, out."

### Subtitle/CC File Generation
For long-form videos, do NOT burn subtitles into the video. Instead:
1. Generate a separate `captions.srt` file in the output folder
2. Upload this file to YouTube as closed captions
3. This allows viewers to toggle captions on/off

### Background Music Guidelines
- Volume: 5% or lower (barely audible, just fills silence)
- Style: Ambient, cinematic, or motorsport-themed instrumental
- No vocals or prominent melodies that compete with narration
- Consider using no music for technical/serious segments
- Music file: `shared/music/background_longform.mp3` (if available)

---

## Quality Checklist

### Before presenting script to user:
- [ ] Hook grabs attention in first 10 seconds
- [ ] Clear narrative arc with tension/conflict
- [ ] No repeated information across segments
- [ ] Varied sentence lengths and structures
- [ ] All facts have referenced sources
- [ ] Visual variety (mix of footage types)
- [ ] "So what?" test passed for each segment
- [ ] Satisfying conclusion that ties back to opening

### Before downloading footage:
- [ ] Search queries specify "b-roll", "no commentary", or "footage"
- [ ] Queries avoid terms like "interview", "explained", "reaction"
- [ ] Queries include "16:9" or "horizontal" where needed
- [ ] Alternative queries ready for segments where stock footage may fail

### Before final assembly:
- [ ] All footage is 16:9 horizontal (no vertical videos)
- [ ] No footage contains talking heads or direct-to-camera speech
- [ ] No footage has heavy text overlays or subtitles
- [ ] Footage content matches the voiceover topic
- [ ] Preview frames verified for each segment
- [ ] End credits duration matches content (no blank time after)
- [ ] Background music volume is 5% or lower
- [ ] Separate .srt caption file generated

---

## API Keys Location
- ElevenLabs: `shared/creds/elevenlabs`
- YouTube: `shared/creds/youtube_client_secrets.json`
- SerpAPI (for fact-checking): `SERPAPI_KEY` environment variable

## Voice Settings
- Voice: Jarnathan - Confident and Versatile
- Voice ID: c6SfcYrb2t09NHXiT80T
- Model: eleven_multilingual_v2
- Best for: Long-form documentary narration, authoritative delivery
