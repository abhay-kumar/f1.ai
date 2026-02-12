#!/bin/bash
# Download footage one segment at a time in isolated processes.
# Unlike footage_downloader.py (concurrent), this runs sequentially with
# full subprocess isolation — useful when yt-dlp hangs or leaks memory.
#
# Usage: bash src/download_footage.sh <project> [segment_list]
# Examples:
#   bash src/download_footage.sh my-video                    # All segments with footage_query
#   bash src/download_footage.sh my-video "0 1 3 6 8"       # Specific segments only

set -u

PROJECT="${1:?Usage: download_footage.sh <project> [segment_list]}"
SEGMENT_LIST="${2:-}"

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$BASE_DIR/projects/$PROJECT"
FOOTAGE_DIR="$PROJECT_DIR/footage"
SCRIPT_FILE="$PROJECT_DIR/script.json"

if [ ! -f "$SCRIPT_FILE" ]; then
    echo "Error: $SCRIPT_FILE not found"
    exit 1
fi

mkdir -p "$FOOTAGE_DIR"

# Get segments to download
if [ -n "$SEGMENT_LIST" ]; then
    SEGMENTS=($SEGMENT_LIST)
else
    # Auto-detect: all segments that have a footage_query field
    SEGMENTS=($(python3 -c "
import json
with open('$SCRIPT_FILE') as f:
    s = json.load(f)
for i, seg in enumerate(s['segments']):
    if seg.get('footage_query'):
        print(i)
"))
fi

NUM_SEGMENTS=${#SEGMENTS[@]}
echo "============================================================"
echo "Footage Downloader (shell) - Project: $PROJECT"
echo "Segments: $NUM_SEGMENTS (${SEGMENTS[*]})"
echo "============================================================"
echo ""

DOWNLOADED=0
CACHED=0
FAILED=0

for seg in "${SEGMENTS[@]}"; do
    OUTFILE="$FOOTAGE_DIR/segment_$(printf '%02d' $seg).mp4"

    # Skip if already downloaded
    if [ -f "$OUTFILE" ]; then
        SIZE=$(stat -f%z "$OUTFILE" 2>/dev/null || stat -c%s "$OUTFILE" 2>/dev/null || echo 0)
        SIZE_MB=$((SIZE / 1048576))
        echo "[Seg $seg] Already exists (${SIZE_MB}MB) - skipping"
        CACHED=$((CACHED + 1))
        continue
    fi

    # Get query from script.json
    QUERY=$(python3 -c "
import json
with open('$SCRIPT_FILE') as f:
    s = json.load(f)
print(s['segments'][$seg].get('footage_query', s['segments'][$seg]['text'][:50]))
" 2>/dev/null)

    echo "[Seg $seg] Searching: ${QUERY:0:60}..."

    # Search in a subprocess that dies cleanly
    VIDEO_ID=$(python3 -c "
import subprocess, sys
result = subprocess.run(
    ['yt-dlp', '--no-warnings', '--flat-playlist',
     '--print', '%(id)s', 'ytsearch1:$QUERY'],
    capture_output=True, text=True, timeout=30
)
if result.stdout.strip():
    print(result.stdout.strip().split('\n')[0])
" 2>/dev/null)

    if [ -z "$VIDEO_ID" ]; then
        echo "         No results found"
        FAILED=$((FAILED + 1))
        continue
    fi

    TITLE=$(python3 -c "
import subprocess
result = subprocess.run(
    ['yt-dlp', '--no-warnings', '--print', '%(title)s',
     '--no-download', 'https://youtube.com/watch?v=$VIDEO_ID'],
    capture_output=True, text=True, timeout=15
)
print(result.stdout.strip()[:80])
" 2>/dev/null)

    echo "         -> $TITLE (ID: $VIDEO_ID)"

    # Download only first 60 seconds
    yt-dlp --no-warnings \
        -f "137+140/bestvideo[height<=1080]+bestaudio/best[height<=1080]" \
        --merge-output-format mp4 \
        --download-sections "*0-60" \
        -o "$OUTFILE" \
        "https://www.youtube.com/watch?v=$VIDEO_ID" 2>&1 | tail -3

    if [ -f "$OUTFILE" ]; then
        SIZE=$(stat -f%z "$OUTFILE" 2>/dev/null || stat -c%s "$OUTFILE" 2>/dev/null || echo 0)
        SIZE_MB=$((SIZE / 1048576))
        echo "         Downloaded (${SIZE_MB}MB)"
        DOWNLOADED=$((DOWNLOADED + 1))

        # Update script.json with footage filename and title
        python3 -c "
import json
with open('$SCRIPT_FILE') as f:
    s = json.load(f)
s['segments'][$seg]['footage'] = 'segment_$(printf '%02d' $seg).mp4'
s['segments'][$seg]['footage_title'] = '''$TITLE'''
with open('$SCRIPT_FILE', 'w') as f:
    json.dump(s, f, indent=2)
" 2>/dev/null
    else
        echo "         FAILED"
        FAILED=$((FAILED + 1))
    fi

    # Brief pause between downloads
    sleep 2
done

echo ""
echo "============================================================"
echo "Download Complete: $DOWNLOADED new, $CACHED cached, $FAILED failed"
echo "Total files: $(ls "$FOOTAGE_DIR"/segment_*.mp4 2>/dev/null | wc -l | tr -d ' ')"
echo "============================================================"
