#!/usr/bin/env python3
"""
Google Image Search - Scrapes Google Images and Google Search for YouTube URLs
using Playwright headless Chromium.

Provides two main search capabilities:
1. Google Images search for finding specific people, events, logos
2. Google Search with site:youtube.com for finding specific YouTube videos
   (much more accurate than yt-dlp ytsearch)

Usage:
    from src.google_image_search import search_google_images, search_google_for_youtube

    # Find images of a specific person
    results = search_google_images("Fred Vasseur Ferrari F1 team principal")

    # Find specific YouTube videos
    videos = search_google_for_youtube("Red Bull RB22 F1 2026 Bahrain testing")
"""

import atexit
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

# Lazy browser singleton
_browser = None
_playwright = None
_last_request_time = 0.0
GOOGLE_SEARCH_DELAY = 2.0  # seconds between Google requests

# Cache: query -> (timestamp, results)
_search_cache: Dict[str, Tuple[float, list]] = {}
CACHE_TTL = 3600  # 1 hour


def _get_browser():
    """Get or create a lazy singleton Playwright browser instance."""
    global _browser, _playwright

    if _browser is not None:
        try:
            # Check if browser is still alive
            _browser.contexts
            return _browser
        except Exception:
            _browser = None
            _playwright = None

    try:
        from playwright.sync_api import sync_playwright

        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        atexit.register(_cleanup_browser)
        return _browser
    except Exception as e:
        print(f"  [Google Search] Playwright launch failed: {e}")
        return None


def _cleanup_browser():
    """Cleanup browser on exit."""
    global _browser, _playwright
    try:
        if _browser:
            _browser.close()
        if _playwright:
            _playwright.stop()
    except Exception:
        pass
    _browser = None
    _playwright = None


def _rate_limit():
    """Enforce delay between Google requests."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < GOOGLE_SEARCH_DELAY:
        time.sleep(GOOGLE_SEARCH_DELAY - elapsed)
    _last_request_time = time.time()


def _check_cache(query: str) -> Optional[list]:
    """Check if cached results exist and are still fresh."""
    if query in _search_cache:
        ts, results = _search_cache[query]
        if time.time() - ts < CACHE_TTL:
            return results
    return None


def search_google_images(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search Google Images for a query using Playwright.

    Returns list of dicts: [{"url": ..., "title": ..., "source": ...}]
    Returns empty list if search fails (caller should fall through to Pexels).
    """
    cache_key = f"img:{query}"
    cached = _check_cache(cache_key)
    if cached is not None:
        return cached[:max_results]

    browser = _get_browser()
    if browser is None:
        return []

    results = []
    context = None
    try:
        _rate_limit()

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?tbm=isch&q={encoded_query}"

        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1500)  # Let images load

        if _is_captcha_page(page):
            print(f"  [Google Images] CAPTCHA detected, falling back to Pexels")
            context.close()
            context = None
            _search_cache[cache_key] = (time.time(), [])
            return []

        # Extract image URLs from Google Images results
        # Google Images stores full-res URLs in data attributes or script tags
        results = _extract_image_urls(page, max_results)

        context.close()
        context = None

    except Exception as e:
        print(f"  [Google Images] Search failed for '{query[:40]}': {e}")
        if context:
            try:
                context.close()
            except Exception:
                pass

    _search_cache[cache_key] = (time.time(), results)
    return results[:max_results]


def _extract_image_urls(page, max_results: int = 5) -> List[Dict[str, str]]:
    """Extract full-resolution image URLs from a Google Images result page.

    Google Images embeds full-res URLs in JavaScript data as [url, width, height]
    arrays. This method parses those to get actual downloadable URLs, not thumbnails.
    """
    results = []

    try:
        content = page.content()

        # Parse full-size image URLs from JS data: ["https://...jpg",width,height]
        matches = re.findall(
            r'\["(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)",(\d+),(\d+)\]',
            content,
        )

        seen_urls = set()
        for url_str, w_str, h_str in matches:
            w, h = int(w_str), int(h_str)

            # Filter: reasonably sized (not thumbnails), not Google's own images
            if w < 200 or h < 200:
                continue
            if "gstatic" in url_str or "google.com" in url_str:
                continue

            # Unescape URL encoding
            url_clean = (
                url_str.replace("\\u003d", "=")
                .replace("\\u0026", "&")
                .replace("\\\\u003d", "=")
                .replace("\\\\u0026", "&")
            )

            if url_clean in seen_urls:
                continue
            seen_urls.add(url_clean)

            # Prefer landscape images (better for video backgrounds)
            # but accept portraits too (for person shots)
            results.append(
                {
                    "url": url_clean,
                    "title": "",
                    "source": "google_images",
                    "width": w,
                    "height": h,
                }
            )

            if len(results) >= max_results * 3:
                break  # Get extra candidates for size filtering

        # Sort by resolution (largest first) and take top results
        results.sort(key=lambda r: r["width"] * r["height"], reverse=True)
        results = results[:max_results]

    except Exception as e:
        print(f"  [Google Images] URL extraction error: {e}")

    return results


