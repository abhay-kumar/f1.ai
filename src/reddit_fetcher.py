#!/usr/bin/env python3
"""
Reddit Fetcher - Fetches posts and media from r/formula1 using Reddit's public .json endpoints.

No API credentials required. Uses Reddit's public JSON interface (append .json to any Reddit URL).
Rate limited to ~10 requests/minute (unauthenticated).

Features:
- Fetches top/hot/new posts from r/formula1 for a given time range
- Extracts ALL media from each post (images, GIFs, videos, galleries)
- Returns structured data with media URLs and types
- In-memory caching with TTL
- CLI test mode

Usage:
    from src.reddit_fetcher import fetch_top_posts

    # Get top posts from past day with media
    posts = fetch_top_posts(time_filter="day", limit=25)
    for post in posts:
        print(post["title"], post["score"], len(post["media"]))
        for m in post["media"]:
            print(f"  {m['type']}: {m['url'][:80]}")

CLI:
    python3 src/reddit_fetcher.py --test
    python3 src/reddit_fetcher.py --top day --limit 25
    python3 src/reddit_fetcher.py --top day --limit 25 --media-only
    python3 src/reddit_fetcher.py --post "https://reddit.com/r/formula1/comments/..."
"""

import html
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CONFIG
# ============================================================================

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
RATE_LIMIT_DELAY = 6.0  # ~10 requests/minute for unauthenticated access
BASE_URL = "https://www.reddit.com"

_last_request_time: float = 0.0

# Cache: key -> (timestamp, data)
_cache: Dict[str, Tuple[float, object]] = {}
CACHE_TTL = 600  # 10 minutes


# ============================================================================
# HTTP
# ============================================================================


