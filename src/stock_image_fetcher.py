#!/usr/bin/env python3
"""
Stock Image Fetcher - Downloads high-quality stock images for video segments.

Uses free stock photo APIs:
- Pexels (primary - generous free tier)
- Unsplash (fallback)

Features:
- Keyword-based search with F1/motorsport context
- High-resolution landscape images (16:9 compatible)
- Local caching to avoid re-downloads
- Multiple images per segment for variety
"""

import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cache directory for downloaded images
CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "stock_images"
)


# API Keys - loaded from shared/creds
def get_api_key(name: str) -> Optional[str]:
    """Load API key from shared/creds folder."""
    creds_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "shared",
        "creds",
        name,
    )
    if os.path.exists(creds_path):
        with open(creds_path) as f:
            return f.read().strip()
    return os.environ.get(f"{name.upper()}_API_KEY")


# Search query enhancers for F1 content
F1_QUERY_MAPPINGS = {
    # Technical terms -> visual search terms
    "sustainable fuel": "green energy fuel technology",
    "e-fuel": "renewable energy hydrogen",
    "electrolysis": "water hydrogen science laboratory",
    "fischer-tropsch": "chemical plant industrial",
    "carbon capture": "industrial plant environment technology",
    "syngas": "chemical factory industrial",
    "power unit": "engine technology engineering",
    "mgu-k": "electric motor technology",
    "mgu-h": "turbocharger engine technology",
    "compression ratio": "engine piston mechanical",
    "fuel flow": "fuel technology engineering",
    "energy density": "fuel energy science",
    "aerodynamics": "wind tunnel technology",
    "downforce": "aerodynamics wind technology",
    # People/teams
    "ferrari": "red racing car motorsport",
    "mercedes": "silver racing car motorsport",
    "red bull": "racing car motorsport",
    "aston martin": "green racing car motorsport",
    "mclaren": "orange racing car motorsport",
    "f1": "formula one racing motorsport",
    "formula 1": "formula one racing motorsport",
    "pit lane": "motorsport racing pit stop",
    "barcelona": "racing circuit track motorsport",
}

# Fallback generic queries for common topics
TOPIC_FALLBACKS = {
    "technology": ["technology innovation", "futuristic technology", "engineering"],
    "science": ["science laboratory", "scientific research", "chemistry"],
    "engineering": ["engineering mechanical", "industrial technology", "machinery"],
    "environment": ["green energy", "sustainable technology", "environment nature"],
    "racing": ["motorsport racing", "race track", "speed motion"],
    "business": ["business partnership", "corporate handshake", "teamwork"],
}


def enhance_query(query: str) -> str:
    """Enhance search query with better visual search terms."""
    query_lower = query.lower()

    # Check for direct mappings
    for term, replacement in F1_QUERY_MAPPINGS.items():
        if term in query_lower:
            return replacement

    # Check for topic fallbacks
    for topic, alternatives in TOPIC_FALLBACKS.items():
        if topic in query_lower:
            return alternatives[0]

    # Clean up technical jargon
    query = query.replace("GRAPHIC:", "").replace("graphic:", "").strip()

    # Remove overly specific terms
    remove_terms = [
        "2026",
        "2025",
        "2024",
        "explained",
        "analysis",
        "overview",
        "diagram",
    ]
    for term in remove_terms:
        query = query.replace(term, "").strip()

    return query if query else "technology innovation"


def get_cache_path(query: str, index: int = 0) -> str:
    """Get cache path for a query."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
    return os.path.join(CACHE_DIR, f"{query_hash}_{index}.jpg")


def search_pexels(query: str, per_page: int = 5) -> List[Dict]:
    """
    Search Pexels for stock photos.

    Returns list of image info: [{url, photographer, width, height}, ...]
    """
    api_key = get_api_key("pexels")
    if not api_key:
        return []

    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page={per_page}&orientation=landscape"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": api_key,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            },
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())

        results = []
        for photo in data.get("photos", []):
            # Get large2x for high quality (1880px width typically)
            results.append(
                {
                    "url": photo["src"]["large2x"],
                    "photographer": photo["photographer"],
                    "width": photo["width"],
                    "height": photo["height"],
                    "source": "pexels",
                    "id": photo["id"],
                }
            )

        return results

    except Exception as e:
        print(f"  Pexels search error: {e}")
        return []


def search_unsplash(query: str, per_page: int = 5) -> List[Dict]:
    """
    Search Unsplash for stock photos.

    Returns list of image info: [{url, photographer, width, height}, ...]
    """
    api_key = get_api_key("unsplash")
    if not api_key:
        return []

    try:
        url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(query)}&per_page={per_page}&orientation=landscape"
        req = urllib.request.Request(
            url, headers={"Authorization": f"Client-ID {api_key}"}
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())

        results = []
        for photo in data.get("results", []):
            # Get regular size (1080px width)
            results.append(
                {
                    "url": photo["urls"]["regular"],
                    "photographer": photo["user"]["name"],
                    "width": photo["width"],
                    "height": photo["height"],
                    "source": "unsplash",
                    "id": photo["id"],
                }
            )

        return results

    except Exception as e:
        print(f"  Unsplash search error: {e}")
        return []


def download_image(url: str, output_path: str) -> bool:
    """Download image from URL to local path."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())

        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000

    except Exception as e:
        print(f"  Download error: {e}")
        return False


