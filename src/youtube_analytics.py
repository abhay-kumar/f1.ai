#!/usr/bin/env python3
"""
YouTube Analytics - Channel performance analysis and diagnostics
Uses YouTube Data API v3 + YouTube Analytics API v2

Reports:
- Channel overview (subscribers, views, watch time trends)
- Top performing videos (by views, watch time, CTR)
- Traffic sources breakdown
- Audience demographics
- Shorts vs long-form comparison
- Per-video retention analysis
- CTR diagnostics (impressions vs clicks)
"""

import argparse
import json
import os
import pickle
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import SHARED_DIR

# YouTube API imports
try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# Scopes: read-only analytics + read-only data API
SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]
CLIENT_SECRETS_FILE = f"{SHARED_DIR}/creds/youtube_client_secrets.json"
TOKEN_FILE = f"{SHARED_DIR}/creds/youtube_analytics_token.pickle"


def get_authenticated_services() -> Tuple[object, object]:
    """Authenticate and return (youtube_data, youtube_analytics) service pair."""
    credentials = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"Error: YouTube credentials not found at {CLIENT_SECRETS_FILE}")
                print("\nSetup instructions:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Enable YouTube Data API v3 AND YouTube Analytics API")
                print("3. Create OAuth 2.0 credentials (Desktop app)")
                print("4. Download and save as: shared/creds/youtube_client_secrets.json")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)

    youtube = build("youtube", "v3", credentials=credentials)
    analytics = build("youtubeAnalytics", "v2", credentials=credentials)
    return youtube, analytics


def get_channel_id(youtube) -> str:
    """Get the authenticated user's channel ID."""
    response = youtube.channels().list(part="id", mine=True).execute()
    return response["items"][0]["id"]


def get_all_video_ids(youtube) -> List[Dict]:
    """Get all uploaded video IDs with titles."""
    # Get uploads playlist ID
    response = youtube.channels().list(part="contentDetails", mine=True).execute()
    uploads_playlist = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = []
    next_page = None

    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist,
            maxResults=50,
            pageToken=next_page,
        )
        response = request.execute()

        for item in response["items"]:
            videos.append({
                "id": item["snippet"]["resourceId"]["videoId"],
                "title": item["snippet"]["title"],
                "published": item["snippet"]["publishedAt"],
            })

        next_page = response.get("nextPageToken")
        if not next_page:
            break

    return videos


def format_number(n: int) -> str:
    """Format large numbers with K/M suffixes."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def format_duration(minutes: float) -> str:
    """Format minutes into readable duration."""
    if minutes >= 60:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}m"
    return f"{minutes:.0f}m"


def format_seconds(seconds: float) -> str:
    """Format seconds into m:ss."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


# ============================================================================
# REPORTS
# ============================================================================


