---
name: f1-scriptwriting
description: Use whenever writing F1 video scripts, hooks, narration, segment text, daily news copy, or any written content for the F1 Burnouts channel — even outside a formal pipeline command. Auto-trigger when script writing, hooks, narration, story structure, or segment text is mentioned.
---

# F1 Scriptwriting

## The Golden Rules

### 1. Hook First, Context Second
- **First 10 seconds are critical** — open with intrigue, not background
- Start with a provocative question, surprising fact, or dramatic moment
- Save "In this video, we'll explore..." for AFTER the hook

**BAD Opening:**
> "Lewis Hamilton is one of the greatest Formula One drivers of all time. In this video, we'll look at his career."

**GOOD Opening:**
> "Forty-four. That's the number Lewis Hamilton saw when he looked at his championship standings after Abu Dhabi 2021. Not first. Second. And in that moment, everything changed."

### 2. Create Narrative Tension
- Every great video has conflict, stakes, or mystery
- Ask questions that demand answers
- Create "open loops" — introduce ideas that pay off later
- Use phrases like: "But what nobody expected was..." / "That's when everything fell apart..."

### 3. Show, Don't Just Tell
- Instead of stating facts, paint scenes
- Use sensory details: sounds, sights, atmosphere

**TELLING:**
> "Senna and Prost had a famous rivalry in 1989."

**SHOWING:**
> "The gravel flew. Metal scraped against metal. As Senna climbed out of his McLaren at Suzuka, he locked eyes with Prost across the runoff area. Neither man blinked. The 1989 championship had just exploded."

### 4. Vary Pacing and Rhythm
- Alternate between fast, punchy segments and slower, reflective ones
- Short sentences create urgency. They punch. They hit.
- Longer, flowing sentences allow the viewer to breathe and absorb the weight of what you're describing, building anticipation for what comes next.
- Use strategic pauses (segment breaks) for dramatic effect

### 5. The "So What?" Test
Every segment must answer: "Why should the viewer care?"
- Connect facts to emotions
- Relate historical events to present-day implications
- Show how this affects drivers, teams, or the sport

---

## Writing Techniques

### The Curiosity Gap
Introduce information that creates a gap between what viewers know and what they want to know:
- "There's one race that Ferrari wishes everyone would forget."
- "Only three people know what really happened in that meeting."

### Foreshadowing
Plant seeds that pay off later:
- "Little did Verstappen know, this decision would haunt him for years."
- "Remember that corner. It becomes important later."

### Parallel Structure
Connect past and present, or compare two stories:
- "In 1976, Lauda walked through fire. In 2019, another driver faced a different kind of inferno."

### Rule of Three
Group information in threes for rhythm and memorability:
- "He was fast. He was fearless. He was seventeen years old."

### Intuitive Storytelling
Make complex topics accessible:
- Use analogies viewers can relate to
- Build from simple to complex
- Define jargon when first used (but briefly)
- Use concrete examples, not abstract concepts

**ABSTRACT:**
> "The aerodynamic regulations significantly impacted downforce generation."

**INTUITIVE:**
> "Imagine pressing your hand out a car window at highway speed. Now imagine doing that at 200 miles per hour. That's the force these new rules just took away from the cars."

---

## Content Structure

### The 10-Minute Formula (Long-Form)

```
[0:00-0:30]   COLD OPEN - The hook, no context needed
[0:30-1:30]   SETUP - What we're exploring and why it matters
[1:30-4:00]   ACT 1 - The beginning/origin of the story
[4:00-4:30]   TRANSITION - Pivot point, things are about to change
[4:30-7:00]   ACT 2 - The conflict/development/main action
[7:00-7:30]   TRANSITION - The turning point
[7:30-9:00]   ACT 3 - Resolution/climax/aftermath
[9:00-9:45]   REFLECTION - What it means, legacy, impact
[9:45-10:00]  CLOSE - Call to action, tease future content
```

### Section Types