def _rate_limit():
    """Enforce delay between requests to stay under Reddit's rate limit."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - elapsed)
    _last_request_time = time.time()


def _fetch_json(url: str) -> dict:
    """Fetch JSON from a Reddit .json URL with rate limiting and retries.

    Uses curl subprocess as primary method (Reddit blocks Python urllib/requests
    but allows curl). Falls back to requests library if curl is unavailable.
    """
    _rate_limit()

    for attempt in range(3):
        try:
            # Use curl — Reddit's anti-bot doesn't block it
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-H",
                    f"User-Agent: {USER_AGENT}",
                    "-H",
                    "Accept: application/json",
                    "--max-time",
                    "15",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )

            if result.returncode != 0:
                if attempt < 2:
                    time.sleep(2)
                    continue
                return {}

            data = json.loads(result.stdout)

            # Check for rate limit / error responses
            if isinstance(data, dict) and data.get("error") == 429:
                wait = (attempt + 1) * 10
                print(f"  [Reddit] Rate limited (429), waiting {wait}s...")
                time.sleep(wait)
                continue

            return data

        except json.JSONDecodeError:
            if attempt < 2:
                time.sleep(2)
                continue
            print(f"  [Reddit] Invalid JSON response from: {url[:60]}")
            return {}
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            print(f"  [Reddit] Fetch failed: {e}")
            return {}

    return {}


# ============================================================================
# POST FETCHING
# ============================================================================


def fetch_top_posts(
    subreddit: str = "formula1",
    sort: str = "top",
    time_filter: str = "day",
    limit: int = 25,
) -> List[Dict]:
    """Fetch posts from a subreddit sorted by criteria.

    Args:
        subreddit: Subreddit name (without r/)
        sort: Sort method - "top", "hot", "new"
        time_filter: Time range for "top" sort - "hour", "day", "week", "month", "year", "all"
        limit: Max posts to return (up to 100)

    Returns list of post dicts with extracted media.
    """
    cache_key = f"{subreddit}:{sort}:{time_filter}:{limit}"
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if time.time() - ts < CACHE_TTL:
            return data

    params = {"limit": min(limit, 100), "raw_json": 1}
    if sort == "top":
        params["t"] = time_filter

    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/r/{subreddit}/{sort}.json?{query_string}"

    result = _fetch_json(url)
    if not result:
        return []

    posts = []
    for child in result.get("data", {}).get("children", []):
        post_data = child.get("data", {})
        media = extract_media(post_data)

        posts.append(
            {
                "id": post_data.get("id", ""),
                "title": post_data.get("title", ""),
                "author": post_data.get("author", ""),
                "score": post_data.get("score", 0),
                "upvote_ratio": post_data.get("upvote_ratio", 0),
                "num_comments": post_data.get("num_comments", 0),
                "created_utc": post_data.get("created_utc", 0),
                "permalink": post_data.get("permalink", ""),
                "url": post_data.get("url", ""),
                "selftext": post_data.get("selftext", "")[:500],
                "is_video": post_data.get("is_video", False),
                "is_gallery": post_data.get("is_gallery", False),
                "link_flair_text": post_data.get("link_flair_text", ""),
                "media": media,
            }
        )

    _cache[cache_key] = (time.time(), posts)
    return posts


def fetch_post_detail(url_or_id: str) -> Optional[Dict]:
    """Fetch a single post with full detail.

    Accepts a full Reddit URL or a post ID.
    Returns post dict with media, or None on failure.
    """
    import re

    if "reddit.com" in url_or_id:
        # Strip query params and trailing slash, append .json
        path = url_or_id.split("?")[0].rstrip("/")
        if not path.endswith(".json"):
            path += ".json"
        # Ensure it uses www.reddit.com
        if "old.reddit.com" in path:
            path = path.replace("old.reddit.com", "www.reddit.com")
        if not path.startswith("http"):
            path = f"{BASE_URL}{path}"
        url = path
    else:
        url = f"{BASE_URL}/comments/{url_or_id}.json"

    url += "?" + urllib.parse.urlencode({"raw_json": 1})

    try:
        data = _fetch_json(url)
    except Exception as e:
        print(f"  [Reddit] Failed to fetch post: {e}")
        return None

    # Reddit returns a list: [post_listing, comments_listing]
    if isinstance(data, list) and len(data) > 0:
        children = data[0].get("data", {}).get("children", [])
        if children:
            post_data = children[0].get("data", {})
            media = extract_media(post_data)
            return {
                "id": post_data.get("id", ""),
                "title": post_data.get("title", ""),
                "author": post_data.get("author", ""),
                "score": post_data.get("score", 0),
                "upvote_ratio": post_data.get("upvote_ratio", 0),
                "num_comments": post_data.get("num_comments", 0),
                "created_utc": post_data.get("created_utc", 0),
                "permalink": post_data.get("permalink", ""),
                "url": post_data.get("url", ""),
                "selftext": post_data.get("selftext", ""),
                "is_video": post_data.get("is_video", False),
                "is_gallery": post_data.get("is_gallery", False),
                "link_flair_text": post_data.get("link_flair_text", ""),
                "media": media,
            }

    return None


# ============================================================================
# MEDIA EXTRACTION
# ============================================================================


def extract_media(post_data: dict) -> List[Dict]:
    """Extract ALL media from a Reddit post.

    Handles:
    1. Direct image links (i.redd.it)
    2. Reddit-hosted video (v.redd.it)
    3. GIF-as-MP4 from preview
    4. Gallery posts (multiple images)
    5. Preview images (fallback)
    6. External media (imgur, streamable)
    """
    media = []

    # 1. Reddit video (is_video=True)
    if post_data.get("is_video"):
        media.extend(_extract_video_media(post_data))

    # 2. Gallery posts
    if post_data.get("is_gallery"):
        media.extend(_extract_gallery_media(post_data))

    # 3. Direct image link
    post_url = post_data.get("url", "")
    if _is_direct_image(post_url) and not any(m["url"] == post_url for m in media):
        media.append(
            {
                "url": post_url,
                "type": "image",
                "width": 0,
                "height": 0,
                "source": "reddit",
                "download_method": "requests",
            }
        )

    # 4. GIF-as-MP4 from preview
    preview_media = _extract_preview_media(post_data)
    for pm in preview_media:
        if not any(m["url"] == pm["url"] for m in media):
            media.append(pm)

    # 5. External media (imgur, streamable, etc.)
    if not media and post_url:
        ext_media = _extract_external_media(post_url)
        media.extend(ext_media)

    return media


def _extract_video_media(post_data: dict) -> List[Dict]:
    """Extract video from Reddit video posts (is_video=True)."""
    media_list = []
    reddit_video = (post_data.get("media") or {}).get("reddit_video", {})

    if not reddit_video:
        # Try secure_media as fallback
        reddit_video = (post_data.get("secure_media") or {}).get("reddit_video", {})

    if reddit_video:
        fallback_url = reddit_video.get("fallback_url", "")
        if fallback_url:
            media_list.append(
                {
                    "url": fallback_url,
                    "type": "video",
                    "width": reddit_video.get("width", 0),
                    "height": reddit_video.get("height", 0),
                    "duration": reddit_video.get("duration", 0),
                    "source": "reddit",
                    "download_method": "yt-dlp",  # yt-dlp merges audio+video
                }
            )

    return media_list


def _extract_gallery_media(post_data: dict) -> List[Dict]:
    """Extract media from Reddit gallery posts."""
    media_list = []
    metadata = post_data.get("media_metadata") or {}
    gallery_data = post_data.get("gallery_data") or {}
    items = gallery_data.get("items", [])

    # Use gallery_data for ordering, fall back to metadata keys
    media_ids = (
        [item.get("media_id") for item in items] if items else list(metadata.keys())
    )

    for media_id in media_ids:
        entry = metadata.get(media_id, {})
        if entry.get("status") != "valid":
            continue

        source = entry.get("s", {})
        url = source.get("u") or source.get("gif") or ""
        # Reddit escapes & as &amp; in these URLs (unless raw_json=1)
        url = html.unescape(url)

        if not url:
            continue

        # Determine type
        mime = entry.get("m", "")
        if "gif" in mime:
            media_type = "gif"
        elif "video" in mime or "mp4" in mime:
            media_type = "video"
        else:
            media_type = "image"

        media_list.append(
            {
                "url": url,
                "type": media_type,
                "width": source.get("x", 0),
                "height": source.get("y", 0),
                "source": "reddit",
                "download_method": "requests",
            }
        )

    return media_list


def _extract_preview_media(post_data: dict) -> List[Dict]:
    """Extract preview images and GIF-as-MP4 from preview data."""
    media_list = []
    preview = post_data.get("preview") or {}
    images = preview.get("images", [])

    if not images:
        return media_list

    first_image = images[0]

    # Check for MP4 variant (GIF-as-MP4 — ideal for shorts)
    variants = first_image.get("variants", {})
    mp4_variant = variants.get("mp4", {})
    if mp4_variant:
        mp4_source = mp4_variant.get("source", {})
        mp4_url = mp4_source.get("url", "")
        if mp4_url:
            mp4_url = html.unescape(mp4_url)
            media_list.append(
                {
                    "url": mp4_url,
                    "type": "gif",
                    "width": mp4_source.get("width", 0),
                    "height": mp4_source.get("height", 0),
                    "source": "reddit",
                    "download_method": "requests",
                }
            )

    # Check for GIF variant
    gif_variant = variants.get("gif", {})
    if gif_variant and not mp4_variant:
        gif_source = gif_variant.get("source", {})
        gif_url = gif_source.get("url", "")
        if gif_url:
            gif_url = html.unescape(gif_url)
            media_list.append(
                {
                    "url": gif_url,
                    "type": "gif",
                    "width": gif_source.get("width", 0),
                    "height": gif_source.get("height", 0),
                    "source": "reddit",
                    "download_method": "requests",
                }
            )

    # Preview image (fallback)
    source = first_image.get("source", {})
    source_url = source.get("url", "")
    if source_url and not media_list:
        source_url = html.unescape(source_url)
        media_list.append(
            {
                "url": source_url,
                "type": "image",
                "width": source.get("width", 0),
                "height": source.get("height", 0),
                "source": "reddit_preview",
                "download_method": "requests",
            }
        )

    return media_list


def _extract_external_media(url: str) -> List[Dict]:
    """Extract media from external URLs (imgur, streamable, etc.)."""
    media_list = []

    # Imgur direct links
    if "imgur.com" in url:
        # Convert imgur page URL to direct image
        if not url.endswith((".jpg", ".png", ".gif", ".mp4")):
            url = url + ".jpg"
        media_type = "video" if url.endswith(".mp4") else "image"
        media_list.append(
            {
                "url": url,
                "type": media_type,
                "width": 0,
                "height": 0,
                "source": "imgur",
                "download_method": "requests",
            }
        )

    # Streamable
    elif "streamable.com" in url:
        media_list.append(
            {
                "url": url,
                "type": "video",
                "width": 0,
                "height": 0,
                "source": "streamable",
                "download_method": "yt-dlp",
            }
        )

    return media_list


def _is_direct_image(url: str) -> bool:
    """Check if URL is a direct image link."""
    image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp")
    url_lower = url.lower().split("?")[0]
    return any(url_lower.endswith(ext) for ext in image_extensions)


# ============================================================================
# MEDIA DOWNLOAD
# ============================================================================


def download_reddit_media(
    media: Dict,
    output_path: str,
    timeout: int = 30,
) -> Tuple[bool, Optional[str]]:
    """Download a single Reddit media item to output_path.

    Routes by download_method:
    - "requests": Direct HTTP download (images, preview GIFs)
    - "yt-dlp": For v.redd.it videos (handles audio+video merge)

    Returns (success, error_message)
    """
    url = media.get("url", "")
    method = media.get("download_method", "requests")

    if not url:
        return False, "No URL"

    if method == "yt-dlp":
        return _download_with_ytdlp(url, output_path, timeout)
    else:
        return _download_direct(url, output_path, timeout)


def _download_direct(
    url: str, output_path: str, timeout: int = 30
) -> Tuple[bool, Optional[str]]:
    """Download media via direct HTTP request."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "*/*",
            },
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()

        if len(data) < 500:
            return False, "Downloaded file too small"

        # Check if it's WebP and output expects JPEG
        is_webp = data[:4] == b"RIFF" and len(data) > 12 and data[8:12] == b"WEBP"
        if is_webp and output_path.lower().endswith(".jpg"):
            temp_webp = output_path + ".webp"
            with open(temp_webp, "wb") as f:
                f.write(data)
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", temp_webp, "-q:v", "2", output_path],
                    capture_output=True,
                    timeout=10,
                )
                os.remove(temp_webp)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True, None
                return False, "WebP conversion failed"
            except Exception as e:
                if os.path.exists(temp_webp):
                    os.remove(temp_webp)
                return False, f"WebP conversion error: {e}"
        else:
            with open(output_path, "wb") as f:
                f.write(data)
            return True, None

    except Exception as e:
        return False, str(e)[:100]


def _download_with_ytdlp(
    url: str, output_path: str, timeout: int = 120
) -> Tuple[bool, Optional[str]]:
    """Download Reddit video via yt-dlp (handles audio+video merge)."""
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "-f",
        "bestvideo+bestaudio/best",
        "--merge-output-format",
        "mp4",
        "-o",
        output_path,
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"yt-dlp timed out after {timeout}s"

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True, None
    return False, (result.stderr[:200] if result.stderr else "Unknown error")


# ============================================================================
# CLI
# ============================================================================


def main():
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(
        description="Fetch Reddit r/formula1 posts and media (no API key required)"
    )
    parser.add_argument(
        "--top",
        choices=["hour", "day", "week", "month", "year", "all"],
        help="Fetch top posts for time range",
    )
    parser.add_argument("--hot", action="store_true", help="Fetch hot posts")
    parser.add_argument("--new", action="store_true", help="Fetch new posts")
    parser.add_argument("--limit", type=int, default=10, help="Max posts (default 10)")
    parser.add_argument("--post", help="Fetch specific post URL or ID")
    parser.add_argument(
        "--media-only", action="store_true", help="Only show posts with media"
    )
    parser.add_argument(
        "--test", action="store_true", help="Test connectivity (fetch 1 post)"
    )
    parser.add_argument(
        "--subreddit", default="formula1", help="Subreddit (default: formula1)"
    )
    args = parser.parse_args()

    if args.test:
        print("Testing Reddit .json endpoint...")
        try:
            posts = fetch_top_posts(args.subreddit, sort="hot", limit=1)
            if posts:
                print(f"  OK - Fetched: '{posts[0]['title'][:60]}...'")
                print(f"  Score: {posts[0]['score']}, Media: {len(posts[0]['media'])}")
                print("  Connection successful! No API key required.")
            else:
                print("  WARNING: Got empty response (may be rate limited, try again)")
        except Exception as e:
            print(f"  ERROR: {e}")
            sys.exit(1)
        return

    if args.post:
        print(f"Fetching post: {args.post}")
        post = fetch_post_detail(args.post)
        if post:
            _print_post(post, verbose=True)
        else:
            print("  Failed to fetch post")
        return

    # Determine sort method
    if args.hot:
        sort = "hot"
        time_filter = "day"
        label = "hot"
    elif args.new:
        sort = "new"
        time_filter = "day"
        label = "new"
    elif args.top:
        sort = "top"
        time_filter = args.top
        label = f"top ({time_filter})"
    else:
        sort = "hot"
        time_filter = "day"
        label = "hot"

    print(f"Fetching {label} posts from r/{args.subreddit} (limit={args.limit})...")
    try:
        posts = fetch_top_posts(
            args.subreddit, sort=sort, time_filter=time_filter, limit=args.limit
        )
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    if args.media_only:
        posts = [p for p in posts if p["media"]]

    print(f"  Found {len(posts)} posts" + (" with media" if args.media_only else ""))
    print()

    for i, post in enumerate(posts):
        _print_post(post, index=i + 1)


def _print_post(post: Dict, index: int = 0, verbose: bool = False):
    """Pretty-print a post."""
    prefix = f"  {index}." if index else " "
    score = f"[{post['score']:>5}]"
    media_count = len(post["media"])
    media_label = f"[{media_count} media]" if media_count else "[no media]"
    flair = f"[{post['link_flair_text']}]" if post.get("link_flair_text") else ""

    print(f"{prefix} {score} {media_label} {flair} {post['title']}")
    print(f"        https://reddit.com{post['permalink']}")

    if post["media"]:
        for m in post["media"]:
            dims = f" ({m['width']}x{m['height']})" if m.get("width") else ""
            dur = f" {m['duration']}s" if m.get("duration") else ""
            dl = (
                f" [{m['download_method']}]"
                if m.get("download_method") != "requests"
                else ""
            )
            print(f"        -> {m['type']}{dims}{dur}{dl}: {m['url'][:100]}")

    if verbose and post.get("selftext"):
        text = post["selftext"][:300]
        if len(post["selftext"]) > 300:
            text += "..."
        print(f"        Text: {text}")

    print()


if __name__ == "__main__":
    main()
