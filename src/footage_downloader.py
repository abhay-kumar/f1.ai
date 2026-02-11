#!/usr/bin/env python3
"""
Footage Downloader - Downloads YouTube clips for video segments

Features:
- Official F1 channel prioritization
- Smart query enhancement
- Title-based filtering (avoid interviews, press conferences)
- Multi-candidate search with scoring
- Optional validation integration
"""

import argparse
import json
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir

# Concurrency settings
MAX_CONCURRENT_DOWNLOADS = 3  # Be respectful to YouTube

# Thread-safe print
print_lock = threading.Lock()

# ============================================================================
# OFFICIAL F1 CHANNEL CONFIGURATION
# ============================================================================

OFFICIAL_CHANNELS = [
    "FORMULA 1",
    "Formula 1",
    "F1",
    "Sky Sports F1",
    "Red Bull Racing",
    "Mercedes-AMG PETRONAS F1 Team",
    "Scuderia Ferrari",
    "McLaren",
    "Aston Martin Aramco F1 Team",
    "BWT Alpine F1 Team",
    "Williams Racing",
]

# Good keywords (indicate clean B-roll)
GOOD_KEYWORDS = [
    "highlights",
    "onboard",
    "race edit",
    "best moments",
    "compilation",
    "season review",
    "battle",
    "overtake",
    "pit stop",
    "start",
    "finish",
    "podium",
    "top 10",
    "pole lap",
    "fastest lap",
    "crash",
    "incident",
    "qualifying",
    "sprint",
    "team radio",
]

# Bad keywords (indicate talking heads or problematic content)
BAD_KEYWORDS = [
    "interview",
    "press conference",
    "reaction",
    "reacts",
    "podcast",
    "explained",
    "breakdown",
    "analysis",
    "vlog",
    "behind the scenes",
    "documentary",
    "full race",
    "live stream",
    "watch along",
    "my thoughts",
    "opinion",
    "review",
    "preview",
    "prediction",
]


def enhance_query(query: str, visual: str = "") -> str:
    """Enhance query to target official F1 B-roll content.
    Uses visual description to add specificity when available."""
    query_lower = query.lower()

    has_good = any(kw in query_lower for kw in GOOD_KEYWORDS)
    has_f1 = "f1" in query_lower or "formula" in query_lower

    enhanced = query

    if not has_f1:
        enhanced = f"{query} F1"

    # Extract shot-type keywords from visual description
    if visual:
        visual_lower = visual.lower()
        shot_keywords = [
            "aerial",
            "onboard",
            "pit lane",
            "podium",
            "close-up",
            "wide shot",
            "cockpit",
            "garage",
            "grid",
            "factory",
            "overhead",
            "trackside",
            "flyover",
        ]
        for keyword in shot_keywords:
            if keyword in visual_lower and keyword not in query_lower:
                enhanced = f"{enhanced} {keyword}"
                break

    if not has_good:
        if "race" in query_lower or "gp" in query_lower:
            enhanced = f"{enhanced} highlights"
        elif any(
            name in query_lower
            for name in ["verstappen", "hamilton", "leclerc", "norris", "alonso"]
        ):
            enhanced = f"{enhanced} onboard"
        else:
            enhanced = f"{enhanced} highlights"

    return enhanced


def score_result(title: str, channel: str, query: str = "", visual: str = "") -> float:
    """Score a search result (higher = better). Includes query and visual relevance."""
    title_lower = title.lower()
    channel_lower = channel.lower()

    score = 0.5

    # Official channel boost
    for official in OFFICIAL_CHANNELS:
        if official.lower() in channel_lower:
            score += 0.25
            break

    # Good keywords boost
    for good in GOOD_KEYWORDS:
        if good in title_lower:
            score += 0.08

    # Bad keywords penalty
    for bad in BAD_KEYWORDS:
        if bad in title_lower:
            score -= 0.25

    # Query relevance: how many significant query words appear in the title
    filler = {
        "f1",
        "formula",
        "1",
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "in",
        "at",
        "for",
        "to",
        "on",
    }
    if query:
        query_words = [
            w for w in query.lower().split() if w not in filler and len(w) > 1
        ]
        if query_words:
            matches = sum(1 for w in query_words if w in title_lower)
            relevance = matches / len(query_words)
            score += relevance * 0.15  # Up to +0.15 for full match

    # Visual description relevance
    if visual:
        visual_words = [
            w for w in visual.lower().split() if w not in filler and len(w) > 2
        ]
        if visual_words:
            matches = sum(1 for w in visual_words if w in title_lower)
            visual_relevance = matches / len(visual_words)
            score += visual_relevance * 0.10  # Up to +0.10 for visual match

    return max(0, min(1, score))


