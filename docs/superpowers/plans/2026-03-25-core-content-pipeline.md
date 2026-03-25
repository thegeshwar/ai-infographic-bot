# Core Content Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core content generation pipeline (discover → select → create) and use it to generate 8 test posts per account, displayed on test.dev.thegeshwar.com for review.

**Architecture:** Claude Code skills drive the pipeline. A Python renderer creates infographic images from structured content. No Anthropic API calls from code — Claude itself writes all content. The old multi-story digest code is deleted and replaced with a single-story narrative renderer.

**Tech Stack:** Python (Pillow for image rendering), Claude Code skills (YAML), HTML/CSS for test.dev gallery

---

## File Map

### Delete (old digest architecture — no longer needed)
- `src/discover/` — entire directory (Claude does discovery, not Python)
- `src/curate/` — entire directory (Claude does curation, not Python)
- `src/post/` — entire directory (rebuilt later in Phase 2)
- `src/pipeline.py` — old orchestrator
- `src/notify.py` — rebuilt later
- `src/history.py` — rebuilt later
- `src/logging_config.py` — rebuilt later
- `tests/test_discover.py`, `tests/test_curate.py`, `tests/test_post.py`, `tests/test_automation.py` — old tests
- `scripts/` — rebuilt later

### Create (new single-story renderer)
- `src/render/__init__.py` — package init
- `src/render/model.py` — `StoryContent` dataclass (the content contract between Claude and the renderer)
- `src/render/templates.py` — 12 visual templates (6 personal + 6 CU Circuits)
- `src/render/engine.py` — single-story layout engine (Pillow-based)
- `src/render/fonts.py` — font loading helper
- `src/render/cli.py` — CLI to render a story from a JSON file (for testing)
- `tests/test_render.py` — renderer tests

### Create (content generation skill)
- `.claude/skills/infographic-preview.md` — the `/infographic preview` skill definition
- `.claude/skills/lib/strategy.md` — strategy rotation instructions for Claude
- `.claude/skills/lib/content-pillars.md` — pillar definitions and discovery sources

### Create (data files)
- `data/config/templates.json` — template registry (maps template names to rendering params)
- `data/config/pillars.json` — content pillar definitions per account
- `data/config/strategies.json` — all variable options (voice, format, hook, depth, caption style)

### Create (test gallery)
- `gallery/index.html` — test.dev gallery page showing all generated test posts
- `gallery/posts/` — generated images + caption JSON files

### Modify
- `requirements.txt` — remove `anthropic`, `feedparser`, `beautifulsoup4`, `schedule`; keep `Pillow`, `click`, `python-dotenv`, `httpx`
- `run.py` — simplified CLI with just `render` subcommand for now
- `src/config.py` — simplified (remove social media creds, keep paths)

---

## Task 1: Clean Out Old Architecture

**Files:**
- Delete: `src/discover/`, `src/curate/`, `src/post/`, `src/pipeline.py`, `src/notify.py`, `src/history.py`, `src/logging_config.py`
- Delete: `tests/test_discover.py`, `tests/test_curate.py`, `tests/test_post.py`, `tests/test_automation.py`
- Delete: `scripts/`
- Modify: `requirements.txt`
- Modify: `src/config.py`

- [ ] **Step 1: Delete old source modules**

```bash
rm -rf src/discover src/curate src/post src/pipeline.py src/notify.py src/history.py src/logging_config.py
rm -rf tests/test_discover.py tests/test_curate.py tests/test_post.py tests/test_automation.py tests/test_generate.py
rm -rf scripts/
```

- [ ] **Step 2: Simplify requirements.txt**

```
httpx>=0.27
Pillow>=11.0
python-dotenv>=1.0
click>=8.1
```

- [ ] **Step 3: Simplify src/config.py**

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / os.getenv("OUTPUT_DIR", "output")
GALLERY_DIR = ROOT_DIR / "gallery"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove old digest pipeline, simplify for content engine rebuild"
```

---

## Task 2: Story Content Model

**Files:**
- Create: `src/render/__init__.py`
- Create: `src/render/model.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_render.py
"""Tests for the single-story renderer."""