def report_overview(youtube, analytics, days: int = 28):
    """Channel overview: subscribers, views, watch time, engagement."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    prev_start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")
    prev_end = start_date

    # Current period
    current = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost,likes,comments,shares",
    ).execute()

    # Previous period for comparison
    previous = analytics.reports().query(
        ids="channel==MINE",
        startDate=prev_start,
        endDate=prev_end,
        metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost,likes,comments,shares",
    ).execute()

    # Channel snapshot from Data API
    channel = youtube.channels().list(part="statistics,snippet", mine=True).execute()
    ch = channel["items"][0]
    stats = ch["statistics"]
    channel_name = ch["snippet"]["title"]

    cur = current["rows"][0] if current.get("rows") else [0] * 7
    prev = previous["rows"][0] if previous.get("rows") else [0] * 7

    def delta(cur_val, prev_val):
        if prev_val == 0:
            return "+new" if cur_val > 0 else "flat"
        pct = ((cur_val - prev_val) / prev_val) * 100
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.0f}%"

    net_subs = cur[2] - cur[3]
    prev_net_subs = prev[2] - prev[3]

    print(f"\n{'=' * 60}")
    print(f"  CHANNEL OVERVIEW: {channel_name}")
    print(f"  Period: last {days} days ({start_date} to {end_date})")
    print(f"{'=' * 60}")

    print(f"\n  Total Subscribers:  {format_number(int(stats['subscriberCount']))}")
    print(f"  Total Views:        {format_number(int(stats['viewCount']))}")
    print(f"  Total Videos:       {stats['videoCount']}")

    print(f"\n  {'METRIC':<25} {'CURRENT':>10} {'PREVIOUS':>10} {'CHANGE':>10}")
    print(f"  {'-' * 55}")
    print(f"  {'Views':<25} {format_number(int(cur[0])):>10} {format_number(int(prev[0])):>10} {delta(cur[0], prev[0]):>10}")
    print(f"  {'Watch Time':<25} {format_duration(cur[1]):>10} {format_duration(prev[1]):>10} {delta(cur[1], prev[1]):>10}")
    print(f"  {'Net Subscribers':<25} {'+' + str(net_subs) if net_subs >= 0 else str(net_subs):>10} {'+' + str(prev_net_subs) if prev_net_subs >= 0 else str(prev_net_subs):>10} {delta(net_subs, prev_net_subs) if prev_net_subs != 0 else 'n/a':>10}")
    print(f"  {'Likes':<25} {format_number(int(cur[4])):>10} {format_number(int(prev[4])):>10} {delta(cur[4], prev[4]):>10}")
    print(f"  {'Comments':<25} {format_number(int(cur[5])):>10} {format_number(int(prev[5])):>10} {delta(cur[5], prev[5]):>10}")
    print(f"  {'Shares':<25} {format_number(int(cur[6])):>10} {format_number(int(prev[6])):>10} {delta(cur[6], prev[6]):>10}")

    # Avg views per video
    video_count = int(stats["videoCount"])
    if video_count > 0 and cur[0] > 0:
        avg_views = cur[0] / video_count
        print(f"\n  Avg Views/Video (lifetime): {format_number(int(int(stats['viewCount']) / video_count))}")

    print()


def report_top_videos(youtube, analytics, days: int = 28, limit: int = 15, sort_by: str = "views"):
    """Top performing videos ranked by views, watch time, or CTR."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    sort_metric = {
        "views": "-views",
        "watchtime": "-estimatedMinutesWatched",
        "duration": "-averageViewDuration",
        "retention": "-averageViewPercentage",
    }.get(sort_by, "-views")

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        dimensions="video",
        metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,subscribersGained",
        maxResults=limit,
        sort=sort_metric,
    ).execute()

    if not response.get("rows"):
        print("No video data available for this period.")
        return

    # Fetch video titles
    video_ids = [row[0] for row in response["rows"]]
    titles = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        vids = youtube.videos().list(part="snippet", id=",".join(batch)).execute()
        for item in vids["items"]:
            titles[item["id"]] = item["snippet"]["title"]

    print(f"\n{'=' * 90}")
    print(f"  TOP {limit} VIDEOS (by {sort_by}, last {days} days)")
    print(f"{'=' * 90}")
    print(f"\n  {'#':<4} {'TITLE':<40} {'VIEWS':>8} {'WATCH':>8} {'AVG DUR':>8} {'RET%':>6} {'LIKES':>6} {'SUBS':>5}")
    print(f"  {'-' * 85}")

    for i, row in enumerate(response["rows"], 1):
        vid_id, views, watch_min, avg_dur, avg_pct, likes, subs = row
        title = titles.get(vid_id, vid_id)[:38]
        print(
            f"  {i:<4} {title:<40} {format_number(int(views)):>8} "
            f"{format_duration(watch_min):>8} {format_seconds(avg_dur):>8} "
            f"{avg_pct:.0f}%{'':<3} {int(likes):>6} {'+' + str(int(subs)):>5}"
        )

    print()


