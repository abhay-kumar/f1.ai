#!/usr/bin/env python3
"""
Qwen3-TTS Sleep Audio Generator

Generates long-form audio for sleep videos using local Qwen3-TTS model.
Optimized for MLX on Apple Silicon for faster generation.

Features:
- CustomVoice model with preset speakers for consistent voice
- Chunked processing for 3+ hour content
- MLX backend for Apple Silicon GPU acceleration
- Progress tracking and resumable generation
- Breath reduction post-processing

Usage:
    python3 src/qwen_sleep_audio_generator.py --project f1-history-sleep
    python3 src/qwen_sleep_audio_generator.py --project f1-history-sleep --segment 1
    python3 src/qwen_sleep_audio_generator.py --project f1-history-sleep --preview
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PROJECTS_DIR


# ============================================================================
# Configuration
# ============================================================================

# CustomVoice speaker for consistent voice across chunks
# Available: Vivian, Serena, Dylan, Eric, Ryan, Aiden, Uncle_Fu, Ono_Anna, Sohee
DEFAULT_SPEAKER = "Ryan"

# Instruct parameter for calm sleep narration
DEFAULT_INSTRUCT = "Speak very slowly and gently, like a soothing bedtime story narrator. Soft, warm, and relaxing voice."

# Chunk size for processing (words) - prevents memory issues on long text
MAX_CHUNK_WORDS = 500  # ~4 minutes per chunk at slow pace

# Output settings
SAMPLE_RATE = 24000  # Qwen MLX outputs 24kHz
OUTPUT_FORMAT = "mp3"
MP3_BITRATE = "192k"

# Breath reduction settings
ENABLE_BREATH_REDUCTION = True


# ============================================================================
# MLX Backend Functions (Apple Silicon Optimized)
# ============================================================================

def check_mlx_available():
    """Check if MLX is available for Apple Silicon acceleration"""
    try:
        import mlx_audio
        return True
    except ImportError:
        return False


def load_qwen_model_mlx(model_size: str = "1.7b"):
    """Load Qwen3-TTS CustomVoice model via MLX backend for Apple Silicon

    Args:
        model_size: "0.6b" or "1.7b"

    Returns:
        (model, model_id) tuple
    """
    from mlx_audio.tts.utils import load_model

    if model_size == "0.6b":
        model_id = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"
    else:
        model_id = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"

    print(f"Loading MLX model: {model_id}")
    print("Using Apple Silicon GPU acceleration")
    print("(First run will download from HuggingFace - ~3GB)")

    start = time.time()
    model = load_model(model_id)
    load_time = time.time() - start
    print(f"Model loaded in {load_time:.1f}s")

    return model, model_id


def generate_audio_chunk_mlx(
    model,
    model_id: str,
    text: str,
    speaker: str = DEFAULT_SPEAKER,
    instruct: str = DEFAULT_INSTRUCT,
    language: str = "English"
) -> tuple:
    """Generate audio for a single chunk of text using MLX CustomVoice

    Args:
        model: Loaded MLX model
        model_id: Model identifier string
        text: Text to synthesize
        speaker: Speaker name (Ryan, Eric, Serena, etc.)
        instruct: Style instruction for delivery
        language: Language (default English)

    Returns:
        (audio_array, sample_rate) tuple
    """
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

    # Convert MLX array to numpy if needed
    if hasattr(audio, 'tolist'):
        audio = np.array(audio.tolist(), dtype=np.float32)
    elif not isinstance(audio, np.ndarray):
        audio = np.array(audio, dtype=np.float32)

    return audio, SAMPLE_RATE


# ============================================================================
# Text Processing Functions
# ============================================================================

def chunk_text(text: str, max_words: int = MAX_CHUNK_WORDS) -> list:
    """Split text into chunks at sentence boundaries

    Ensures chunks don't exceed max_words while keeping sentences intact.

    Args:
        text: Full text to split
        max_words: Maximum words per chunk

    Returns:
        List of text chunks
    """
    import re

    # Split into sentences (handles ., !, ?)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = []
    current_words = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_words = len(sentence.split())

        # If single sentence exceeds max, split it further
        if sentence_words > max_words:
            # Save current chunk first
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_words = 0

            # Split long sentence by commas or semicolons
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
            # Save current chunk and start new one
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_words = sentence_words
        else:
            current_chunk.append(sentence)
            current_words += sentence_words

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


# ============================================================================
# Audio File Functions
# ============================================================================

def save_audio_wav(audio_data, sample_rate: int, output_path: str):
    """Save audio as WAV file"""
    import soundfile as sf
    import numpy as np

    if not isinstance(audio_data, np.ndarray):
        audio_data = np.array(audio_data, dtype=np.float32)

    # Normalize if needed (prevent clipping)
    max_val = np.max(np.abs(audio_data))
    if max_val > 1.0:
        audio_data = audio_data / max_val * 0.95

    sf.write(output_path, audio_data, sample_rate)
    return output_path


def convert_wav_to_mp3(wav_path: str, mp3_path: str, bitrate: str = MP3_BITRATE, reduce_breaths: bool = True):
    """Convert WAV to MP3 using FFmpeg with optional breath reduction

    Args:
        wav_path: Input WAV file
        mp3_path: Output MP3 file
        bitrate: MP3 bitrate
        reduce_breaths: Apply breath/silence reduction filter
    """
    import subprocess

    # Build filter chain
    filters = []

    if reduce_breaths:
        # Breath reduction filter chain:
        # 1. highpass: Remove low rumble (breath sounds are often low frequency)
        # 2. afftdn: Gentle noise reduction for breath sounds
        filters.extend([
            "highpass=f=80",
            "afftdn=nf=-20",
        ])

    # Always normalize volume to -18 LUFS (podcast/audiobook standard)
    # This ensures consistent, audible volume
    filters.append("loudnorm=I=-18:TP=-1.5:LRA=11")

    # Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", wav_path,
    ]

    if filters:
        cmd.extend(["-af", ",".join(filters)])

    cmd.extend([
        "-codec:a", "libmp3lame",
        "-b:a", bitrate,
        "-ar", "44100",
        "-ac", "1",
        mp3_path
    ])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")

    # Clean up WAV file
    os.remove(wav_path)
    return mp3_path


def concatenate_audio_files(audio_files: list, output_path: str):
    """Concatenate multiple audio files using FFmpeg"""
    import subprocess
    import tempfile

    if len(audio_files) == 1:
        import shutil
        shutil.copy(audio_files[0], output_path)
        return output_path

    # Create concat list file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for audio_file in audio_files:
            escaped_path = audio_file.replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
        concat_list = f.name

    try:
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


# ============================================================================
# Main Generation Functions
# ============================================================================

def generate_segment_audio(
    model,
    model_id: str,
    segment: dict,
    output_dir: Path,
    segment_index: int,
    speaker: str = DEFAULT_SPEAKER,
    instruct: str = DEFAULT_INSTRUCT
) -> str:
    """Generate audio for a single segment (era)

    Handles chunking internally for long segments.
    Uses CustomVoice with fixed speaker for consistent voice across all chunks.

    Args:
        model: Loaded Qwen model
        model_id: Model identifier
        segment: Segment dict with text, era, title
        output_dir: Directory to save audio
        segment_index: 1-indexed segment number
        speaker: Speaker name (Ryan, Eric, Serena, etc.)
        instruct: Style instruction for delivery

    Returns:
        Path to generated MP3 file
    """
    import numpy as np

    text = segment.get("text", "")
    era = segment.get("era", f"segment_{segment_index:02d}")
    title = segment.get("title", "Untitled")

    word_count = len(text.split())

    print(f"\n{'='*60}")
    print(f"Segment {segment_index}: {era} - {title}")
    print(f"Text length: {word_count} words")
    print(f"Speaker: {speaker}")
    print(f"{'='*60}")

    # Check if output already exists (resumable)
    output_name = f"era_{segment_index:02d}_{era.lower().replace(' ', '_')}"
    mp3_path = output_dir / f"{output_name}.mp3"

    if mp3_path.exists():
        duration = get_audio_duration(str(mp3_path))
        if duration > 0:
            print(f"Already exists: {mp3_path} ({duration/60:.1f} minutes)")
            return str(mp3_path)

    # Chunk the text for processing
    chunks = chunk_text(text)
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

    # Concatenate all chunks
    print("Concatenating chunks...")
    full_audio = np.concatenate(chunk_audios)

    # Save as WAV first, then convert to MP3 with breath reduction
    wav_path = output_dir / f"{output_name}.wav"

    save_audio_wav(full_audio, SAMPLE_RATE, str(wav_path))
    convert_wav_to_mp3(str(wav_path), str(mp3_path), reduce_breaths=ENABLE_BREATH_REDUCTION)

    final_duration = len(full_audio) / SAMPLE_RATE
    overall_rtf = total_gen_time / final_duration if final_duration > 0 else 0

    print(f"\nSaved: {mp3_path}")
    print(f"Duration: {final_duration/60:.1f} minutes")
    print(f"Generation time: {total_gen_time/60:.1f} minutes")
    print(f"Overall RTF: {overall_rtf:.2f}x")

    return str(mp3_path)


def generate_all_audio(project_dir: Path, model_size: str = "1.7b"):
    """Generate audio for all segments in a project

    Args:
        project_dir: Path to project directory
        model_size: Model size ("0.6b" or "1.7b")

    Returns:
        List of generated MP3 file paths
    """
    # Check MLX availability
    if not check_mlx_available():
        print("ERROR: MLX not available.")
        print("This script requires Apple Silicon with MLX for fast generation.")
        print("\nInstall with: pip install mlx-audio")
        sys.exit(1)

    # Load script
    script_path = project_dir / "script.json"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    with open(script_path) as f:
        script = json.load(f)

    # Create output directory
    audio_dir = project_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    # Get speaker and instruct from script or use defaults
    speaker = script.get("speaker", DEFAULT_SPEAKER)
    instruct = script.get("instruct", DEFAULT_INSTRUCT)
    print(f"Speaker: {speaker}")
    print(f"Instruct: {instruct[:80]}...")

    # Load model once (reuse for all segments)
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
            model, model_id, segment, audio_dir, i, speaker, instruct
        )
        segment_files.append(mp3_path)

        # Progress estimate
        elapsed = time.time() - overall_start
        if i > 0:
            avg_per_segment = elapsed / i
            remaining = (total_segments - i) * avg_per_segment
            print(f"\nProgress: {i}/{total_segments} segments")
            print(f"Elapsed: {elapsed/60:.1f} min, Est. remaining: {remaining/60:.1f} min")

    # Concatenate all segments into final audio
    if len(segment_files) > 1:
        print(f"\n{'='*60}")
        print("Creating final concatenated audio...")
        final_path = audio_dir / "full_narration.mp3"
        concatenate_audio_files(segment_files, str(final_path))

        final_duration = get_audio_duration(str(final_path))
        total_time = time.time() - overall_start

        print(f"\nFinal audio: {final_path}")
        print(f"Total duration: {final_duration/3600:.2f} hours")
        print(f"Total generation time: {total_time/3600:.2f} hours")
        print(f"Overall RTF: {total_time/final_duration:.2f}x")
    elif len(segment_files) == 1:
        import shutil
        final_path = audio_dir / "full_narration.mp3"
        shutil.copy(segment_files[0], final_path)

    return segment_files


def preview_script(project_dir: Path):
    """Preview script structure without generating audio"""
    script_path = project_dir / "script.json"

    with open(script_path) as f:
        script = json.load(f)

    print(f"Title: {script.get('title', 'Untitled')}")
    print(f"Format: {script.get('format', 'unknown')}")
    print(f"Target duration: {script.get('duration_target', 0) / 60:.0f} minutes")
    print(f"Speaker: {script.get('speaker', DEFAULT_SPEAKER)}")
    print(f"Instruct: {script.get('instruct', DEFAULT_INSTRUCT)[:80]}...")
    print(f"\nSegments: {len(script.get('segments', []))}")

    total_words = 0
    for i, seg in enumerate(script.get("segments", []), 1):
        text = seg.get("text", "")
        words = len(text.split())
        total_words += words
        duration_mins = words / 120
        print(f"\n  {i}. {seg.get('era', 'Unknown')}: {seg.get('title', 'Untitled')}")
        print(f"     {words} words (~{duration_mins:.1f} min)")
        if text:
            preview = text[:100].replace('\n', ' ')
            print(f"     Preview: \"{preview}...\"")

    estimated_hours = total_words / 120 / 60
    print(f"\n{'='*60}")
    print(f"Total: {total_words:,} words")
    print(f"Estimated duration: ~{estimated_hours:.1f} hours (at 120 WPM)")

    # Estimate generation time (~1x RTF on Apple Silicon with CustomVoice)
    est_gen_time = estimated_hours * 1.2
    print(f"Estimated generation time: ~{est_gen_time:.1f} hours (on Apple Silicon)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate sleep audio using Qwen3-TTS CustomVoice on Apple Silicon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview script structure
    python3 src/qwen_sleep_audio_generator.py --project f1-history-sleep --preview

    # Generate single segment (for testing)
    python3 src/qwen_sleep_audio_generator.py --project f1-history-sleep --segment 1

    # Generate all audio
    python3 src/qwen_sleep_audio_generator.py --project f1-history-sleep

    # Use smaller model for faster generation
    python3 src/qwen_sleep_audio_generator.py --project f1-history-sleep --model 0.6b
        """
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Project name (folder in projects/)"
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
        preview_script(project_dir)
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
        speaker = script.get("speaker", DEFAULT_SPEAKER)
        instruct = script.get("instruct", DEFAULT_INSTRUCT)
        audio_dir = project_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        print(f"Speaker: {speaker}")
        print(f"Instruct: {instruct[:80]}...")

        generate_segment_audio(
            model, model_id,
            segments[args.segment - 1],
            audio_dir,
            args.segment,
            speaker,
            instruct
        )
    else:
        generate_all_audio(project_dir, args.model)


if __name__ == "__main__":
    main()