from src.render.model import StoryContent


class TestStoryContent:
    def test_create_minimal(self):
        story = StoryContent(
            hook="This changes everything.",
            headline="GPT-5 Scores 95% on ARC-AGI",
            body=[
                "OpenAI's latest model just achieved what many thought impossible.",
                "The ARC-AGI benchmark tests genuine reasoning ability.",
            ],
            insight="This isn't incremental. It's a phase change in AI capability.",
            source="TechCrunch",
            source_url="https://techcrunch.com/gpt5",
            pillar="breaking-ai",
            account="personal",
        )
        assert story.hook == "This changes everything."
        assert story.account == "personal"
        assert len(story.body) == 2

    def test_defaults(self):
        story = StoryContent(
            hook="Hook",
            headline="Headline",
            body=["Body"],
            insight="Insight",
            source="Source",
            source_url="https://example.com",
            pillar="industry-intel",
            account="company",
        )
        assert story.hashtags == []
        assert story.caption == ""
        assert story.strategy == {}

    def test_to_dict_roundtrip(self):
        story = StoryContent(
            hook="Hook",
            headline="Headline",
            body=["Line 1", "Line 2"],
            insight="Insight",
            source="Source",
            source_url="https://example.com",
            pillar="breaking-ai",
            account="personal",
            hashtags=["#AI", "#Tech"],
            caption="Great post about AI",
            strategy={"voice": "analyst", "format": "infographic"},
        )
        d = story.to_dict()
        restored = StoryContent.from_dict(d)
        assert restored.headline == story.headline
        assert restored.strategy == story.strategy
        assert restored.hashtags == story.hashtags
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/ai-infographic-bot && source .venv/bin/activate && python -m pytest tests/test_render.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement the model**

```python
# src/render/__init__.py
from .model import StoryContent

__all__ = ["StoryContent"]
```

```python
# src/render/model.py
"""Data model for single-story infographic content."""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict


@dataclass
class StoryContent:
    """Everything needed to render a single-story infographic and post it."""

    # Content
    hook: str                    # The scroll-stopping opening line
    headline: str                # Main headline (10 words max)
    body: list[str]              # Story body as paragraphs/sections
    insight: str                 # Key takeaway / unique angle
    source: str                  # Source name (e.g., "TechCrunch")
    source_url: str              # Original article URL

    # Metadata
    pillar: str                  # Content pillar (e.g., "breaking-ai")
    account: str                 # "personal" or "company"

    # Optional
    hashtags: list[str] = field(default_factory=list)
    caption: str = ""            # LinkedIn caption (companion to image)
    strategy: dict = field(default_factory=dict)  # voice, format, hook, etc.

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> StoryContent:
        return cls(**data)

    def to_json(self, path: str) -> None:
        from pathlib import Path
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def from_json(cls, path: str) -> StoryContent:
        from pathlib import Path
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_render.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/render/ tests/test_render.py
git commit -m "feat: add StoryContent data model for single-story infographics"
```

---

## Task 3: Template System

**Files:**
- Create: `src/render/templates.py`
- Create: `data/config/templates.json`
- Test: `tests/test_render.py` (append)

- [ ] **Step 1: Write the test**

Append to `tests/test_render.py`:

```python
from src.render.templates import get_template, list_templates


class TestTemplates:
    def test_list_personal_templates(self):
        templates = list_templates("personal")
        assert len(templates) == 6
        assert "dark-glassmorphism" in templates

    def test_list_company_templates(self):
        templates = list_templates("company")
        assert len(templates) == 6
        assert "circuit-board-dark" in templates

    def test_get_template_has_required_keys(self):
        t = get_template("dark-glassmorphism")
        required = ["bg", "text_primary", "text_secondary", "text_muted",
                     "card_bg", "card_border", "card_radius", "accent_line"]
        for key in required:
            assert key in t, f"Missing key: {key}"

    def test_unknown_template_raises(self):
        import pytest
        with pytest.raises(KeyError):
            get_template("nonexistent")

    def test_each_template_renders_valid(self):
        for name in list_templates("personal") + list_templates("company"):
            t = get_template(name)
            assert isinstance(t["bg"], (str, list))
            assert t["text_primary"].startswith("#")
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement templates.py**

```python
# src/render/templates.py
"""Visual template definitions for 12 infographic styles."""