def report_ctr(youtube, analytics, days: int = 28):
    """Click-through rate diagnostics: impressions vs clicks."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Channel-level CTR
    try:
        channel_ctr = analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views,videoThumbnailImpressions,videoThumbnailImpressionsClickRate",
        ).execute()
    except Exception as e:
        print(f"CTR data not available: {e}")
        print("Note: Impression data requires sufficient view volume.")
        return

    # Per-video CTR (top impressions)
    video_ctr = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        dimensions="video",
        metrics="views,videoThumbnailImpressions,videoThumbnailImpressionsClickRate",
        maxResults=15,
        sort="-videoThumbnailImpressions",
    ).execute()

    print(f"\n{'=' * 70}")
    print(f"  CTR DIAGNOSTICS (last {days} days)")
    print(f"{'=' * 70}")

    if channel_ctr.get("rows"):
        row = channel_ctr["rows"][0]
        views, impressions, ctr = row
        print(f"\n  Channel Average:")
        print(f"    Impressions:  {format_number(int(impressions))}")
        print(f"    Views:        {format_number(int(views))}")
        print(f"    CTR:          {ctr:.1%}")
        print()
        if ctr < 0.02:
            print("  ** LOW CTR: Thumbnails and titles need improvement.")
            print("     Benchmark: 2-10% CTR is typical for most channels.")
        elif ctr < 0.05:
            print("  CTR is average. Room for improvement in thumbnails/titles.")
        else:
            print("  CTR is strong. Thumbnails and titles are working well.")

    if video_ctr.get("rows"):
        # Fetch titles
        video_ids = [row[0] for row in video_ctr["rows"]]
        titles = {}
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            vids = youtube.videos().list(part="snippet", id=",".join(batch)).execute()
            for item in vids["items"]:
                titles[item["id"]] = item["snippet"]["title"]

        print(f"\n  {'TITLE':<40} {'IMPR':>10} {'VIEWS':>8} {'CTR':>8}")
        print(f"  {'-' * 68}")

        for row in video_ctr["rows"]:
            vid_id, views, impressions, ctr = row
            title = titles.get(vid_id, vid_id)[:38]
            ctr_str = f"{ctr:.1%}"
            flag = " !!" if ctr < 0.02 else ""
            print(f"  {title:<40} {format_number(int(impressions)):>10} {format_number(int(views)):>8} {ctr_str:>8}{flag}")

    print()


def report_traffic(analytics, days: int = 28):
    """Traffic source breakdown."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        dimensions="insightTrafficSourceType",
        metrics="views,estimatedMinutesWatched",
        sort="-views",
    ).execute()

    if not response.get("rows"):
        print("No traffic data available.")
        return

    total_views = sum(row[1] for row in response["rows"])

    # Friendly names for traffic source types
    source_names = {
        "YT_SEARCH": "YouTube Search",
        "RELATED_VIDEO": "Suggested Videos",
        "EXT_URL": "External Links",
        "SUBSCRIBER": "Subscribers",
        "NOTIFICATION": "Notifications",
        "ADVERTISING": "Ads",
        "ANNOTATION": "Annotations",
        "END_SCREEN": "End Screens",
        "EMBEDDED": "Embedded",
        "YT_CHANNEL": "Channel Page",
        "YT_OTHER_PAGE": "Other YouTube",
        "PLAYLIST": "Playlists",
        "NO_LINK_OTHER": "Direct/Unknown",
        "SHORTS": "Shorts Feed",
        "YT_PLAYLIST_PAGE": "Playlist Page",
    }

    print(f"\n{'=' * 60}")
    print(f"  TRAFFIC SOURCES (last {days} days)")
    print(f"{'=' * 60}")
    print(f"\n  {'SOURCE':<30} {'VIEWS':>10} {'%':>8} {'WATCH TIME':>12}")
    print(f"  {'-' * 60}")

    for row in response["rows"]:
        source_type, views, watch_min = row
        name = source_names.get(source_type, source_type)
        pct = (views / total_views * 100) if total_views > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"  {name:<30} {format_number(int(views)):>10} {pct:>6.1f}%  {format_duration(watch_min):>10}  {bar}")

    print(f"\n  Total: {format_number(int(total_views))} views")
    print()


