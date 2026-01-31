#!/usr/bin/env python3
"""
Qwen3-TTS Local PoC - Run TTS entirely on local hardware with no API calls

Backends:
    - MLX (recommended for Apple Silicon): pip install mlx-audio
    - PyTorch/CUDA (for NVIDIA GPUs): pip install qwen-tts soundfile torch

Models (auto-downloaded on first run):
    MLX models (from mlx-community):
        - mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16 (smaller, faster)
        - mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16 (better quality)
        - mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16 (custom voice design)

    PyTorch models (from Qwen):
        - Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice
        - Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign
        - Qwen/Qwen3-TTS-12Hz-0.6B-Base

Available Voices (CustomVoice model):
    - Vivian: Female, Chinese, professional
    - Serena: Female, English, warm
    - Dylan: Male, English, energetic
    - Eric: Male, English, authoritative
    - Ryan: Male, English, casual
    - Aiden: Male, English, young
    - Uncle_Fu: Male, Chinese, mature
    - Ono_Anna: Female, Japanese
    - Sohee: Female, Korean

Usage:
    # MLX backend (Apple Silicon - recommended)
    python3 src/qwen_tts_poc.py --text "Hello world" --backend mlx
    python3 src/qwen_tts_poc.py --text "Welcome to F1!" --voice Dylan --backend mlx
    python3 src/qwen_tts_poc.py --text "Breaking news" --voice Eric --backend mlx --model 0.6b

    # PyTorch backend (NVIDIA CUDA)
    python3 src/qwen_tts_poc.py --text "Hello world" --backend pytorch

    # Voice design (custom voice from description)
    python3 src/qwen_tts_poc.py --voice-design "A confident male sports commentator" --text "And they're off!"
"""

import argparse
import sys
import time
import numpy as np


# ============================================================================
# MLX Backend (Apple Silicon optimized)
# ============================================================================

def check_mlx_dependencies():
    """Check MLX dependencies"""
    try:
        import mlx_audio
        return True
    except ImportError:
        return False


def load_model_mlx(model_size: str = "1.7b", model_type: str = "custom_voice"):
    """Load Qwen3-TTS model using MLX backend

    Args:
        model_size: "0.6b" or "1.7b"
        model_type: "custom_voice", "voice_design", or "base"

    Returns:
        Loaded MLX model
    """
    from mlx_audio.tts.utils import load_model

    # Map to MLX model IDs
    model_map = {
        ("0.6b", "base"): "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16",
        ("0.6b", "custom_voice"): "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16",
        ("1.7b", "custom_voice"): "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16",
        ("1.7b", "voice_design"): "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16",
        ("1.7b", "base"): "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16",
    }

    key = (model_size, model_type)
    if key not in model_map:
        # Fallback
        if model_size == "0.6b":
            model_id = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"
        else:
            model_id = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
    else:
        model_id = model_map[key]

    print(f"Loading MLX model: {model_id}")
    print("(First run will download from HuggingFace)")

    model = load_model(model_id)
    return model, model_id


def generate_speech_mlx(
    model,
    model_id: str,
    text: str,
    voice: str = "Dylan",
    language: str = "English",
    instruct: str = None,
) -> tuple:
    """Generate speech using MLX backend

    Returns:
        (audio_array, sample_rate)
    """
    # Determine which generation method to use based on model
    if "VoiceDesign" in model_id:
        # Voice design model
        results = list(model.generate_voice_design(
            text=text,
            language=language,
            instruct=instruct or "A natural speaking voice",
        ))
    elif "CustomVoice" in model_id:
        # Custom voice model with preset speakers
        kwargs = {
            "text": text,
            "speaker": voice,
            "language": language,
        }
        if instruct:
            kwargs["instruct"] = instruct
        results = list(model.generate_custom_voice(**kwargs))
    else:
        # Base model - simpler generation
        results = list(model.generate(
            text=text,
            language=language,
        ))

    if not results:
        raise RuntimeError("No audio generated")

    audio = results[0].audio
    # MLX models output at 24kHz
    sample_rate = 24000

    # Convert to numpy if needed
    if hasattr(audio, 'tolist'):
        audio = np.array(audio.tolist(), dtype=np.float32)

    return audio, sample_rate


# ============================================================================
# PyTorch Backend (CUDA/CPU)
# ============================================================================

