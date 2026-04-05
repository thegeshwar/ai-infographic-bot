# Infographic Design Rules

MANDATORY rules for every infographic. Violating these produces low quality output.

## Accuracy Above All
Every visual element must be factually correct. If a legend has 4 colors, all 4 must appear in the graphic AND the legend. If locations are plotted, they must be in the correct relative positions. If a chart shows growth, the bars must actually increase. **Never fake visual accuracy.** If you cannot represent something accurately (like a detailed country outline), use an abstract alternative that is honest about what it is. An inaccurate graphic is worse than no graphic.

## Container
- Exactly `width:1920px; height:1080px` (16:9 landscape, LinkedIn article format)
- All styles inline. All SVGs inline. No external assets, fonts, or images.
- Must render cleanly in headless Chromium.
- **LANDSCAPE LAYOUT**: This is a wide format. Think cinematic, editorial spreads — NOT tall stacked mobile layouts. Use the full horizontal space with multi-column designs.

## Typography (LARGE — this is viewed on screens and phones)
- Hero numbers: 100px to 120px font-weight 900, tight letter-spacing. NEVER above 140px.
- Stat numbers: 44px to 56px font-weight 900
- Section headers: 26px to 34px font-weight 700
- Body/description text: 20px to 24px, font-weight 300 to 400, line-height 1.5 to 1.7. Use max-width of columns (typically 600px to 800px per column) to keep line lengths comfortable.
- Labels under stats: 18px to 22px font-weight 300 to 400, uppercase, letter-spacing 2px+. NEVER below 18px.
- Chart axis labels and values: 18px+ minimum
- Chart bar/line labels: 18px+ minimum
- Footer: 13px muted text
- **BALANCE RULE:** The ratio between your largest text and smallest text (excluding footer) should not exceed 7:1.
- **HORIZONTAL RULE:** In landscape, text blocks should NOT span the full 1920px width. Use columns (2-3 columns) or constrain text to 600-800px max-width sections. Let the layout breathe horizontally.

## Infographic Types

Not every story is best told with stats. Choose the type that best serves the story's data and narrative.

### Stat-Driven
Big numbers, charts, data grids. The classic infographic.
- Two-Column Split (60/40 or 50/50): hero stat left, supporting data right
- Three-Column Dashboard: equal columns, each a data point
- Hero Left + Data Right: large number anchors the left, structured data fills right

### Timeline
Progression, milestones, historical change.
- Left-to-right horizontal timeline spanning the full width
- Nodes evenly spaced with visible connecting line (4px+ stroke)
- Data/labels above and below the timeline

### Process / Flow
How something works, supply chains, step-by-step.
- Horizontal flow with arrows or connected nodes
- Each step is a visual block with icon + short label
- Works well as a full-width band across the middle

### Comparison / Versus
Two things side by side: countries, products, before/after.
- Left vs Right split with color-coded sides
- Matching metrics on each side for easy scanning
- Clear visual "winner" highlights where applicable

### Map / Geographic
Regional stories, trade flows, where things come from.

**NEVER freehand SVG map outlines.** Use the map generator to get accurate geographic SVG:

```bash
python3 scripts/generate_map.py --country India --states \
  --highlight "Gujarat:#FF9933,Assam:#138808" \
  --label "Sanand:23.0,72.4" --label "Morigaon:26.2,92.3" \
  --width 700 --height 700
```

The script outputs clean inline SVG with accurate Natural Earth boundaries. Embed its output directly in your HTML. Available options:
- `--country NAME` with optional `--states` for state/province boundaries
- `--countries "India,China,Japan"` for multi-country maps
- `--highlight "Region:#hexcolor"` to color-fill specific states or countries
- `--label "City:lat,lon"` to place named markers (use correct coordinates)
- `--style dark|light` for stroke/fill presets matching your background
- `--width` and `--height` to fit your layout

The map is a visual element inside your design. The SVG map handles geography; you handle the data storytelling.