def fetch_stock_image(
    query: str, output_path: str, use_cache: bool = True
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Fetch a stock image for the given query.

    Args:
        query: Search query (will be enhanced for better results)
        output_path: Where to save the image
        use_cache: Whether to use cached images

    Returns:
        (success, image_path, attribution)
    """
    # Check cache first
    cache_path = get_cache_path(query)
    if use_cache and os.path.exists(cache_path):
        # Copy from cache
        import shutil

        shutil.copy(cache_path, output_path)
        return True, output_path, "Cached image"

    # Enhance query for better search results
    enhanced_query = enhance_query(query)
    print(f"  Searching: '{enhanced_query}'")

    # Try Pexels first (better free tier)
    results = search_pexels(enhanced_query)

    # Fallback to Unsplash
    if not results:
        results = search_unsplash(enhanced_query)

    # Try with simpler query if no results
    if not results and " " in enhanced_query:
        simple_query = enhanced_query.split()[0]
        print(f"  Retrying with: '{simple_query}'")
        results = search_pexels(simple_query)
        if not results:
            results = search_unsplash(simple_query)

    if not results:
        return False, None, "No images found"

    # Download first result
    image_info = results[0]
    print(f"  Found: {image_info['source']} by {image_info['photographer']}")

    if download_image(image_info["url"], output_path):
        # Cache the image
        if use_cache:
            import shutil

            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            shutil.copy(output_path, cache_path)

        attribution = (
            f"Photo by {image_info['photographer']} ({image_info['source'].title()})"
        )
        return True, output_path, attribution

    return False, None, "Download failed"


def fetch_multiple_images(
    query: str, output_dir: str, count: int = 3
) -> List[Tuple[str, str]]:
    """
    Fetch multiple images for a query (for variety/transitions).

    Returns list of (image_path, attribution) tuples.
    """
    enhanced_query = enhance_query(query)

    # Search both APIs
    results = search_pexels(enhanced_query, per_page=count)
    if len(results) < count:
        results.extend(search_unsplash(enhanced_query, per_page=count - len(results)))

    downloaded = []
    for i, image_info in enumerate(results[:count]):
        output_path = os.path.join(output_dir, f"image_{i:02d}.jpg")
        if download_image(image_info["url"], output_path):
            attribution = f"Photo by {image_info['photographer']} ({image_info['source'].title()})"
            downloaded.append((output_path, attribution))

    return downloaded


# Person image database for quotes
PERSON_IMAGES = {
    # F1 Team Principals
    "christian horner": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Christian_Horner_2022.jpg/440px-Christian_Horner_2022.jpg",
    "toto wolff": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Toto_Wolff_2018.jpg/440px-Toto_Wolff_2018.jpg",
    "fred vasseur": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Fred_Vasseur_2023.jpg/440px-Fred_Vasseur_2023.jpg",
    "andrea stella": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Andrea_Stella_2023.jpg/440px-Andrea_Stella_2023.jpg",
    # F1 Drivers
    "lewis hamilton": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Lewis_Hamilton_2016_Malaysia_2.jpg/440px-Lewis_Hamilton_2016_Malaysia_2.jpg",
    "max verstappen": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Max_Verstappen_2017_Malaysia_3.jpg/440px-Max_Verstappen_2017_Malaysia_3.jpg",
    "charles leclerc": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Charles_Leclerc_2018.jpg/440px-Charles_Leclerc_2018.jpg",
    "lando norris": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Lando_Norris_2019.jpg/440px-Lando_Norris_2019.jpg",
    # F1 Team Principals (additional)
    "mike krack": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Mike_Krack_2022.jpg/440px-Mike_Krack_2022.jpg",
    "james vowles": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/James_Vowles_2023.jpg/440px-James_Vowles_2023.jpg",
    "ayao komatsu": "generic_executive",
    "laurent mekies": "generic_executive",
    # F1 Drivers (additional)
    "fernando alonso": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Fernando_Alonso_2016_Malaysia_2.jpg/440px-Fernando_Alonso_2016_Malaysia_2.jpg",
    "romain grosjean": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Romain_Grosjean_2019.jpg/440px-Romain_Grosjean_2019.jpg",
    "heinz-harald frentzen": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Heinz-Harald_Frentzen_2006.jpg/440px-Heinz-Harald_Frentzen_2006.jpg",
    # F1 Technical/Officials
    "pat symonds": "generic_executive",
    "stefano domenicali": "generic_executive",
    "mohammed ben sulayem": "generic_executive",
    "pierre waché": "generic_executive",
    "sultan bin sulayem": "generic_executive",
    "pierre wache": "generic_executive",
    # Company executives
    "toshihiro mibe": "generic_executive",
    "pierre-olivier calendini": "generic_executive",
}


def get_person_image(
    name: str, output_path: str, use_google: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Get image of a person for quote overlays.

    Priority: PERSON_IMAGES dict -> Google Images -> Pexels -> silhouette

    Returns (success, image_path)
    """
    name_lower = name.lower()

    # Check if we have a direct URL
    if name_lower in PERSON_IMAGES:
        url = PERSON_IMAGES[name_lower]

        if url == "generic_executive":
            # Try Google Images first for generic executives
            if use_google:
                try:
                    from src.google_image_search import (
                        download_image_url,
                        search_google_images,
                    )

                    results = search_google_images(
                        f"{name} portrait photo", max_results=3
                    )
                    for r in results:
                        success, err = download_image_url(r["url"], output_path)
                        if success and os.path.getsize(output_path) > 5000:
                            return True, output_path
                except Exception:
                    pass

            # Fallback to stock photo silhouette
            return fetch_stock_image(
                "business executive portrait silhouette",
                output_path,
                use_cache=True,
            )[:2]

        # Download the Wikipedia image
        if download_image(url, output_path):
            return True, output_path

    # Try Google Images for people not in the dict
    if use_google:
        try:
            from src.google_image_search import (
                download_image_url,
                search_google_images,
            )

            results = search_google_images(f"{name} portrait photo", max_results=3)
            for r in results:
                success, err = download_image_url(r["url"], output_path)
                if success and os.path.getsize(output_path) > 5000:
                    return True, output_path
        except Exception:
            pass

    # Fallback: search Pexels for the person
    success, path, _ = fetch_stock_image(
        f"{name} portrait", output_path, use_cache=True
    )
    if success:
        return True, path

    # Ultimate fallback: generic silhouette
    return fetch_stock_image("person silhouette dark", output_path, use_cache=True)[:2]


def main():
    """CLI for testing stock image fetching."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch stock images for video segments"
    )
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--output", default="test_image.jpg", help="Output path")
    parser.add_argument("--person", help="Get person image for quote")
    parser.add_argument("--test", action="store_true", help="Test API connectivity")
    args = parser.parse_args()

    if args.test:
        print("Testing API connectivity...")

        pexels_key = get_api_key("pexels")
        print(f"Pexels API key: {'Found' if pexels_key else 'Not found'}")

        unsplash_key = get_api_key("unsplash")
        print(f"Unsplash API key: {'Found' if unsplash_key else 'Not found'}")

        if pexels_key:
            results = search_pexels("formula 1 racing", per_page=1)
            print(f"Pexels test search: {'Success' if results else 'Failed'}")

        if unsplash_key:
            results = search_unsplash("racing car", per_page=1)
            print(f"Unsplash test search: {'Success' if results else 'Failed'}")

        return

    if args.person:
        success, path = get_person_image(args.person, args.output)
        if success:
            print(f"Downloaded person image: {path}")
        else:
            print("Failed to get person image")
        return

    if args.query:
        success, path, attribution = fetch_stock_image(args.query, args.output)
        if success:
            print(f"Downloaded: {path}")
            print(f"Attribution: {attribution}")
        else:
            print(f"Failed: {attribution}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
