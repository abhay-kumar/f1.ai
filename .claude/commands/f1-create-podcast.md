# Create F1 Podcast

Create an F1 Burnouts podcast episode (~20 minutes) with the host discussing provided topics directly with the audience.

## Parameters

- `$ARGUMENTS` - Synopsis/topics for the episode (required). Single topic or comma-separated list.

## Instructions

> Host persona, voice patterns, and quality checklist: see **f1-podcast-voice** skill
> Script writing guidelines: see **f1-scriptwriting** skill

### TTS Engine: Google Gemini 2.5 with SSML

- **Free tier**: gemini-2.5-flash-preview-tts
- **Emotion markers** in text: `[excited]`, `[sarcastic]`, `[whispering]`
- **Full SSML support**: pauses, emphasis, prosody (auto-applied by `ssml_generator.py`)
- **Available voices**: Charon (default, authoritative), Kore (firm), Puck (upbeat), Zephyr (bright), Enceladus (breathy), Aoede (breezy)

### Project Structure
```
projects/{name}/
├── script.json         # Podcast script with segments
└── output/
    ├── cover_art.jpg   # Podcast cover (1400x1400)
    └── final.mp3       # Final podcast with intro/outro music
```

### Workflow

1. **Parse Topics**: Extract topics from `$ARGUMENTS`

2. **Review Previous Episodes** (REQUIRED): Fetch `https://media.rss.com/f1-burnouts/feed.xml` via WebFetch. Read transcripts from recent 2-3 episodes. Build a "Previously Covered" summary: key topics, running jokes, predictions to revisit, hot takes to confirm/contradict. Use for back-references and avoiding repetition.

3. **Research F1 Media Commentary** (REQUIRED): Web search Sky Sports F1, The Race, Autosport, PlanetF1, GPFans, Motorsport.com. Find controversial opinions, hot takes, interesting quotes, under-reported angles. Build 3-5 "Media Talking Points" to weave into script.

4. **Research Current Facts** (if needed): Web search for stats, technical details, quotes

5. **Generate Script**: Create `script.json`:
   ```json
   {
     "title": "Episode Title",
     "format": "podcast",
     "duration_target": 1200,
     "tts_engine": "gemini",
     "voice": "Charon",
     "host": { "name": "Host", "description": "The host of F1 Burnouts" },
     "segments": [
       { "id": 1, "text": "Welcome back to F1 Burnouts!...", "context": "Intro", "emotion": "energetic" },
       { "id": 2, "text": "Now, let me tell you why this matters...", "context": "Main topic", "emotion": "intrigued" }
     ]
   }
   ```

6. **Script Guidelines**:
   - **Target**: ~20 minutes (~3000-3500 words total)
   - **Flow**: Hook → Intro → Deep dives → Hot takes → Heartfelt moment → Sign-off
   - **Content**: Engineering depth, historical context, balanced criticism, strong opinions
   - **Previous episodes**: Reference naturally 1-2 times, don't re-explain covered topics
   - **Media commentary**: Weave in 2-3 pundit opinions as natural conversation points
   - **Emotion markers**: Place at start of emotionally distinct passages, sparingly

7. **CHECKPOINT - Script Review**: Present complete script with segments, emotions, estimated duration (~150 words/min). **STOP and wait for user approval.**

8. **Generate Audio & Add Music**:
   ```bash
   # Step 1: Generate podcast audio (CHUNKED MODE — prevents voice degradation)
   python3 src/gemini_podcast_audio_generator.py --project {name} --chunked

   # Step 2: Add intro/outro music
   python3 src/podcast_music_mixer.py --project {name} \
     --music shared/music/podcast_default.mp3 \
     --documentary \
     --output projects/{name}/output/final.mp3
   ```

   **Options**: `--model pro` (paid, highest quality), `--voice Kore`, `--preview` (transcript preview), `--dry-run` (music preview)

   **WARNING**: Always use `--chunked` for podcasts > 5 minutes — voice degrades after ~4 min without it.

9. **Verify Output**: Check duration matches expectations, smooth transitions, report final audio location.

### Technical Notes

#### Gemini TTS Voice Degradation
Chunked mode splits into ~250-word chunks (~60-90s each), keeping each TTS request under the degradation threshold. SSML preserved within chunks.

#### Gemini TTS Ad-Lib Fix
Gemini sometimes generates extra speech in the last chunk. Detect with silence detection:
```bash
ffmpeg -i projects/{name}/audio/chunk_NNN.mp3 -af "silencedetect=noise=-28dB:d=0.3" -f null - 2>&1 | grep silence | tail -5
```
Fix: trim at silence gap (`ffmpeg -y -i chunk.mp3 -t {cut_point} -c:a libmp3lame -b:a 256k chunk.mp3`) or delete and regenerate.

### Background Music

| Section | Timing | Description |
|---------|--------|-------------|
| **Intro** | 00:00 - 00:12 | Music at 80%, fades out as voice starts |
| **Content** | 00:12 - end-10s | Pure voice, NO music |
| **Outro** | last 10s - end | Music fades in, swells after voice ends |

Default track: `shared/music/podcast_default.mp3` (energetic rock, ~2.5 min). Credit: Alex-Productions — No Copyright Music.

### Output
**Final Podcast**: `projects/{name}/output/final.mp3` — MP3, 256kbps, 44.1kHz, intro/outro music, normalized to -16 LUFS, ~20 minutes.

### API Key
Google AI: `shared/creds/google_ai` (free at https://aistudio.google.com/apikey)

### After Creation
Suggest: upload to podcast platform, generate transcript for show notes.
