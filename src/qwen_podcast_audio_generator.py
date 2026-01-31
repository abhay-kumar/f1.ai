#!/usr/bin/env python3
"""
Qwen3-TTS Podcast Audio Generator

Generates podcast audio using local Qwen3-TTS model with emotion-aware instruct mapping.
Optimized for MLX on Apple Silicon for fast, consistent voice generation.

Features:
- Strips Gemini-style emotion markers and maps to Qwen instruct parameters
- CustomVoice model with preset speakers (Ryan, Eric, Dylan, etc.)
- Chunked processing for long segments (~8+ min each)
- Transition music between segments
- MLX backend for Apple Silicon GPU acceleration

Usage:
    python3 src/qwen_podcast_audio_generator.py --project f1-2026-engine-revolution
    python3 src/qwen_podcast_audio_generator.py --project f1-2026-engine-revolution --voice Eric
    python3 src/qwen_podcast_audio_generator.py --project f1-2026-engine-revolution --preview
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PROJECTS_DIR


# ============================================================================
# Configuration
# ============================================================================

# Default speaker - Ryan selected by user
DEFAULT_SPEAKER = "Ryan"

# Emotion-to-Instruct mapping for podcast delivery
EMOTION_INSTRUCT_MAP = {
    # Segment-level emotions
    "energetic": "High energy, enthusiastic podcast host. Engaging and lively delivery with passion for the subject.",
    "intrigued": "Curious and investigative tone. Building intrigue and drawing the listener in with interesting discoveries.",
    "excited": "Excited and animated delivery. Conveying genuine enthusiasm and wonder at the topics being discussed.",
    "contemplative": "Thoughtful and reflective. Taking time to consider the implications of what's being discussed.",
    "serious": "Serious and authoritative tone. Conveying the gravity and importance of the subject matter.",
    "humorous": "Light-hearted and playful. Finding the humor in situations while still being informative.",

    # Default for unmarked segments
    "default": "Natural, conversational podcast host. Engaging storytelling with varied pacing and emotional range.",
}

# Inline marker to instruct suffix mapping
INLINE_MARKER_MAP = {
    "excited": "with excitement and energy",
    "laughing": "with warmth and amusement, as if chuckling",
    "sarcastic": "with dry, knowing sarcasm",
    "sighing": "with a reflective sigh, slight exasperation",
    "intrigued": "with curiosity and building interest",
    "speaking slowly": "slowly and deliberately for emphasis",
    "whispering": "in a hushed, conspiratorial tone",
}

# Chunk size for processing
MAX_CHUNK_WORDS = 400  # Slightly smaller for podcast pacing

# Output settings
SAMPLE_RATE = 24000
OUTPUT_FORMAT = "mp3"
MP3_BITRATE = "192k"

# Transition music settings
TRANSITION_MUSIC_DURATION = 3.0  # seconds of music between segments


# ============================================================================
# Text Processing Functions
# ============================================================================

def strip_emotion_markers(text: str) -> str:
    """Remove Gemini-style emotion markers from text

    Markers like [excited], [laughing], [sarcastic], [speaking slowly] are stripped.

    Args:
        text: Text with potential emotion markers

    Returns:
        Clean text without markers
    """
    # Pattern matches [word] or [word word] markers
    pattern = r'\[(?:excited|laughing|sarcastic|sighing|intrigued|speaking slowly|whispering|speaking|slowly|chuckling|amused|contemplative|serious)\]'
    cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Clean up double spaces and leading/trailing whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()

    return cleaned


def get_instruct_for_segment(segment: dict) -> str:
    """Get the instruct parameter for a segment based on its emotion

    Args:
        segment: Segment dict with 'emotion' field

    Returns:
        Instruct string for Qwen TTS
    """
    emotion = segment.get("emotion", "default").lower()
    return EMOTION_INSTRUCT_MAP.get(emotion, EMOTION_INSTRUCT_MAP["default"])


def chunk_text_for_podcast(text: str, max_words: int = MAX_CHUNK_WORDS) -> list:
    """Split podcast text into chunks at natural pause points

    Podcast-optimized: prefers splits at paragraph breaks, then sentences.

    Args:
        text: Full segment text
        max_words: Maximum words per chunk

    Returns:
        List of text chunks
    """
    # First, split by paragraph (double newline or explicit break)
    paragraphs = re.split(r'\n\n+', text)

    chunks = []
    current_chunk = []
    current_words = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Split paragraph into sentences
        sentences = re.split(r'(?<=[.!?])\s+', para)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_words = len(sentence.split())

            # If single sentence exceeds max, split it further
            if sentence_words > max_words:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_words = 0

                # Split by commas/semicolons
                parts = re.split(r'[,;]\s*', sentence)
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    part_words = len(part.split())
                    if current_words + part_words > max_words and current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = [part]
                        current_words = part_words
                    else:
                        current_chunk.append(part)
                        current_words += part_words
            elif current_words + sentence_words > max_words and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_words = sentence_words
            else:
                current_chunk.append(sentence)
                current_words += sentence_words

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


# ============================================================================
# MLX Backend Functions
# ============================================================================

def check_mlx_available():
    """Check if MLX is available"""
    try:
        import mlx_audio
        return True
    except ImportError:
        return False


def load_qwen_model_mlx(model_size: str = "1.7b"):
    """Load Qwen3-TTS CustomVoice model via MLX"""
    from mlx_audio.tts.utils import load_model

    if model_size == "0.6b":
        model_id = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"
    else:
        model_id = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"

    print(f"Loading MLX model: {model_id}")
    print("Using Apple Silicon GPU acceleration")

    start = time.time()
    model = load_model(model_id)
    load_time = time.time() - start
    print(f"Model loaded in {load_time:.1f}s")

    return model, model_id


def generate_audio_chunk_mlx(
    model,
    model_id: str,
    text: str,
    speaker: str,
    instruct: str,
    language: str = "English"
) -> tuple:
    """Generate audio for a chunk using MLX CustomVoice"""
    import numpy as np

    results = list(model.generate_custom_voice(
        text=text,
        speaker=speaker,
        language=language,
        instruct=instruct,
    ))

    if not results:
        raise RuntimeError("No audio generated")

    audio = results[0].audio

    # Convert MLX array to numpy
    if hasattr(audio, 'tolist'):
        audio = np.array(audio.tolist(), dtype=np.float32)
    elif not isinstance(audio, np.ndarray):
        audio = np.array(audio, dtype=np.float32)

    return audio, SAMPLE_RATE


# ============================================================================
# Audio File Functions
# ============================================================================

def save_audio_wav(audio_data, sample_rate: int, output_path: str):
    """Save audio as WAV file"""
    import soundfile as sf
    import numpy as np

    if not isinstance(audio_data, np.ndarray):
        audio_data = np.array(audio_data, dtype=np.float32)

    # Normalize to prevent clipping
    max_val = np.max(np.abs(audio_data))
    if max_val > 1.0:
        audio_data = audio_data / max_val * 0.95

    sf.write(output_path, audio_data, sample_rate)
    return output_path


def convert_wav_to_mp3(wav_path: str, mp3_path: str, bitrate: str = MP3_BITRATE):
    """Convert WAV to MP3 with podcast-standard loudness normalization"""
    import subprocess

    # Podcast loudness: -16 LUFS (standard for podcasts/spoken word)
    cmd = [
        "ffmpeg", "-y",
        "-i", wav_path,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-codec:a", "libmp3lame",
        "-b:a", bitrate,
        "-ar", "44100",
        "-ac", "1",
        mp3_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")

    os.remove(wav_path)
    return mp3_path


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds"""
    import subprocess

    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0.0
    return float(result.stdout.strip())