| Section | Purpose | Tone | Length |
|---------|---------|------|--------|
| `cold_open` | Hook viewer instantly | Dramatic, intriguing | 15-30s |
| `intro` | Establish topic and stakes | Confident, inviting | 30-60s |
| `origin` | Background, how it began | Narrative, scene-setting | 60-90s |
| `rising_action` | Building tension/conflict | Escalating, engaging | 60-120s |
| `climax` | Peak moment, main event | Intense, vivid | 60-90s |
| `aftermath` | Immediate consequences | Reflective, impactful | 45-60s |
| `analysis` | Expert insight, deeper meaning | Thoughtful, authoritative | 60-90s |
| `legacy` | Long-term impact, relevance | Contemplative, connecting | 45-60s |
| `conclusion` | Wrap up, final thoughts | Satisfying, memorable | 30-45s |

### Text Length & Pacing

| Segment Type | Words | Duration | Sentences |
|--------------|-------|----------|-----------|
| Hook/Punch | 25-40 | 10-15s | 2-3 short |
| Standard | 50-70 | 20-25s | 3-5 mixed |
| Reflective | 60-80 | 25-30s | 3-4 flowing |
| Technical | 40-60 | 15-20s | 2-4 clear |

### Shot Pacing: No Static Image > 6 Seconds

**CRITICAL RULE**: No single static image should be on screen for more than 6 seconds. Viewers lose attention on static holds, and >8s causes literal video freeze frames in the assembler.

**When writing `text_cue` for shots, check**: If a shot's text_cue covers more than ~15 words (~6s of narration), it's too long for a single image. Split it.

**How to fix segments with long single-image holds:**
1. **Best**: Add more shots — if narration mentions 3 people, use 3 separate image shots (one per person)
2. **Good**: Mix source types — image + YouTube clip, or image + quote overlay
3. **Acceptable**: Split same image into two shots with different Ken Burns (zoom_in → zoom_out)

**Example — BAD (one image for ~14s):**
```json
{ "label": "Carlos Sainz", "text_cue": "Carlos Sainz, George Russell, Valtteri Bottas — all potentially available. A team could poach a proven driver", "source_type": "image" }
```

**Example — GOOD (one image per person):**
```json
{ "label": "Carlos Sainz", "text_cue": "Carlos Sainz,", "source_type": "image" },
{ "label": "George Russell", "text_cue": "George Russell,", "source_type": "image" },
{ "label": "Valtteri Bottas", "text_cue": "Valtteri Bottas — all potentially available.", "source_type": "image" }
```

### One Entity = One Shot

When narration lists people, teams, or concepts by name, each named entity gets its own shot. Never pack multiple names into one shot's `text_cue`.

**Count the names, match the shots:**
- "Sainz, Russell, Bottas" → 3 shots (one per driver)
- "BYD is the frontrunner, Lotus is the dark horse" → 2 shots (one per brand)
- "Porsche, Hyundai, and Toyota all said no" → 3 shots (one per manufacturer)

**Why this matters**: The assembler divides shot duration proportionally by `text_cue` character position. A single shot covering 3 names means all 3 get the same static image — viewers see "Sainz" while hearing about "Bottas."

### Summary/Prediction Segments Need Extra Shots

Resolution and prediction segments reference many concepts in quick succession. These need 4+ shots minimum — more than average segments. A single YouTube clip cannot carry ~20s of narration that bounces between topics.

**Pattern**: For any segment that references 3+ distinct entities (teams, people, concepts), plan at least one shot per entity plus a closing shot.

---

## Sentence Variety

Mix these patterns:
- **Punchy**: "He won. Again." (2-4 words)
- **Standard**: "The championship battle continued into the final race." (8-12 words)
- **Flowing**: "As the lights went out in Abu Dhabi, both drivers knew that everything they had worked for across twenty-one grueling races came down to this single moment." (25+ words)

---

## Transition Phrases

**Avoid overusing:**
- "Now let's talk about..."
- "Moving on to..."
- "Next, we'll look at..."

**Use instead:**
- Scene shifts: "Three thousand miles away..." / "Meanwhile, in Maranello..."
- Time jumps: "Fast forward to 2019." / "Rewind to his first race."
- Contrast: "But the data told a different story." / "Yet something felt wrong."
- Consequence: "The implications were immediate." / "What followed changed everything."

---