def search_youtube(query, max_results=3):
    """Search YouTube and return video IDs with titles (basic version)"""
    cmd = [
        "yt-dlp",
        "--no-warnings",
        f"ytsearch{max_results}:{query}",
        "--get-id",
        "--get-title",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")
    videos = []
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            videos.append({"title": lines[i], "id": lines[i + 1]})
    return videos


def search_youtube_enhanced(
    query: str, max_results: int = 8, visual: str = ""
) -> List[Dict]:
    """
    Search YouTube with enhanced query and metadata extraction.
    Returns results sorted by quality score.
    """
    enhanced = enhance_query(query, visual)

    # yt-dlp command to get title, id, channel, duration
    cmd = [
        "yt-dlp",
        "--no-warnings",
        f"ytsearch{max_results}:{enhanced}",
        "--print",
        "%(title)s|||%(id)s|||%(channel)s|||%(duration)s",
        "--no-download",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    videos = []
    for line in result.stdout.strip().split("\n"):
        if "|||" not in line:
            continue

        parts = line.split("|||")
        if len(parts) >= 4:
            title, video_id, channel, duration = parts[0], parts[1], parts[2], parts[3]

            # Score this result (pass original query and visual for relevance scoring)
            quality_score = score_result(title, channel, query, visual)

            # Skip obviously bad content
            if quality_score < 0.2:
                continue

            videos.append(
                {
                    "title": title,
                    "id": video_id,
                    "channel": channel,
                    "duration": duration,
                    "score": quality_score,
                    "is_official": any(
                        o.lower() in channel.lower() for o in OFFICIAL_CHANNELS
                    ),
                }
            )

    # Sort by score (best first)
    videos.sort(key=lambda v: v["score"], reverse=True)

    return videos


def download_video(video_id: str, output_path: str) -> Tuple[bool, Optional[str]]:
    """Download a YouTube video"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "-f",
        "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
        "--merge-output-format",
        "mp4",
        "-o",
        output_path,
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(output_path):
        return True, None
    return False, result.stderr[:200] if result.stderr else "Unknown error"


def download_segment(args: Tuple) -> Tuple[int, bool, Optional[str], Optional[str]]:
    """Download footage for a single segment (for concurrent execution) - basic version"""
    idx, segment, footage_dir, footage_file = args

    full_path = f"{footage_dir}/{footage_file}"

    if os.path.exists(full_path):
        return idx, True, "cached", None

    query = segment.get("footage_query", segment["text"][:50])
    videos = search_youtube(query, max_results=1)

    if not videos:
        return idx, False, None, "No search results"

    success, error = download_video(videos[0]["id"], full_path)
    if success:
        return idx, True, videos[0]["title"][:50], None
    return idx, False, None, error


def download_segment_enhanced(
    segment: Dict, output_path: str, validate: bool = False, max_candidates: int = 5
) -> Tuple[bool, Optional[str]]:
    """
    Enhanced download with smart candidate selection and optional validation.

    Args:
        segment: Segment dict from script.json
        output_path: Where to save the video
        validate: Whether to validate candidates before accepting
        max_candidates: Maximum candidates to try

    Returns:
        (success, error_message)
    """
    if os.path.exists(output_path):
        return True, None

    query = segment.get("footage_query", segment.get("text", "")[:50])
    visual = segment.get("visual", "")

    # Get ranked candidates
    candidates = search_youtube_enhanced(
        query, max_results=max_candidates + 3, visual=visual
    )

    if not candidates:
        return False, "No search results"

    # Try to import validator
    validate_fn = None
    if validate:
        try:
            from src.footage_validator import quick_validate

            validate_fn = quick_validate
        except ImportError:
            pass

    # Try each candidate
    for candidate in candidates[:max_candidates]:
        # Download to temp path first
        temp_path = output_path + ".temp"

        success, error = download_video(candidate["id"], temp_path)
        if not success:
            continue

        # Validate if function provided
        if validate_fn:
            is_valid, reason = validate_fn(temp_path, segment.get("text", ""))
            if not is_valid:
                try:
                    os.remove(temp_path)
                except:
                    pass
                continue

        # Success - move to final location
        try:
            os.rename(temp_path, output_path)
        except:
            import shutil

            shutil.move(temp_path, output_path)

        return True, None

    return False, "All candidates failed validation"


def download_segment_smart(
    args: Tuple,
) -> Tuple[int, bool, Optional[str], Optional[str], Optional[str]]:
    """
    Smart download with candidate selection and scoring.
    Returns: (idx, success, title, error, source_type)
    """
    idx, segment, footage_dir, footage_file, validate = args

    full_path = f"{footage_dir}/{footage_file}"

    if os.path.exists(full_path):
        return idx, True, "cached", None, "cached"

    query = segment.get("footage_query", segment.get("text", "")[:50])
    visual = segment.get("visual", "")

    # Get ranked candidates
    candidates = search_youtube_enhanced(query, max_results=5, visual=visual)

    if not candidates:
        return idx, False, None, "No search results", None

    # Try to import validator
    validate_fn = None
    if validate:
        try:
            from src.footage_validator import quick_validate

            validate_fn = quick_validate
        except ImportError:
            pass

    # Try each candidate
    for candidate in candidates:
        temp_path = f"{footage_dir}/.temp_{footage_file}"

        success, error = download_video(candidate["id"], temp_path)
        if not success:
            continue

        # Validate if function provided
        if validate_fn:
            is_valid, reason = validate_fn(temp_path, segment.get("text", ""))
            if not is_valid:
                try:
                    os.remove(temp_path)
                except:
                    pass
                continue

        # Success - move to final location
        try:
            os.rename(temp_path, full_path)
        except:
            import shutil

            shutil.move(temp_path, full_path)

        source = "official" if candidate.get("is_official") else "youtube"
        return idx, True, candidate["title"][:50], None, source

    return idx, False, None, "All candidates failed", None


def safe_print(msg: str):
    """Thread-safe printing"""
    with print_lock:
        print(msg, flush=True)


def main():
    parser = argparse.ArgumentParser(description="Download footage from YouTube")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--segment", type=int, help="Segment ID to download for")
    parser.add_argument("--query", help="Custom search query")
    parser.add_argument("--url", help="Direct YouTube URL")
    parser.add_argument(
        "--list", action="store_true", help="List all segments and their footage status"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show candidates, do not download (single-segment mode)",
    )
    parser.add_argument(
        "--sequential", action="store_true", help="Disable concurrent downloads"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=MAX_CONCURRENT_DOWNLOADS,
        help=f"Max concurrent downloads (default: {MAX_CONCURRENT_DOWNLOADS})",
    )
    args = parser.parse_args()

    project_dir = get_project_dir(args.project)
    footage_dir = f"{project_dir}/footage"
    script_file = f"{project_dir}/script.json"

    if not os.path.exists(script_file):
        print(f"Error: Script not found at {script_file}")
        sys.exit(1)

    os.makedirs(footage_dir, exist_ok=True)

    with open(script_file) as f:
        script = json.load(f)

    segments = script["segments"]

    if args.list:
        print("=" * 60)
        print(f"Footage Status - Project: {args.project}")
        print("=" * 60)
        for i, seg in enumerate(segments):
            footage_file = f"{footage_dir}/{seg.get('footage', f'segment_{i:02d}.mp4')}"
            status = "OK" if os.path.exists(footage_file) else "MISSING"
            print(f"[{i}] {status:7} | {seg['context']}")
            if "footage_title" in seg:
                print(f"    Title: {seg['footage_title'][:60]}")
            print(f"    Text: {seg['text'][:50]}...")
            if seg.get("visual"):
                print(f"    Visual: {seg['visual'][:60]}")
            if "footage_query" in seg:
                print(f"    Query: {seg['footage_query']}")
            print()
        return

    if args.segment is not None:
        segment = segments[args.segment]
        output_file = f"{footage_dir}/segment_{args.segment:02d}.mp4"

        if args.url:
            # Direct URL download
            video_id = args.url.split("v=")[-1].split("&")[0]
            print(f"Downloading from URL: {args.url}")
            success, error = download_video(video_id, output_file)
            if success:
                print(f"Saved to: {output_file}")
                # Fetch and store video title
                title_cmd = [
                    "yt-dlp",
                    "--no-warnings",
                    "--print",
                    "%(title)s",
                    "--no-download",
                    args.url,
                ]
                title_result = subprocess.run(title_cmd, capture_output=True, text=True)
                video_title = (
                    title_result.stdout.strip()
                    if title_result.returncode == 0
                    else None
                )
                # Update script with footage filename and title
                segment["footage"] = f"segment_{args.segment:02d}.mp4"
                if video_title:
                    segment["footage_title"] = video_title
                    print(f"Title: {video_title}")
                with open(script_file, "w") as f:
                    json.dump(script, f, indent=2)
            else:
                print(f"Download failed: {error}")
        else:
            # Search with enhanced ranking
            query = args.query or segment.get("footage_query", segment["text"][:50])
            visual = segment.get("visual", "")
            print(f"Original query: {query}")
            if visual:
                print(f"Visual: {visual}")
            print(f"Enhanced query: {enhance_query(query, visual)}")
            print("-" * 60)

            videos = search_youtube_enhanced(query, max_results=8, visual=visual)
            print(f"{'Score':<6} {'Channel':<25} {'Title'}")
            print("-" * 60)
            for i, v in enumerate(videos):
                official = "*" if v.get("is_official") else " "
                marker = " <--" if i == 0 and not args.dry_run else ""
                print(
                    f"{v['score']:.2f}{official}  {v['channel'][:23]:<23}  {v['title'][:40]}{marker}"
                )

            print()
            print("* = Official F1 channel")

            if args.dry_run:
                print("\n[Dry run] No download. To download a specific video:")
                print(
                    f"  python3 src/footage_downloader.py --project {args.project} --segment {args.segment} --url https://youtube.com/watch?v=VIDEO_ID"
                )
            elif videos:
                # Auto-download top result
                top = videos[0]
                print(f"\nDownloading top result: {top['title'][:60]}...")
                if os.path.exists(output_file):
                    os.remove(output_file)
                success, error = download_video(top["id"], output_file)
                if success:
                    print(f"Saved to: {output_file}")
                    segment["footage"] = f"segment_{args.segment:02d}.mp4"
                    segment["footage_title"] = top["title"]
                    with open(script_file, "w") as f:
                        json.dump(script, f, indent=2)
                else:
                    print(f"Download failed: {error}")
                    print("\nTo try a different video:")
                    print(
                        f"  python3 src/footage_downloader.py --project {args.project} --segment {args.segment} --url https://youtube.com/watch?v=VIDEO_ID"
                    )
            else:
                print("\nNo candidates found. Try a different --query.")
    else:
        # Download all missing footage
        print("=" * 60)
        print(f"Downloading All Footage - Project: {args.project}")
        print(
            f"Concurrency: {'Sequential' if args.sequential else f'{args.workers} workers'}"
        )
        print("=" * 60)

        # Prepare tasks
        tasks = []
        for i, seg in enumerate(segments):
            footage_file = seg.get("footage", f"segment_{i:02d}.mp4")
            tasks.append((i, seg, footage_dir, footage_file))

        downloaded = 0
        cached = 0
        failed = 0

        if args.sequential:
            # Sequential processing
            for task in tasks:
                idx, seg, _, footage_file = task
                print(f"[{idx}] Processing: {seg['context']}...", end=" ", flush=True)
                idx, success, title, error = download_segment(task)
                if title == "cached":
                    print("Cached")
                    cached += 1
                elif success:
                    segments[idx]["footage"] = f"segment_{idx:02d}.mp4"
                    segments[idx]["footage_title"] = title
                    print(f"Done - {title}")
                    downloaded += 1
                else:
                    print(f"Failed: {error}")
                    failed += 1
        else:
            # Concurrent processing
            print(f"\nDownloading {len(tasks)} segments concurrently...\n")

            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                future_to_idx = {
                    executor.submit(download_segment, task): task[0] for task in tasks
                }

                for future in as_completed(future_to_idx):
                    idx, success, title, error = future.result()
                    seg = segments[idx]

                    if title == "cached":
                        safe_print(f"[{idx}] Cached: {seg['context']}")
                        cached += 1
                    elif success:
                        segments[idx]["footage"] = f"segment_{idx:02d}.mp4"
                        segments[idx]["footage_title"] = title
                        safe_print(f"[{idx}] Downloaded: {seg['context']} -> {title}")
                        downloaded += 1
                    else:
                        safe_print(f"[{idx}] Failed: {seg['context']} - {error}")
                        failed += 1

        # Save updated script
        with open(script_file, "w") as f:
            json.dump(script, f, indent=2)

        print(f"\n{'=' * 60}")
        print(f"Downloaded: {downloaded} | Cached: {cached} | Failed: {failed}")


if __name__ == "__main__":
    main()
