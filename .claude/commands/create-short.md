# Create Short Video

Create an F1 short video based on user's prompt. This command handles the entire pipeline from script to final video.

## User Input
$ARGUMENTS

## Instructions

You are creating a short-form vertical video (9:16, ~60 seconds) for mobile consumption.

### Project Structure
```
f1.ai/
├── projects/           # Each short gets its own folder
│   └── {project-name}/
│       ├── script.json     # Video script with segments
│       ├── audio/          # Generated voiceovers (cached)
│       ├── footage/        # Downloaded source clips
│       ├── temp/           # Intermediate files
│       └── output/         # Final video
├── shared/
│   ├── music/              # Reusable background music
│   └── creds/              # API keys
├── src/                    # Core modules
│   ├── audio_generator.py
│   ├── footage_downloader.py
│   ├── video_assembler.py
│   └── preview_extractor.py
└── .claude/commands/
```

### Workflow

1. **Understand the Prompt**: Analyze what story/narrative the user wants
2. **Research** (if needed): Search web for facts, quotes, sources
3. **Create Script**: Generate `script.json` with segments containing:
   - `text`: Voiceover text
   - `context`: Segment purpose
   - `footage_query`: YouTube search query for relevant footage
   - `footage_start`: Timestamp in source video (verify with previews!)

4. **Download Footage**: Use yt-dlp to find and download clips
5. **Extract Previews**: Generate thumbnail frames to verify content matches
6. **Verify Footage**: CRITICAL - Check preview images to ensure:
   - Footage matches the narrative (not wrong era/drivers)
   - Timestamp shows the actual moment needed
   - Update `footage_start` based on visual verification

7. **Generate Audio**: Use ElevenLabs API (caches to avoid re-generation)
8. **Assemble Video**: Run video assembler with:
   - Consistent 30fps (avoids timestamp issues)
   - Blur-pad effect (no cropping)
   - Background music mixed at 15%
   - GPU encoding (VideoToolbox)

9. **Verify Final Output**: Check that:
   - Video and audio durations match
   - Video plays correctly throughout
   - Content syncs with narration

### Critical Lessons Learned

1. **Always verify footage with preview images** - YouTube search often returns wrong/related videos
2. **Force consistent framerate (30fps)** - Mixed framerates cause audio/video desync
3. **Use `split` filter in FFmpeg** - Can't consume same stream twice without splitting
4. **Re-encode during concat** - Stream copy causes timestamp corruption with mixed sources
5. **Cache audio files** - Don't regenerate voiceovers during video editing iterations
6. **Check video/audio stream durations** - They must match in final output

### API Keys Location
- ElevenLabs: `shared/creds/elevenlabs`

### Voice Settings
- Voice: Bradford (NNl6r8mD7vthiJatiJt1) - Expressive British storyteller
- Model: eleven_multilingual_v2

### Commands to Use
```bash
# Generate audio (run once, caches results)
python3 src/audio_generator.py --project {name}

# Download footage for a segment
python3 src/footage_downloader.py --project {name} --segment {id} --query "search terms"

# Extract preview frames
python3 src/preview_extractor.py --project {name}

# Assemble final video
python3 src/video_assembler.py --project {name}
```

### Video Features
- **Blur-pad effect**: Full footage shown centered, blurred version as background (no cropping)
- **Text captions**: White text in top blur area matching narration (auto-wrapped)
- **Background music**: Epic cinematic track mixed at 15% volume
- **GPU encoding**: VideoToolbox for fast processing

### Output
Final video: `projects/{name}/output/final.mp4`
- Format: 1080x1920 (9:16 vertical)
- Duration: ~60 seconds
- Framerate: 30fps
- Audio: Voiceover + background music
- Captions: Auto-generated from script text
