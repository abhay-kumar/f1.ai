# Create F1 Podcast

Create an F1 Burnouts podcast episode with the host discussing the provided topics directly with the audience. The content must be **engaging, funny, intriguing, and sometimes sarcastic** - leveraging Gemini TTS with SSML for expressive, professional podcast delivery.

## Parameters

- `$ARGUMENTS` - Synopsis/topics for the podcast episode (required). Can be a single topic or comma-separated list.

## The Host

The podcast features a single passionate host speaking directly to the audience:

### The Host of F1 Burnouts
- **Voice**: Charon (Gemini TTS) - Informative, engaging, authoritative
- **Background**: Expert in both engineering and F1 motorsport regulations/history
- **Team Affinity**: Proud McLaren fan (and not shy about it!) but respects all teams
- **Core Values**: 
  - Objective and fair - gives credit where due, critical when warranted (even of McLaren)
  - Passionate about engineering excellence across all teams
  - Cares deeply about climate change initiatives in F1
  - Strong advocate for women in F1
  - Wishes well for underperforming teams and departing drivers/teams
- **Personality Traits**:
  - Witty and quick with comebacks
  - Self-aware about their own biases (and jokes about it)
  - Finds humor in F1's absurdities and drama
  - Can be delightfully sarcastic when the situation calls for it
  - Genuinely cares about the sport and its future
- **Tone**: 
  - Immersive storytelling with intrigue
  - Humor and sarcasm woven throughout
  - Heartfelt when the moment calls for it
  - Brutal honesty when needed
  - Family-friendly (no swearing) - engages kids and adults alike
- **Speaking Style**: Conversational, as if talking directly to a friend about F1

## TTS Engine: Google Gemini 2.5 with SSML

This podcast uses **Google Gemini 2.5 TTS** with **comprehensive SSML enhancement** for immersive, expressive audio.

### Why Gemini TTS?
- **Free tier available** (gemini-2.5-flash-preview-tts)
- **Emotion markers** directly in text: `[excited]`, `[sarcastic]`, `[whispering]`
- **Full SSML support** for pauses, emphasis, and prosody control
- **Natural speech** with context-aware pacing
- **Hybrid control**: Mix [markers] and SSML tags for maximum expressiveness

### SSML Features (Auto-Applied by ssml_generator.py)

The script is automatically enhanced with professional podcast SSML:

#### 1. Strategic Pauses (`<break>`)
- **After greetings**: Let the energy land (0.9s after "Welcome back!")
- **Before reveals**: Build anticipation (0.6s before "But here's the thing...")
- **Comedic timing**: Perfect pause after setup, before punchline
- **Rhetorical questions**: Let them sink in (0.7s after "?")
- **Transitions**: Smooth segment changes (0.4-0.5s)

#### 2. Word Emphasis (`<emphasis>`)
- **Strong**: "incredible", "billion", "never", "championship"
- **Moderate**: "actually", "crucial", "amazing", "exactly"
- **Reduced**: Intimate phrases like "just between us"

#### 3. Number Processing (`<say-as>`)
- Years: "2024" reads as "twenty twenty-four"
- Large numbers: "1,000,000" reads naturally
- Percentages: "50%" reads as "fifty percent"
- Lap times: "1:23.456" reads properly

#### 4. Emotion Markers (Gemini-specific)
```
[excited]      - High energy, celebrations
[sarcastic]    - Dry humor, ironic observations
[empathetic]   - Heartfelt moments, tributes
[speaking slowly] - Dramatic emphasis
[whispering]   - Intimate asides
[laughing]     - Genuine humor moments
[sighing]      - Exasperation, reflection
```

### Available Voices
- **Charon** (default) - Informative, authoritative (ideal for podcasts)
- **Kore** - Firm, confident
- **Puck** - Upbeat, energetic
- **Zephyr** - Bright, lively
- **Enceladus** - Breathy, intimate
- **Aoede** - Breezy, conversational

## Instructions

You are creating a ~20 minute podcast episode where the host speaks directly to the audience about F1 topics. **The content must be engaging, funny, intriguing, and sometimes sarcastic.**

### Project Structure
```
projects/{project-name}/
├── script.json         # Podcast script with segments
└── output/
    ├── cover_art.jpg   # Podcast cover art (1400x1400)
    └── final.mp3       # Final podcast with intro/outro music
```

### Workflow

1. **Parse Topics**: Extract the topics/synopsis from `$ARGUMENTS`

2. **Research** (if needed): Search web for recent facts, quotes, technical details

