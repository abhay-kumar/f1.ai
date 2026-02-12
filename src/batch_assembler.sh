#!/bin/bash
# Batch Assembler Shell Script — truly zero-overhead parent process.
# Runs each segment in its own Python subprocess, then concat/mix.
#
# Usage: bash src/batch_assembler.sh <project> <resolution> [start_from] [flags]
# Example: bash src/batch_assembler.sh 12th-team-manufacturers hd 14 --no-yt-search

set -euo pipefail

PROJECT="${1:?Usage: batch_assembler.sh <project> <resolution> [start_from] [flags...]}"
RESOLUTION="${2:-hd}"
START_FROM="${3:-0}"
shift 3 2>/dev/null || true
FLAGS="$*"

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$BASE_DIR/projects/$PROJECT"
TEMP_DIR="$PROJECT_DIR/temp"
OUTPUT_DIR="$PROJECT_DIR/output"
AUDIO_DIR="$PROJECT_DIR/audio"
SCRIPT_FILE="$PROJECT_DIR/script.json"

mkdir -p "$TEMP_DIR" "$OUTPUT_DIR"

# Parse resolution
if [ "$RESOLUTION" = "4k" ]; then
    WIDTH=3840; HEIGHT=2160
else
    WIDTH=1920; HEIGHT=1080
fi

# Count segments
NUM_SEGMENTS=$(python3 -c "import json; print(len(json.load(open('$SCRIPT_FILE'))['segments']))")

echo "======================================================================"
echo "Batch Assembler (shell) - Project: $PROJECT"
echo "Resolution: ${WIDTH}x${HEIGHT} | Segments: $NUM_SEGMENTS"
echo "Starting from: segment $START_FROM | Flags: $FLAGS"
echo "======================================================================"

# Check for --no-yt-search flag
NO_YT_SEARCH="False"
if echo "$FLAGS" | grep -q "no-yt-search"; then
    NO_YT_SEARCH="True"
fi

NO_SFX="False"
if echo "$FLAGS" | grep -q "no-sfx"; then
    NO_SFX="True"
fi

NO_MUSIC="False"
if echo "$FLAGS" | grep -q "no-music"; then
    NO_MUSIC="True"
fi

# Phase 1: Intro
INTRO_PATH="$TEMP_DIR/intro.mp4"
if [ ! -f "$INTRO_PATH" ] && ! echo "$FLAGS" | grep -q "no-intro"; then
    echo ""
    echo "[Intro] Creating animated intro..."
    python3 -c "
import sys; sys.path.insert(0, '$BASE_DIR')
import os; os.chdir('$BASE_DIR')
from src.intro_generator import create_intro_video
ok = create_intro_video('$INTRO_PATH', $WIDTH, $HEIGHT)
print('OK' if ok else 'FAIL')
" 2>/dev/null && echo "    Intro created" || echo "    Intro failed"
elif [ -f "$INTRO_PATH" ]; then
    echo "[Intro] Using cached"
fi

# Phase 2: Process segments one at a time
echo ""
echo "Processing $NUM_SEGMENTS segments..."
echo ""

FAILED_SEGMENTS=""