def _is_captcha_page(page) -> bool:
    """Detect if Google is showing a CAPTCHA page."""
    try:
        html = page.content()[:2000].lower()
        return "captcha" in html or "recaptcha" in html or "unusual traffic" in html
    except Exception:
        return False


def search_google_for_youtube(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search Google with 'site:youtube.com' to find specific YouTube videos.
    Much more accurate than yt-dlp ytsearch for finding specific content.

    Returns list of dicts: [{"url": ..., "title": ..., "channel": ...}]
    Returns empty list if search fails (caller should fall through to ytsearch).

    Note: Google regular search triggers CAPTCHAs more readily than Images search.
    This function will return empty on CAPTCHA and let the caller use ytsearch fallback.
    """
    cache_key = f"yt:{query}"
    cached = _check_cache(cache_key)
    if cached is not None:
        return cached[:max_results]

    browser = _get_browser()
    if browser is None:
        return []

    results = []
    context = None
    try:
        _rate_limit()

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        search_query = f"site:youtube.com {query}"
        encoded_query = urllib.parse.quote(search_query)
        url = f"https://www.google.com/search?q={encoded_query}"

        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1000)

        if _is_captcha_page(page):
            print(f"  [Google→YouTube] CAPTCHA detected, falling back to ytsearch")
            context.close()
            context = None
            _search_cache[cache_key] = (time.time(), [])
            return []

        results = _extract_youtube_urls(page, max_results)

        context.close()
        context = None

    except Exception as e:
        print(f"  [Google→YouTube] Search failed for '{query[:40]}': {e}")
        if context:
            try:
                context.close()
            except Exception:
                pass

    _search_cache[cache_key] = (time.time(), results)
    return results[:max_results]


def _extract_youtube_urls(page, max_results: int = 5) -> List[Dict[str, str]]:
    """Extract YouTube video URLs from Google Search results."""
    results = []

    try:
        # Google search results have links in <a> tags within result divs
        links = page.query_selector_all("a[href*='youtube.com/watch']")

        seen_ids = set()
        for link in links:
            try:
                href = link.get_attribute("href") or ""

                # Extract YouTube video ID
                video_id_match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", href)
                if not video_id_match:
                    continue

                video_id = video_id_match.group(1)
                if video_id in seen_ids:
                    continue
                seen_ids.add(video_id)

                # Get title from the link text or parent
                title = ""
                h3 = link.query_selector("h3")
                if h3:
                    title = h3.text_content() or ""
                if not title:
                    title = link.text_content() or ""
                title = title.strip()

                # Try to get channel from the result snippet
                channel = ""
                parent = link.evaluate_handle(
                    "el => el.closest('div[data-snf]') || el.parentElement"
                )
                if parent:
                    cite = page.evaluate(
                        """el => {
                            const cite = el.querySelector('cite');
                            return cite ? cite.textContent : '';
                        }""",
                        parent,
                    )
                    if cite and "youtube.com" in cite:
                        # Extract channel from URL like youtube.com › @channel
                        channel_match = re.search(r"@([^\s›]+)", cite)
                        if channel_match:
                            channel = channel_match.group(1)

                results.append(
                    {
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "title": title[:100],
                        "channel": channel,
                        "video_id": video_id,
                    }
                )

                if len(results) >= max_results:
                    break
            except Exception:
                continue

    except Exception as e:
        print(f"  [Google→YouTube] URL extraction error: {e}")

    return results


def download_image_url(
    url: str, output_path: str, timeout: int = 15
) -> Tuple[bool, Optional[str]]:
    """
    Download an image from a URL with proper headers.
    Handles WebP -> JPEG conversion automatically.

    Returns: (success, error_message)
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Referer": "https://www.google.com/",
            },
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()

        if len(data) < 1000:
            return False, "Image too small (likely error page)"

        # Check if it's WebP and convert to JPEG
        is_webp = data[:4] == b"RIFF" and data[8:12] == b"WEBP"

        if is_webp and output_path.lower().endswith(".jpg"):
            # Write WebP to temp, convert with ffmpeg
            temp_webp = output_path + ".webp"
            with open(temp_webp, "wb") as f:
                f.write(data)

            try:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        temp_webp,
                        "-q:v",
                        "2",
                        output_path,
                    ],
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


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 src/google_image_search.py <query> [--youtube]")
        sys.exit(1)

    query = sys.argv[1]
    is_youtube = "--youtube" in sys.argv

    if is_youtube:
        print(f"Searching Google for YouTube: {query}")
        results = search_google_for_youtube(query, max_results=5)
        for i, r in enumerate(results):
            print(f"  [{i}] {r['title']}")
            print(f"      URL: {r['url']}")
            if r.get("channel"):
                print(f"      Channel: {r['channel']}")
    else:
        print(f"Searching Google Images: {query}")
        results = search_google_images(query, max_results=5)
        for i, r in enumerate(results):
            print(f"  [{i}] {r['title'][:60]}")
            print(f"      URL: {r['url'][:80]}")

    _cleanup_browser()
