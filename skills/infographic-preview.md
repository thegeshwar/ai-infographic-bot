# Infographic Preview Skill

Dry-run of the content pipeline. Discovers news, selects a story, designs a unique infographic, shows the result. Does NOT post or send for approval.

## Usage
`/infographic preview personal` or `/infographic preview company`

## Steps

### 1. Read Context
- Read `skills/lib/content-pillars.md` for source guidance
- Read `skills/lib/strategy.md` for strategy options
- Read `skills/lib/design-rules.md` for MANDATORY visual design rules
- Check `data/personal-log.json` or `data/company-log.json` for history

### 2. Discover Stories
Use WebSearch for 5-8 trending stories relevant to the account.

### 3. Select ONE Story
Pick the best story for: relevance, timeliness, visual potential, pillar diversity.
Identify 2 alternatives with reasoning.

### 4. Select Strategy
Pick: voice, hook style, depth, caption style.
Rotate through untested combinations.

### 5. Research Deeply
Use WebSearch/WebFetch to read the full article and gather context, data, quotes.

### 6. Write Content
Create the text content:
- **hook**: Scroll-stopping opening (max 15 words)
- **headline**: Story in max 10 words, specific names and numbers
- **body**: 3-4 paragraphs telling the story in chosen voice
- **insight**: Unique takeaway nobody else is saying
- **caption**: LinkedIn caption that COMPLEMENTS the image (never repeats it). Ends with engagement prompt.
- **hashtags**: 5-8 strategic mix

### 7. Design the Infographic (CRITICAL STEP)

This is where you act as a CREATIVE DIRECTOR. Do NOT use a fixed template. Brainstorm the best visual approach for THIS specific story.

**Think about:** What visual format tells this story best?
- Stat with a big hero number and supporting data cards?
- Comparison/versus with side-by-side columns?
- Timeline with connected nodes showing progression?
- Process flow with numbered steps?
- Data dashboard with SVG charts?
- Icon grid with key facts?
- Bold statement (poster style, minimal)?
- Before/after showing transformation?
- Pyramid/hierarchy showing layers?
- Network diagram showing connections?

**Then write custom HTML/CSS.** The html field in StoryContent contains a complete 1080x1350 inline-styled HTML design. You must follow ALL rules in `skills/lib/design-rules.md`.

### 8. Render
```bash
cd ~/ai-infographic-bot && source .venv/bin/activate
python run.py render <json-path> --output-dir output
```

### 9. Show Results
Display image, caption, strategy, alternatives. Ask for feedback.

## Content Quality Bar
- Hook MUST stop the scroll
- Headline MUST be specific (names, numbers)
- Body MUST tell a story, not summarize
- Insight MUST be unique
- Caption MUST invite engagement