def report_demographics(analytics, days: int = 90):
    """Audience age and gender breakdown."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        dimensions="ageGroup,gender",
        metrics="viewerPercentage",
    ).execute()

    if not response.get("rows"):
        print("No demographic data available (may need more views).")
        return

    # Aggregate by age group and gender
    age_totals = {}
    gender_totals = {}

    for row in response["rows"]:
        age, gender, pct = row
        age_totals[age] = age_totals.get(age, 0) + pct
        gender_totals[gender] = gender_totals.get(gender, 0) + pct

    age_labels = {
        "age13-17": "13-17",
        "age18-24": "18-24",
        "age25-34": "25-34",
        "age35-44": "35-44",
        "age45-54": "45-54",
        "age55-64": "55-64",
        "age65-": "65+",
    }

    print(f"\n{'=' * 50}")
    print(f"  AUDIENCE DEMOGRAPHICS (last {days} days)")
    print(f"{'=' * 50}")

    print(f"\n  AGE GROUP")
    print(f"  {'-' * 40}")
    for age_key in ["age13-17", "age18-24", "age25-34", "age35-44", "age45-54", "age55-64", "age65-"]:
        pct = age_totals.get(age_key, 0)
        label = age_labels.get(age_key, age_key)
        bar = "#" * int(pct)
        print(f"  {label:<8} {pct:>5.1f}%  {bar}")

    print(f"\n  GENDER")
    print(f"  {'-' * 40}")
    gender_labels = {"male": "Male", "female": "Female", "user_specified": "Other"}
    for g in ["male", "female", "user_specified"]:
        pct = gender_totals.get(g, 0)
        label = gender_labels.get(g, g)
        bar = "#" * int(pct)
        print(f"  {label:<12} {pct:>5.1f}%  {bar}")

    print()


def report_content_type(analytics, days: int = 28):
    """Shorts vs long-form video performance comparison."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        dimensions="creatorContentType",
        metrics="views,estimatedMinutesWatched,averageViewDuration",
    ).execute()

    if not response.get("rows"):
        print("No content type data available.")
        return

    type_names = {
        "SHORTS": "Shorts",
        "VIDEO_ON_DEMAND": "Long-form",
        "LIVE_STREAM": "Live Streams",
        "STORY": "Stories",
        "UNSPECIFIED": "Other",
    }

    print(f"\n{'=' * 60}")
    print(f"  SHORTS vs LONG-FORM (last {days} days)")
    print(f"{'=' * 60}")
    print(f"\n  {'TYPE':<15} {'VIEWS':>10} {'WATCH TIME':>12} {'AVG DURATION':>14}")
    print(f"  {'-' * 55}")

    for row in response["rows"]:
        content_type, views, watch_min, avg_dur = row
        name = type_names.get(content_type, content_type)
        print(f"  {name:<15} {format_number(int(views)):>10} {format_duration(watch_min):>12} {format_seconds(avg_dur):>14}")

    print()


def report_retention(youtube, analytics, video_id: str, days: int = 90):
    """Audience retention curve for a specific video."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Get video title
    vid_info = youtube.videos().list(part="snippet,statistics,contentDetails", id=video_id).execute()
    if not vid_info.get("items"):
        print(f"Video not found: {video_id}")
        return

    title = vid_info["items"][0]["snippet"]["title"]

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        dimensions="elapsedVideoTimeRatio",
        metrics="audienceWatchRatio,relativeRetentionPerformance",
        filters=f"video=={video_id}",
    ).execute()

    if not response.get("rows"):
        print(f"No retention data for: {title}")
        return

    print(f"\n{'=' * 60}")
    print(f"  RETENTION: {title[:50]}")
    print(f"{'=' * 60}")
    print(f"\n  {'POSITION':>10} {'RETENTION':>12} {'vs SIMILAR':>12}  CURVE")
    print(f"  {'-' * 55}")

    rows = response["rows"]
    # Show ~20 data points evenly spaced
    step = max(1, len(rows) // 20)

    for i in range(0, len(rows), step):
        row = rows[i]
        position, retention, relative = row
        pct_pos = position * 100
        bar = "#" * int(retention * 40)
        rel_label = "above avg" if relative > 1 else "below avg" if relative < 1 else "average"
        print(f"  {pct_pos:>8.0f}%  {retention:>10.1%}  {relative:>10.2f}x  {bar}")

    # Find biggest drop-off
    if len(rows) > 2:
        max_drop = 0
        drop_pos = 0
        for i in range(1, len(rows)):
            drop = rows[i - 1][1] - rows[i][1]
            if drop > max_drop:
                max_drop = drop
                drop_pos = rows[i][0]

        print(f"\n  Biggest drop-off: {drop_pos * 100:.0f}% into the video ({max_drop:.1%} of viewers left)")

    print()


def report_trends(analytics, days: int = 28):
    """Daily view/subscriber trends."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        dimensions="day",
        metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost",
        sort="day",
    ).execute()

    if not response.get("rows"):
        print("No trend data available.")
        return

    print(f"\n{'=' * 70}")
    print(f"  DAILY TRENDS (last {days} days)")
    print(f"{'=' * 70}")
    print(f"\n  {'DATE':<12} {'VIEWS':>8} {'WATCH':>8} {'NET SUBS':>9}  VIEWS")
    print(f"  {'-' * 65}")

    max_views = max(row[1] for row in response["rows"]) if response["rows"] else 1

    for row in response["rows"]:
        day, views, watch_min, subs_gained, subs_lost = row
        net_subs = int(subs_gained) - int(subs_lost)
        bar_len = int((views / max_views) * 30) if max_views > 0 else 0
        bar = "#" * bar_len
        net_str = f"+{net_subs}" if net_subs >= 0 else str(net_subs)
        print(f"  {day:<12} {format_number(int(views)):>8} {format_duration(watch_min):>8} {net_str:>9}  {bar}")

    # Weekly averages
    total_views = sum(row[1] for row in response["rows"])
    total_watch = sum(row[2] for row in response["rows"])
    num_days = len(response["rows"])
    print(f"\n  Daily avg: {format_number(int(total_views / num_days))} views, {format_duration(total_watch / num_days)} watch time")

    print()


