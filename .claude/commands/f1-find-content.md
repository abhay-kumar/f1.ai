# Find F1 Short Ideas

Discover evergreen F1 content ideas from Reddit, F1 news outlets, blogs, and social media for short-form videos — heartwarming stories, historical facts, little-known trivia, and timeless moments (NOT breaking news).

## Parameters

- `$ARGUMENTS` - Time range: `day` (past 24 hours), `week` (past 7 days), or `month` (past 30 days). Defaults to `week` if not specified.

## Instructions

You are searching multiple F1 sources for evergreen content — heartwarming stories, historical facts, lesser-known trivia, emotional moments, and timeless narratives. **Skip breaking news, race results, and current-season drama.** Focus on content that would be just as interesting in 6 months as it is today.

**Time Range**: Based on the `$ARGUMENTS` parameter:
- `day` → Search for content from the past 24 hours / yesterday
- `week` (default) → Search for content from the past 7 days
- `month` → Search for content from the past 30 days

### Workflow

1. **Load existing ideas**: Read `shared/reddit_ideas.json` to get all previously proposed and used ideas. This file tracks every idea ever surfaced, with `"status": "proposed"` or `"status": "used"`. You MUST skip any idea that overlaps with an existing entry (same topic, same driver story, same historical event) — regardless of status. Compare by topic/synopsis similarity, not just exact title match.

2. **Search all sources in parallel**: Run these simultaneously:

   **a) Reddit** — Use the Reddit API fetcher:
   ```bash
   python3 src/reddit_fetcher.py --top {time_range} --limit 25
   ```
   No API key needed — uses Reddit's public `.json` endpoints.
   If the fetcher fails (rate limited), fall back to web search: `site:reddit.com/r/formula1`

   **b) F1 news outlets & blogs** — Use web search to find evergreen stories from major sources:
   - `site:formula1.com features OR history OR "did you know"` — Official F1 site features
   - `site:motorsport.com formula1 history OR legend OR story OR "little known"` — Motorsport.com
   - `site:racefans.net f1 history OR trivia OR forgotten` — RaceFans
   - `site:the-race.com f1 history OR story OR remarkable` — The Race
   - `site:wtf1.com f1 story OR history OR amazing` — WTF1 (fan-focused)
   - `site:bbc.co.uk/sport/formula1 feature OR history` — BBC F1
   - `f1 "little known" OR "did you know" OR "untold story" OR forgotten history` — General

   **c) Social media & video** — Search for trending F1 stories:
   - `f1 heartwarming OR wholesome OR emotional moment` — General feel-good
   - `f1 history amazing fact trivia` — Historical trivia
   - `formula 1 inspiring story driver origin` — Origin stories

   Run 3-5 web searches in parallel targeting different source categories. Prioritize searches likely to surface evergreen content, not news.

3. **Analyze all results**: For each story/thread/article found, evaluate:
   - Is it an evergreen story/fact that works in 60 seconds?
   - Does it have emotional hook (heartwarming, surprising, nostalgic, inspiring)?
   - Is it visually representable with available F1 footage?
   - Would it still be interesting 6 months from now? (If not, skip it)
   - **SKIP**: Breaking news, race results, transfer rumors, current-season standings, regulation changes

4. **Generate Top 10 Ideas**: Create 10 unique, compelling video concepts:
   - Each idea should be specific enough to create a script
   - Include a catchy title and brief synopsis
   - Note the source that inspired it (Reddit thread, article URL, etc.)
   - **Include media URLs** if available (Reddit images/GIFs, article photos)

5. **Present Results**: Display the ideas in a clear, actionable format. If any ideas were skipped due to overlap with existing entries, mention how many were filtered out (e.g., "3 ideas skipped — already in reddit_ideas.json").

6. **Save new ideas**: After presenting, append all new ideas to `shared/reddit_ideas.json`. Each entry should follow this format:
   ```json
   {
     "id": "kebab-case-short-id",
     "title": "The Title",
     "synopsis": "2-3 sentence description",
     "reddit_source": "Source — Reddit thread title, article URL, or outlet name",
     "proposed_date": "YYYY-MM-DD",
     "status": "proposed"
   }
   ```
   Read the file, parse the JSON, push new entries to the `ideas` array, and write it back. Use the current date for `proposed_date`.

### Idea Quality Criteria

Good evergreen F1 ideas typically include:
- **Heartwarming moments**: Sportsmanship, friendships, wholesome fan interactions, drivers helping each other
- **Historical facts**: Little-known stories from F1's past, forgotten legends, pivotal moments
- **Unknown trivia**: "Did you know..." style revelations that surprise even hardcore fans
- **Driver origin stories**: How they got into racing, personal struggles, family sacrifices
- **Emotional milestones**: First wins, retirements, comebacks, father-son moments
- **Engineering marvels**: Legendary car designs, innovative solutions, banned technologies
- **Rivalries with respect**: Competitors who became friends, mutual admiration stories
- **Statistical surprises**: Counter-intuitive records, streaks, and data points
- **Behind-the-scenes**: Mechanic stories, pit lane traditions, unsung heroes
- **Cultural impact**: How F1 shaped countries, cities, or inspired people outside racing

**AVOID these (they're news, not evergreen):**
- Current race results or standings
- Transfer/contract rumors
- Regulation changes or FIA decisions
- Weekend previews or reviews
- Current-season controversies

### Output Format

Present the ideas as a numbered list:

```
## Top 10 F1 Short Ideas ([TIME_RANGE] ending [DATE])

1. **[Title]**
   Synopsis: [2-3 sentence description]
   Source: [Reddit thread, article URL, or outlet]
   Media: [Any media URLs found — images, GIFs, video links]
   Why it works: [Brief explanation]

2. ...
```

### After Finding Ideas

Suggest the user can create any video by running:
```
/f1-create-short [paste the synopsis here]
```

### Notes

- Focus on timeless stories that translate well to visual short-form content
- Avoid ideas requiring extensive footage that may be hard to find
- Prefer universally interesting topics over niche technical discussions
- Evergreen content works year-round — no need to tie to race weekends
- Reddit threads about history, trivia, and emotional moments tend to surface even during off-season — these are gold
- If a thread or article is mostly about current news but contains a historical nugget, extract just the evergreen part
- F1 outlet feature articles often contain richer, better-researched stories than Reddit posts — prioritize these for historical and trivia content
- Cross-reference stories across sources — if both Reddit AND an outlet cover the same historical moment, it's likely a strong idea
