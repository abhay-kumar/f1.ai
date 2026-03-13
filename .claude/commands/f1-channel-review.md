# F1 Channel Review

Run a full YouTube channel diagnostic using the YouTube Analytics API.

## Instructions

Run the full diagnostic report:

```bash
python3 src/youtube_analytics.py diagnostic --days 28
```

After the report completes, analyze the output and provide actionable recommendations:

1. **CTR Analysis** - If CTR is below 2%, suggest specific thumbnail/title improvements based on what's working
2. **Retention Analysis** - Identify if shorts or long-form have better engagement, and what topics perform best
3. **Traffic Sources** - Determine if the channel is too dependent on one source and how to diversify
4. **Content Strategy** - Compare shorts vs long-form performance and recommend the right mix
5. **Growth Trajectory** - Look at subscriber trends and identify what's driving or stalling growth

If the user wants to dive deeper into a specific video's retention:
```bash
python3 src/youtube_analytics.py retention --video VIDEO_ID --days 90
```

Other available reports (run individually if needed):
- `python3 src/youtube_analytics.py overview --days 28` - Channel snapshot with period comparison
- `python3 src/youtube_analytics.py top --days 28 --sort views` - Top videos (sort: views/watchtime/duration/retention)
- `python3 src/youtube_analytics.py ctr --days 28` - Click-through rate per video
- `python3 src/youtube_analytics.py traffic --days 28` - Traffic source breakdown
- `python3 src/youtube_analytics.py trends --days 28` - Daily view/subscriber chart
- `python3 src/youtube_analytics.py demographics --days 90` - Age/gender audience breakdown
- `python3 src/youtube_analytics.py content-type --days 28` - Shorts vs long-form comparison

## First-Time Setup

If authentication fails, the user needs to:
1. Enable YouTube Analytics API at https://console.cloud.google.com/apis/library/youtubeanalytics.googleapis.com
2. The module will open a browser for OAuth consent (one-time, uses separate token from upload)
3. Analytics data has 48-72 hour delay - recent uploads won't show immediately