## Avoiding Repetition

**REPETITION TO AVOID:**
- Restating the same fact in different words
- Summarizing what you just said
- Repeating the thesis in every section
- Using the same transition phrases

**REPETITION THAT WORKS:**
- Key phrases for emphasis ("And once again, Red Bull...")
- Callback references to earlier points
- Thematic echoes that tie the narrative together
- Repeating a word for stylistic impact ("Champion. Champion of Britain. Champion of the world.")

---

## News Writing Style (Daily News / Shorts)

- **Crisp and punchy**: No filler words, every word counts
- **Active voice**: "Ferrari reveals" not "It was revealed by Ferrari"
- **Present tense** for immediacy: "Hamilton admits...", "Mercedes confirms..."
- **Specific details**: Include names, numbers, dates
- **Natural flow**: Stories should transition smoothly
- **NEVER use the word "Quote"**: Integrate quotes naturally — "In his words: I'll never forget this"

### Daily News Hook Patterns
- Segment 0 is always the BIGGEST story as a scroll-stopping hook
- NEVER a generic "Welcome to F1 Daily News" intro
- Bold claim, shocking quote, or dramatic development
- Example: "Max Verstappen just dropped a bombshell. He says we are close to the end of his Formula One career."
- Segment 2 should CONTINUE the hook story with more details (satisfying payoff)

### Example News Segments

**Good**: "Lewis Hamilton finally drove a Ferrari at Fiorano today. The SF-26 marks his first competitive laps in red, with Ferrari finishing the car just one day before launch."

**Bad**: "So there's been some exciting news from Ferrari today. Lewis Hamilton, who as you know moved from Mercedes, has finally had the chance to drive the new car."

---

## Mandatory Subscribe CTA (ALL Formats)

**Every video MUST end with a follow/subscribe CTA.** Analytics show 0.2% sub conversion — most viewers watch but never subscribe because we don't ask.

### CTA Patterns (rotate, don't repeat the same one):
- "Follow F1 Burnouts for your daily F1 fix. Drop your take in the comments."
- "If you made it this far, hit subscribe. We drop F1 content every single day."
- "That's it for today. Follow for more, and tell me who you think wins in the comments."
- "Subscribe if you want this in your feed every day. See you tomorrow."

### CTA Rules:
- **Shorts**: Final segment, 1 sentence, natural and conversational
- **Long-form**: Dedicated outro segment, can be 2-3 sentences with specific ask
- **Podcasts**: Already handled by outro segment
- **NEVER skip the CTA** — it's the #1 cheapest growth lever

---

## SEO & Discoverability

### Title Optimization
- **Shorts titles**: Use curiosity gaps, not dates. "The Man With More F1 Races Than Any Driver" >>> "F1 Fun Fact #47"
- **Daily News titles**: Include `#Shorts` tag AND the biggest story hook. Example: "F1 Daily News - March 1, 2026 #Shorts"
- **Long-form titles**: Front-load the hook, keep under 60 chars. Avoid generic "F1 Video About X"

### Tag Strategy (in script.json `tags` field)
Every script.json SHOULD include a `tags` array with:
1. **Base tags**: `["F1", "Formula 1", "Formula1", "Racing", "Motorsport"]`
2. **Driver tags**: Every driver mentioned by name gets their full name as a tag
3. **Team tags**: Every team mentioned gets their full name as a tag
4. **Topic tags**: Championship, qualifying, testing, rivalry, history, debut, etc.
5. **Shorts tag**: `"Shorts"` for all short-form content

**BAD** (generic): `["F1", "Formula 1", "Racing", "Shorts"]`
**GOOD** (specific): `["F1", "Formula 1", "Max Verstappen", "Verstappen", "Red Bull Racing", "Daniel Ricciardo", "Number 3", "F1 2026", "Shorts"]`

---

## Cold Open Patterns

The cold open needs NO context — drop the viewer into the most dramatic moment:
- A specific number or statistic that shocks
- A vivid scene description (sounds, sights, atmosphere)
- A provocative question the viewer can't ignore
- A quote that reframes everything

The setup segment AFTER the cold open provides the "why this matters" context.
