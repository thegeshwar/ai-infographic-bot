# Infographic Design Rules

MANDATORY rules for every infographic. Violating these produces low quality output.

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
- Labels under stats: 16px to 20px font-weight 300 to 400, uppercase, letter-spacing 2px+. NEVER below 14px.
- Chart axis labels and values: 14px+ minimum
- Chart bar/line labels: 16px+ minimum
- Footer: 13px muted text
- **BALANCE RULE:** The ratio between your largest text and smallest text (excluding footer) should not exceed 7:1.
- **HORIZONTAL RULE:** In landscape, text blocks should NOT span the full 1920px width. Use columns (2-3 columns) or constrain text to 600-800px max-width sections. Let the layout breathe horizontally.

## Landscape Layout Patterns
Choose from these proven 1920x1080 layout approaches:

### Two-Column Split (60/40 or 50/50)
- Left side: hero number/stat + headline + key insight
- Right side: supporting data, chart, or stat grid
- Vertical divider line or color block separating halves

### Three-Column Dashboard
- Equal or weighted columns across the width
- Each column holds a stat, chart, or data point
- Connected by a horizontal header bar or timeline

### Hero Left + Data Right
- Large hero element (number, icon, logo) takes the left 40%
- Right 60% contains structured data: stats, bullet points, mini charts
- Strong visual weight on the left anchors the eye

### Full-Width Cinematic
- Large background visual/gradient treatment
- Centered text block (max 900px wide) floating on the background
- Best for bold-statement or single-stat stories

### Timeline Horizontal
- Left-to-right timeline spanning the full width
- Nodes evenly spaced across 1920px
- Data/labels above and below the timeline line

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

## Color
- Restrained palette: ONE accent color + white + 2-3 grays on the background
- Personal branding: dark backgrounds (#0a0a1a to #0d1117), accent blue (#4f8cff)
- CU Circuits branding: dark bg (#0a0a0a to #111), accents: copper (#cd7f32), PCB green (#006644), or orange (#ff6600)
- CU Circuits light variant: #fafafa bg, green (#006644) accent (use for market data/research posts)
- No rainbow. No neon. No glow effects (box-shadow with blur > 4px).

## Layout Spacing & Golden Ratio Placement (CRITICAL)

**THE #1 RULE: No gaps, no overlaps.** Content must flow naturally from top to bottom within each column with consistent spacing. The viewer's eye should never hit a void or a collision.

### Golden Ratio Content Distribution
Use the golden ratio (1:1.618) to place content vertically within the 1080px height:
- **Primary content zone** (top 61.8% = ~668px from top): Hero numbers, headlines, key stats, main data
- **Secondary content zone** (bottom 38.2% = ~412px): Supporting data, charts, insight, components
- The **golden line** sits at ~668px from the top. Your most important visual element should anchor near the top, and secondary content should fill below naturally.

### BANNED: justify-content: space-between on columns
- **NEVER** use `justify-content: space-between` on vertical flex containers for content layout. This creates massive gaps between top and bottom content blocks.
- **INSTEAD** use `justify-content: flex-start` and control spacing with explicit `margin-bottom` values between sections.
- Use consistent vertical rhythm: 24px between related items, 40-48px between sections, 60px between major zones.

### Vertical Space Budget (1080px)
Before writing HTML, calculate your vertical space:
- Top padding: 60px
- Bottom footer + padding: 60px
- **Available content height: ~960px**
- Divide this among your content blocks. If you have 4 sections, each gets ~240px max. If 3 sections, ~320px each.
- **Add up all your content heights + gaps BEFORE coding.** If the total exceeds 960px, cut content. If it's under 700px, your content is too sparse — add more data or increase spacing proportionally.

### Gap Prevention Rules
- Every column must have content that spans at least 75% of the available vertical height (720px of 960px usable)
- Between any two content blocks, the gap must be between 24px and 60px. Never more than 60px between adjacent content.
- If a column has fewer content blocks, increase the size of existing elements (larger charts, bigger stat numbers, more generous line-height) rather than leaving dead space.

### Overlap Prevention Rules
- Always use `box-sizing: border-box` on all content containers
- When using absolute positioning, calculate exact pixel positions — never eyeball it
- For flex layouts, set explicit `min-height` and `max-height` on sections to prevent content from growing into neighbors
- Test: if your largest text block were 20% longer, would it collide with the next section? Build in that buffer.

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
- All node labels: 16px+ minimum
- In landscape, spread the diagram wider — use the horizontal space

## Pyramid/Hierarchy Shapes
- Use SVG polygon or clip-path for proper trapezoid shapes
- In landscape, pyramids can be rendered HORIZONTALLY (left = narrow/top, right = wide/base)
- Top layer must be at least 240px wide (enough for readable text)
- Text inside layers: 18px+ minimum

## Background Decorative Elements
- Decorative SVGs add visual richness
- Opacity range: 0.08 to 0.25. Never below 0.05 or above 0.35.
- Options:
  - **Dot grid**: scattered small SVG circles at varying sizes/opacities
  - **Circuit traces**: right-angle SVG paths with via dots (great for CU Circuits)
  - **Concentric rings**: behind hero numbers, stroke-width 2-3px
  - **Geometric mesh**: connected dots forming triangles
  - **Wave patterns**: SVG sine wave paths along edges
  - **Gradient orbs**: soft radial gradient circles for depth
  - **Topic icon grid** (RECOMMENDED): Repeating pattern of muted SVG line icons related to the story topic. Use SVG `<pattern>` with 60x60 to 80x80 tiles. Accent color at opacity 0.04 to 0.10.
- Every post MUST have at least one decorative background element. Plain flat backgrounds look cheap.

### CRITICAL: Background Variety Rule
- **DO NOT reuse the same background pattern across consecutive posts.**
- **Vary these independently:**
  1. **Main background**: Don't always use dark navy. Try: dark warm charcoal (#1a1410), deep teal (#0a1a1a), dark plum (#140a18), muted dark green (#0a140e), near-black with warm undertone (#12100e).
  2. **Pattern type**: Rotate between dot grids, topic icon grids, wave patterns, geometric mesh, concentric rings.
  3. **Orb placement**: Vary — centered behind hero, single large orb off one edge, horizontal band, bottom glow, or no orbs.

## Comparison Layouts
- In landscape, comparisons work especially well as LEFT vs RIGHT columns
- Use color coding consistently (same color = same entity throughout)
- SVG progress bars or indicators for each metric
- Clear "winner" highlights where applicable

## Text Content Rules
- NEVER use dashes: -, --, —, or –. Rewrite the sentence.
- Keep text on the infographic SHORT. Punchy labels, not paragraphs.
- The caption (not the image) carries the narrative depth.

## Footer
- Personal: "thegeshwar" bottom right, source bottom left
- Company: "cucircuits.com" bottom left, source bottom right
- Cu Circuits logo (company only): top left corner. **DO NOT copy base64 from these instructions.** Generate at render time:
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
1. Is any text smaller than 14px (excluding footer)? Fix it. Labels should be 16px+.
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
