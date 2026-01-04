# Long-Form Script JSON Format

This document describes the extended script.json format for long-form videos with references.

## Complete Example

```json
{
  "title": "The Rise of Max Verstappen: From Youngest Driver to Four-Time Champion",
  "format": "longform",
  "resolution": "4k",
  "duration_target": 600,
  "voice": {
    "name": "Jarnathan",
    "description": "Confident and Versatile - ideal for documentary narration"
  },
  "segments": [
    {
      "id": 1,
      "section": "intro",
      "text": "At just seventeen years old, Max Verstappen became the youngest driver ever to compete in Formula One. What followed would reshape the sport forever.",
      "context": "Opening hook - establishes the remarkable nature of the story",
      "footage_query": "Verstappen F1 debut 2015 Australia",
      "footage_start": 45,
      "references": [
        {
          "claim": "Youngest driver ever to compete in Formula One at seventeen",
          "source": "Formula 1 Official",
          "url": "https://www.formula1.com/en/drivers/max-verstappen.html",
          "date": "2024-01-15"
        }
      ]
    },
    {
      "id": 2,
      "section": "early_career",
      "text": "Born in Belgium to former F1 driver Jos Verstappen and karting champion Sophie Kumpen, Max had racing in his blood. By age four, he was already competing in karts.",
      "context": "Background and racing heritage",
      "footage_query": "Young Max Verstappen karting childhood",
      "footage_start": 0,
      "references": [
        {
          "claim": "Son of Jos Verstappen and Sophie Kumpen",
          "source": "Red Bull Racing",
          "url": "https://www.redbullracing.com/int-en/drivers/max-verstappen",
          "date": "2024-01-10"
        },
        {
          "claim": "Started karting at age four",
          "source": "F1 Official Driver Profile",
          "url": "https://www.formula1.com/en/drivers/max-verstappen.html",
          "date": "2024-01-15"
        }
      ]
    },
    {
      "id": 3,
      "section": "f1_debut",
      "text": "In 2015, Toro Rosso handed Verstappen a seat alongside Carlos Sainz. He immediately turned heads with his aggressive style and raw speed.",
      "context": "First F1 season highlights",
      "footage_query": "Verstappen Toro Rosso 2015 highlights overtakes",
      "footage_start": 20,
      "references": [
        {
          "claim": "Joined Toro Rosso in 2015 with Carlos Sainz",
          "source": "Scuderia AlphaTauri",
          "url": "https://www.scuderiaalphatauri.com/en/history",
          "date": "2024-01-12"
        }
      ]
    }
  ],
  "references_summary": [
    {
      "source": "Formula 1 Official",
      "url": "https://www.formula1.com",
      "claims_supported": [1, 2, 5, 8, 12]
    },
    {
      "source": "Red Bull Racing",
      "url": "https://www.redbullracing.com",
      "claims_supported": [2, 6, 9, 14]
    },
    {
      "source": "FIA",
      "url": "https://www.fia.com",
      "claims_supported": [4, 7, 11]
    }
  ]
}
```

## Field Descriptions

### Root Level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Video title (displayed on YouTube) |
| `format` | string | No | "longform" for long videos, "short" for shorts |
| `resolution` | string | No | "4k" or "hd" (default: "4k") |
| `duration_target` | number | Yes | Target duration in seconds (600 = 10 min) |
| `voice` | object | No | Voice configuration override |
| `segments` | array | Yes | Array of segment objects |
| `references_summary` | array | No | Consolidated list of sources |

### Segment Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | number | Yes | Unique segment identifier (1-indexed) |
| `section` | string | No | Section name: intro, main, conclusion, etc. |
| `text` | string | Yes | Voiceover narration text |
| `context` | string | No | Editorial note (not rendered in video) |
| `footage_query` | string | Yes | YouTube search query for source footage |
| `footage_start` | number | No | Timestamp in source video (seconds) |
| `footage` | string | Auto | Filename of downloaded footage (auto-populated) |
| `references` | array | Yes* | Sources for claims in this segment |

*Required for long-form videos with fact-checking enabled.

### Reference Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim` | string | Yes | The specific factual claim being cited |
| `source` | string | Yes | Name of the source (publication, organization) |
| `url` | string | Yes | URL to the source |
| `date` | string | No | Date accessed or published (YYYY-MM-DD) |

### References Summary Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | Name of the source |
| `url` | string | Yes | URL to the source |
| `claims_supported` | array | No | Segment IDs this source supports |

## Section Types

Recommended section names for organizing long-form content:

- `intro` - Opening hook and topic introduction
- `background` - Context and history
- `main_1`, `main_2`, etc. - Main content sections
- `analysis` - Deeper analysis or expert commentary
- `timeline` - Chronological events
- `comparison` - Comparing subjects/eras
- `statistics` - Data and numbers
- `quotes` - Direct quotes from subjects
- `controversy` - Controversial topics or debates
- `legacy` - Impact and lasting effects
- `conclusion` - Summary and final thoughts

## Guidelines

### Engagement
- **Hook**: First segment should grab attention immediately
- **Variety**: Mix narrative, facts, quotes, and analysis
- **Pacing**: Vary segment lengths (15-30 seconds each)
- **Transitions**: Brief bridging text between sections

### References
- Every factual claim needs a source
- Use reputable sources (F1 Official, team sites, major sports outlets)
- Include access dates for web sources
- Verify statistics match official records

### Duration Planning
For a 10-minute video (~600 seconds):
- Intro: 30-60 seconds (2-3 segments)
- Main content: 7-8 minutes (20-30 segments)
- Conclusion: 30-60 seconds (2-3 segments)
- Credits: 15 seconds (auto-generated)

### Avoiding Repetition
- Don't repeat the same information
- Vary sentence structures
- Use different words for similar concepts
- Progress the narrative forward with each segment