def concatenate_with_transitions(
    audio_files: list,
    output_path: str,
    music_path: str = None,
    transition_duration: float = TRANSITION_MUSIC_DURATION
):
    """Concatenate audio files with optional music transitions between them

    Args:
        audio_files: List of audio file paths
        output_path: Output path for concatenated audio
        music_path: Optional path to transition music
        transition_duration: Duration of transition in seconds
    """
    import subprocess
    import tempfile

    if len(audio_files) == 1 and not music_path:
        import shutil
        shutil.copy(audio_files[0], output_path)
        return output_path

    # Create concat list
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for i, audio_file in enumerate(audio_files):
            escaped_path = os.path.abspath(audio_file).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
        concat_list = f.name

    try:
        # Simple concatenation (transition music handled separately if needed)
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Concatenation failed: {result.stderr}")
    finally:
        os.remove(concat_list)

    return output_path


# ============================================================================
# Main Generation Functions
# ============================================================================

def generate_segment_audio(
    model,
    model_id: str,
    segment: dict,
    output_dir: Path,
    segment_index: int,
    speaker: str
) -> str:
    """Generate audio for a single podcast segment

    Args:
        model: Loaded Qwen model
        model_id: Model identifier
        segment: Segment dict with text, emotion, context
        output_dir: Directory to save audio
        segment_index: 1-indexed segment number
        speaker: Speaker name

    Returns:
        Path to generated MP3 file
    """
    import numpy as np

    raw_text = segment.get("text", "")
    emotion = segment.get("emotion", "default")
    context = segment.get("context", f"Segment {segment_index}")

    # Strip emotion markers from text
    clean_text = strip_emotion_markers(raw_text)
    word_count = len(clean_text.split())

    # Get instruct based on segment emotion
    instruct = get_instruct_for_segment(segment)

    print(f"\n{'='*60}")
    print(f"Segment {segment_index}: {context}")
    print(f"Emotion: {emotion}")
    print(f"Text length: {word_count} words (cleaned)")
    print(f"Speaker: {speaker}")
    print(f"Instruct: {instruct[:60]}...")
    print(f"{'='*60}")

    # Check if output already exists
    output_name = f"segment_{segment_index:02d}"
    mp3_path = output_dir / f"{output_name}.mp3"

    if mp3_path.exists():
        duration = get_audio_duration(str(mp3_path))
        if duration > 0:
            print(f"Already exists: {mp3_path} ({duration/60:.1f} minutes)")
            return str(mp3_path)

    # Chunk the text
    chunks = chunk_text_for_podcast(clean_text)
    print(f"Split into {len(chunks)} chunks")

    # Generate audio for each chunk
    chunk_audios = []
    total_gen_time = 0
    total_audio_duration = 0

    for i, chunk in enumerate(chunks):
        chunk_words = len(chunk.split())
        print(f"  Chunk {i+1}/{len(chunks)}: {chunk_words} words...", end=" ", flush=True)
        start_time = time.time()

        audio, sr = generate_audio_chunk_mlx(model, model_id, chunk, speaker, instruct)
        chunk_audios.append(audio)

        duration = len(audio) / sr
        elapsed = time.time() - start_time
        total_gen_time += elapsed
        total_audio_duration += duration

        rtf = elapsed / duration if duration > 0 else 0
        print(f"{duration:.1f}s audio in {elapsed:.1f}s (RTF: {rtf:.2f}x)")

    # Concatenate chunks
    print("Concatenating chunks...")
    full_audio = np.concatenate(chunk_audios)

    # Save as WAV then convert to MP3
    wav_path = output_dir / f"{output_name}.wav"
    save_audio_wav(full_audio, SAMPLE_RATE, str(wav_path))
    convert_wav_to_mp3(str(wav_path), str(mp3_path))

    final_duration = len(full_audio) / SAMPLE_RATE
    overall_rtf = total_gen_time / final_duration if final_duration > 0 else 0

    print(f"\nSaved: {mp3_path}")
    print(f"Duration: {final_duration/60:.1f} minutes")
    print(f"Generation time: {total_gen_time/60:.1f} minutes")
    print(f"Overall RTF: {overall_rtf:.2f}x")

    return str(mp3_path)


