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
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir
from src.shot_assembler import (
    get_shot_source_ext,
    normalize_segment,
    shot_footage_filename,
)

# Concurrency settings
MAX_CONCURRENT_DOWNLOADS = 4  # Parallel download workers

# Format strings for yt-dlp
FORMAT_HD = "137+140/bestvideo[height<=1080]+bestaudio/best[height<=1080]"
FORMAT_4K = "bestvideo[height<=2160]+bestaudio/best[height<=2160]"

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
        "--no-check-formats",
        f"ytsearch{max_results}:{query}",
        "--get-id",
        "--get-title",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
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
        "--no-check-formats",
        f"ytsearch{max_results}:{enhanced}",
        "--print",
        "%(title)s|||%(id)s|||%(channel)s|||%(duration)s",
        "--no-download",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        safe_print(f"  [Search] yt-dlp search timed out for: {enhanced[:50]}")
        return []

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


def download_video(
    video_id: str, output_path: str, use_4k: bool = False
) -> Tuple[bool, Optional[str]]:
    """Download a YouTube video with optimized speed settings."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    fmt = FORMAT_4K if use_4k else FORMAT_HD
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "--concurrent-fragments",
        "4",
        "-f",
        fmt,
        "--merge-output-format",
        "mp4",
        "-o",
        output_path,
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        # Clean up partial files left by yt-dlp
        import glob

        for f in glob.glob(f"{output_path}*"):
            if f != output_path:
                try:
                    os.remove(f)
                except OSError:
                    pass
        return False, "Download timed out after 180s"
    if os.path.exists(output_path):
        return True, None
    return False, result.stderr[:200] if result.stderr else "Unknown error"


def download_segment(args: Tuple) -> Tuple[int, bool, Optional[str], Optional[str]]:
    """Download footage for a single segment (for concurrent execution) with enhanced search"""
    idx, segment, footage_dir, footage_file = args

    full_path = f"{footage_dir}/{footage_file}"

    if os.path.exists(full_path):
        return idx, True, "cached", None

    query = segment.get("footage_query", segment["text"][:50])
    visual = segment.get("visual", "")
    videos = search_youtube_enhanced(query, max_results=3, visual=visual)

    if not videos:
        # Fallback to basic search if enhanced returns nothing
        videos = search_youtube(query, max_results=1)

    if not videos:
        return idx, False, None, "No search results"

    top = videos[0]
    video_id = top["id"]
    title = top.get("title", "")[:50]

    success, error = download_video(video_id, full_path)
    if success:
        return idx, True, title, None
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


def download_image(query: str, output_path: str) -> Tuple[bool, Optional[str]]:
    """Download a stock image from Pexels for an image shot.

    Searches Pexels for the query and downloads the top result.
    Falls back to a simple placeholder if Pexels API is unavailable.
    """
    # Try to load Pexels API key
    creds_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "shared",
        "creds",
        "pexels",
    )
    api_key = None
    if os.path.exists(creds_path):
        with open(creds_path) as f:
            api_key = f.read().strip()

    if not api_key:
        api_key = os.environ.get("PEXELS_API_KEY")

    if not api_key:
        return False, "No Pexels API key (shared/creds/pexels)"

    try:
        # Add F1 context to query for better results
        search_query = (
            query
            if "f1" in query.lower() or "formula" in query.lower()
            else f"{query} Formula 1"
        )
        search_url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(search_query)}&per_page=3&orientation=landscape"
        req = urllib.request.Request(
            search_url,
            headers={
                "Authorization": api_key,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            },
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())

        photos = data.get("photos", [])
        if not photos:
            return False, f"No images found for: {query}"

        # Download the first image
        image_url = photos[0]["src"]["large2x"]
        req = urllib.request.Request(
            image_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())

        return True, None
    except Exception as e:
        return False, str(e)[:100]


def get_download_tasks(segments: list, footage_dir: str) -> list:
    """Build download tasks from segments, respecting shot lists.

    For segments with shots arrays, creates one task per downloadable shot.
    For legacy segments (no shots), creates one task per segment.

    Returns list of task dicts with keys:
        seg_idx, shot_idx, query, visual, footage_file, footage_start,
        source_type, image_query
    """
    tasks = []
    for seg_idx, seg in enumerate(segments):
        seg = normalize_segment(seg)
        shots = seg.get("shots", [])

        if len(shots) > 1:
            # Multi-shot segment: one task per shot
            for shot_idx, shot in enumerate(shots):
                source_type = shot.get("source_type", "youtube_clip")
                if source_type not in ("youtube_clip", "image"):
                    continue  # Skip non-downloadable shots (quote_overlay, veo3, etc.)

                ext = get_shot_source_ext(source_type)
                footage_file = shot.get(
                    "footage", shot_footage_filename(seg_idx, shot_idx, ext)
                )

                tasks.append(
                    {
                        "seg_idx": seg_idx,
                        "shot_idx": shot_idx,
                        "query": shot.get("footage_query", ""),
                        "image_query": shot.get("image_query", ""),
                        "visual": shot.get("label", ""),
                        "footage_file": footage_file,
                        "footage_start": shot.get("footage_start", 0),
                        "source_type": source_type,
                        "reddit_media_url": shot.get("reddit_media_url", ""),
                        "reddit_media_type": shot.get("reddit_media_type", ""),
                        "reddit_image_url": shot.get("reddit_image_url", ""),
                    }
                )
        else:
            # Single-shot / legacy segment
            footage_file = seg.get("footage", f"segment_{seg_idx:02d}.mp4")
            tasks.append(
                {
                    "seg_idx": seg_idx,
                    "shot_idx": None,
                    "query": seg.get("footage_query", seg.get("text", "")[:50]),
                    "image_query": "",
                    "visual": seg.get("visual", ""),
                    "footage_file": footage_file,
                    "footage_start": seg.get("footage_start", 0),
                    "source_type": "youtube_clip",
                    "reddit_media_url": seg.get("reddit_media_url", ""),
                    "reddit_media_type": seg.get("reddit_media_type", ""),
                    "reddit_image_url": "",
                }
            )

    return tasks


def download_task(
    args: Tuple,
) -> Tuple[int, Optional[int], bool, Optional[str], Optional[str]]:
    """Download footage or image for a single task (for concurrent execution).

    The task dict may contain:
        use_google: bool - Use Google search for better results
        validate: bool - Validate with Gemini vision after download
        max_candidates: int - Max candidates to try (default 5)

    Returns: (seg_idx, shot_idx, success, title_or_status, error)
    """
    task, footage_dir = args

    full_path = os.path.join(footage_dir, task["footage_file"])
    use_google = task.get("use_google", False)
    validate = task.get("validate", False)
    max_candidates = task.get("max_candidates", 5)

    if os.path.exists(full_path):
        return task["seg_idx"], task["shot_idx"], True, "cached", None

    # Reddit media priority (highest — try before YouTube/Google/Pexels)
    reddit_url = task.get("reddit_media_url") or task.get("reddit_image_url")
    if reddit_url:
        success, error = _download_reddit_task(reddit_url, full_path)
        if success:
            return (
                task["seg_idx"],
                task["shot_idx"],
                True,
                f"reddit: {reddit_url[:40]}",
                None,
            )
        safe_print(
            f"  [Reddit] Failed for seg {task['seg_idx']} ({error}), falling back"
        )

    if task["source_type"] == "image":
        return _download_image_task(
            task, full_path, use_google, validate, max_candidates
        )
    else:
        return _download_video_task(
            task, full_path, footage_dir, use_google, validate, max_candidates
        )


def _download_reddit_task(
    reddit_url: str, full_path: str
) -> Tuple[bool, Optional[str]]:
    """Download media from a Reddit URL (highest priority source).

    Handles:
    - i.redd.it images: direct HTTP download
    - preview.redd.it GIF-as-MP4: direct HTTP download
    - v.redd.it videos: yt-dlp (handles audio+video merge)
    - packaged-media.redd.it: yt-dlp

    Returns (success, error_message)
    """
    if not reddit_url:
        return False, "No Reddit URL"

    # Direct HTTP download for images and preview GIF-as-MP4
    if any(d in reddit_url for d in ["i.redd.it", "preview.redd.it"]):
        try:
            req = urllib.request.Request(
                reddit_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()

            if len(data) < 500:
                return False, "Downloaded file too small"

            with open(full_path, "wb") as f:
                f.write(data)
            return True, None
        except Exception as e:
            return False, str(e)[:100]

    # yt-dlp for v.redd.it and packaged-media.redd.it (handles audio+video merge)
    if any(d in reddit_url for d in ["v.redd.it", "packaged-media.redd.it", "redd.it"]):
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "-f",
            "bestvideo+bestaudio/best",
            "--merge-output-format",
            "mp4",
            "-o",
            full_path,
            reddit_url,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return False, "yt-dlp timed out"

        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            return True, None
        return False, (result.stderr[:200] if result.stderr else "Unknown error")

    # Unknown Reddit URL pattern — try direct download first, then yt-dlp
    try:
        req = urllib.request.Request(
            reddit_url,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
        if len(data) > 500:
            with open(full_path, "wb") as f:
                f.write(data)
            return True, None
    except Exception:
        pass

    # Fallback to yt-dlp
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "-f",
        "bestvideo+bestaudio/best",
        "--merge-output-format",
        "mp4",
        "-o",
        full_path,
        reddit_url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return False, "yt-dlp timed out"

    if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
        return True, None
    return False, "All download methods failed"


def _download_image_task(
    task: Dict, full_path: str, use_google: bool, validate: bool, max_candidates: int
) -> Tuple[int, Optional[int], bool, Optional[str], Optional[str]]:
    """Download an image with optional Google search and Gemini validation."""
    query = task["image_query"] or task["query"]
    if not query:
        return task["seg_idx"], task["shot_idx"], False, None, "No image query"

    label = task.get("visual", query[:40])

    # Build candidate list
    candidates = []

    if use_google:
        try:
            from src.google_image_search import search_google_images

            results = search_google_images(query, max_results=max_candidates)
            for r in results:
                candidates.append({"url": r["url"], "source": "google"})
        except Exception as e:
            safe_print(f"  [Google Images] Error: {e}")

    # Always add Pexels as fallback (via existing download_image)
    if not candidates:
        # No Google results, use direct Pexels download
        success, error = download_image(query, full_path)
        if success:
            if validate:
                is_match, conf, reason = _validate_file(full_path, label, query)
                if not is_match:
                    safe_print(f"  [Validate] MISMATCH ({conf:.1f}): {reason[:50]}")
                    # Keep it anyway as best effort since no other candidates
            return (
                task["seg_idx"],
                task["shot_idx"],
                success,
                f"image: {query[:40]}",
                error,
            )
        return task["seg_idx"], task["shot_idx"], False, None, error

    # Try each Google Images candidate
    best_path = None
    best_conf = 0.0
    for i, candidate in enumerate(candidates[:max_candidates]):
        temp_path = full_path + f".candidate_{i}"
        try:
            from src.google_image_search import download_image_url

            success, err = download_image_url(candidate["url"], temp_path)
            if not success:
                continue

            if os.path.getsize(temp_path) < 5000:
                os.remove(temp_path)
                continue

            if validate:
                is_match, conf, reason = _validate_file(temp_path, label, query)
                if is_match:
                    os.rename(temp_path, full_path)
                    return (
                        task["seg_idx"],
                        task["shot_idx"],
                        True,
                        f"image[google,validated]: {query[:30]}",
                        None,
                    )
                else:
                    safe_print(
                        f"  [Validate] Candidate {i} MISMATCH ({conf:.1f}): {reason[:40]}"
                    )
                    if conf > best_conf:
                        if best_path and os.path.exists(best_path):
                            os.remove(best_path)
                        best_path = temp_path
                        best_conf = conf
                    else:
                        os.remove(temp_path)
            else:
                # No validation, accept first successful download
                os.rename(temp_path, full_path)
                return (
                    task["seg_idx"],
                    task["shot_idx"],
                    True,
                    f"image[google]: {query[:30]}",
                    None,
                )

        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # All candidates failed validation — use best effort
    if best_path and os.path.exists(best_path):
        os.rename(best_path, full_path)
        return (
            task["seg_idx"],
            task["shot_idx"],
            True,
            f"image[google,unverified]: {query[:25]}",
            None,
        )

    # Fall back to Pexels
    success, error = download_image(query, full_path)
    if success:
        return (
            task["seg_idx"],
            task["shot_idx"],
            True,
            f"image[pexels]: {query[:30]}",
            None,
        )
    return (
        task["seg_idx"],
        task["shot_idx"],
        False,
        None,
        error or "All candidates failed",
    )


def _download_video_task(
    task: Dict,
    full_path: str,
    footage_dir: str,
    use_google: bool,
    validate: bool,
    max_candidates: int,
) -> Tuple[int, Optional[int], bool, Optional[str], Optional[str]]:
    """Download a YouTube video with optional Google search and Gemini validation."""
    query = task["query"] or task["visual"]
    if not query:
        return task["seg_idx"], task["shot_idx"], False, None, "No footage query"

    label = task.get("visual", query[:40])
    visual = task["visual"]
    footage_start = task.get("footage_start", 5)

    # Build candidate list
    candidates = []

    if use_google:
        try:
            from src.google_image_search import search_google_for_youtube

            results = search_google_for_youtube(query, max_results=max_candidates)
            for r in results:
                candidates.append(
                    {
                        "id": r["video_id"],
                        "title": r["title"],
                        "source": "google",
                    }
                )
        except Exception:
            pass

    # Add yt-dlp results (primary or fallback)
    yt_videos = search_youtube_enhanced(
        query, max_results=max_candidates, visual=visual
    )
    if not yt_videos:
        yt_videos = search_youtube(query, max_results=3)
    for v in yt_videos:
        if v["id"] not in [c["id"] for c in candidates]:
            candidates.append(
                {
                    "id": v["id"],
                    "title": v.get("title", ""),
                    "source": "ytsearch",
                }
            )

    if not candidates:
        return task["seg_idx"], task["shot_idx"], False, None, "No search results"

    if not validate:
        # Without validation, download first candidate (existing behavior)
        top = candidates[0]
        success, error = download_video(top["id"], full_path)
        if success:
            return (
                task["seg_idx"],
                task["shot_idx"],
                True,
                top.get("title", "")[:50],
                None,
            )
        return task["seg_idx"], task["shot_idx"], False, None, error

    # With validation: validate thumbnails first (fast), then download winner
    best_candidate = None
    best_conf = 0.0

    for i, candidate in enumerate(candidates[:max_candidates]):
        source = candidate.get("source", "")

        # Validate via YouTube thumbnail (instant — no video download needed)
        is_match, conf, reason = _validate_thumbnail(candidate["id"], label, query)

        if is_match:
            safe_print(
                f"  [Thumbnail] Candidate {i} ({source}) MATCH ({conf:.1f}): {reason[:40]}"
            )
            # Thumbnail matched — download the full video
            success, error = download_video(candidate["id"], full_path)
            if success:
                title = candidate.get("title", "")[:40]
                return (
                    task["seg_idx"],
                    task["shot_idx"],
                    True,
                    f"{title}[{source},validated]",
                    None,
                )
            # Full download failed — try next candidate
            continue
        else:
            safe_print(
                f"  [Thumbnail] Candidate {i} ({source}) MISMATCH ({conf:.1f}): {reason[:40]}"
            )
            if conf > best_conf:
                best_candidate = candidate
                best_conf = conf

    # All candidates failed thumbnail validation — download best effort
    if best_candidate:
        success, error = download_video(best_candidate["id"], full_path)
        if success:
            best_title = best_candidate.get("title", "")[:40]
            return (
                task["seg_idx"],
                task["shot_idx"],
                True,
                f"{best_title}[unverified]",
                None,
            )

    return (
        task["seg_idx"],
        task["shot_idx"],
        False,
        None,
        "All candidates failed validation",
    )


def _validate_thumbnail(
    video_id: str, label: str, query: str
) -> Tuple[bool, float, str]:
    """Validate a YouTube video by its thumbnail (instant, no download needed).

    Downloads the YouTube thumbnail image and validates with Gemini vision.
    Much faster than downloading the full video for validation.
    Returns (is_match, confidence, reason).
    """
    import tempfile

    # YouTube thumbnail URLs in order of quality
    thumb_urls = [
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    ]

    thumb_path = None
    try:
        for url in thumb_urls:
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        data = resp.read()
                        if len(data) > 1000:  # Skip placeholder thumbnails
                            thumb_path = tempfile.mktemp(suffix=".jpg")
                            with open(thumb_path, "wb") as f:
                                f.write(data)
                            break
            except Exception:
                continue

        if not thumb_path:
            return True, 0.5, "No thumbnail available"

        from src.gemini_vision_validator import validate_shot

        return validate_shot(thumb_path, label, query, footage_start=0)
    except Exception as e:
        return True, 0.5, f"Thumbnail validation error: {e}"
    finally:
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except OSError:
                pass


def _validate_file(
    file_path: str, label: str, query: str, footage_start: float = 5.0
) -> Tuple[bool, float, str]:
    """Validate a file with Gemini vision. Returns (is_match, confidence, reason)."""
    try:
        from src.gemini_vision_validator import validate_shot

        return validate_shot(file_path, label, query, footage_start)
    except Exception as e:
        # If validator unavailable, skip validation (accept file)
        return True, 0.5, f"Validator error: {e}"


def safe_print(msg: str):
    """Thread-safe printing"""
    with print_lock:
        print(msg, flush=True)


def _update_script_footage(segments, seg_idx, shot_idx, footage_file, title):
    """Update a segment or shot in the script with downloaded footage info."""
    seg = segments[seg_idx]
    if shot_idx is not None and "shots" in seg:
        seg["shots"][shot_idx]["footage"] = footage_file
        if title and not title.startswith("image:"):
            seg["shots"][shot_idx]["footage_title"] = title
    else:
        seg["footage"] = footage_file
        if title and not title.startswith("image:"):
            seg["footage_title"] = title


def main():
    parser = argparse.ArgumentParser(description="Download footage from YouTube")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--segment", type=int, help="Segment ID to download for")
    parser.add_argument(
        "--shot", type=int, help="Shot index within segment (use with --segment)"
    )
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
    parser.add_argument(
        "--4k",
        action="store_true",
        dest="use_4k",
        help="Download 4K resolution (up to 2160p) instead of HD (1080p)",
    )
    parser.add_argument(
        "--google-search",
        action="store_true",
        dest="google_search",
        help="Use Google search for better YouTube/image results",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate footage with Gemini vision after download",
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
            seg_norm = normalize_segment(dict(seg))  # Don't mutate original
            shots = seg_norm.get("shots", [])
            has_multi_shots = "shots" in seg and len(seg.get("shots", [])) > 1

            if has_multi_shots:
                # Multi-shot segment: show per-shot status
                total_shots = len(shots)
                ok_count = 0
                for shot_idx, shot in enumerate(shots):
                    source_type = shot.get("source_type", "youtube_clip")
                    if source_type not in ("youtube_clip", "image"):
                        ok_count += 1  # Non-downloadable shots are always "OK"
                        continue
                    ext = get_shot_source_ext(source_type)
                    footage_file = shot.get(
                        "footage", shot_footage_filename(i, shot_idx, ext)
                    )
                    if os.path.exists(os.path.join(footage_dir, footage_file)):
                        ok_count += 1

                seg_status = (
                    "OK" if ok_count == total_shots else f"{ok_count}/{total_shots}"
                )
                print(f"[{i}] {seg_status:7} | {seg['context']} ({total_shots} shots)")

                for shot_idx, shot in enumerate(shots):
                    source_type = shot.get("source_type", "youtube_clip")
                    ext = get_shot_source_ext(source_type)
                    footage_file = shot.get(
                        "footage", shot_footage_filename(i, shot_idx, ext)
                    )
                    exists = os.path.exists(os.path.join(footage_dir, footage_file))

                    if source_type not in ("youtube_clip", "image"):
                        shot_status = "SKIP"
                    elif exists:
                        shot_status = "OK"
                    else:
                        shot_status = "MISS"

                    label = shot.get("label", f"Shot {shot_idx}")[:45]
                    print(
                        f"    Shot {shot_idx}: {shot_status:4} {footage_file} - {label} [{source_type}]"
                    )
            else:
                # Legacy single-shot segment
                footage_file = (
                    f"{footage_dir}/{seg.get('footage', f'segment_{i:02d}.mp4')}"
                )
                status = "OK" if os.path.exists(footage_file) else "MISSING"
                print(f"[{i}] {status:7} | {seg['context']}")
                if "footage_title" in seg:
                    print(f"    Title: {seg['footage_title'][:60]}")

            print(f"    Text: {seg['text'][:50]}...")
            if seg.get("visual"):
                print(f"    Visual: {seg['visual'][:60]}")
            if not has_multi_shots and "footage_query" in seg:
                print(f"    Query: {seg['footage_query']}")
            print()
        return

    if args.segment is not None:
        segment = segments[args.segment]

        # Determine output file based on --shot flag
        if args.shot is not None:
            seg_norm = normalize_segment(dict(segment))
            shots = seg_norm.get("shots", [])
            if args.shot >= len(shots):
                print(
                    f"Error: Shot {args.shot} does not exist (segment has {len(shots)} shots)"
                )
                sys.exit(1)
            shot = shots[args.shot]
            source_type = shot.get("source_type", "youtube_clip")
            ext = get_shot_source_ext(source_type)
            output_file = f"{footage_dir}/{shot.get('footage', shot_footage_filename(args.segment, args.shot, ext))}"
        else:
            output_file = f"{footage_dir}/segment_{args.segment:02d}.mp4"

        if args.url:
            # Direct URL download
            video_id = args.url.split("v=")[-1].split("&")[0]
            print(f"Downloading from URL: {args.url} ({'4K' if args.use_4k else 'HD'})")
            success, error = download_video(video_id, output_file, use_4k=args.use_4k)
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
                if args.shot is not None and "shots" in segment:
                    segment["shots"][args.shot]["footage"] = os.path.basename(
                        output_file
                    )
                    if video_title:
                        segment["shots"][args.shot]["footage_title"] = video_title
                else:
                    segment["footage"] = f"segment_{args.segment:02d}.mp4"
                    if video_title:
                        segment["footage_title"] = video_title
                if video_title:
                    print(f"Title: {video_title}")
                with open(script_file, "w") as f:
                    json.dump(script, f, indent=2)
            else:
                print(f"Download failed: {error}")
        else:
            # Search with enhanced ranking
            if args.shot is not None:
                seg_norm = normalize_segment(dict(segment))
                shot = seg_norm["shots"][args.shot]
                query = args.query or shot.get(
                    "footage_query", shot.get("image_query", "")
                )
                visual = shot.get("label", "")
            else:
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
                print(
                    f"\nDownloading top result ({'4K' if args.use_4k else 'HD'}): {top['title'][:60]}..."
                )
                if os.path.exists(output_file):
                    os.remove(output_file)
                success, error = download_video(
                    top["id"], output_file, use_4k=args.use_4k
                )
                if success:
                    print(f"Saved to: {output_file}")
                    if args.shot is not None and "shots" in segment:
                        segment["shots"][args.shot]["footage"] = os.path.basename(
                            output_file
                        )
                        segment["shots"][args.shot]["footage_title"] = top["title"]
                    else:
                        segment["footage"] = f"segment_{args.segment:02d}.mp4"
                        segment["footage_title"] = top["title"]
                    with open(script_file, "w") as f:
                        json.dump(script, f, indent=2)
                else:
                    print(f"Download failed: {error}")
                    shot_flag = f" --shot {args.shot}" if args.shot is not None else ""
                    print("\nTo try a different video:")
                    print(
                        f"  python3 src/footage_downloader.py --project {args.project} --segment {args.segment}{shot_flag} --url https://youtube.com/watch?v=VIDEO_ID"
                    )
            else:
                print("\nNo candidates found. Try a different --query.")
    else:
        # Download all missing footage (supports multi-shot segments)
        print("=" * 60)
        print(f"Downloading All Footage - Project: {args.project}")
        print(f"Resolution: {'4K (2160p)' if args.use_4k else 'HD (1080p)'}")
        # Force sequential mode when validating (Gemini rate limits)
        if getattr(args, "validate", False) and not args.sequential:
            args.sequential = True
            print("Concurrency: Sequential (required for --validate)")
        else:
            print(
                f"Concurrency: {'Sequential' if args.sequential else f'{args.workers} workers'}"
            )
        print("=" * 60)

        # Build download tasks from segments (respects shot lists)
        dl_tasks = get_download_tasks(segments, footage_dir)

        # Inject validation and search flags into each task
        for task in dl_tasks:
            task["use_google"] = getattr(args, "google_search", False)
            task["validate"] = getattr(args, "validate", False)

        features = []
        if getattr(args, "google_search", False):
            features.append("Google Search")
        if getattr(args, "validate", False):
            features.append("Gemini Validation")
        if features:
            print(f"Features: {', '.join(features)}")

        print(
            f"\n{len(dl_tasks)} download tasks ({sum(1 for t in dl_tasks if t['shot_idx'] is not None)} shots, "
            f"{sum(1 for t in dl_tasks if t['shot_idx'] is None)} legacy segments)\n"
        )

        downloaded = 0
        cached = 0
        failed = 0

        if args.sequential:
            for task in dl_tasks:
                seg_idx = task["seg_idx"]
                shot_idx = task["shot_idx"]
                label = task["visual"] or segments[seg_idx].get("context", "")
                shot_str = f" shot {shot_idx}" if shot_idx is not None else ""
                print(
                    f"[{seg_idx}{shot_str}] Processing: {label}...", end=" ", flush=True
                )

                seg_idx, shot_idx, success, title, error = download_task(
                    (task, footage_dir)
                )
                if title == "cached":
                    print("Cached")
                    cached += 1
                elif success:
                    print(f"Done - {title}")
                    downloaded += 1
                    # Update script with downloaded filename
                    _update_script_footage(
                        segments, seg_idx, shot_idx, task["footage_file"], title
                    )
                else:
                    print(f"Failed: {error}")
                    failed += 1
        else:
            print(f"Downloading {len(dl_tasks)} items concurrently...\n")

            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                future_to_task = {
                    executor.submit(download_task, (task, footage_dir)): task
                    for task in dl_tasks
                }

                for future in as_completed(future_to_task):
                    seg_idx, shot_idx, success, title, error = future.result()
                    task = future_to_task[future]
                    label = task["visual"] or segments[seg_idx].get("context", "")
                    shot_str = f" shot {shot_idx}" if shot_idx is not None else ""

                    if title == "cached":
                        safe_print(f"[{seg_idx}{shot_str}] Cached: {label}")
                        cached += 1
                    elif success:
                        safe_print(
                            f"[{seg_idx}{shot_str}] Downloaded: {label} -> {title}"
                        )
                        downloaded += 1
                        _update_script_footage(
                            segments, seg_idx, shot_idx, task["footage_file"], title
                        )
                    else:
                        safe_print(f"[{seg_idx}{shot_str}] Failed: {label} - {error}")
                        failed += 1

        # Check for duplicate video downloads (across all shots and segments)
        title_to_items = {}
        for task in dl_tasks:
            seg = segments[task["seg_idx"]]
            if task["shot_idx"] is not None and "shots" in seg:
                shot = seg["shots"][task["shot_idx"]]
                title = shot.get("footage_title", "")
            else:
                title = seg.get("footage_title", "")
            if title and title != "cached" and not title.startswith("image:"):
                key = f"[{task['seg_idx']}]" + (
                    f" shot {task['shot_idx']}" if task["shot_idx"] is not None else ""
                )
                title_to_items.setdefault(title, []).append(key)
        duplicates = {t: items for t, items in title_to_items.items() if len(items) > 1}
        if duplicates:
            print(f"\n{'!' * 60}")
            print("WARNING: Duplicate videos detected!")
            for title, items in duplicates.items():
                item_list = ", ".join(items)
                print(f"  {item_list} share: {title}")
            print(
                "Consider using --segment N --shot M --query to find different footage"
            )
            print(f"{'!' * 60}")

        # Save updated script
        with open(script_file, "w") as f:
            json.dump(script, f, indent=2)

        print(f"\n{'=' * 60}")
        print(f"Downloaded: {downloaded} | Cached: {cached} | Failed: {failed}")


if __name__ == "__main__":
    main()
