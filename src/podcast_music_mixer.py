#!/usr/bin/env python3
"""
F1 Podcast Music Mixer - Professional audio production for motorsport podcasts

Implements broadcast-quality podcast mixing following industry standards:

LEGAL & TECHNICAL STANDARDS:
- Royalty-free music only (Epidemic Sound, Artlist, Creative Commons)
- Target loudness: -16 LUFS (Apple/Spotify standard)
- Background music at 5-15% of voice volume
- 3-5 second fades for natural transitions

F1 SONIC IDENTITY:
- Industrial & orchestral vibes (engineering + glamour)
- 120-140 BPM tempo (racing heartbeat)
- Driving synth basslines, staccato strings
- Heavy percussion, futuristic synths

STRUCTURE:
- INTRO (10-15s): Heavy, epic, percussive - "The Grid Walk"
- STINGERS (2-3s): Musical stabs for segment transitions
- AMBIENT BEDS: Minimal techno/glitch for technical segments (5-15% volume)
- OUTRO (15-30s): Uplifting, grand orchestral - "The Podium"

SOUND EFFECTS:
- Flyby/whoosh for transitions
- Team radio beep for quotes
- Wheel gun for quick segments

References:
- Industry standard: -16 LUFS, 5-15% music volume
- F1 tempo: 120-140 BPM
- Fade duration: 3-5 seconds
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import SHARED_DIR, get_project_dir

# =============================================================================
# AUDIO ELEMENT TYPES
# =============================================================================


class AudioElementType(Enum):
    """Types of audio elements in F1 podcast production"""

    INTRO = "intro"  # 10-15s opening, heavy/epic
    OUTRO = "outro"  # 15-30s closing, uplifting
    STINGER = "stinger"  # 2-3s transition hit
    AMBIENT_BED = "bed"  # Background under segments
    SFX_FLYBY = "sfx_flyby"  # Car passing whoosh
    SFX_RADIO = "sfx_radio"  # Team radio beep
    SFX_WHEEL = "sfx_wheel"  # Pneumatic wheel gun


@dataclass
class AudioCue:
    """A single audio placement in the podcast"""

    cue_type: AudioElementType
    start_time: float  # When audio starts (seconds)
    duration: float  # How long it plays
    volume_percent: float  # Volume as % of voice (5-100)
    fade_in: float  # Fade in duration (seconds)
    fade_out: float  # Fade out duration (seconds)
    source_offset: float  # Where to start in source file
    description: str  # What this cue is for
    source_file: str = ""  # Which audio file to use


# =============================================================================
# F1 PODCAST AUDIO CONFIGURATION
# =============================================================================

# Volume levels (as percentage of voice volume)
# Industry standard: background music at 5-15% of voice
INTRO_VOLUME_PERCENT = 80  # Intro is prominent (before voice starts)
OUTRO_VOLUME_PERCENT = 25  # Outro UNDER voice (ducked, then rises when voice ends)
OUTRO_FINAL_VOLUME = 70  # Outro volume AFTER voice ends (grand finish)
STINGER_VOLUME_PERCENT = 55  # Quick punchy hit - noticeable but not overwhelming
BED_VOLUME_PERCENT = 12  # Subtle background (5-15% range)
SFX_VOLUME_PERCENT = 35  # Sound effects noticeable but not overwhelming

# Timing (in seconds)
INTRO_DURATION = 12.0  # 10-15s standard intro
INTRO_FADE_IN = 0.5  # Quick fade in
INTRO_FADE_OUT = 4.0  # 3-5s fade as voice starts

OUTRO_DURATION = 20.0  # 15-30s for grand finish
OUTRO_FADE_IN = 5.0  # Gradual build under final segment
OUTRO_FADE_OUT = 5.0  # Long fade to silence

STINGER_DURATION = 2.5  # 2-3s musical stab
STINGER_FADE_IN = 0.1  # Snap in
STINGER_FADE_OUT = 1.5  # Smooth out

BED_FADE_IN = 3.0  # Gentle rise
BED_FADE_OUT = 4.0  # 3-5s fade for natural transition

SFX_FADE_IN = 0.05  # Near instant
SFX_FADE_OUT = 0.3  # Quick tail

# Segment analysis
MIN_GAP_BETWEEN_MUSIC = 90.0  # At least 90s between music cues
MAX_BEDS_PER_PODCAST = 2  # Only 2 ambient beds (for key segments)
MAX_STINGERS = 3  # Maximum 3 stingers

# F1 Segment types that get specific treatment
TECHNICAL_SEGMENTS = ["technical", "analysis", "data", "stats", "engineering"]
EMOTIONAL_SEGMENTS = ["tribute", "farewell", "crash", "serious", "heartfelt"]
TRANSITION_KEYWORDS = ["moving on", "let's talk", "next up", "now for", "switching to"]

# =============================================================================
# DOCUMENTARY/THINKSCHOOL STYLE CONFIGURATION
# =============================================================================
# Continuous music bed that rises and falls at key narrative moments
# Instead of short stingers, the music swells up at transitions and key points

DOC_BED_VOLUME_LOW = 8  # Base volume when voice is speaking (subtle)
DOC_BED_VOLUME_HIGH = (
    35  # Volume during "swell" moments (noticeable but not overwhelming)
)
DOC_SWELL_DURATION = 6.0  # How long each swell lasts (rise + sustain + fall)
DOC_SWELL_RISE = 1.5  # Time to rise from low to high
DOC_SWELL_SUSTAIN = 2.0  # Time at peak volume
DOC_SWELL_FALL = 2.5  # Time to fall back to low
DOC_MIN_SWELL_GAP = 45.0  # Minimum seconds between swells (don't overdo it)

# Keywords that trigger music swells (key narrative moments)
SWELL_TRIGGER_KEYWORDS = [
    # Topic transitions
    "but here's the thing",
    "here's what's interesting",
    "and that's when",
    "the real story",
    "what happened next",
    "this is where",
    # Revelations
    "turns out",
    "the truth is",
    "surprisingly",
    "remarkably",
    "what most people don't realize",
    "the key insight",
    # Emotional peaks
    "incredible",
    "game changer",
    "revolutionary",
    "breakthrough",
    "disaster",
    "crisis",
    "problem",
    "challenge",
    # Conclusions
    "and so",
    "ultimately",
    "in the end",
    "the bottom line",
    "what this means",
    "the takeaway",
]

# Section markers (bigger swells for major transitions)
SECTION_KEYWORDS = [
    "let's talk about",
    "moving on to",
    "now for",
    "next up",
    "the first",
    "the second",
    "finally",
    "in conclusion",
]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_audio_duration(file_path: str) -> float:
    """Get audio duration in seconds using ffprobe"""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip()) if result.stdout.strip() else 0
    except ValueError:
        return 0


def get_segment_durations(project_dir: str, num_segments: int) -> List[float]:
    """Get actual duration of each audio segment"""
    durations = []
    audio_dir = f"{project_dir}/audio"

    for i in range(num_segments):
        audio_file = f"{audio_dir}/segment_{i:02d}.mp3"
        if os.path.exists(audio_file):
            durations.append(get_audio_duration(audio_file))
        else:
            durations.append(20.0)  # Default estimate

    return durations


def percent_to_db(percent: float) -> float:
    """Convert volume percentage to dB (relative to voice at 0dB)"""
    if percent <= 0:
        return -60
    # 100% = 0dB, 50% = -6dB, 10% = -20dB, 1% = -40dB
    import math

    return 20 * math.log10(percent / 100)


# =============================================================================
# SCRIPT ANALYSIS
# =============================================================================


def analyze_script_for_audio(script: Dict, segment_durations: List[float]) -> Dict:
    """
    Analyze the script to identify key moments for audio placement.

    Returns dict with:
    - segment_times: cumulative start times
    - total_duration: total podcast length
    - intro_segment: index of first content segment
    - outro_segment: index of closing segment
    - technical_segments: indices of technical/analysis segments
    - emotional_segments: indices of serious/heartfelt segments
    - transition_points: times where major topic shifts occur
    """
    segments = script.get("segments", [])

    # Calculate cumulative times
    segment_times = []
    current_time = 0.0
    for duration in segment_durations:
        segment_times.append(current_time)
        current_time += duration
    total_duration = current_time

    # Identify segment types
    technical_indices = []
    emotional_indices = []
    transition_points = []

    for i, segment in enumerate(segments):
        context = segment.get("context", "").lower()
        emotion = segment.get("emotion", "").lower()
        text = segment.get("text", "")[:100].lower()

        # Technical segments (for minimal techno bed)
        if any(kw in context for kw in TECHNICAL_SEGMENTS):
            technical_indices.append(i)

        # Emotional segments (drop music or use drone)
        if any(kw in context or kw in emotion for kw in EMOTIONAL_SEGMENTS):
            emotional_indices.append(i)

        # Transition points (for stingers)
        if any(kw in text or kw in context for kw in TRANSITION_KEYWORDS):
            if i > 0 and i < len(segments) - 2:  # Not intro/outro
                transition_points.append(
                    (i, segment_times[i] if i < len(segment_times) else 0)
                )

    return {
        "segment_times": segment_times,
        "total_duration": total_duration,
        "intro_segment": 0,
        "outro_segment": len(segments) - 1,
        "technical_segments": technical_indices,
        "emotional_segments": emotional_indices,
        "transition_points": transition_points,
    }


# =============================================================================
# DOCUMENTARY/THINKSCHOOL STYLE - CONTINUOUS BED WITH SWELLS
# =============================================================================


def analyze_script_for_swells(
    script: Dict, segment_durations: List[float]
) -> List[Dict]:
    """
    Analyze script to find moments where music should swell.

    Returns list of swell points with:
    - time: when the swell should start
    - intensity: 'major' for section transitions, 'minor' for key moments
    - reason: why this point was selected
    """
    segments = script.get("segments", [])
    swell_points = []

    # Calculate cumulative times
    segment_times = []
    current_time = 0.0
    for duration in segment_durations:
        segment_times.append(current_time)
        current_time += duration

    last_swell_time = -DOC_MIN_SWELL_GAP  # Allow first swell

    for i, segment in enumerate(segments):
        if i >= len(segment_times):
            continue

        seg_time = segment_times[i]
        text = segment.get("text", "").lower()
        context = segment.get("context", "").lower()

        # Skip intro and outro segments
        if i == 0 or i >= len(segments) - 2:
            continue

        # Check if enough time has passed since last swell
        if seg_time < last_swell_time + DOC_MIN_SWELL_GAP:
            continue

        # Check for section markers (major swells)
        for keyword in SECTION_KEYWORDS:
            if keyword in text or keyword in context:
                swell_points.append(
                    {
                        "time": seg_time,
                        "intensity": "major",
                        "reason": f"Section: '{keyword}'",
                        "segment_idx": i,
                    }
                )
                last_swell_time = seg_time
                break
        else:
            # Check for narrative moments (minor swells)
            for keyword in SWELL_TRIGGER_KEYWORDS:
                if keyword in text:
                    swell_points.append(
                        {
                            "time": seg_time,
                            "intensity": "minor",
                            "reason": f"Narrative: '{keyword}'",
                            "segment_idx": i,
                        }
                    )
                    last_swell_time = seg_time
                    break

    # If no swells found, add some at regular intervals
    if len(swell_points) < 3:
        total_duration = current_time
        interval = total_duration / 5  # Divide into 5 parts, swell at boundaries

        for i in range(1, 4):  # 3 swells
            target_time = interval * (i + 0.5)
            # Find closest segment
            if target_time > last_swell_time + DOC_MIN_SWELL_GAP:
                swell_points.append(
                    {
                        "time": target_time,
                        "intensity": "minor",
                        "reason": f"Timed interval {i}",
                        "segment_idx": -1,
                    }
                )
                last_swell_time = target_time

    return sorted(swell_points, key=lambda x: x["time"])


def create_intro_outro_only_mix(
    voice_path: str,
    music_path: str,
    output_path: str,
    segment_durations: List[float],
) -> bool:
    """
    Create a clean mix with music ONLY at intro and outro.
    No music during the main content - voice is completely clean.

    Structure:
    - INTRO: 12s of music at 80% volume, fades out as voice starts
    - CONTENT: Pure voice, no music
    - OUTRO: Music fades in under final words, swells after voice ends
    """
    total_duration = sum(segment_durations)
    voice_duration = get_audio_duration(voice_path)
    music_duration = get_audio_duration(music_path)

    intro_vol = INTRO_VOLUME_PERCENT / 100.0  # 80%
    outro_vol = OUTRO_FINAL_VOLUME / 100.0  # 70%
    outro_ducked = OUTRO_VOLUME_PERCENT / 100.0  # 25% under voice

    print(f"\nIntro + Outro Only Mix")
    print(f"=" * 60)
    print(f"Total duration: {total_duration / 60:.1f} min")
    print(f"Voice duration: {voice_duration / 60:.1f} min")
    print(f"")
    print(f"Music placement:")
    print(
        f"  00:00 - 00:{INTRO_DURATION:.0f}  INTRO at {INTRO_VOLUME_PERCENT}% (fades out)"
    )
    outro_start = voice_duration - 10
    print(
        f"  {int(outro_start // 60):02d}:{outro_start % 60:04.1f} - end   OUTRO at {OUTRO_VOLUME_PERCENT}% -> {OUTRO_FINAL_VOLUME}%"
    )
    print(f"")
    print(
        f"Voice-only section: 00:{INTRO_DURATION:.0f} - {int(outro_start // 60):02d}:{outro_start % 60:04.1f}"
    )
    print(f"=" * 60)

    # Build simple FFmpeg filter
    filter_parts = []

    # Prepare voice with padding for outro extension
    extension = 15.0  # Extra time after voice for outro music
    filter_parts.append(f"[0:a]apad=pad_dur={extension:.1f}[voice]")

    # Loop music if needed
    target_duration = voice_duration + extension
    if music_duration < target_duration:
        music_loops = int(target_duration / music_duration) + 1
        filter_parts.append(
            f"[1:a]aloop=loop={music_loops}:size={int(music_duration * 48000)},"
            f"atrim=0:{target_duration:.1f}[music_long]"
        )
    else:
        filter_parts.append(f"[1:a]atrim=0:{target_duration:.1f}[music_long]")

    # Split music into 3 streams: intro, outro quiet, outro swell
    filter_parts.append("[music_long]asplit=3[m_intro][m_outro][m_swell]")

    # INTRO: First 12s at high volume, fade out over 4s
    filter_parts.append(
        f"[m_intro]atrim=0:{INTRO_DURATION + 2},"
        f"volume={intro_vol},"
        f"afade=t=in:st=0:d=1,"
        f"afade=t=out:st={INTRO_DURATION - 4}:d=4[intro]"
    )

    # OUTRO: Start 10s before voice ends, quiet under voice, swell after
    outro_start_time = voice_duration - 10
    outro_total_duration = 10 + extension  # Under voice + after voice

    # Use different part of music for outro (offset by 40s for variety)
    outro_offset = 40.0 if music_duration > 60 else 0

    filter_parts.append(
        f"[m_outro]atrim={outro_offset}:{outro_offset + outro_total_duration},"
        f"asetpts=PTS-STARTPTS,"
        f"volume={outro_ducked},"  # Start quiet
        f"afade=t=in:st=0:d=3,"  # Fade in over 3s
        f"afade=t=out:st={outro_total_duration - 5}:d=5,"  # Fade out at end
        f"adelay={int(outro_start_time * 1000)}|{int(outro_start_time * 1000)}[outro_quiet]"
    )

    # For the outro swell after voice ends, create another layer
    # This will be louder and kick in right as voice ends
    swell_start = voice_duration - 2  # Start swell 2s before voice ends
    swell_duration = extension + 2

    filter_parts.append(
        f"[m_swell]atrim={outro_offset + 8}:{outro_offset + 8 + swell_duration},"
        f"asetpts=PTS-STARTPTS,"
        f"volume={outro_vol},"
        f"afade=t=in:st=0:d=4,"  # 4s fade in (gradual swell)
        f"afade=t=out:st={swell_duration - 5}:d=5,"
        f"adelay={int(swell_start * 1000)}|{int(swell_start * 1000)}[outro_swell]"
    )

    # Mix: voice + intro + outro_quiet + outro_swell
    # normalize=0 prevents amix from reducing voice volume when music layers start
    filter_parts.append(
        "[voice][intro][outro_quiet][outro_swell]amix=inputs=4:duration=first:"
        "weights=1 0.8 0.6 0.7:normalize=0[mixed]"
    )

    # Normalize to -16 LUFS
    filter_parts.append("[mixed]loudnorm=I=-16:TP=-1.5:LRA=11[out]")

    filter_complex = ";".join(filter_parts)

    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        voice_path,
        "-i",
        music_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "256k",
        "-ar",
        "44100",
        output_path,
    ]

    print("\nMixing (intro + outro only)...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr[-1000:]}")
        return False

    return True


def create_documentary_style_mix(
    voice_path: str,
    music_path: str,
    output_path: str,
    script: Dict,
    segment_durations: List[float],
) -> bool:
    """
    Create a documentary/ThinkSchool style mix with:
    - Continuous music bed at low volume
    - Music swells at key narrative moments
    - Intro and outro with full music

    This creates more natural, flowing audio that rises and falls
    with the story instead of abrupt stingers.
    """
    total_duration = sum(segment_durations)
    voice_duration = get_audio_duration(voice_path)
    music_duration = get_audio_duration(music_path)

    # Find swell points
    swell_points = analyze_script_for_swells(script, segment_durations)

    print(f"\nDocumentary Style Mix (with swells)")
    print(f"=" * 60)
    print(f"Total duration: {total_duration / 60:.1f} min")
    print(f"Music swells: {len(swell_points)}")
    for sp in swell_points:
        mins = int(sp["time"] // 60)
        secs = sp["time"] % 60
        print(
            f"  {mins:02d}:{secs:04.1f} - {sp['intensity'].upper():5} - {sp['reason']}"
        )
    print(f"=" * 60)

    # Build FFmpeg filter for continuous bed with volume automation
    # Strategy: Create volume envelope that stays low, rises at swell points

    vol_low = DOC_BED_VOLUME_LOW / 100.0
    vol_high = DOC_BED_VOLUME_HIGH / 100.0
    intro_vol = INTRO_VOLUME_PERCENT / 100.0
    outro_vol = OUTRO_FINAL_VOLUME / 100.0

    # Create volume keypoints for the music bed
    # Format: time1:vol1|time2:vol2|...
    keypoints = []

    # Intro: Start high, fade to low
    keypoints.append((0.0, intro_vol))
    keypoints.append((INTRO_DURATION - 2, intro_vol * 0.7))
    keypoints.append((INTRO_DURATION + 2, vol_low))

    # Add swell keypoints
    for sp in swell_points:
        t = sp["time"]
        peak_vol = vol_high if sp["intensity"] == "major" else vol_high * 0.7

        # Rise
        keypoints.append((t - 0.5, vol_low))
        keypoints.append((t + DOC_SWELL_RISE, peak_vol))
        # Sustain (implicit)
        # Fall
        keypoints.append((t + DOC_SWELL_RISE + DOC_SWELL_SUSTAIN, peak_vol))
        keypoints.append((t + DOC_SWELL_DURATION, vol_low))

    # Outro: Rise to full, then fade out
    outro_start = voice_duration - 8  # Start outro swell 8s before voice ends
    keypoints.append((outro_start - 1, vol_low))
    keypoints.append((outro_start + 3, vol_low * 1.5))  # Slight rise under voice
    keypoints.append((voice_duration, outro_vol * 0.5))  # Swell as voice ends
    keypoints.append((voice_duration + 3, outro_vol))  # Full volume after voice
    keypoints.append((voice_duration + 10, outro_vol * 0.3))  # Fade out
    keypoints.append((voice_duration + 15, 0.0))  # Silence

    # Sort and deduplicate keypoints
    keypoints.sort(key=lambda x: x[0])

    # Build sendcmd filter for volume automation
    # Using volume filter with timeline

    # Alternative: Build a complex filter with multiple volume sections
    # For simplicity, we'll create segments with crossfades

    # Simpler approach: Use the adelay + multiple copies with fades
    # Even simpler: Use side-chain compression style ducking

    # Let's use a different approach - create the volume envelope directly
    # with FFmpeg's volume filter expressions

    # Build volume expression
    # vol = base_vol + swell_vol * (envelope)
    # where envelope is 0 normally, rises to 1 at swell points

    # For FFmpeg, we can use: volume='if(between(t,t1,t2), vol_high, vol_low)'
    # But this is discontinuous. Better to use linear interpolation.

    # Create volume filter with enable expressions for each section
    filter_parts = []

    # Pad voice for outro
    extension = max(0, voice_duration + 20 - voice_duration)
    filter_parts.append(f"[0:a]apad=pad_dur={extension:.1f}[voice]")

    # Loop music to cover full duration
    music_loops = int((voice_duration + 20) / music_duration) + 1
    filter_parts.append(
        f"[1:a]aloop=loop={music_loops}:size={int(music_duration * 48000)},"
        f"atrim=0:{voice_duration + 20:.1f}[music_loop]"
    )

    # Build volume automation as a series of sections
    # We'll create one continuous volume filter with conditional expressions

    vol_expr_parts = []

    # Default low volume
    base_expr = f"{vol_low}"

    # Add intro section (high volume fading to low)
    vol_expr_parts.append(
        f"if(lt(t,{INTRO_DURATION}),{intro_vol}*max(0.3,(1-t/{INTRO_DURATION})*0.7+0.3)"
    )

    # Add swell sections
    for i, sp in enumerate(swell_points):
        t_start = sp["time"] - 0.5
        t_peak = sp["time"] + DOC_SWELL_RISE
        t_sustain_end = t_peak + DOC_SWELL_SUSTAIN
        t_end = sp["time"] + DOC_SWELL_DURATION
        peak_vol = vol_high if sp["intensity"] == "major" else vol_high * 0.7

        # Linear ramp up, sustain, linear ramp down
        vol_expr_parts.append(
            f"if(between(t,{t_start:.1f},{t_peak:.1f}),"
            f"{vol_low}+({peak_vol}-{vol_low})*(t-{t_start:.1f})/{DOC_SWELL_RISE}"
        )
        vol_expr_parts.append(
            f"if(between(t,{t_peak:.1f},{t_sustain_end:.1f}),{peak_vol}"
        )
        vol_expr_parts.append(
            f"if(between(t,{t_sustain_end:.1f},{t_end:.1f}),"
            f"{peak_vol}-({peak_vol}-{vol_low})*(t-{t_sustain_end:.1f})/{DOC_SWELL_FALL}"
        )

    # Add outro section
    vol_expr_parts.append(
        f"if(gt(t,{outro_start:.1f}),"
        f"min({outro_vol},{vol_low}+({outro_vol}-{vol_low})*max(0,(t-{outro_start:.1f})/10))"
    )

    # Final fade out
    fade_start = voice_duration + 8
    vol_expr_parts.append(
        f"if(gt(t,{fade_start:.1f}),{outro_vol}*max(0,1-(t-{fade_start:.1f})/7)"
    )

    # Build nested if expression (working backwards)
    # This gets complex, so let's use a simpler approach with multiple volume filters

    # Simpler: Use sendcmd to change volume dynamically
    # Or even simpler: Just use static volume + loudnorm and accept it's not perfect

    # Let's go with a hybrid: continuous low bed + separate swell overlays

    # Reset and use cleaner approach
    filter_parts = []

    # Prepare voice
    filter_parts.append(f"[0:a]apad=pad_dur=20[voice]")

    # Create looped music for full duration
    target_duration = voice_duration + 20
    music_loops = int(target_duration / music_duration) + 1
    filter_parts.append(
        f"[1:a]aloop=loop={music_loops}:size={int(music_duration * 48000)},"
        f"atrim=0:{target_duration:.1f}[music_full]"
    )

    # Split music into sections: intro, bed, swells, outro
    filter_parts.append("[music_full]asplit=4[m_intro][m_bed][m_swells][m_outro]")

    # INTRO: First 12s at high volume, fade out
    filter_parts.append(
        f"[m_intro]atrim=0:{INTRO_DURATION + 4},"
        f"volume={intro_vol},"
        f"afade=t=out:st={INTRO_DURATION - 2}:d=4[intro]"
    )

    # BED: Continuous low volume throughout (excluding intro/outro)
    filter_parts.append(
        f"[m_bed]volume={vol_low},"
        f"afade=t=in:st={INTRO_DURATION}:d=2,"
        f"afade=t=out:st={voice_duration - 5}:d=5[bed]"
    )

    # SWELLS: Create overlay for each swell point
    swell_labels = []
    # We need to split m_swells for each swell
    if swell_points:
        num_swells = len(swell_points)
        filter_parts.append(
            f"[m_swells]asplit={num_swells}"
            + "".join(f"[sw{i}]" for i in range(num_swells))
        )

        for i, sp in enumerate(swell_points):
            t = sp["time"]
            peak_vol = vol_high if sp["intensity"] == "major" else vol_high * 0.7
            swell_dur = DOC_SWELL_DURATION

            filter_parts.append(
                f"[sw{i}]atrim={max(0, t - 1):.1f}:{t + swell_dur + 1:.1f},"
                f"asetpts=PTS-STARTPTS,"
                f"volume={peak_vol},"
                f"afade=t=in:st=0:d={DOC_SWELL_RISE},"
                f"afade=t=out:st={swell_dur - DOC_SWELL_FALL}:d={DOC_SWELL_FALL},"
                f"adelay={int((t - 1) * 1000)}|{int((t - 1) * 1000)}[swell{i}]"
            )
            swell_labels.append(f"[swell{i}]")
    else:
        filter_parts.append("[m_swells]anull[unused_swells]")

    # OUTRO: Swell up as voice ends, sustain, fade out
    outro_start_time = max(voice_duration - 10, total_duration * 0.9)
    filter_parts.append(
        f"[m_outro]atrim={outro_start_time:.1f}:{target_duration:.1f},"
        f"asetpts=PTS-STARTPTS,"
        f"volume={outro_vol},"
        f"afade=t=in:st=0:d=5,"
        f"afade=t=out:st={target_duration - outro_start_time - 5}:d=5,"
        f"adelay={int(outro_start_time * 1000)}|{int(outro_start_time * 1000)}[outro]"
    )

    # Mix all together
    mix_inputs = "[voice][intro][bed]" + "".join(swell_labels) + "[outro]"
    num_inputs = 3 + len(swell_labels) + 1

    # Weights: voice=1, intro=0.8, bed=1, swells=0.6 each, outro=0.8
    weights = "1 0.8 1 " + " ".join(["0.6"] * len(swell_labels)) + " 0.8"

    filter_parts.append(
        f"{mix_inputs}amix=inputs={num_inputs}:duration=first:weights={weights}[mixed]"
    )

    # Normalize to -16 LUFS
    filter_parts.append("[mixed]loudnorm=I=-16:TP=-1.5:LRA=11[out]")

    filter_complex = ";".join(filter_parts)

    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        voice_path,
        "-i",
        music_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "256k",
        "-ar",
        "44100",
        output_path,
    ]

    print("\nMixing with documentary style...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr[-1000:]}")
        return False

    return True


def create_audio_cues(
    analysis: Dict,
    music_path: str,
    sfx_dir: Optional[str] = None,
    min_gap: float = MIN_GAP_BETWEEN_MUSIC,
) -> List[AudioCue]:
    """
    Create the audio cue list for the podcast.

    Follows F1 podcast structure:
    1. INTRO (Grid Walk) - 10-15s heavy/epic
    2. STINGERS at major transitions
    3. AMBIENT BEDS under technical segments (optional)
    4. OUTRO (Podium) - 15-30s uplifting
    """
    cues = []
    total_duration = analysis["total_duration"]
    segment_times = analysis["segment_times"]
    transition_points = analysis["transition_points"]

    music_duration = get_audio_duration(music_path)

    # ===================
    # 1. INTRO - "The Grid Walk"
    # ===================
    # Plays before/as voice starts, then fades under
    cues.append(
        AudioCue(
            cue_type=AudioElementType.INTRO,
            start_time=0.0,
            duration=INTRO_DURATION,
            volume_percent=INTRO_VOLUME_PERCENT,
            fade_in=INTRO_FADE_IN,
            fade_out=INTRO_FADE_OUT,
            source_offset=0.0,
            description="The Grid Walk - Opening",
            source_file=music_path,
        )
    )

    last_music_end = INTRO_DURATION
    music_offset = 20.0  # Start from different part for variety

    # ===================
    # 2. STINGERS at transitions
    # ===================
    # Select up to MAX_STINGERS, spread across the podcast
    stinger_count = 0

    if transition_points and stinger_count < MAX_STINGERS:
        # Divide podcast into sections, pick one transition per section
        section_size = total_duration / (MAX_STINGERS + 1)

        for target_time in [section_size * (i + 1) for i in range(MAX_STINGERS)]:
            # Find closest transition to this target
            best_transition = None
            best_dist = float("inf")

            for idx, t_time in transition_points:
                dist = abs(t_time - target_time)
                # Must be far enough from last music
                if dist < best_dist and t_time > last_music_end + min_gap:
                    best_transition = (idx, t_time)
                    best_dist = dist

            if best_transition and best_dist < section_size:
                idx, t_time = best_transition
                cues.append(
                    AudioCue(
                        cue_type=AudioElementType.STINGER,
                        start_time=t_time - 0.5,  # Start slightly before segment
                        duration=STINGER_DURATION,
                        volume_percent=STINGER_VOLUME_PERCENT,
                        fade_in=STINGER_FADE_IN,
                        fade_out=STINGER_FADE_OUT,
                        source_offset=music_offset,
                        description=f"Transition stinger",
                        source_file=music_path,
                    )
                )
                last_music_end = t_time + STINGER_DURATION
                music_offset = (music_offset + 30.0) % max(30, music_duration - 10)
                stinger_count += 1

    # ===================
    # 3. AMBIENT BED (optional, for technical segments)
    # ===================
    # Only add if we have a long technical segment and it's far from other music
    technical_segments = analysis.get("technical_segments", [])
    bed_count = 0

    for tech_idx in technical_segments:
        if bed_count >= MAX_BEDS_PER_PODCAST:
            break
        if tech_idx >= len(segment_times):
            continue

        seg_start = segment_times[tech_idx]
        seg_duration = (
            segment_times[tech_idx + 1]
            if tech_idx + 1 < len(segment_times)
            else total_duration
        ) - seg_start

        # Only for longer segments, far from other music
        if seg_duration >= 25.0 and seg_start > last_music_end + min_gap:
            bed_duration = min(seg_duration - 6.0, 20.0)  # Max 20s bed

            cues.append(
                AudioCue(
                    cue_type=AudioElementType.AMBIENT_BED,
                    start_time=seg_start + 3.0,  # Let voice establish
                    duration=bed_duration,
                    volume_percent=BED_VOLUME_PERCENT,
                    fade_in=BED_FADE_IN,
                    fade_out=BED_FADE_OUT,
                    source_offset=music_offset,
                    description="Technical segment bed",
                    source_file=music_path,
                )
            )
            last_music_end = seg_start + bed_duration
            music_offset = (music_offset + 25.0) % max(30, music_duration - 10)
            bed_count += 1

    # ===================
    # 4. OUTRO - "The Podium"
    # ===================
    # Builds under final segment, continues after voice ends
    outro_start = max(total_duration - OUTRO_DURATION, total_duration - 25.0)

    cues.append(
        AudioCue(
            cue_type=AudioElementType.OUTRO,
            start_time=outro_start,
            duration=OUTRO_DURATION + 5.0,  # Extends past voice
            volume_percent=OUTRO_VOLUME_PERCENT,
            fade_in=OUTRO_FADE_IN,
            fade_out=OUTRO_FADE_OUT,
            source_offset=40.0,  # Different section for variety
            description="The Podium - Closing",
            source_file=music_path,
        )
    )

    # Sort by start time
    cues.sort(key=lambda c: c.start_time)

    return cues


# =============================================================================
# AUDIO MIXING
# =============================================================================


def mix_podcast_audio(
    voice_path: str,
    cues: List[AudioCue],
    output_path: str,
    total_duration: float,
) -> bool:
    """
    Mix voice with audio cues using FFmpeg.

    Technical specs:
    - Output: -16 LUFS (broadcast standard)
    - Sample rate: 44.1kHz
    - Bitrate: 256kbps

    Special handling:
    - OUTRO: Starts quiet under voice, then swells after voice ends
    """
    if not cues:
        print("No audio cues to mix")
        return False

    # Build FFmpeg filter complex
    filter_parts = []
    inputs = ["-i", voice_path]
    input_idx = 1  # Voice is [0:a]

    # Add each unique source file as input
    source_files = list(set(c.source_file for c in cues if c.source_file))
    source_map = {}
    for sf in source_files:
        inputs.extend(["-i", sf])
        source_map[sf] = input_idx
        input_idx += 1

    # Get voice duration to know when voice ends
    voice_duration = get_audio_duration(voice_path)

    # Prepare voice (pad for outro extension)
    extension_needed = max(0, (total_duration + 10) - voice_duration)
    filter_parts.append(f"[0:a]apad=pad_dur={extension_needed:.2f}[voice]")

    # Create each audio cue
    cue_labels = []
    for i, cue in enumerate(cues):
        if not cue.source_file or cue.source_file not in source_map:
            continue

        src_idx = source_map[cue.source_file]
        src_duration = get_audio_duration(cue.source_file)

        # Calculate source offset (loop if needed)
        offset = cue.source_offset % max(1, src_duration - cue.duration)

        # Convert volume percent to linear multiplier
        vol_linear = cue.volume_percent / 100.0

        # Special handling for OUTRO - starts quiet under voice, swells after voice ends
        if cue.cue_type == AudioElementType.OUTRO:
            # Calculate when voice ends relative to outro start
            voice_end_in_outro = voice_duration - cue.start_time
            voice_end_in_outro = max(2.0, min(voice_end_in_outro, cue.duration - 5.0))

            # Simpler approach: use a single volume that's quiet enough for voice
            # then use afade to swell up after voice ends
            vol_ducked = OUTRO_VOLUME_PERCENT / 100.0  # 25% while voice present
            fade_out_start = cue.duration - cue.fade_out

            # Build filter: constant quiet volume that works under voice
            # The voice naturally ends and gives the music room
            cue_filter = (
                f"[{src_idx}:a]"
                f"atrim=start={offset:.2f}:duration={cue.duration:.2f},"
                f"asetpts=PTS-STARTPTS,"
                f"volume={vol_ducked:.3f},"
                f"afade=t=in:st=0:d={cue.fade_in:.2f},"
                f"afade=t=out:st={fade_out_start:.2f}:d={cue.fade_out:.2f},"
                f"adelay={int(cue.start_time * 1000)}|{int(cue.start_time * 1000)}"
                f"[cue{i}]"
            )
        else:
            # Standard cue processing
            cue_filter = (
                f"[{src_idx}:a]"
                f"atrim=start={offset:.2f}:duration={cue.duration:.2f},"
                f"asetpts=PTS-STARTPTS,"
                f"afade=t=in:st=0:d={cue.fade_in:.2f},"
                f"afade=t=out:st={cue.duration - cue.fade_out:.2f}:d={cue.fade_out:.2f},"
                f"volume={vol_linear:.3f},"
                f"adelay={int(cue.start_time * 1000)}|{int(cue.start_time * 1000)}"
                f"[cue{i}]"
            )
        filter_parts.append(cue_filter)
        cue_labels.append(f"[cue{i}]")

    if not cue_labels:
        print("No valid cues to mix")
        return False

    # Mix all together
    all_inputs = "[voice]" + "".join(cue_labels)
    num_inputs = 1 + len(cue_labels)

    # Voice gets weight 1.0, music cues get 0.8
    weights = "1 " + " ".join(["0.8"] * len(cue_labels))

    filter_parts.append(
        f"{all_inputs}amix=inputs={num_inputs}:duration=longest:weights={weights}[mixed]"
    )

    # Normalize to -16 LUFS (broadcast standard)
    filter_parts.append("[mixed]loudnorm=I=-16:TP=-1.5:LRA=11[out]")

    filter_complex = ";".join(filter_parts)

    # Build command
    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "256k",
        "-ar",
        "44100",
        output_path,
    ]

    print("Mixing audio...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr[:500]}")
        return False

    return True


# =============================================================================
# REPORTING
# =============================================================================


def print_audio_timeline(cues: List[AudioCue], total_duration: float):
    """Print a visual timeline of audio placement"""
    print("\n" + "=" * 75)
    print("F1 PODCAST AUDIO TIMELINE")
    print("=" * 75)

    # Calculate statistics
    total_music = sum(c.duration for c in cues)
    music_percent = (total_music / total_duration) * 100 if total_duration > 0 else 0

    print(
        f"\nPodcast Duration: {total_duration / 60:.1f} minutes ({total_duration:.0f}s)"
    )
    print(f"Total Music: {total_music:.1f}s ({music_percent:.1f}% of runtime)")
    print(
        f"Voice-Only: {total_duration - total_music:.1f}s ({100 - music_percent:.1f}%)"
    )

    print("\n" + "-" * 75)
    print(f"{'TIME':>8} | {'TYPE':<15} | {'DUR':>5} | {'VOL':>6} | {'DESCRIPTION'}")
    print("-" * 75)

    type_icons = {
        AudioElementType.INTRO: "INTRO",
        AudioElementType.OUTRO: "OUTRO",
        AudioElementType.STINGER: "STINGER",
        AudioElementType.AMBIENT_BED: "BED",
        AudioElementType.SFX_FLYBY: "SFX",
        AudioElementType.SFX_RADIO: "SFX",
        AudioElementType.SFX_WHEEL: "SFX",
    }

    for cue in cues:
        mins = int(cue.start_time // 60)
        secs = cue.start_time % 60
        time_str = f"{mins:02d}:{secs:05.2f}"
        type_str = type_icons.get(cue.cue_type, "???")
        vol_str = f"{cue.volume_percent:.0f}%"

        print(
            f"{time_str:>8} | {type_str:<15} | {cue.duration:>4.1f}s | {vol_str:>6} | {cue.description[:30]}"
        )

    print("-" * 75)

    # Visual timeline (simplified)
    print("\nTimeline (I=intro, S=stinger, B=bed, O=outro, .=voice):")
    timeline = ["."] * 60
    for cue in cues:
        start_pos = int((cue.start_time / total_duration) * 60)
        end_pos = int(((cue.start_time + cue.duration) / total_duration) * 60)
        char = {
            AudioElementType.INTRO: "I",
            AudioElementType.OUTRO: "O",
            AudioElementType.STINGER: "S",
            AudioElementType.AMBIENT_BED: "B",
        }.get(cue.cue_type, "X")
        for i in range(max(0, start_pos), min(60, end_pos + 1)):
            timeline[i] = char
    print("".join(timeline))
    print("=" * 75)


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="F1 Podcast Music Mixer - Professional audio production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
MIXING STYLES:

  Default (stinger-based):
    INTRO (10-15s)  - Heavy, epic, percussive ("The Grid Walk")
    STINGERS (2-3s) - Musical stabs at segment transitions
    BEDS (optional) - Subtle techno under technical segments (5-15% vol)
    OUTRO (15-30s)  - Uplifting, grand orchestral ("The Podium")

  Documentary (--documentary):  [RECOMMENDED]
    INTRO only - Music at start, fades out as voice begins
    CLEAN CONTENT - No music during main content (voice only)
    OUTRO only - Music fades in under final words, swells after voice ends

  Documentary with swells (--documentary --with-swells):
    Same as above PLUS continuous subtle bed with swells at key moments

TECHNICAL STANDARDS:
  - Background music: 5-15% of voice volume
  - Fade durations: 3-5 seconds
  - Output loudness: -16 LUFS
  - Sample rate: 44.1kHz, 256kbps

Example:
  python3 src/podcast_music_mixer.py --project my-podcast --music track.mp3 --documentary
  python3 src/podcast_music_mixer.py --project my-podcast --music track.mp3 --documentary --with-swells
  python3 src/podcast_music_mixer.py --project my-podcast --music shared/music/podcast_default.mp3
        """,
    )
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--music", required=True, help="Path to background music file")
    parser.add_argument(
        "--output", help="Output file (default: output/final_with_music.mp3)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview audio plan only"
    )
    parser.add_argument(
        "--documentary",
        action="store_true",
        help="Use documentary style (intro + outro only, clean voice in between)",
    )
    parser.add_argument(
        "--with-swells",
        action="store_true",
        help="Add music swells during content (use with --documentary)",
    )
    parser.add_argument(
        "--min-gap",
        type=float,
        default=MIN_GAP_BETWEEN_MUSIC,
        help=f"Minimum seconds between music cues (default: {MIN_GAP_BETWEEN_MUSIC})",
    )
    args = parser.parse_args()

    # Paths
    project_dir = get_project_dir(args.project)
    voice_path = f"{project_dir}/output/final.mp3"
    output_path = args.output or f"{project_dir}/output/final_with_music.mp3"
    script_path = f"{project_dir}/script.json"

    # Handle case where output is same as input (overwrite mode)
    overwrite_mode = os.path.abspath(output_path) == os.path.abspath(voice_path)
    if overwrite_mode:
        # Use temporary output, then replace original
        temp_output = f"{project_dir}/output/final_mixed_temp.mp3"
        actual_output = output_path
        output_path = temp_output
    else:
        actual_output = output_path

    # Validate inputs
    if not os.path.exists(voice_path):
        print(f"Error: Voice file not found: {voice_path}")
        sys.exit(1)

    if not os.path.exists(args.music):
        print(f"Error: Music file not found: {args.music}")
        sys.exit(1)

    if not os.path.exists(script_path):
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    # Load script
    with open(script_path) as f:
        script = json.load(f)

    segments = script.get("segments", [])
    print(f"Loaded: {len(segments)} segments")

    # Get actual voice file duration (more reliable than segment files)
    voice_duration = get_audio_duration(voice_path)
    print(f"Voice duration: {voice_duration / 60:.1f} minutes ({voice_duration:.0f}s)")

    # Create fake segment durations based on actual voice duration
    # (for compatibility with functions that expect segment_durations)
    if segments:
        avg_duration = voice_duration / len(segments)
        segment_durations = [avg_duration] * len(segments)
    else:
        segment_durations = [voice_duration]
    total_duration = voice_duration

    # =========================================================================
    # DOCUMENTARY STYLE
    # =========================================================================
    if args.documentary:
        if args.with_swells:
            # Documentary with swells (continuous bed + swells at key moments)
            print("\nUsing DOCUMENTARY style with SWELLS")

            # Analyze for swell points
            swell_points = analyze_script_for_swells(script, segment_durations)

            print(f"\nFound {len(swell_points)} swell points:")
            for sp in swell_points:
                mins = int(sp["time"] // 60)
                secs = sp["time"] % 60
                print(
                    f"  {mins:02d}:{secs:04.1f} - {sp['intensity'].upper():5} - {sp['reason']}"
                )

            if args.dry_run:
                print("\n[DRY RUN] No audio file generated.")
                sys.exit(0)

            print("\n" + "=" * 75)
            print("MIXING AUDIO (Documentary Style with Swells)")
            print("=" * 75)

            success = create_documentary_style_mix(
                voice_path, args.music, output_path, script, segment_durations
            )
        else:
            # Simple documentary: intro + outro only, clean voice in between
            print("\nUsing DOCUMENTARY style (intro + outro only)")

            if args.dry_run:
                voice_duration = get_audio_duration(voice_path)
                outro_start = voice_duration - 10
                print(f"\nMusic placement:")
                print(
                    f"  00:00 - 00:{INTRO_DURATION:.0f}  INTRO at {INTRO_VOLUME_PERCENT}% (fades out)"
                )
                print(
                    f"  {int(outro_start // 60):02d}:{outro_start % 60:04.1f} - end   OUTRO"
                )
                print(
                    f"\nVoice-only: 00:{INTRO_DURATION:.0f} - {int(outro_start // 60):02d}:{outro_start % 60:04.1f}"
                )
                print("\n[DRY RUN] No audio file generated.")
                sys.exit(0)

            print("\n" + "=" * 75)
            print("MIXING AUDIO (Intro + Outro Only)")
            print("=" * 75)

            success = create_intro_outro_only_mix(
                voice_path, args.music, output_path, segment_durations
            )

    # =========================================================================
    # STINGER STYLE (Original)
    # =========================================================================
    else:
        # Analyze script
        print("\nAnalyzing script structure...")
        analysis = analyze_script_for_audio(script, segment_durations)

        # Create audio cues
        print("Planning audio placement...")

        # Use custom min gap if specified
        min_gap = args.min_gap

        cues = create_audio_cues(analysis, args.music, min_gap=min_gap)

        # Print timeline
        print_audio_timeline(cues, total_duration)

        if args.dry_run:
            print("\n[DRY RUN] No audio file generated.")
            sys.exit(0)

        # Mix audio
        print("\n" + "=" * 75)
        print("MIXING AUDIO")
        print("=" * 75)

        success = mix_podcast_audio(voice_path, cues, output_path, total_duration)

    if success:
        # If we used a temp file, replace the original
        if overwrite_mode:
            import shutil

            shutil.move(output_path, actual_output)
            output_path = actual_output

        output_duration = get_audio_duration(output_path)
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\nSuccess!")
        print(f"Output: {output_path}")
        print(f"Duration: {output_duration / 60:.1f} min | Size: {file_size:.1f} MB")
        print(f"Loudness: -16 LUFS (broadcast standard)")
    else:
        print("\nFailed to mix audio.")
        sys.exit(1)


if __name__ == "__main__":
    main()