for i in $(seq 0 $((NUM_SEGMENTS - 1))); do
    SEG_NUM=$((i + 1))
    OUTPUT_PATH="$TEMP_DIR/segment_$(printf '%02d' $i).mp4"
    AUDIO_PATH="$AUDIO_DIR/segment_$(printf '%02d' $i).mp3"

    # Skip cached segments
    if [ "$i" -lt "$START_FROM" ] && [ -f "$OUTPUT_PATH" ]; then
        DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUTPUT_PATH" 2>/dev/null || echo "0")
        echo "[$SEG_NUM/$NUM_SEGMENTS] Cached (${DUR}s)"
        continue
    fi

    # Skip already-created segments before start_from
    if [ "$i" -lt "$START_FROM" ] && [ ! -f "$OUTPUT_PATH" ]; then
        echo "[$SEG_NUM/$NUM_SEGMENTS] Missing (skipped)"
        continue
    fi

    # Remove existing if re-processing
    [ -f "$OUTPUT_PATH" ] && rm "$OUTPUT_PATH"

    # Get context for display
    CONTEXT=$(python3 -c "import json; s=json.load(open('$SCRIPT_FILE'))['segments'][$i]; print(s.get('context','segment')[:40])" 2>/dev/null || echo "segment")

    printf "[$SEG_NUM/$NUM_SEGMENTS] $CONTEXT... "

    # Run in subprocess — this is the key isolation point
    RESULT=$(python3 -c "
import sys, os, json, shutil
sys.path.insert(0, '$BASE_DIR')
os.chdir('$BASE_DIR')

from src.image_video_assembler import (
    create_segment_video, detect_color_grade, apply_color_grade, get_duration
)

with open('$SCRIPT_FILE') as f:
    script = json.load(f)
seg = script['segments'][$i]

work_dir = '$TEMP_DIR/visuals'
os.makedirs(work_dir, exist_ok=True)

success, error, vtype = create_segment_video(
    $i, seg, '$AUDIO_PATH',
    work_dir, '$OUTPUT_PATH', $WIDTH, $HEIGHT,
    use_veo3=False, use_yt_search=(not $NO_YT_SEARCH),
)

if success:
    grade = detect_color_grade(seg)
    if grade != 'none':
        graded = '$OUTPUT_PATH.graded.mp4'
        if apply_color_grade('$OUTPUT_PATH', graded, grade):
            os.replace(graded, '$OUTPUT_PATH')
    dur = get_duration('$OUTPUT_PATH')
    print(f'OK|{vtype}|{grade}|{dur:.1f}')
else:
    print(f'FAIL|{error}')

# Cleanup
seg_work = os.path.join(work_dir, f'segment_$(printf '%02d' $i)')
if os.path.exists(seg_work):
    shutil.rmtree(seg_work, ignore_errors=True)
" 2>/dev/null || echo "FAIL|subprocess_error")

    if echo "$RESULT" | grep -q "^OK|"; then
        VTYPE=$(echo "$RESULT" | cut -d'|' -f2)
        GRADE=$(echo "$RESULT" | cut -d'|' -f3)
        DUR=$(echo "$RESULT" | cut -d'|' -f4)
        GRADE_LABEL=""
        [ "$GRADE" != "none" ] && GRADE_LABEL=" grade=$GRADE"
        echo "Done (${DUR}s) [${VTYPE}${GRADE_LABEL}]"
    else
        ERROR=$(echo "$RESULT" | sed 's/FAIL|//')
        echo "Failed: $ERROR"
        FAILED_SEGMENTS="$FAILED_SEGMENTS $i"
    fi

    # Force memory cleanup between segments
    sleep 1
done

# Count successes
CREATED=$(ls "$TEMP_DIR"/segment_*.mp4 2>/dev/null | wc -l | tr -d ' ')
echo ""
echo "Segments created: $CREATED/$NUM_SEGMENTS"
[ -n "$FAILED_SEGMENTS" ] && echo "Failed segments:$FAILED_SEGMENTS"

if [ "$CREATED" -eq 0 ]; then
    echo "No segments created!"
    exit 1
fi

# Phase 3: Post-processing in subprocess
echo ""
echo "Post-processing..."

python3 -c "
import sys, os, json, subprocess as sp
sys.path.insert(0, '$BASE_DIR')
os.chdir('$BASE_DIR')

from src.image_video_assembler import (
    gpu_enc_args, add_transition_sfx, add_background_music,
    detect_music_mood, generate_srt_captions, create_outro_video, get_duration
)
from src.config import (
    LONGFORM_AUDIO_BITRATE, MUSIC_VOLUME_LONGFORM,
    MUSIC_VOLUME_UPLIFTING, MUSIC_VOLUME_ATMOSPHERIC,
)

temp_dir = '$TEMP_DIR'
output_dir = '$OUTPUT_DIR'
width, height = $WIDTH, $HEIGHT

# Collect segment videos
segment_videos = []
intro_path = '$INTRO_PATH'
if os.path.exists(intro_path):
    segment_videos.append(intro_path)

segment_durations = []
for i in range($NUM_SEGMENTS):
    path = os.path.join(temp_dir, f'segment_{i:02d}.mp4')
    if os.path.exists(path):
        dur = get_duration(path)
        segment_videos.append(path)
        segment_durations.append(dur)

# Outro
outro_path = os.path.join(temp_dir, 'outro.mp4')
if not os.path.exists(outro_path):
    if create_outro_video(outro_path, width, height):
        segment_videos.append(outro_path)
        print('Outro created')

# Concatenate
print(f'Concatenating {len(segment_videos)} segments...')
concat_file = os.path.join(temp_dir, 'concat.txt')
with open(concat_file, 'w') as f:
    for v in segment_videos:
        f.write(f\"file '{v}'\n\")

concat_output = os.path.join(temp_dir, 'concat.mp4')
enc = gpu_enc_args()
cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
       *enc, '-c:a', 'aac', '-b:a', LONGFORM_AUDIO_BITRATE, concat_output]
sp.run(cmd, capture_output=True, text=True, timeout=600)

if not os.path.exists(concat_output):
    print('Concatenation failed!')
    sys.exit(1)

# SFX
no_sfx = $NO_SFX
if not no_sfx and segment_durations:
    print('Adding transition SFX...')
    sfx_output = os.path.join(temp_dir, 'with_sfx.mp4')
    if add_transition_sfx(concat_output, sfx_output, segment_durations):
        concat_output = sfx_output

# Music
final_output = os.path.join(output_dir, 'final.mp4')
no_music = $NO_MUSIC
if not no_music:
    print('Adding background music...')
    with open('$SCRIPT_FILE') as f:
        script = json.load(f)
    segments = script['segments']

    segment_volumes = []
    intro_offset = 0.0
    if os.path.exists(intro_path):
        intro_dur = get_duration(intro_path)
        segment_volumes.append((0.0, intro_dur, MUSIC_VOLUME_UPLIFTING))
        intro_offset = intro_dur

    cumulative = intro_offset
    for idx, dur in enumerate(segment_durations):
        if idx < len(segments):
            mood = detect_music_mood(segments[idx])
            vol = {'uplifting': MUSIC_VOLUME_UPLIFTING,
                    'atmospheric': MUSIC_VOLUME_ATMOSPHERIC}.get(mood, MUSIC_VOLUME_LONGFORM)
        else:
            vol = MUSIC_VOLUME_LONGFORM
        segment_volumes.append((cumulative, cumulative + dur, vol))
        cumulative += dur

    add_background_music(concat_output, final_output, segment_volumes=segment_volumes)
else:
    sp.run(['cp', concat_output, final_output])

# Captions
with open('$SCRIPT_FILE') as f:
    script = json.load(f)
generate_srt_captions(script, '$AUDIO_DIR', os.path.join(output_dir, 'captions.srt'))

if os.path.exists(final_output):
    size_mb = os.path.getsize(final_output) / (1024 * 1024)
    duration = get_duration(final_output)
    print(f'Duration: {duration / 60:.1f} minutes ({duration:.0f}s)')
    print(f'Size: {size_mb:.1f}MB')
else:
    print('Failed to create final video')
    sys.exit(1)
" 2>&1

echo ""
echo "======================================================================"
echo "DONE: $OUTPUT_DIR/final.mp4"
echo "======================================================================"
