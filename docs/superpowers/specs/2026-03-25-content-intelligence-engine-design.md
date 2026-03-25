# Content Intelligence Engine — Design Spec

## Overview

A Claude Code-driven content intelligence system that discovers news, creates LinkedIn posts (infographics and story posts), experiments with different content strategies, tracks engagement, and learns what works over time.

**Two accounts:**
- **Personal (thegeshwar)** — 1 post/day, broad tech/money/breaking news
- **CU Circuits company page** — 3 posts/week, PCB fab/3D printing/manufacturing industry

**Core principle:** Each post tells ONE story, deeply and well. Every post is an experiment. Claude tracks results and gets smarter.

---

## Architecture

Claude Code CLI is the orchestrator. No autonomous Python pipeline. No Anthropic API calls from code. The user invokes a skill, Claude does everything.

### Two Skills

**`/infographic personal`** — Create and post to personal LinkedIn
**`/infographic company`** — Create and post to CU Circuits company page

Both skills follow the same pipeline internally:

```
DISCOVER → SELECT → CREATE → APPROVE (iMessage) → POST → SCHEDULE FOLLOWUP
```

A separate followup skill handles engagement measurement:

**`/infographic check`** — Claude checks engagement on recent posts, updates the content log

### Scheduling

Cron-based remote triggers:
- Personal: daily at optimized time (initially 8am, adjusted by engagement data)
- Company: Mon/Wed/Fri at optimized time (initially 9am, adjusted)
- Engagement check: daily at 10pm (checks all posts 24h+ old that haven't been measured)

All scheduled runs still require iMessage approval before posting.

---

## Pipeline Detail

### Stage 1: Discover

Claude uses its tools (WebSearch, WebFetch, RSS reading) to find today's trending stories. No Python scraping infrastructure needed — Claude IS the scraper.

**Personal account sources:**
- Tech: Hacker News, TechCrunch, The Verge, Ars Technica
- AI/ML: ArXiv, Papers With Code, AI news sites
- Money: Bloomberg Tech, Crunchbase, funding announcements
- Breaking: Twitter/X trending, major outlet breaking news

**CU Circuits sources:**
- PCB industry: PCB007, EE Times, Electronics Weekly
- 3D printing: All3DP, 3DPrint.com, Additive Manufacturing
- India manufacturing: Economic Times (industry), Make in India news
- Standards: IPC news, electronics supply chain
- Competitors: What are JLCPCB, PCBWay, Lion Circuits posting?

Claude searches 5-8 sources, reads headlines and summaries, builds a mental shortlist.

### Stage 2: Select

Claude reads the content log (`data/content-log.json`) to understand:
- What strategies have worked best recently
- What topics have been covered (avoid repeats)
- What content pillars haven't been served lately

Claude then picks **1 primary story + 2 alternatives** with reasoning:
- Primary: the story with the best combination of newsworthiness, relevance to audience, and visual potential
- Alternatives: different topics/angles for variety

### Stage 3: Create

Claude selects a content strategy using **explore/exploit** logic:

**Strategy selection algorithm:**

*Phase 1 — Pure exploration (posts 1-50):*
Systematically rotate through under-tested variable combinations. Ensures every voice, format, and hook gets tried at least 5 times before any exploitation begins. Random within the under-tested set.

*Phase 2 — Guided exploitation (posts 50+):*
1. Read content log, calculate average engagement rate per variable value
2. Only "exploit" a value if it has been tested at least 8 times (confidence threshold)
3. 70% of the time: pick from top-performing values (exploit)
4. 30% of the time: pick from under-tested or random values (explore)
5. As data grows (>100 posts), shift to 85/15
6. Never repeat the exact same strategy combination as the last 3 posts

*Note:* Variable interactions (e.g., "Contrarian + Bold claim" vs "Contrarian + Question") are intentionally ignored for simplicity. Marginal averages are a rough but workable heuristic at this volume.

**Variables rotated:**

| Variable | Personal Options | CU Circuits Options |
|----------|-----------------|-------------------|
| Voice | Analyst, Builder, Commentator, Storyteller, Contrarian, Curious Explorer | Industry Expert, Helpful Engineer, Scrappy Startup, Data Analyst, Educator, Insider |
| Format | Single-story infographic, Data visualization, Quote card + analysis, Timeline, Before/After comparison, Story post (text + hero image) | Single-story infographic, DFM tip card, Price/data comparison, Manufacturing process visual, Industry trend chart, Customer story spotlight |
| Hook | Question, Bold claim, Statistic, Contrarian take, "Here's what everyone missed", Future prediction | Did you know, Common mistake, Cost comparison, Industry stat, "Stop doing this", New standard/tech alert |
| Depth | Minimal (hook + 3 points), Medium (full narrative arc), Dense (visual essay) | Minimal, Medium, Dense |
| Caption | Opinion-led, Question-led, Short & punchy, Long-form analysis, "Thread-style" numbered points | Expert take, Practical advice, Industry analysis, Question to audience, Company perspective |
| Visual | Dark Glassmorphism, Neon Gradient, Clean Editorial, Midnight Teal, Warm Mono, Polar Light | Circuit Board Dark, Copper & Navy, Clean Fabrication, Solder Mask Blue, 3D Print Orange, India Tech Gradient |

**Content creation — what Claude actually produces:**

1. **The infographic image** — Generated via Pillow (Python). Claude writes the content, calls a Python script to render it. The image tells the story visually:
   - Hook/headline at top
   - The story body — context, facts, narrative
   - Key insight or takeaway
   - Branded footer with account identity

2. **The caption** — Written by Claude in the selected style. Includes:
   - Opening hook (first 2 lines are crucial — they show above the fold)
   - Body that COMPLEMENTS the image (not repeats it)
   - Strategic hashtags (5-8, mix of broad and niche)
   - Engagement prompt (question, "agree or disagree?", "save this for later")

3. **Metadata** — strategy choices, story source, reasoning for selection

### Stage 4: Approve (iMessage)

**Two-phase approval (solves the "Claude can't wait 2 hours" problem):**

The pipeline splits into two skills:
- **`/infographic draft personal|company`** — Runs stages 1-3, creates the post, sends iMessage for approval, saves state to `data/drafts/<id>.json` with status `pending_approval`, then EXITS.
- **`/infographic post <id>`** — Called after approval is received. Reads the draft, posts it, logs to content-log.json.

**For manual runs:** User runs `/infographic personal` which calls draft, then the user approves via iMessage, then the user runs `/infographic post <id>` (or Claude auto-posts if running interactively and the reply comes quickly).

**For scheduled runs:** Cron fires `/infographic draft`. A second cron runs every 15 minutes checking `data/drafts/` for approved drafts and posts them via `/infographic post`.

**iMessage send:** Via `osascript`:
```applescript
tell application "Messages"
    set targetService to 1st account whose service type = iMessage
    set targetBuddy to participant "approver_id" of targetService
    send "message" to targetBuddy
end tell
```

**iMessage read (poll for reply):** Via SQLite query on `~/Library/Messages/chat.db`:
- Query the most recent message from the approver after the draft timestamp
- Parse for ✅, 1, 2, or ❌
- The 15-minute cron does this check automatically

**Approval state in draft file:**
```json
{
  "id": "2026-03-25-personal-001",
  "status": "pending_approval|approved|rejected|posted|failed",
  "account": "personal",
  "created_at": "...",
  "approved_at": null,
  "story": { "..." },
  "strategy": { "..." },
  "caption": "...",
  "image_path": "...",
  "alternatives": [...]
}
```

**Approval config:** stored in `data/config/approval.json`:
```json
{
  "personal": {"approver": "self", "timeout_minutes": 120},
  "company": {"approver": "self", "timeout_minutes": 120}
}
```

### Stage 5: Post

**Important:** Chrome DevTools MCP runs its own isolated Chrome instance and CANNOT use user profiles. Therefore, posting uses **`open -na "Google Chrome"` with Profile 2 (thejeshwa@gmail.com)** controlled via **osascript + cliclick** for real Chrome automation with the user's actual LinkedIn session.

**Posting mechanism:**
1. Claude opens Chrome with Profile 2: `open -na "Google Chrome" --args --profile-directory="Profile 2"`
2. Claude uses `osascript` to navigate to LinkedIn post creation
3. Claude uses `cliclick` and `osascript` to:
   - Click "Start a post"
   - Upload the image via file dialog automation
   - Type the caption
   - For company: select "Post as CU Circuits" from the post-as dropdown
   - Click Post
4. Claude captures the post URL from the browser
5. Logs everything to content-log.json

**Engagement scraping** also uses the real Chrome profile (same method) since LinkedIn analytics are only visible to the post author. **Fallback:** If scraping fails, Claude prompts for manual entry via `/infographic log --id X --likes N --comments N --shares N`.

**Session handling:** The user's real Chrome profile maintains its own LinkedIn session. If LinkedIn requires re-auth, Claude detects it and pauses for manual login.

### Stage 6: Measure (Followup)

Runs via `/infographic check` or scheduled cron.

Claude visits each unscored post URL via Chrome DevTools MCP and reads:
- Impressions (if visible)
- Likes/reactions count
- Comments count
- Shares/reposts count

Records to content-log.json under the post's entry. Calculates engagement rate.

---

## Data Model

### content-log.json

```json
[
  {
    "id": "2026-03-25-personal-001",
    "account": "personal|company",
    "posted_at": "2026-03-25T08:00:00",
    "post_url": "https://linkedin.com/posts/...",
    "story": {
      "headline": "GPT-5 scores 95% on ARC-AGI",
      "source": "https://...",
      "pillar": "breaking-ai"
    },
    "strategy": {
      "voice": "commentator",
      "format": "single-story-infographic",
      "hook": "contrarian",
      "depth": "medium",
      "visual_template": "dark-glassmorphism",
      "caption_style": "opinion-led"
    },
    "caption": "Full caption text...",
    "image_path": "output/2026-03-25-personal-001.png",
    "alternatives_offered": [
      {"headline": "Alt story 1", "reason": "..."},
      {"headline": "Alt story 2", "reason": "..."}
    ],
    "approval": {
      "sent_to": "self",
      "approved_at": "2026-03-25T07:45:00",
      "response": "approved"
    },
    "engagement": {
      "24h": {"likes": 0, "comments": 0, "shares": 0, "impressions": 0},
      "72h": {"likes": 0, "comments": 0, "shares": 0, "impressions": 0},
      "measured_at": null
    },
    "status": "drafted|pending_approval|approved|rejected|posted|post_failed|measured|measure_failed",
    "engagement_rate": null
  }
]
```

**Engagement rate formula:** `(likes + comments*2 + shares*3) / impressions * 100`. Comments and shares are weighted higher because they indicate deeper engagement. If impressions are unavailable (common for non-premium), fallback: `likes + comments*2 + shares*3` (raw weighted score).

**Content pillar enum** (enforced in log entries):
- Personal: `breaking-ai`, `money-moves`, `builders-edge`, `policy-ethics`, `future-signals`
- Company: `dfm-tips`, `industry-intel`, `new-tech`, `made-in-india`, `customer-stories`, `standards-process`

### strategy-weights.json (auto-generated from content log)

Claude recalculates this before each post by reading the content log. Not manually maintained.

```json
{
  "personal": {
    "sample_size": 30,
    "explore_ratio": 0.15,
    "best_performing": {
      "voice": {"commentator": 3.2, "analyst": 2.8, "builder": 2.1},
      "format": {"single-story-infographic": 3.5, "data-viz": 2.9},
      "hook": {"statistic": 3.8, "contrarian": 3.1}
    }
  },
  "company": { "..." : "..." }
}
```

### approval.json

```json
{
  "personal": {"approver": "self", "timeout_minutes": 120},
  "company": {"approver": "self", "timeout_minutes": 120}
}
```

---

## Branding

### Personal Account

Six visual templates (selected from playground, refined later):
- Dark Glassmorphism, Neon Gradient, Clean Editorial, Midnight Teal, Warm Mono, Polar Light

All share: "thegeshwar" watermark, consistent footer format, 1080x1350 (LinkedIn optimal).

### CU Circuits Company Page

**Brand identity from cucircuits.com:**
- Logo: Bold "Cu" monogram with circuit-node dot, "CIRCUITS" in wide-spaced caps
- Colors: Pure black (#000000) background, pure white (#FFFFFF) text/logo
- Tagline: "The Ability to build anything. Made Easy."
- Tone: Minimal, bold, confident
- Location: Chennai, India
- Services: PCB Manufacturing, 3D Printing

Six visual templates:
- Circuit Board Dark, Copper & Navy, Clean Fabrication, Solder Mask Blue, 3D Print Orange, India Tech Gradient

All share: CU Circuits logo, "cucircuits.com" footer, consistent brand presence.

---

## Content Pillars

### Personal

| Pillar | Description | Example |
|--------|-------------|---------|
| Breaking AI | Major AI/ML announcements, model releases, benchmarks | "GPT-5 just dropped — here's what's different" |
| Money Moves | Funding, acquisitions, market shifts | "Why VCs poured $2B into AI infra this week" |
| Builder's Edge | New tools, frameworks, developer experience | "This open-source tool replaces 3 paid services" |
| Policy & Ethics | Regulation, safety, societal impact | "EU AI Act is now enforceable — what changes" |
| Future Signals | Emerging trends, predictions, what to watch | "3 papers from this week that'll matter in 2027" |

### CU Circuits

| Pillar | Description | Example |
|--------|-------------|---------|
| DFM Tips | Design-for-manufacturing practical advice | "5 via mistakes that add $2 to your PCB cost" |
| Industry Intel | Supply chain, pricing, market trends | "Copper at 5-year low — what it means for your BOM" |
| New Tech | Manufacturing technology advances | "HDI PCBs under $5 — how Indian fabs made it possible" |
| Made in India | Indian manufacturing ecosystem growth | "India's PCB output grew 40% in 2025" |
| Customer Stories | Real products, from design to fab | "How a Bangalore startup went from breadboard to 10K units" |
| Standards & Process | IPC updates, certifications, best practices | "IPC-2581 is replacing Gerber — here's what to do" |

---

## Posting Schedule

### Personal
- **Frequency:** Start at 5 posts/week (weekdays only) for the first month to establish engagement baselines. Ramp to daily once the system is learning effectively. Posting with low engagement can train LinkedIn's algorithm to suppress the account.
- **Initial time:** 8:00 AM IST (optimized over time based on engagement data)
- **Optimization:** After 30 posts, Claude analyzes time-of-day engagement and suggests schedule changes

### CU Circuits
- **Frequency:** 3 posts/week (Mon, Wed, Fri)
- **Initial time:** 9:00 AM IST
- **Optimization:** Same as above

---

## Implementation Components

### Python utilities (minimal, Claude-driven)

1. **`src/generate/renderer.py`** — COMPLETE REWRITE REQUIRED. The current renderer is a multi-story digest layout (takes `list[dict]` of headlines+bullets). It must be rebuilt for single-story narrative layout:
   - New function signature: `render_story(story: StoryContent, template: str, format: str) -> Path`
   - `StoryContent` dataclass: `hook`, `headline`, `body_sections` (list of text blocks), `key_insight`, `source`, `footer_text`
   - Template system rebuilt for the 12 new visual styles (6 personal + 6 company)
   - Layout engine: hook at top (large), headline, flowing body text, insight callout box, branded footer
   - The old multi-story renderer is deleted

2. **`data/content-log.json`** — Flat JSON file per account (`personal-log.json`, `company-log.json`) to avoid write conflicts. Claude reads/writes directly.

3. **`data/config/approval.json`** — Approval configuration.

4. **`data/drafts/`** — Pending approval drafts as individual JSON files.

### Claude Code skills

1. **`/infographic personal`** — Interactive: draft + approve + post in one session
2. **`/infographic company`** — Interactive: draft + approve + post in one session
3. **`/infographic draft personal|company`** — Create draft, send for iMessage approval, exit (for cron)
4. **`/infographic post <id>`** — Post an approved draft (for cron or manual)
5. **`/infographic check`** — Engagement measurement for recent posts
6. **`/infographic stats`** — Show content log analysis (what's working, trends)
7. **`/infographic preview personal|company`** — Dry run: discover, select, create — shows output without sending approval or posting. For testing and development.
8. **`/infographic log --id X --likes N --comments N --shares N`** — Manual engagement entry fallback when scraping fails

### Scheduled triggers (cron)

1. Personal post — daily 8am IST
2. Company post — Mon/Wed/Fri 9am IST
3. Engagement check — daily 10pm IST

### Chrome DevTools MCP (for posting and measuring)

- Profile 2 (thejeshwa@gmail.com) for LinkedIn access
- Post creation, image upload, caption entry
- Company page posting via admin access
- Engagement metric scraping from post URLs

### iMessage (for approval)

- Send image + caption preview + alternatives
- Wait for reply
- Parse response (✅, 1, 2, ❌)

---

## What's NOT in Scope (YAGNI)

- No database (JSON files are fine for this volume)
- No web dashboard (use `/infographic stats` in CLI)
- No multi-platform (LinkedIn only for now)
- No autonomous posting without approval (always requires iMessage confirmation)
- No A/B testing within a single post (one strategy per post, compare across posts)
- No paid promotion integration
- No comment reply automation