TEMPLATES = {
    # ── Personal (6) ──────────────────────────────────────────
    "dark-glassmorphism": {
        "account": "personal",
        "bg": "#0a0a1a",
        "card_bg": "rgba(255,255,255,0.06)",
        "card_border": "rgba(255,255,255,0.1)",
        "card_radius": 16,
        "text_primary": "#ffffff",
        "text_secondary": "#c0c0d0",
        "text_muted": "#707090",
        "accent_line": "#4f8cff",
        "hook_color": "#4f8cff",
        "insight_bg": "#1a1a3a",
        "footer_text": "thegeshwar",
    },
    "neon-gradient": {
        "account": "personal",
        "bg": ["#1a0533", "#0a1628"],
        "card_bg": "rgba(255,255,255,0.04)",
        "card_border": "rgba(138,43,226,0.3)",
        "card_radius": 12,
        "text_primary": "#ffffff",
        "text_secondary": "#d0b8ff",
        "text_muted": "#8060b0",
        "accent_line": "#bf5fff",
        "hook_color": "#bf5fff",
        "insight_bg": "#1a0a30",
        "footer_text": "thegeshwar",
    },
    "clean-editorial": {
        "account": "personal",
        "bg": "#f8f8f8",
        "card_bg": "#ffffff",
        "card_border": "#e0e0e0",
        "card_radius": 4,
        "text_primary": "#111111",
        "text_secondary": "#444444",
        "text_muted": "#999999",
        "accent_line": "#0066ff",
        "hook_color": "#0066ff",
        "insight_bg": "#f0f4ff",
        "footer_text": "thegeshwar",
    },
    "midnight-teal": {
        "account": "personal",
        "bg": "#0d1117",
        "card_bg": "#161b22",
        "card_border": "#30363d",
        "card_radius": 10,
        "text_primary": "#e6edf3",
        "text_secondary": "#8b949e",
        "text_muted": "#484f58",
        "accent_line": "#2dd4bf",
        "hook_color": "#2dd4bf",
        "insight_bg": "#0d1f1d",
        "footer_text": "thegeshwar",
    },
    "warm-mono": {
        "account": "personal",
        "bg": "#1c1917",
        "card_bg": "#292524",
        "card_border": "#44403c",
        "card_radius": 8,
        "text_primary": "#fafaf9",
        "text_secondary": "#a8a29e",
        "text_muted": "#78716c",
        "accent_line": "#f59e0b",
        "hook_color": "#f59e0b",
        "insight_bg": "#2c2520",
        "footer_text": "@thegeshwar",
    },
    "polar-light": {
        "account": "personal",
        "bg": ["#eef2ff", "#e0e7ff"],
        "card_bg": "#ffffff",
        "card_border": "#c7d2fe",
        "card_radius": 20,
        "text_primary": "#1e1b4b",
        "text_secondary": "#4338ca",
        "text_muted": "#6366f1",
        "accent_line": "#818cf8",
        "hook_color": "#4338ca",
        "insight_bg": "#eef2ff",
        "footer_text": "thegeshwar",
    },

    # ── CU Circuits (6) ──────────────────────────────────────
    "circuit-board-dark": {
        "account": "company",
        "bg": "#0a0a0a",
        "card_bg": "#0d1a0d",
        "card_border": "#1a4d2e",
        "card_radius": 8,
        "text_primary": "#e0ffe0",
        "text_secondary": "#88cc88",
        "text_muted": "#447744",
        "accent_line": "#d4a017",
        "hook_color": "#d4a017",
        "insight_bg": "#0a1a0a",
        "footer_text": "cucircuits.com",
        "logo": True,
    },
    "copper-navy": {
        "account": "company",
        "bg": "#0c1222",
        "card_bg": "#111c33",
        "card_border": "#1e3050",
        "card_radius": 10,
        "text_primary": "#ffffff",
        "text_secondary": "#8899bb",
        "text_muted": "#556688",
        "accent_line": "#cd7f32",
        "hook_color": "#cd7f32",
        "insight_bg": "#0f1830",
        "footer_text": "cucircuits.com",
        "logo": True,
    },
    "clean-fabrication": {
        "account": "company",
        "bg": "#fafafa",
        "card_bg": "#ffffff",
        "card_border": "#d4d4d4",
        "card_radius": 6,
        "text_primary": "#171717",
        "text_secondary": "#525252",
        "text_muted": "#a3a3a3",
        "accent_line": "#006644",
        "hook_color": "#006644",
        "insight_bg": "#f0faf5",
        "footer_text": "cucircuits.com",
        "logo": True,
        "grid_pattern": True,
    },
    "solder-mask-blue": {
        "account": "company",
        "bg": ["#002244", "#001133"],
        "card_bg": "rgba(255,255,255,0.08)",
        "card_border": "rgba(255,255,255,0.15)",
        "card_radius": 8,
        "text_primary": "#ffffff",
        "text_secondary": "#aaccee",
        "text_muted": "#6699cc",
        "accent_line": "#ffffff",
        "hook_color": "#88ccff",
        "insight_bg": "#001a3a",
        "footer_text": "cucircuits.com",
        "logo": True,
    },
    "threed-print-orange": {
        "account": "company",
        "bg": "#1a1a1a",
        "card_bg": "#242424",
        "card_border": "#3d3d3d",
        "card_radius": 12,
        "text_primary": "#ffffff",
        "text_secondary": "#cccccc",
        "text_muted": "#888888",
        "accent_line": "#ff6600",
        "hook_color": "#ff6600",
        "insight_bg": "#2a1a0a",
        "footer_text": "cucircuits.com",
        "logo": True,
    },
    "india-tech-gradient": {
        "account": "company",
        "bg": "#111111",
        "card_bg": "#1c1c1c",
        "card_border": "#333333",
        "card_radius": 10,
        "text_primary": "#f5f5f5",
        "text_secondary": "#bbbbbb",
        "text_muted": "#777777",
        "accent_line": "#ff9933",
        "hook_color": "#138808",
        "insight_bg": "#1a1a0a",
        "footer_text": "cucircuits.com",
        "logo": True,
        "tricolor_accent": ["#ff9933", "#ffffff", "#138808"],
    },
}