def check_pytorch_dependencies():
    """Check PyTorch dependencies"""
    missing = []
    try:
        import torch
    except ImportError:
        missing.append("torch")

    try:
        import soundfile
    except ImportError:
        missing.append("soundfile")

    try:
        import qwen_tts
    except ImportError:
        missing.append("qwen-tts")

    return missing


def get_pytorch_device(force_cpu: bool = False):
    """Detect best available device for PyTorch inference"""
    import torch

    if force_cpu:
        print("Using CPU (forced)")
        return "cpu"

    if torch.cuda.is_available():
        device = "cuda:0"
        gpu_name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"Using CUDA: {gpu_name} ({vram:.1f}GB VRAM)")
    elif torch.backends.mps.is_available():
        # MPS has issues with large convolutions in the audio decoder
        print("Apple MPS detected but has conv limitations - using CPU")
        print("(Tip: Use --backend mlx for Apple Silicon acceleration)")
        device = "cpu"
    else:
        device = "cpu"
        print("Using CPU (no GPU detected)")

    return device


def load_model_pytorch(model_size: str = "1.7b", model_type: str = "custom_voice", device: str = "cuda:0"):
    """Load Qwen3-TTS model using PyTorch backend"""
    import torch
    from qwen_tts import Qwen3TTSModel

    model_map = {
        ("0.6b", "base"): "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        ("0.6b", "custom_voice"): "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
        ("1.7b", "custom_voice"): "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        ("1.7b", "voice_design"): "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        ("1.7b", "base"): "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    }

    key = (model_size, model_type)
    model_id = model_map.get(key, "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")

    print(f"Loading PyTorch model: {model_id}")
    print("(First run will download ~3GB from HuggingFace)")

    dtype = torch.bfloat16 if device != "cpu" else torch.float32

    try:
        model = Qwen3TTSModel.from_pretrained(
            model_id,
            device_map=device,
            dtype=dtype,
            attn_implementation="flash_attention_2",
        )
        print("Using FlashAttention 2")
    except Exception:
        model = Qwen3TTSModel.from_pretrained(
            model_id,
            device_map=device,
            dtype=dtype,
        )
        print("Using default attention")

    return model, model_id


def generate_speech_pytorch(
    model,
    model_id: str,
    text: str,
    voice: str = "Dylan",
    language: str = "English",
    instruct: str = None,
) -> tuple:
    """Generate speech using PyTorch backend"""
    if "VoiceDesign" in model_id:
        wavs, sr = model.generate_voice_design(
            text=text,
            language=language,
            instruct=instruct or "A natural speaking voice",
        )
    else:
        kwargs = {
            "text": text,
            "language": language,
            "speaker": voice,
        }
        if instruct:
            kwargs["instruct"] = instruct
        wavs, sr = model.generate_custom_voice(**kwargs)

    return wavs[0], sr


# ============================================================================
# Common Functions
# ============================================================================

def save_audio(audio_data, sample_rate: int, output_path: str):
    """Save audio to file"""
    import soundfile as sf

    # Ensure numpy array
    if not isinstance(audio_data, np.ndarray):
        audio_data = np.array(audio_data, dtype=np.float32)

    sf.write(output_path, audio_data, sample_rate)
    print(f"Saved: {output_path}")

    duration = len(audio_data) / sample_rate
    print(f"Duration: {duration:.2f}s")
    return duration


def detect_best_backend():
    """Auto-detect the best available backend"""
    import platform

    # Check if we're on Apple Silicon
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        if check_mlx_dependencies():
            return "mlx"

    # Check PyTorch/CUDA
    missing = check_pytorch_dependencies()
    if not missing:
        try:
            import torch
            if torch.cuda.is_available():
                return "pytorch"
        except:
            pass

    # Fallback: prefer MLX on Mac, PyTorch otherwise
    if platform.system() == "Darwin":
        if check_mlx_dependencies():
            return "mlx"

    return "pytorch"


def main():
    parser = argparse.ArgumentParser(
        description="Qwen3-TTS Local PoC - Generate speech locally with no API calls",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  MLX backend (Apple Silicon):
    python3 src/qwen_tts_poc.py --text "Hello, this is a test" --backend mlx
    python3 src/qwen_tts_poc.py --text "Breaking F1 news!" --voice Eric --backend mlx
    python3 src/qwen_tts_poc.py --text "Quick test" --backend mlx --model 0.6b

  PyTorch backend (NVIDIA CUDA):
    python3 src/qwen_tts_poc.py --text "Hello world" --backend pytorch

  With style instruction:
    python3 src/qwen_tts_poc.py --text "And they cross the line!" --voice Dylan --instruct "excited sports commentary"

  Voice design (custom voice from description):
    python3 src/qwen_tts_poc.py --voice-design "A deep, authoritative male news anchor" --text "Welcome to the show"

Available voices: Vivian, Serena, Dylan, Eric, Ryan, Aiden, Uncle_Fu, Ono_Anna, Sohee
        """,
    )

    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="Text to synthesize",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default="Dylan",
        help="Voice name for CustomVoice model (default: Dylan)",
    )
    parser.add_argument(
        "--instruct",
        type=str,
        default=None,
        help="Style instruction (e.g., 'excited', 'calm', 'professional')",
    )
    parser.add_argument(
        "--voice-design",
        type=str,
        default=None,
        dest="voice_design",
        help="Use VoiceDesign model with this voice description instead of preset voices",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="English",
        help="Language (default: English)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: output_qwen.wav in current dir)",
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["auto", "mlx", "pytorch"],
        default="auto",
        help="Backend to use: mlx (Apple Silicon), pytorch (CUDA/CPU), auto (detect)",
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=["0.6b", "1.7b"],
        default="1.7b",
        help="Model size: 0.6b (faster) or 1.7b (better quality, default)",
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force CPU usage for PyTorch backend",
    )

    args = parser.parse_args()

    # Set default output
    if args.output is None:
        args.output = "output_qwen.wav"

    print("=" * 60)
    print("Qwen3-TTS Local PoC")
    print("=" * 60)
    print(f"Text: {args.text[:80]}{'...' if len(args.text) > 80 else ''}")

    # Detect backend
    backend = args.backend
    if backend == "auto":
        backend = detect_best_backend()
        print(f"Auto-detected backend: {backend}")
    else:
        print(f"Backend: {backend}")

    # Determine model type
    model_type = "voice_design" if args.voice_design else "custom_voice"

    # Load model and generate based on backend
    start_load = time.time()

    if backend == "mlx":
        if not check_mlx_dependencies():
            print("\nMLX not installed. Install with:")
            print("  pip install mlx-audio")
            sys.exit(1)

        print(f"Using Apple Silicon GPU acceleration via MLX")
        model, model_id = load_model_mlx(args.model, model_type)
        load_time = time.time() - start_load
        print(f"Model loaded in {load_time:.1f}s")

        print("\nGenerating speech...")
        print(f"Voice: {args.voice}")
        if args.instruct:
            print(f"Style: {args.instruct}")

        start_gen = time.time()
        audio, sr = generate_speech_mlx(
            model,
            model_id,
            args.text,
            args.voice,
            args.language,
            args.voice_design or args.instruct,
        )

    else:  # pytorch
        missing = check_pytorch_dependencies()
        if missing:
            print(f"\nMissing PyTorch dependencies: {', '.join(missing)}")
            print("Install with:")
            print(f"  pip install {' '.join(missing)}")
            sys.exit(1)

        device = get_pytorch_device(force_cpu=args.cpu)
        model, model_id = load_model_pytorch(args.model, model_type, device)
        load_time = time.time() - start_load
        print(f"Model loaded in {load_time:.1f}s")

        print("\nGenerating speech...")
        print(f"Voice: {args.voice}")
        if args.instruct:
            print(f"Style: {args.instruct}")

        start_gen = time.time()
        audio, sr = generate_speech_pytorch(
            model,
            model_id,
            args.text,
            args.voice,
            args.language,
            args.voice_design or args.instruct,
        )

    gen_time = time.time() - start_gen
    print(f"Generation took {gen_time:.2f}s")

    # Save output
    duration = save_audio(audio, sr, args.output)

    # Calculate real-time factor
    rtf = gen_time / duration if duration > 0 else 0
    print(f"Real-time factor: {rtf:.2f}x (lower is better)")

    print("\n" + "=" * 60)
    print("Done! No API calls were made - all processing was local.")
    print("=" * 60)


if __name__ == "__main__":
    main()