3. **Generate Script**: Create `script.json` with this podcast format:
   ```json
   {
     "title": "Podcast Episode Title",
     "format": "podcast",
     "duration_target": 1200,
     "tts_engine": "gemini",
     "voice": "Charon",
     "host": {
       "name": "Host",
       "description": "The host of F1 Burnouts - engineering expert and F1 historian"
     },
     "segments": [
       {
         "id": 1,
         "text": "Welcome back to F1 Burnouts! I'm your host, and today we're diving into...",
         "context": "Intro",
         "emotion": "energetic"
       },
       {
         "id": 2,
         "text": "Now, let me tell you why this matters...",
         "context": "Main topic",
         "emotion": "intrigued"
       }
     ]
   }
   ```

4. **Script Guidelines - MAKING IT ENGAGING**:

   **STORYTELLING & INTRIGUE**:
   - Hook the audience in the first 10 seconds with something surprising or provocative
   - Build narratives with tension, reveals, and payoffs
   - Use cliffhangers within segments ("But wait... it gets better")
   - Drop hints about what's coming ("You're not going to believe what happened next")
   - Create mystery: "There's one detail that everyone seems to be missing..."

   **HUMOR & SARCASM**:
   - F1 is inherently dramatic - lean into the absurdity
   - Sarcasm works best when it's self-aware and affectionate
   - Mock predictable outcomes: "In news that shocked absolutely no one..."
   - Playful jabs at team tendencies: "Ferrari doing Ferrari things"
   - Self-deprecating humor about your own McLaren bias
   - Timing is everything - set up, pause, deliver
   
   **EMOTION & VARIATION**:
   - Alternate between energy levels - don't be one-note
   - Go from excited to contemplative to sarcastic to heartfelt
   - Use silence (pauses) as a tool - let big moments breathe
   - Show genuine passion for the sport, not manufactured enthusiasm
   - Be vulnerable when appropriate - share real reactions

   **DIRECT AUDIENCE ENGAGEMENT**:
   - Speak TO the audience, not at them ("you", "let me tell you", "think about this")
   - Pose rhetorical questions and pause
   - Anticipate and address counter-arguments
   - Create inside jokes that return throughout the episode
   - Make the listener feel like they're in on something

   **CONTENT DEPTH**:
   - Engineering depth: Explain technical concepts accessibly but accurately
   - Historical context: Connect current events to F1 history
   - Balanced criticism: Praise AND critique where deserved (including McLaren)
   - Hot takes: Don't be afraid to have strong opinions (but defend them)
   
   **STRUCTURE**:
   - **Target duration**: ~20 minutes (approximately 3000-3500 words total)
   - **Flow**: Hook -> Intro -> Deep dives -> Hot takes -> Heartfelt moment -> Sign-off
   - Vary segment lengths - not everything needs equal time
   - End strong - the last impression matters

5. **Writing for Gemini TTS with SSML**:

   The `ssml_generator.py` will automatically enhance your script, but write with these features in mind:

   **PUNCTUATION FOR PACING**:
   ```
   Ellipses (...) = trailing off, building suspense
   Em-dashes (—) = interruptions, asides, dramatic interjections  
   Exclamation marks = energy (use sparingly!)
   Question marks = pause for thought
   ```

   **EMOTION MARKERS IN TEXT** (Gemini reads these as instructions):
   ```
   "[excited] And this is where it gets absolutely wild!"
   "[speaking slowly] Think about that for a moment."
   "[sarcastic] Oh, what a surprise, another Ferrari strategy error."
   "[whispering] Now, here's something most people don't know..."
   "[laughing] I mean, you can't make this stuff up!"
   ```

   **WHEN TO USE INLINE MARKERS**:
   - At the START of emotionally distinct passages
   - For dramatic delivery shifts mid-segment
   - Sparingly - one per paragraph maximum
   - For comedic effect (sarcasm, mock surprise)

   **PHRASES THAT TRIGGER AUTO-PAUSES**:
   - "Welcome back to..." (0.9s pause after)
   - "But here's the thing..." (0.6s pause before)
   - "And in news that shocked no one..." (0.7s pause after)
   - Questions ending in "?" (0.7s pause after)
   - "Now," at start of sentence (0.5s pause before)

   **WORDS THAT GET AUTO-EMPHASIZED**:
   - Strong: incredible, billion, never, first, championship, zero
   - Moderate: actually, crucial, exactly, really