**Map label rules (MANDATORY when using maps):**
- **NEVER overlay text labels on the map using absolute positioning.** Labels positioned with percentage coordinates overlap when locations are close together. This is the #1 cause of garbled, unreadable map infographics.
- **Use a numbered legend pattern instead:**
  1. Place small numbered markers (circles with numbers) on the map at each location
  2. Put the legend (numbered list with details) in a separate column or below the map
  3. Each legend entry: number + city/state + company + investment amount
- **If you must label directly on the map**, limit to 2 locations maximum and ensure at least 150px vertical separation between labels.
- **For 3+ locations:** Always use the numbered legend pattern. No exceptions.
- **Map sizing:** Maps with legends work best in a 55/45 or 60/40 two-column split — map on one side, legend + stats on the other. Do NOT cram both into one column.

### Anatomy / Diagram
Breaking down a product, system, or concept.
- Central illustration with labeled callout lines pointing to components
- Great for "inside a PCB", "layers of a chip", "parts of a system"

### Ranking / Leaderboard
Top N lists, market share, competitive positioning.
- Horizontal bars or stepped podium layout
- Ranked top to bottom or left to right
- Size/color encoding for magnitude

### Quote / Callout
Expert insights, bold claims, opinion-led pieces.
- Large quote text (50-70px) as the hero element
- Attribution + context arranged around it
- Supporting data or stats in secondary position

### Full-Width Cinematic
Bold single-statement stories.
- Large background visual/gradient treatment
- Centered text block (max 900px wide) floating on the background
- Minimal data, maximum visual impact

