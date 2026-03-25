# Infographic Preview Skill

Dry-run of the content pipeline. Discovers news, selects a story, generates the infographic and caption, shows the result. Does NOT post or send for approval.

## Usage
`/infographic preview personal` or `/infographic preview company`

## Steps

### 1. Read Context
- Read `skills/lib/content-pillars.md` for source guidance
- Read `skills/lib/strategy.md` for strategy options
- Check `data/personal-log.json` or `data/company-log.json` for history

### 2. Discover Stories
Use WebSearch for 5-8 trending stories relevant to the account.

### 3. Select ONE Story
Pick the best story for: relevance, timeliness, visual potential, pillar diversity.
Identify 2 alternatives with reasoning.

### 4. Select Strategy
Pick: voice, hook style, depth, caption style, visual template.
Rotate through untested combinations.

### 5. Research Deeply
Use WebSearch/WebFetch to read the full article and gather context, data, quotes.

### 6. Write Content
Create a StoryContent JSON:
- **hook**: Scroll-stopping opening (max 15 words)
- **headline**: Story in max 10 words, specific names
- **body**: 3-4 paragraphs telling the story in chosen voice
- **insight**: Unique takeaway nobody else is saying
- **caption**: LinkedIn caption that complements (not repeats) the image
- **hashtags**: 5-8 strategic mix

Save to `data/drafts/<account>-<date>-<slug>.json`

### 7. Render
```bash
cd ~/ai-infographic-bot && source .venv/bin/activate
python run.py render <json-path> --template <template> --output-dir output
```

### 8. Show Results
Display image, caption, strategy, alternatives. Ask for feedback.

## Quality Bar
- Hook MUST stop the scroll
- Headline MUST be specific (names, numbers)
- Body MUST tell a story, not summarize
- Insight MUST be unique
- Caption MUST invite engagement