def generate_podcast_audio(
    project_dir: Path,
    speaker: str = DEFAULT_SPEAKER,
    model_size: str = "1.7b",
    add_music: bool = False
):
    """Generate complete podcast audio for a project

    Args:
        project_dir: Path to project directory
        speaker: Speaker name (Ryan, Eric, Dylan, etc.)
        model_size: Model size ("0.6b" or "1.7b")
        add_music: Whether to add intro/outro music (handled separately)

    Returns:
        Path to final podcast audio
    """
    # Check MLX availability
    if not check_mlx_available():
        print("ERROR: MLX not available.")
        print("Install with: pip install mlx-audio")
        sys.exit(1)

    # Load script
    script_path = project_dir / "script.json"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    with open(script_path) as f:
        script = json.load(f)

    # Create directories
    audio_dir = project_dir / "audio"
    output_dir = project_dir / "output"
    audio_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    print(f"\nProject: {script.get('title', 'Untitled')}")
    print(f"Format: {script.get('format', 'podcast')}")
    print(f"Speaker: {speaker}")

    # Load model
    print("\nLoading Qwen3-TTS CustomVoice model...")
    model, model_id = load_qwen_model_mlx(model_size)

    # Generate each segment
    segment_files = []
    segments = script.get("segments", [])
    total_segments = len(segments)

    print(f"\nGenerating {total_segments} segments...")
    overall_start = time.time()

    for i, segment in enumerate(segments, 1):
        mp3_path = generate_segment_audio(
            model, model_id, segment, audio_dir, i, speaker
        )
        segment_files.append(mp3_path)

        elapsed = time.time() - overall_start
        if i > 0:
            avg_per_segment = elapsed / i
            remaining = (total_segments - i) * avg_per_segment
            print(f"\nProgress: {i}/{total_segments} segments")
            print(f"Elapsed: {elapsed/60:.1f} min, Est. remaining: {remaining/60:.1f} min")

    # Concatenate all segments
    print(f"\n{'='*60}")
    print("Creating final podcast audio...")

    voice_only_path = output_dir / "voice_only.mp3"
    concatenate_with_transitions(segment_files, str(voice_only_path))

    final_duration = get_audio_duration(str(voice_only_path))
    total_time = time.time() - overall_start

    print(f"\nVoice-only audio: {voice_only_path}")
    print(f"Total duration: {final_duration/60:.1f} minutes")
    print(f"Total generation time: {total_time/60:.1f} minutes")
    print(f"Overall RTF: {total_time/final_duration:.2f}x")

    print(f"\n{'='*60}")
    print("Done! Voice audio generated successfully.")
    print(f"\nTo add intro/outro music, run:")
    print(f"  python3 src/podcast_music_mixer.py --project {project_dir.name} \\")
    print(f"    --input {voice_only_path} \\")
    print(f"    --documentary")
    print(f"{'='*60}")

    return str(voice_only_path)


