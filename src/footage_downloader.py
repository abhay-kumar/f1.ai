#!/usr/bin/env python3
"""
Footage Downloader - Downloads YouTube clips for video segments
Uses yt-dlp for downloading
"""
import os
import sys
import json
import argparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_project_dir

def search_youtube(query, max_results=3):
    """Search YouTube and return video IDs with titles"""
    cmd = ["yt-dlp", "--no-warnings", f"ytsearch{max_results}:{query}", "--get-id", "--get-title"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    videos = []
    for i in range(0, len(lines), 2):
        if i+1 < len(lines):
            videos.append({"title": lines[i], "id": lines[i+1]})
    return videos

def download_video(video_id, output_path):
    """Download a YouTube video"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp", "--no-warnings",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
        "--merge-output-format", "mp4",
        "-o", output_path,
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)

def main():
    parser = argparse.ArgumentParser(description='Download footage from YouTube')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--segment', type=int, help='Segment ID to download for')
    parser.add_argument('--query', help='Custom search query')
    parser.add_argument('--url', help='Direct YouTube URL')
    parser.add_argument('--list', action='store_true', help='List all segments and their footage status')
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
            print(f"    Text: {seg['text'][:50]}...")
            if 'footage_query' in seg:
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
            if download_video(video_id, output_file):
                print(f"Saved to: {output_file}")
                # Update script with footage filename
                segment['footage'] = f"segment_{args.segment:02d}.mp4"
                with open(script_file, 'w') as f:
                    json.dump(script, f, indent=2)
            else:
                print("Download failed")
        else:
            # Search and select
            query = args.query or segment.get('footage_query', segment['text'][:50])
            print(f"Searching: {query}")
            print("-" * 40)

            videos = search_youtube(query)
            for i, v in enumerate(videos):
                print(f"[{i}] {v['title'][:60]}")

            print("\nUse --url to download a specific video")
            print(f"Example: python3 src/footage_downloader.py --project {args.project} --segment {args.segment} --url https://youtube.com/watch?v={{VIDEO_ID}}")
    else:
        # Download all missing footage
        print("=" * 60)
        print(f"Downloading All Footage - Project: {args.project}")
        print("=" * 60)

        for i, seg in enumerate(segments):
            footage_file = seg.get('footage', f'segment_{i:02d}.mp4')
            full_path = f"{footage_dir}/{footage_file}"

            if os.path.exists(full_path):
                print(f"[{i}] Cached: {seg['context']}")
                continue

            query = seg.get('footage_query', seg['text'][:50])
            print(f"[{i}] Searching: {query}...")

            videos = search_youtube(query, max_results=1)
            if videos:
                print(f"    Downloading: {videos[0]['title'][:50]}...")
                if download_video(videos[0]['id'], full_path):
                    seg['footage'] = footage_file
                    print(f"    Done")
                else:
                    print(f"    Failed")
            else:
                print(f"    No results found")

        # Save updated script
        with open(script_file, 'w') as f:
            json.dump(script, f, indent=2)

if __name__ == "__main__":
    main()