def report_full_diagnostic(youtube, analytics, days: int = 28):
    """Run all reports as a full channel diagnostic."""
    report_overview(youtube, analytics, days)
    report_content_type(analytics, days)
    report_top_videos(youtube, analytics, days)
    report_ctr(youtube, analytics, days)
    report_traffic(analytics, days)
    report_trends(analytics, days)
    report_demographics(analytics, min(days * 3, 90))

    # Diagnostics summary
    print(f"{'=' * 60}")
    print(f"  DIAGNOSTIC SUMMARY")
    print(f"{'=' * 60}")
    print(f"\n  Check the reports above for:")
    print(f"  1. CTR below 2% -> improve thumbnails/titles")
    print(f"  2. Low avg view duration -> improve hooks & pacing")
    print(f"  3. Traffic heavily from one source -> diversify")
    print(f"  4. Shorts vs long-form imbalance -> adjust strategy")
    print(f"  5. Subscriber conversion low -> add CTAs")
    print()


def main():
    parser = argparse.ArgumentParser(description="YouTube Channel Analytics")
    parser.add_argument(
        "report",
        choices=["overview", "top", "ctr", "traffic", "demographics", "content-type", "retention", "trends", "diagnostic"],
        help="Report to run",
    )
    parser.add_argument("--days", type=int, default=28, help="Analysis period in days (default: 28)")
    parser.add_argument("--limit", type=int, default=15, help="Number of results for top videos (default: 15)")
    parser.add_argument("--sort", default="views", choices=["views", "watchtime", "duration", "retention"], help="Sort top videos by metric")
    parser.add_argument("--video", help="Video ID for retention report")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted tables")

    args = parser.parse_args()

    print("Authenticating with YouTube...")
    youtube, analytics = get_authenticated_services()
    print("Authenticated.\n")

    if args.report == "overview":
        report_overview(youtube, analytics, args.days)
    elif args.report == "top":
        report_top_videos(youtube, analytics, args.days, args.limit, args.sort)
    elif args.report == "ctr":
        report_ctr(youtube, analytics, args.days)
    elif args.report == "traffic":
        report_traffic(analytics, args.days)
    elif args.report == "demographics":
        report_demographics(analytics, args.days)
    elif args.report == "content-type":
        report_content_type(analytics, args.days)
    elif args.report == "retention":
        if not args.video:
            print("Error: --video VIDEO_ID is required for retention report")
            sys.exit(1)
        report_retention(youtube, analytics, args.video, args.days)
    elif args.report == "trends":
        report_trends(analytics, args.days)
    elif args.report == "diagnostic":
        report_full_diagnostic(youtube, analytics, args.days)


if __name__ == "__main__":
    main()