def preview_podcast_script(project_dir: Path):
    """Preview podcast script with emotion analysis"""
    script_path = project_dir / "script.json"

    with open(script_path) as f:
        script = json.load(f)

    print(f"Title: {script.get('title', 'Untitled')}")
    print(f"Format: {script.get('format', 'podcast')}")
    print(f"Target duration: {script.get('duration_target', 0) / 60:.0f} minutes")
    print(f"Original TTS engine: {script.get('tts_engine', 'unknown')}")
    print(f"Original voice: {script.get('voice', 'unknown')}")
    print(f"\nSegments: {len(script.get('segments', []))}")

    total_words = 0
    total_markers = 0

    for i, seg in enumerate(script.get("segments", []), 1):
        raw_text = seg.get("text", "")
        emotion = seg.get("emotion", "default")
        context = seg.get("context", "")

        # Count markers
        markers = re.findall(r'\[(?:excited|laughing|sarcastic|sighing|intrigued|speaking slowly|whispering)\]', raw_text, re.IGNORECASE)
        total_markers += len(markers)

        # Clean text for word count
        clean_text = strip_emotion_markers(raw_text)
        words = len(clean_text.split())
        total_words += words

        # Estimate duration at ~150 WPM for podcast pacing
        duration_mins = words / 150

        instruct = get_instruct_for_segment(seg)

        print(f"\n  {i}. {context}")
        print(f"     Emotion: {emotion}")
        print(f"     Instruct: {instruct[:50]}...")
        print(f"     Words: {words} (~{duration_mins:.1f} min)")
        print(f"     Markers found: {len(markers)}")
        if clean_text:
            preview = clean_text[:100].replace('\n', ' ')
            print(f"     Preview: \"{preview}...\"")

    estimated_mins = total_words / 150
    print(f"\n{'='*60}")
    print(f"Total: {total_words:,} words")
    print(f"Emotion markers to strip: {total_markers}")
    print(f"Estimated duration: ~{estimated_mins:.1f} minutes (at 150 WPM)")

    # Estimate generation time
    est_gen_time = estimated_mins * 1.0  # ~1x RTF on Apple Silicon
    print(f"Estimated generation time: ~{est_gen_time:.1f} minutes (on Apple Silicon)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate podcast audio using Qwen3-TTS with emotion-aware instruct mapping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview script with emotion analysis
    python3 src/qwen_podcast_audio_generator.py --project f1-2026-engine-revolution --preview

    # Generate podcast with Ryan (default)
    python3 src/qwen_podcast_audio_generator.py --project f1-2026-engine-revolution

    # Generate with different voice
    python3 src/qwen_podcast_audio_generator.py --project f1-2026-engine-revolution --voice Eric

    # Generate single segment (for testing)
    python3 src/qwen_podcast_audio_generator.py --project f1-2026-engine-revolution --segment 1

Available voices: Ryan, Eric, Dylan, Serena, Vivian, Aiden
        """
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Project name (folder in projects/)"
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_SPEAKER,
        help=f"Speaker voice (default: {DEFAULT_SPEAKER})"
    )
    parser.add_argument(
        "--segment",
        type=int,
        help="Generate only this segment number (1-indexed)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview script structure without generating"
    )
    parser.add_argument(
        "--model",
        choices=["0.6b", "1.7b"],
        default="1.7b",
        help="Model size: 0.6b (faster) or 1.7b (better quality, default)"
    )

    args = parser.parse_args()

    project_dir = Path(PROJECTS_DIR) / args.project
    if not project_dir.exists():
        print(f"Error: Project not found: {project_dir}")
        sys.exit(1)

    if args.preview:
        preview_podcast_script(project_dir)
    elif args.segment:
        # Check MLX
        if not check_mlx_available():
            print("ERROR: MLX not available. Install with: pip install mlx-audio")
            sys.exit(1)

        # Load script and generate single segment
        with open(project_dir / "script.json") as f:
            script = json.load(f)

        segments = script.get("segments", [])
        if args.segment < 1 or args.segment > len(segments):
            print(f"Error: Segment {args.segment} not found (have {len(segments)} segments)")
            sys.exit(1)

        model, model_id = load_qwen_model_mlx(args.model)
        audio_dir = project_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        generate_segment_audio(
            model, model_id,
            segments[args.segment - 1],
            audio_dir,
            args.segment,
            args.voice
        )
    else:
        generate_podcast_audio(project_dir, args.voice, args.model)


if __name__ == "__main__":
    main()