6. **Emotional Markers** (segment metadata for SSML enhancement):
   
   | Emotion | Use For | Gemini Marker | Prosody |
   |---------|---------|---------------|---------|
   | `energetic` | Exciting moments, celebrations | `[excited]` | Fast, high pitch |
   | `intrigued` | Mysteries, revelations, setups | `[intrigued]` | Slower, curious |
   | `contemplative` | Thoughtful analysis, reflection | `[speaking slowly]` | Slow, lower pitch |
   | `humorous` | Jokes, light moments | `[playful]` | Normal, slight lift |
   | `sarcastic` | Dry humor, ironic observations | `[sarcastic]` | Slower, deadpan |
   | `heartfelt` | Tributes, emotional moments | `[empathetic]` | Slow, soft |
   | `serious` | Critical analysis, concerns | `[serious]` | Slow, lower pitch |
   | `passionate` | Advocacy, engineering appreciation | `[passionate]` | Fast, high energy |

7. **CHECKPOINT - Script Review**:
   - Present the complete script to the user
   - Show all segments with text, context, and emotion
   - Display estimated duration based on word count (~150 words/minute)
   - **STOP and wait for user approval**
   - Make any requested changes before proceeding

8. **Generate Audio & Add Music**:
   ```bash
   # Step 1: Generate podcast audio (CHUNKED MODE - prevents voice degradation)
   python3 src/gemini_podcast_audio_generator.py --project {name} --chunked

   # Step 2: Add intro/outro music
   python3 src/podcast_music_mixer.py --project {name} \
     --music shared/music/podcast_default.mp3 \
     --documentary
   ```

   **Why Chunked Mode?**
   Gemini TTS voice quality degrades after ~4 minutes of continuous generation (becomes raspy, strained).
   The `--chunked` mode splits content into ~250-word chunks (~60-90 seconds each), keeping each TTS
   request short enough for consistent voice quality. SSML is preserved within each chunk.

   **Audio Generator Options:**
   - `--chunked` - **REQUIRED for podcasts > 5 minutes** (prevents voice degradation)
   - `--model pro` - Use Pro model (paid, highest quality)
   - `--voice Kore` - Change voice (default: Charon)
   - `--preview` - Preview transcript and voice profile
   - `--legacy` - Use old segment-by-segment mode (not recommended)

   **WARNING**: Do NOT use default single-request mode for long podcasts - voice will degrade after ~4 min.
   
   **Music Mixer Options:**
   - `--documentary` - Clean intro/outro only (recommended)
   - `--dry-run` - Preview music placement

9. **Verify Output**:
   - Check total duration matches expectations
   - Ensure smooth transitions between segments
   - Report final audio location

### Voice & Style Patterns

**ENGAGEMENT HOOKS**:
```
"Now, here's where it gets interesting..."
"Stay with me on this one..."
"I know what you're thinking, but hear me out..."
"Let's break this down together..."
"You're going to love this..."
"Okay, buckle up for this one..."
"I need to tell you something that's been bothering me..."
```

**BUILDING INTRIGUE**:
```
"There's something nobody's talking about..."
"And here's the detail everyone missed..."
"But wait... it gets even better."
"Now, what they don't tell you is..."
"The real story? Nobody wants to admit this..."
```

**SARCASM & HUMOR**:
```
"[sarcastic] Oh, what a surprise, another penalty that totally makes sense..."
"And in news that shocked absolutely no one..."
"Because obviously, that's exactly what everyone predicted..."
"[laughing] I mean, you can't make this stuff up!"
"Ferrari being Ferrari, as they say..."
"In other breaking news, water is wet..."
"Ah yes, the classic 'we need to talk about strategy' post-race radio..."
```

**MCLAREN REFERENCES (balanced)**:
```
"Look, I'm a McLaren fan, you all know that, but even I have to admit..."
"As much as it pains my papaya-loving heart..."
"Now, this is where my McLaren bias might show, but objectively speaking..."
"[sighing] Being a McLaren fan builds character, I'll tell you that..."
```

**ENGINEERING APPRECIATION**:
```
"The engineering behind this is absolutely brilliant..."
"This is where the physics gets beautiful..."
"The regulations say X, but the clever interpretation is..."
"Now, from an engineering perspective, this is actually genius..."
```

**HEARTFELT MOMENTS**:
```
"[empathetic] This is what F1 is really about..."
"You have to respect the journey..."
"Regardless of the team, that's a human being who gave everything..."
"[speaking slowly] Take a moment to appreciate what we just witnessed..."
```

**CRITICAL BUT FAIR**:
```
"I love this team, but let's be honest here..."
"Credit where it's due, but also..."
"This isn't criticism for its own sake - this matters because..."
"I hate to say it, but someone needs to..."
```

**SIGN-OFFS**:
```
"[excited] That's all for today's episode of F1 Burnouts. Until next time, keep the rubber on the track!"
"Thanks for listening - now go argue with someone about this on the internet. That's what F1 fans do."
"If you enjoyed this, share it with a friend who needs more F1 drama in their life."
```