def get_template(name: str) -> dict:
    """Return template dict by name. Raises KeyError if not found."""
    return TEMPLATES[name]


def list_templates(account: str) -> list[str]:
    """Return template names for the given account ('personal' or 'company')."""
    return [k for k, v in TEMPLATES.items() if v["account"] == account]
```

- [ ] **Step 4: Run tests**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add 12 visual templates (6 personal + 6 company)"
```

---

## Task 4: Font Loading and Drawing Utilities

**Files:**
- Create: `src/render/fonts.py`
- Test: `tests/test_render.py` (append)

- [ ] **Step 1: Write the test**

```python
from src.render.fonts import load_font


class TestFonts:
    def test_load_default_font(self):
        font = load_font(24)
        assert font is not None
        assert font.size == 24

    def test_load_bold_font(self):
        font = load_font(32, bold=True)
        assert font is not None

    def test_different_sizes(self):
        small = load_font(12)
        large = load_font(48)
        assert small.size < large.size
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement**

```python
# src/render/fonts.py
"""Font loading for macOS."""

from functools import lru_cache
from PIL import ImageFont

_FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
_BOLD_INDEX = 1
_REGULAR_INDEX = 0


@lru_cache(maxsize=32)
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load Helvetica at the given size. Falls back to Pillow default."""
    try:
        index = _BOLD_INDEX if bold else _REGULAR_INDEX
        return ImageFont.truetype(_FONT_PATH, size, index=index)
    except OSError:
        return ImageFont.load_default(size=size)
```

- [ ] **Step 4: Run tests**

- [ ] **Step 5: Commit**

---

## Task 5: Single-Story Rendering Engine

**Files:**
- Create: `src/render/engine.py`
- Test: `tests/test_render.py` (append)

This is the core. The engine takes a `StoryContent` + template name and produces a LinkedIn-optimized PNG.

- [ ] **Step 1: Write the tests**

```python
from pathlib import Path
from PIL import Image
from src.render.engine import render_story
from src.render.model import StoryContent


def _sample_story(account="personal") -> StoryContent:
    if account == "personal":
        return StoryContent(
            hook="This changes everything.",
            headline="GPT-5 Scores 95% on ARC-AGI",
            body=[
                "OpenAI's latest model just achieved what many thought impossible — a 95% score on the ARC-AGI benchmark, which tests genuine reasoning ability rather than pattern matching.",
                "Previous state-of-the-art models peaked at 55%. The jump to 95% represents a qualitative shift in what AI systems can do.",
                "The model uses a novel architecture that combines chain-of-thought reasoning with self-verification loops, essentially checking its own work before committing to an answer.",
            ],
            insight="This isn't incremental improvement. It's a phase change. The gap between 55% and 95% on ARC-AGI is the gap between 'sophisticated autocomplete' and 'something that actually reasons.'",
            source="TechCrunch",
            source_url="https://techcrunch.com/gpt5",
            pillar="breaking-ai",
            account="personal",
            hashtags=["#AI", "#GPT5", "#AGI", "#MachineLearning", "#Tech"],
        )
    else:
        return StoryContent(
            hook="Your via placement is costing you $2 per board.",
            headline="5 Via Mistakes That Inflate Your PCB Cost",
            body=[
                "Most engineers don't think about via costs during schematic capture. But by the time your Gerbers hit the fab, those decisions are locked in.",
                "The biggest offender: using through-hole vias where blind vias would work. Each unnecessary through-hole via adds drilling time and reduces yield.",
                "Other common mistakes include via-in-pad without proper filling, excessive via counts from poor routing, and wrong annular ring sizes that trigger fabricator upcharges.",
            ],
            insight="Run a DFM check before you send to fab. A 10-minute review saves $2/board — which at 1000 units is $2,000 you're leaving on the table.",
            source="CU Circuits Engineering",
            source_url="https://cucircuits.com",
            pillar="dfm-tips",
            account="company",
            hashtags=["#PCB", "#DFM", "#Electronics", "#Manufacturing", "#MadeInIndia"],
        )


class TestRenderEngine:
    def test_renders_valid_png(self, tmp_path):
        story = _sample_story("personal")
        path = render_story(story, template="dark-glassmorphism", output_dir=tmp_path)
        assert path.exists()
        assert path.suffix == ".png"
        img = Image.open(path)
        assert img.format == "PNG"

    def test_linkedin_dimensions(self, tmp_path):
        story = _sample_story("personal")
        path = render_story(story, template="dark-glassmorphism", output_dir=tmp_path)
        img = Image.open(path)
        assert img.size == (1080, 1350)

    def test_each_personal_template(self, tmp_path):
        from src.render.templates import list_templates
        story = _sample_story("personal")
        for tmpl in list_templates("personal"):
            path = render_story(story, template=tmpl, output_dir=tmp_path)
            assert path.exists()
            img = Image.open(path)
            assert img.size[0] > 0

    def test_each_company_template(self, tmp_path):
        from src.render.templates import list_templates
        story = _sample_story("company")
        for tmpl in list_templates("company"):
            path = render_story(story, template=tmpl, output_dir=tmp_path)
            assert path.exists()

    def test_long_body_text_wraps(self, tmp_path):
        story = _sample_story("personal")
        story.body = ["A" * 500]  # Very long paragraph
        path = render_story(story, template="dark-glassmorphism", output_dir=tmp_path)
        assert path.exists()

    def test_company_template_has_logo_area(self, tmp_path):
        story = _sample_story("company")
        path = render_story(story, template="circuit-board-dark", output_dir=tmp_path)
        img = Image.open(path)
        # Logo area should be in top-left — just verify image rendered
        assert img.size == (1080, 1350)
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement the rendering engine**

Create `src/render/engine.py` — the full single-story layout engine. This renders:
1. Background (solid or gradient)
2. Optional tricolor accent bar (India Tech template)
3. Optional grid pattern (Clean Fabrication template)
4. Optional CU Circuits logo (company templates)
5. Hook text (large, accent colored)
6. Headline (bold, prominent)
7. Body paragraphs (wrapped, secondary color)
8. Insight callout box (highlighted background, accent border)
9. Source attribution
10. Footer (branded text, hashtags)

The engine must handle text wrapping, vertical overflow (truncate gracefully), and all 12 templates.

Full implementation is substantial (~200 lines). Build it to pass the tests above.

- [ ] **Step 4: Run tests — iterate until all pass**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: single-story rendering engine with 12 templates"
```

---

## Task 6: Render CLI

**Files:**
- Create: `src/render/cli.py`
- Modify: `run.py`

- [ ] **Step 1: Write the test**

```python
class TestCLI:
    def test_render_from_json(self, tmp_path):
        story = _sample_story("personal")
        json_path = tmp_path / "story.json"
        story.to_json(str(json_path))

        from click.testing import CliRunner
        from run import cli
        result = CliRunner().invoke(cli, [
            "render", str(json_path),
            "--template", "dark-glassmorphism",
            "--output-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert "Saved" in result.output
```

- [ ] **Step 2: Run to verify failure**

- [ ] **Step 3: Implement CLI**

```python
# src/render/cli.py
"""CLI for rendering stories from JSON files."""

import click
from pathlib import Path
from src.render.model import StoryContent
from src.render.engine import render_story


@click.command("render")
@click.argument("story_json", type=click.Path(exists=True))
@click.option("--template", "-t", default="dark-glassmorphism", help="Visual template name")
@click.option("--output-dir", "-o", default="output", help="Output directory")
def render_cmd(story_json: str, template: str, output_dir: str):
    """Render a story JSON file into an infographic image."""
    story = StoryContent.from_json(story_json)
    out = Path(output_dir)
    out.mkdir(exist_ok=True)
    path = render_story(story, template=template, output_dir=out)
    click.echo(f"Saved: {path}")
```

Update `run.py` to register the render command:

```python
#!/usr/bin/env python3
"""CLI entrypoint for the AI Infographic Bot."""

import click
from src.render.cli import render_cmd


@click.group()
def cli():
    """AI Infographic Bot"""
    pass


cli.add_command(render_cmd)

if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: Run tests**

- [ ] **Step 5: Commit**

---

## Task 7: `/infographic preview` Skill

**Files:**
- Create: `.claude/skills/infographic-preview.md`
- Create: `.claude/skills/lib/strategy.md`
- Create: `.claude/skills/lib/content-pillars.md`

This is the Claude Code skill that drives the entire content pipeline. No Python — just instructions for Claude.

- [ ] **Step 1: Create content pillars reference**

```markdown
<!-- .claude/skills/lib/content-pillars.md -->
# Content Pillars

## Personal Account
| Pillar | ID | What to Search | Example |
|--------|----|---------------|---------|
| Breaking AI | breaking-ai | Major AI model releases, benchmark results, company announcements | "GPT-5 released", "Anthropic raises $5B" |
| Money Moves | money-moves | AI funding rounds, acquisitions, market shifts, IPOs | "AI startup raises $500M", "Google acquires X" |
| Builder's Edge | builders-edge | New dev tools, frameworks, open-source releases | "New open-source LLM framework", "Cursor raises series B" |
| Policy & Ethics | policy-ethics | AI regulation, safety debates, ethical concerns | "EU AI Act enforcement", "AI deepfake legislation" |
| Future Signals | future-signals | Research papers, emerging trends, predictions | "Robotics paper from Stanford", "Quantum + AI intersection" |

## CU Circuits Company Account
| Pillar | ID | What to Search | Example |
|--------|----|---------------|---------|
| DFM Tips | dfm-tips | Design-for-manufacturing advice, common PCB mistakes | "Via placement costs", "trace width calculator" |
| Industry Intel | industry-intel | PCB supply chain, copper prices, lead times, market data | "Copper prices drop", "PCB demand forecast" |
| New Tech | new-tech | Manufacturing technology, new processes, equipment | "HDI PCB advances", "3D printed electronics" |
| Made in India | made-in-india | Indian electronics manufacturing growth, policy, infrastructure | "India PCB output grows", "PLI scheme electronics" |
| Customer Stories | customer-stories | Product journeys, from prototype to production | "Startup ships 10K units", "IoT device manufacturing" |
| Standards & Process | standards-process | IPC updates, certifications, best practices | "IPC-2581 adoption", "lead-free solder requirements" |
```

- [ ] **Step 2: Create strategy rotation reference**

```markdown
<!-- .claude/skills/lib/strategy.md -->
# Strategy Rotation

When creating a post, select ONE option from each variable. Rotate through different combinations.

## Voice Options
### Personal
- **Analyst**: Data-driven, authoritative. "Here's what the numbers say."
- **Builder**: Hands-on, practical. "I tried this and here's what happened."
- **Commentator**: Sharp, opinionated. "Everyone's missing the real story here."
- **Storyteller**: Narrative-driven. "Three years ago, nobody thought this was possible."
- **Contrarian**: Challenges consensus. "The hot take is wrong. Here's why."
- **Curious Explorer**: Asks questions. "What if this changes everything we assumed?"

### Company (CU Circuits)
- **Industry Expert**: Formal, authoritative. "Market analysis shows..."
- **Helpful Engineer**: Practical, approachable. "Here's a tip that saves you $2/board."
- **Scrappy Startup**: Bold, ambitious. "We're building the future of fab in India."
- **Data Analyst**: Numbers-focused. "The data is clear..."
- **Educator**: Teaching-focused. "Let me explain why this matters."
- **Insider**: Behind-the-scenes. "What we see on the fab floor..."

## Hook Styles
- **Question**: "Did you know that...?"
- **Bold claim**: "This changes everything about..."
- **Statistic**: "95%. That's the new benchmark for..."
- **Contrarian**: "Everyone's celebrating X. They shouldn't be."
- **What-if**: "What if the biggest AI breakthrough of 2026 isn't a model?"
- **Future prediction**: "In 12 months, this will be the standard."

## Depth
- **Minimal**: Hook + headline + 3 key points + insight. Punchy.
- **Medium**: Full narrative arc. What happened, why it matters, what's next.
- **Dense**: Visual essay. Deep analysis on the image itself.

## Caption Style
- **Opinion-led**: Start with your take, then context.
- **Question-led**: Open with a question that invites discussion.
- **Short & punchy**: 2-3 sentences max. Let the image do the work.
- **Long-form analysis**: 4-6 paragraphs. LinkedIn rewards long text.
- **Thread-style**: Numbered points. "3 things you need to know:"
```

- [ ] **Step 3: Create the preview skill**

```markdown
<!-- .claude/skills/infographic-preview.md -->
---
name: infographic-preview
description: "Preview mode: discover trending news, select a story, generate infographic + caption. No posting, no approval. Use: /infographic preview personal OR /infographic preview company"
user_invocable: true
---

# Infographic Preview

Dry-run of the content pipeline. Discovers news, selects a story, generates the infographic and caption, and shows the result. Does NOT send for approval or post.

## Arguments
- First argument: `personal` or `company`

## Steps

### 1. Read Context
- Read `~/.claude/skills/lib/content-pillars.md` for source guidance
- Read `~/.claude/skills/lib/strategy.md` for strategy options
- Read the content log (`data/personal-log.json` or `data/company-log.json`) if it exists, to understand what's been posted before and what strategies have been tried
- Note which pillars haven't been served recently

### 2. Discover Stories
Use WebSearch to find 5-8 trending stories relevant to the account:

**Personal:** Search for today's trending AI/tech/money news across multiple angles. Use queries like:
- "AI news today 2026"
- "tech funding rounds this week"
- "breaking technology news"

**Company:** Search for PCB/3D printing/electronics manufacturing news:
- "PCB manufacturing news 2026"
- "3D printing electronics"
- "India electronics manufacturing"
- "PCB design tips DFM"

For each story found, note: headline, source, URL, and a 1-sentence summary.

### 3. Select ONE Story
Pick the single best story based on:
- Relevance to the account's audience
- Newsworthiness and timeliness
- Visual potential (can this be told as an infographic?)
- Pillar diversity (don't repeat a pillar from recent posts)

Also identify 2 alternatives with brief reasoning.

### 4. Select Strategy
Pick a strategy combination (voice, hook, depth, caption style). If content log exists with engagement data, use the explore/exploit approach from the spec. Otherwise, pick randomly.

Pick a visual template from the account's 6 options. Rotate through them.

### 5. Write the Content
Create a StoryContent by writing:
- **hook**: A provocative or surprising opening line (max 15 words). Must stop the scroll.
- **headline**: The story in max 10 words. Specific — name the company/model/technique.
- **body**: 3-4 paragraphs telling the story. What happened, why it matters, context.
- **insight**: Your unique takeaway. The thing nobody else is saying. 1-2 sentences.
- **caption**: The LinkedIn caption. This COMPLEMENTS the image — don't repeat it. Add engagement prompt. 5-8 strategic hashtags at the end.

### 6. Render the Image
Save the StoryContent as JSON to `data/drafts/<id>.json`, then run:
```bash
cd ~/ai-infographic-bot && source .venv/bin/activate
python run.py render data/drafts/<id>.json --template <chosen-template> --output-dir output
```

### 7. Show Results
- Display the generated image (use Read tool on the PNG)
- Show the caption
- Show the strategy used
- Show the 2 alternatives
- Ask: "How does this look? Any adjustments?"
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/
git commit -m "feat: add /infographic preview skill with strategy and pillar references"
```

---

## Task 8: Generate 8 Test Posts Per Account

**Files:**
- Uses the `/infographic preview` skill
- Output: `gallery/posts/` directory with images and metadata

- [ ] **Step 1: Run `/infographic preview personal` 8 times**

Each run should use a DIFFERENT strategy combination and visual template. Discover fresh stories each time. Save outputs to `gallery/posts/personal-001/` through `personal-008/`, each containing:
- `image.png` — the rendered infographic
- `meta.json` — story content, strategy, caption, alternatives

- [ ] **Step 2: Run `/infographic preview company` 8 times**

Same approach. Save to `gallery/posts/company-001/` through `company-008/`.

- [ ] **Step 3: Commit all test outputs**

---

## Task 9: Build test.dev Gallery

**Files:**
- Create: `gallery/index.html`

- [ ] **Step 1: Build the gallery HTML**

A single HTML file that:
- Shows all 16 test posts in a responsive grid
- Tabs for Personal / CU Circuits
- Each card shows: the infographic image, the caption below, the strategy tags (voice, hook, template)
- Dark theme matching the playground aesthetic
- Hosted at test.dev.thegeshwar.com

- [ ] **Step 2: Deploy to VPS**

```bash
scp -r gallery/ oracle:/tmp/gallery/
ssh oracle "sudo rm -rf /var/www/test.dev.thegeshwar.com/gallery && sudo mv /tmp/gallery /var/www/test.dev.thegeshwar.com/ && sudo cp /var/www/test.dev.thegeshwar.com/gallery/index.html /var/www/test.dev.thegeshwar.com/index.html"
```

- [ ] **Step 3: Verify**

Open https://test.dev.thegeshwar.com/ and confirm all 16 posts are visible.

- [ ] **Step 4: Commit**

```bash
git add gallery/
git commit -m "feat: test gallery with 16 sample posts on test.dev"
git push
```

---

## Execution Order

Tasks 1-6 build the core renderer (TDD, can be parallelized partially).
Task 7 creates the Claude skill.
Task 8 uses the skill to generate real content.
Task 9 showcases it for review.

After user reviews the 16 posts on test.dev and approves content quality, we proceed to Phase 2: approval flow, posting, engagement tracking.