## Icons and Logos
- NEVER use emoji for icons. Not ever. Not even "just one."
- Use inline SVG line drawings: clean, minimal, monochrome strokes
- SVG icons should be 24x24 to 32x32 for inline use, 40x40+ for featured use
- Keep icons simple: 1-2 colors max, thin clean lines (stroke-width 1.5 to 2)
- Flag emoji (🇮🇳) are the ONLY acceptable emoji, and only when discussing countries
- When icons are not needed, leave them out. White space is better than bad icons.
- **REAL COMPANY LOGOS**: When a story mentions specific companies, create inline SVG recreations of their recognizable logo marks. Simplified but clearly identifiable:
  - Google: the 4-color "G" mark (blue #4285F4, red #EA4335, yellow #FBBC05, green #34A853)
  - NVIDIA: green (#76B900) stylized eye/swoosh mark
  - Samsung: blue (#1428A0) wordmark
  - OpenAI: black hexagonal flower logo
  - Apple: simple apple silhouette
  - Meta: blue infinity loop
  - Microsoft: 4-color window grid
  - Keep SVG logos at 32x32 to 48x48, clean paths only

## Color (FULL CREATIVE FREEDOM)

You choose the palette. Dark or light backgrounds, any accent color. The only rules:

- **Story-driven color.** The accent color should reflect the story's subject matter. Gold/amber for financial stories, green for sustainability or growth, red/coral for disruption or urgency, blue for data or technology, warm tones for manufacturing/hardware, cool tones for software/AI. Make the viewer feel the subject through color before reading a word.
- **Restrained palette.** ONE dominant accent + white/black + 2-3 supporting tones. No rainbow. No neon. No glow effects (box-shadow with blur > 4px).
- **Light backgrounds are welcome.** Cream (#faf8f5), warm white (#f5f0eb), cool white (#f0f4f8), light gray (#eef0f2). Pair with dark text and a strong accent. Light backgrounds work especially well for data-heavy, editorial, or research posts.
- **Dark backgrounds remain strong.** Go beyond generic navy. Try: warm charcoal (#1a1410), deep teal (#0a1a1a), dark plum (#140a18), muted forest (#0a140e), near-black with warm undertone (#12100e).
- **Company posts:** The Cu Circuits logo renders best on dark backgrounds. On light backgrounds, the render engine auto-applies `filter:invert(1)`. Both work.
- **Contrast rule:** Text must be immediately readable. Light text on dark bg OR dark text on light bg. Never muddy mid-tones on mid-tones.

## Layout Spacing & Golden Ratio Placement (CRITICAL)

**THE #1 RULE: No gaps, no overlaps.** Content must flow naturally from top to bottom within each column with consistent spacing. The viewer's eye should never hit a void or a collision.

### Golden Ratio Content Distribution
Use the golden ratio (1:1.618) to place content vertically within the 1080px height:
- **Primary content zone** (top 61.8% = ~668px from top): Hero numbers, headlines, key stats, main data
- **Secondary content zone** (bottom 38.2% = ~412px): Supporting data, charts, insight, components
- The **golden line** sits at ~668px from the top. Your most important visual element should anchor near the top, and secondary content should fill below naturally.

### NO OVERLAPPING ELEMENTS (CRITICAL — THE #1 QUALITY ISSUE)

Overlapping happens when content exceeds the 1080px container. Follow this technique:

**Use a single flex column as your root layout:**
```html
<div style="width:1920px; height:1080px; overflow:hidden; display:flex; flex-direction:column;">
  <div style="height:100px; flex-shrink:0;"><!-- Header --></div>
  <div style="flex:1; display:flex; overflow:hidden;"><!-- Content columns --></div>
  <div style="height:60px; flex-shrink:0;"><!-- Footer --></div>
</div>
```

**Inside each column, use `overflow:hidden`** so content never spills outside its bounds.

**Limit to 3-5 content sections per column.** More than 5 items WILL overlap.

**Use flex ratios, not pixel heights, for children inside flex containers.** Pixel heights (height:250px, height:300px) overflow when they add up to more than the container. Use `flex:1` / `flex:2` instead.

**Overflow check after writing HTML:** Count every explicit `height: Npx` (excluding the 1080 container). If the sum exceeds 1000px, you have overlap. Fix by removing elements or converting to flex ratios.

### BANNED: justify-content: space-between on columns
- **NEVER** use `justify-content: space-between` on vertical flex containers.
- **INSTEAD** use `justify-content: center` or `flex-start` with explicit margins.

### Vertical Space Budget (1080px)
- Header zone: ~100px
- Footer zone: ~60px
- **Available content: ~920px**
- Max 3-5 sections per column. If 3 sections, ~300px each. If 5, ~180px each.

### General Spacing
- Generous whitespace. Minimum 50px padding on all sides. 60-80px preferred on left/right.
- Content must NEVER overflow the 1080px height. Plan your layout before writing HTML.
- Visual hierarchy: the most important element is HUGE, supporting info progressively smaller.
- No walls of text on the infographic. The image is VISUAL. The caption handles storytelling.
- **CRITICAL: MINIMAL BOXES.** Do NOT put everything in bordered cards/boxes. Maximum 1 to 2 boxed elements per entire design. Use open layouts: plain text on background, horizontal/vertical divider lines, whitespace separation, subtle accent lines.
- **BOX STYLE RULES:** When you DO use a box (max 1 to 2), NEVER use generic rounded corners (border-radius 12px+ with a border). Instead:
  - **Left accent border only**: `border-left: 4px solid accent; padding-left: 24px;` no other borders
  - **Bottom accent underline**: thick colored underline below a section
  - **Sharp corners with subtle background**: `border-radius: 0` or max `2px`, barely-there background tint (rgba at 0.04 to 0.08)
  - **Clipped corner / angled edge**: use `clip-path` for one sharp diagonal corner
  - **Full-bleed color block**: solid background color spanning edge to edge, no visible border
  - NEVER: `border-radius: 8px+` with `border: 1px solid`. That looks like every AI-generated dashboard.

## Data Visualization
- Use SVG for charts: proper `<path>`, `<line>`, `<rect>`, `<circle>` elements
- Never use colored divs as fake charts
- In landscape, charts can be WIDER — take advantage of horizontal space. Charts can span 600-900px wide.
- Area charts: SVG path with gradient fill underneath
- Bar charts: SVG rects with proper spacing
- Include axis labels on charts (small, muted text)

## Timelines and Process Flows
- In landscape, timelines run LEFT TO RIGHT (horizontal), not top to bottom
- ALWAYS include a visible connecting line between nodes (4px+ stroke width)
- The line runs continuously from first to last node
- Each node sits ON the line, not floating beside it
- Use SVG for the line and node circles
- Minimum node circle size: 32px diameter
- Space nodes evenly across the available horizontal width

## Network/Constellation Diagrams
- Central node: 120px+ diameter, solid fill background
- Satellite nodes: 70px+ diameter, solid fill backgrounds
- Connecting lines: 3px+ stroke width, visible color
- All node labels: 18px+ minimum
- In landscape, spread the diagram wider — use the horizontal space

## Pyramid/Hierarchy Shapes
- Use SVG polygon or clip-path for proper trapezoid shapes
- In landscape, pyramids can be rendered HORIZONTALLY (left = narrow/top, right = wide/base)
- Top layer must be at least 240px wide (enough for readable text)
- Text inside layers: 18px+ minimum

## Background Design (STORY-DRIVEN, NOT DECORATIVE)

The background is part of the story, not wallpaper. It should reinforce what the infographic is about.

**The principle:** A viewer should be able to guess the subject from the background alone, before reading any text. A post about semiconductor supply chains should feel different from a post about AI funding rounds. The background sets the emotional and thematic context.

**How to think about it:**
- A story about PCB manufacturing: subtle circuit trace patterns, solder-point grids, layered board cross-sections
- A story about market data or finance: clean editorial grids, subtle chart-line echoes, ledger-like structure
- A story about a country (India, US, China): map contour silhouettes, geographic patterns, flag-inspired color zones
- A story about growth or milestones: ascending line motifs, staircase patterns, horizon gradients
- A story about disruption or crisis: fractured geometry, sharp angles, high-contrast splits
- A story about AI or technology: neural mesh patterns, node networks, data flow lines

**Execution:**
- All background elements are SVG (inline) at opacity 0.06 to 0.25. Never below 0.05 or above 0.35.
- Every post MUST have at least one meaningful background element. Plain flat backgrounds look cheap.
- SVG `<pattern>` tiles (60x60 to 80x80) work well for repeating motifs.
- Gradient orbs add depth: soft radial gradients at 0.08 to 0.15 opacity, placed to complement the layout.
- **Vary backgrounds between consecutive posts.** Never repeat the same pattern type back to back.

## Comparison Layouts
- In landscape, comparisons work especially well as LEFT vs RIGHT columns
- Use color coding consistently (same color = same entity throughout)
- SVG progress bars or indicators for each metric
- Clear "winner" highlights where applicable

## Balance Content and Graphics (CRITICAL)

An infographic needs BOTH meaningful text content AND visual elements working together. Too much text makes it a document screenshot. Too many graphics with no context makes it look empty and purposeless. The goal is a well-distributed design where every element earns its space.

**Why this matters:** The best infographics have clear, scannable text (headlines, stats, short labels) supported by graphics that make the data tangible. If someone glances at it for 3 seconds, they should understand the story from the big numbers and visuals. If they look for 10 seconds, the supporting text adds depth.

**Text budget:** Aim for 400 to 1200 characters of visible text (excluding footer). Under 400 looks empty and purposeless. Over 1200 means you're writing paragraphs — cut to punchy labels and let graphics carry the data.

**Graphics budget:** Include 2 to 6 meaningful SVG visual elements (charts, diagrams, data visualizations). More than 6 risks overlapping and clutter. Fewer than 2 makes it a text card. Each SVG should serve a clear purpose — don't add graphics just to hit a number.

**Good visual elements to use (pick 2 to 4 per infographic):**
- SVG bar/line/area charts for trends or comparisons
- Large stat numbers (80px+) with small labels — the number IS the graphic
- SVG icon+stat pairs (icon left, number right)
- SVG horizontal bar comparisons (before vs after)
- SVG timelines with visual nodes for chronological stories

**The distribution rule:** Every element must have breathing room. If you can't fit a visual without it overlapping a neighbor, remove the visual — whitespace is better than collision. Place graphics where they support adjacent text, not crammed into leftover space.

**What does NOT count as a graphic element:**
- Background decorative patterns (those are atmosphere, not content)
- Company logos
- Text in a colored box

## Center Alignment (MANDATORY — NO EXCEPTIONS)

All content in every infographic must be center-aligned. This is not a suggestion — it is a hard rule that applies to every element.

**Why:** Left-aligned and top-aligned content creates uneven gaps, especially in multi-column layouts where columns have different amounts of content. Center alignment guarantees visual balance regardless of content length. It also looks more polished and editorial — like a magazine spread, not a code readme.

**How to implement:**

1. **The outer container** must center its children both horizontally and vertically:
   ```
   display:flex; justify-content:center; align-items:center; text-align:center;
   ```

2. **Every text element** must have `text-align:center` — headings, stats, labels, body text, footer. No exceptions.

3. **Every flex container** (columns, rows, sections) must use:
   - `align-items:center` for cross-axis centering
   - For vertical stacking: `justify-content:center` or `justify-content:flex-start` with equal top/bottom padding to visually center

4. **Multi-column layouts:** Each column's content must be vertically centered within that column. If the left column has more content than the right, the right column's content should sit centered in its space, not pinned to the top.

5. **Stat blocks, labels, icons:** Always centered under/over their associated element.

6. **BANNED alignments:**
   - `text-align:left` — never use this anywhere in the infographic
   - `text-align:right` — never (except footer source attribution)
   - `align-items:flex-start` without compensating padding — content must not hug the top
   - Any layout where content clusters in one corner while the opposite corner is empty

**Self-check:** After writing HTML, search for `text-align:left` and `text-align: left`. If found, replace with `text-align:center`. Search for `align-items:flex-start` — if found, verify the content is visually centered with padding, or switch to `align-items:center`.

## Text Content Rules
- NEVER use dashes: -, --, —, or –. Rewrite the sentence.
- Keep text on the infographic SHORT. Punchy labels, not paragraphs.
- The caption (not the image) carries the narrative depth.

## Footer
- Personal: "thegeshwar" bottom right, source bottom left
- Company: "cucircuits.com" bottom left, source bottom right
- Cu Circuits logo (company only): top left, positioned at `top:36px;left:24px` (not flush to the edge). **DO NOT copy base64 from these instructions.** Generate at render time:
  ```bash
  base64 -i ~/ai-infographic-bot/assets/cu-circuits-logo.png | tr -d '\n'
  ```
  Then: `<img src="data:image/png;base64,<OUTPUT>" alt="Cu Circuits" style="height:72px;width:auto;" />`
  On light backgrounds, add CSS `filter: invert(1)`.
  **IMPORTANT:** The base64 is ~19,000 chars. Always generate from file.
  Do NOT use a green square, do NOT recreate as SVG paths.
- Thin separator line above footer (1px, muted color)

## Before Rendering, Self-Check
Ask yourself:
1. Is any text smaller than 18px (excluding footer)? Fix it. All content text must be 18px+.
2. Is the hero number above 140px? Reduce it.
3. Are there more than 2 bordered boxes/cards? Remove them. Use open layout.
4. Do any boxes have border-radius 8px+? Use sharp corners or left-accent-border instead.
5. Will content overflow 1080px HEIGHT? Count your vertical space.
6. Are there any emoji? Remove them.
7. Are there any dashes in text? Rewrite.
8. Do timelines run horizontally (left to right)? They should in landscape.
9. Are decorative elements visible? Check opacity.
10. Are company logos included as inline SVGs where relevant?
11a. For company posts: is the Cu Circuits logo generated from the asset file?
11. Is the layout using the full 1920px width effectively with columns/splits? No narrow centered strips.
12. Does this look like a design agency made it, or like AI? Be honest.
13. **GOLDEN RATIO CHECK:** Add up all content block heights + gaps per column. Does each column fill 75%+ of available height? Is the max gap between any two blocks under 60px? If not, redistribute content.
14. **NO space-between CHECK:** Search your HTML for `space-between` on vertical flex containers. Replace with `flex-start` + explicit margins.
15. **OVERLAP CHECK:** Does any text block risk colliding with its neighbor if content were slightly longer? Add buffer margins.
16. **MAP LABEL CHECK:** If you have a map with locations, are you using a numbered legend (not overlaid text labels)? Do you have 3+ labels positioned directly on the map? If yes, STOP and switch to the numbered legend pattern.
17. **LEGEND CHECK:** If you have a color-coded legend, does every color in the graphic appear in the legend AND vice versa? No orphan colors.
18. **ACCURACY CHECK:** Are geographic positions correct? Are chart values proportional? Do labels match the data? Would an expert in this field spot an error?