### Example Segment with Full SSML Enhancement

**Script text** (what you write):
```
"Welcome back to F1 Burnouts! Today we're diving into something absolutely wild. [sarcastic] And in news that shocked absolutely no one... Ferrari has once again found a creative way to throw away a race win. Now, here's the thing — and I say this as someone who genuinely respects the Scuderia — their strategy team seems to be operating on a different timeline than the rest of us. But wait... it gets better. Let me tell you what happened next."
```

**After SSML processing** (what Gemini TTS receives):
```
[excited] Welcome back to F1 Burnouts! <break time='0.9s'/> Today we're diving into something <emphasis level="strong">absolutely</emphasis> wild. [sarcastic] And in news that <emphasis level="strong">shocked</emphasis> <emphasis level="strong">absolutely</emphasis> <emphasis level="strong">no one</emphasis>... <break time='0.7s'/> Ferrari has once again found a creative way to throw away a race win. <break time='0.5s'/> Now, <break time='0.5s'/> here's the thing <break time='0.25s'/> and I say this as someone who <emphasis level="moderate">genuinely</emphasis> respects the Scuderia <break time='0.25s'/> their strategy team seems to be operating on a different timeline than the rest of us. <emphasis level="moderate">But</emphasis> wait... <break time='0.5s'/> it gets better. Let me tell <emphasis level="moderate">you</emphasis> what happened next.
```

### Output

**Final Podcast**: `projects/{name}/output/final.mp3`
- Format: MP3, 256kbps
- Sample rate: 44.1kHz
- Intro and outro music included
- Loudness normalized to -16 LUFS
- Duration: ~20 minutes

## Background Music Integration

Clean intro/outro music approach - voice content remains completely clean.

### How It Works

| Section | Timing | Description |
|---------|--------|-------------|
| **Intro** | 00:00 - 00:12 | Music at 80%, fades out as voice starts |
| **Content** | 00:12 - end-10s | Pure voice, NO music |
| **Outro** | last 10s - end | Music fades in, swells after voice ends |

### Podcast Music Track

Default track in `shared/music/podcast_default.mp3` (energetic rock, ~2.5 min)

**Credit**: Track by [Alex-Productions](https://soundcloud.com/alexproductionsmusic) - No Copyright Music

### Music Mixing Command

```bash
# Add intro/outro music (outputs to final.mp3)
python3 src/podcast_music_mixer.py --project {name} \
  --music shared/music/podcast_default.mp3 \
  --documentary \
  --output projects/{name}/output/final.mp3

# Preview without processing
python3 src/podcast_music_mixer.py --project {name} \
  --music shared/music/podcast_default.mp3 \
  --documentary --dry-run
```

### API Key Setup

Get your free Google AI API key:
1. Visit: https://aistudio.google.com/apikey
2. Create/copy your API key
3. Save it: `echo 'YOUR_KEY' > shared/creds/google_ai`

### After Creation

Suggest potential next steps:
- Upload to podcast platform (RSS.com, Spotify, Apple Podcasts)
- Generate transcript for show notes

### Quality Checklist

Before generating audio, verify the script has:
- [ ] A hook in the first 10 seconds
- [ ] At least 3 different emotion types used
- [ ] Sarcasm/humor woven throughout (not just in one section)
- [ ] Rhetorical questions that engage the listener
- [ ] A heartfelt or reflective moment somewhere
- [ ] McLaren reference(s) that are self-aware
- [ ] A strong closing that makes people want more
- [ ] Proper use of punctuation for pacing (... — !)
- [ ] Inline emotion markers for key delivery moments

## Technical Notes

### Gemini TTS Voice Degradation

**Problem**: Gemini TTS voice quality degrades after ~4 minutes of continuous generation (becomes raspy, strained, "throat infection" effect).

**Solution**: Always use `--chunked` mode for podcasts longer than 5 minutes:
```bash
python3 src/gemini_podcast_audio_generator.py --project {name} --chunked
```

**How it works**:
- Splits script into ~250-word chunks (~60-90 seconds each)
- Each chunk is a separate TTS request (stays under degradation threshold)
- SSML and emotion markers are preserved within each chunk
- Chunks are concatenated seamlessly

**Avoid**:
- Single-request mode (default) for long podcasts
- Legacy segment-by-segment mode (`--legacy`)

### Local TTS Alternative (Not Recommended for Podcasts)

Qwen3-TTS 1.7B with MLX (`src/qwen_podcast_audio_generator.py`) is available but:
- Produces more robotic output compared to Gemini
- No SSML support - uses `instruct` parameter instead
- Better suited for sleep/meditation content, not energetic podcasts
