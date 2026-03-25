# Infographic Design Rules

MANDATORY rules for every infographic. Violating these produces low quality output.

## Container
- Exactly `width:1080px; height:1350px` (LinkedIn optimal)
- All styles inline. All SVGs inline. No external assets, fonts, or images.
- Must render cleanly in headless Chromium.

## Typography (LARGE — this is viewed on phones)
- Hero numbers: 160px+ font-weight 900, tight letter-spacing
- Stat numbers: 56px+ font-weight 900
- Section headers: 28px+ font-weight 700
- Body/description text: 18px+ minimum. Never smaller.
- Labels/captions: 14px+ font-weight 300, uppercase, letter-spacing 2px+
- Footer: 12px muted text

## Icons
- NEVER use emoji for icons. Not ever. Not even "just one."
- Use inline SVG line drawings: clean, minimal, monochrome strokes
- SVG icons should be 24x24 to 32x32 for inline use, 40x40+ for featured use
- Keep icons simple: 1-2 colors max, thin clean lines (stroke-width 1.5 to 2)
- Flag emoji (🇮🇳) are the ONLY acceptable emoji, and only when discussing countries
- When icons are not needed, leave them out. White space is better than bad icons.

## Color
- Restrained palette: ONE accent color + white + 2-3 grays on the background
- Personal branding: dark backgrounds (#0a0a1a to #0d1117), accent blue (#4f8cff)
- CU Circuits branding: dark bg (#0a0a0a to #111), accents: copper (#cd7f32), PCB green (#006644), or orange (#ff6600)
- CU Circuits light variant: #fafafa bg, green (#006644) accent (use for market data/research posts)
- No rainbow. No neon. No glow effects (box-shadow with blur > 4px).

## Layout
- Generous whitespace. Minimum 60px padding on all sides.
- Content must NEVER overflow the 1350px height. Plan your layout before writing HTML.
- Visual hierarchy: the most important element is HUGE, supporting info progressively smaller.
- No walls of text on the infographic. The image is VISUAL. The caption handles storytelling.

## Data Visualization
- Use SVG for charts: proper `<path>`, `<line>`, `<rect>`, `<circle>` elements
- Never use colored divs as fake charts
- Area charts: SVG path with gradient fill underneath
- Bar charts: SVG rects with proper spacing
- Include axis labels on charts (small, muted text)

## Timelines and Process Flows
- ALWAYS include a visible connecting line between nodes (4px+ stroke width)
- The line runs continuously from first to last node
- Each node sits ON the line, not floating beside it
- Use SVG for the line and node circles
- Minimum node circle size: 36px diameter

## Network/Constellation Diagrams
- Central node: 140px+ diameter, solid fill background (not just a thin border)
- Satellite nodes: 80px+ diameter, solid fill backgrounds
- Connecting lines: 3px+ stroke width, visible color
- All node labels: 18px+ minimum
- The diagram should feel SOLID and substantial, not thin and wispy

## Pyramid/Hierarchy Shapes
- Use SVG polygon or clip-path for proper trapezoid shapes
- Top layer must be at least 280px wide (enough for readable text)
- Each layer clearly wider than the one above
- Text inside layers: 20px+ minimum

## Background Decorative Elements
- Decorative SVGs (rings, grids, dots, traces) add visual richness
- Opacity range: 0.08 to 0.25. Never below 0.05 (invisible) or above 0.35 (distracting).
- Options to use:
  - **Dot grid**: scattered small SVG circles at varying sizes/opacities
  - **Circuit traces**: right-angle SVG paths with via dots (great for CU Circuits)
  - **Concentric rings**: behind hero numbers, stroke-width 2-3px
  - **Geometric mesh**: connected dots forming triangles
  - **Wave patterns**: SVG sine wave paths along edges
  - **Gradient orbs**: soft radial gradient circles for depth
- Every post should have at least one subtle decorative element. Plain flat backgrounds look cheap.

## Comparison Layouts
- Two columns with clear visual separation
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
- Cu logo (company only): 36x36 green (#006644) square, white "Cu" text, top left, 4px border-radius
- Thin separator line above footer (1px, muted color)

## Before Rendering, Self-Check
Ask yourself:
1. Is any text smaller than 18px? Fix it.
2. Will content overflow 1350px? Count your vertical space.
3. Are there any emoji? Remove them.
4. Are there any dashes in text? Rewrite.
5. Do timelines have connecting lines? Add them.
6. Are decorative elements visible? Check opacity.
7. Does this look like a design agency made it, or like AI? Be honest.
