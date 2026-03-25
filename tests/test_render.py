"""Tests for the single-story renderer."""

from pathlib import Path
from PIL import Image

from src.render.model import StoryContent
from src.render.engine import render_story
from src.render.templates import get_template, list_templates
from src.render.fonts import load_font


# ── Model Tests ─────────────────────────────────────────────────

class TestStoryContent:
    def test_create_minimal(self):
        story = StoryContent(
            hook="This changes everything.",
            headline="GPT-5 Scores 95% on ARC-AGI",
            body=["OpenAI's latest model achieved what many thought impossible.",
                  "The ARC-AGI benchmark tests genuine reasoning ability."],
            insight="This is a phase change in AI capability.",
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
            hook="Hook", headline="Headline", body=["Body"], insight="Insight",
            source="Source", source_url="https://example.com",
            pillar="industry-intel", account="company",
        )
        assert story.hashtags == []
        assert story.caption == ""
        assert story.strategy == {}
        assert story.html == ""

    def test_to_dict_roundtrip(self):
        story = StoryContent(
            hook="Hook", headline="Headline", body=["Line 1", "Line 2"],
            insight="Insight", source="Source", source_url="https://example.com",
            pillar="breaking-ai", account="personal",
            hashtags=["#AI", "#Tech"], caption="Great post about AI",
            strategy={"voice": "analyst"}, html="<div>test</div>",
        )
        d = story.to_dict()
        restored = StoryContent.from_dict(d)
        assert restored.headline == story.headline
        assert restored.html == story.html


# ── Template Tests ──────────────────────────────────────────────

class TestTemplates:
    def test_list_personal_templates(self):
        assert len(list_templates("personal")) == 6

    def test_list_company_templates(self):
        assert len(list_templates("company")) == 6

    def test_get_template_has_required_keys(self):
        t = get_template("dark-glassmorphism")
        for key in ["bg", "text_primary", "text_secondary", "accent_line"]:
            assert key in t

    def test_unknown_template_raises(self):
        import pytest
        with pytest.raises(KeyError):
            get_template("nonexistent")


# ── Font Tests ──────────────────────────────────────────────────

class TestFonts:
    def test_load_default_font(self):
        font = load_font(24)
        assert font is not None
        assert font.size == 24

    def test_load_bold_font(self):
        font = load_font(32, bold=True)
        assert font is not None


# ── Render Engine Tests ─────────────────────────────────────────

SAMPLE_HTML = """
<div style="width:1080px; height:1350px; background:#0a0a1a; color:white;
            display:flex; flex-direction:column; justify-content:center;
            align-items:center; padding:60px;">
  <div style="font-size:120px; font-weight:900; color:#4f8cff;">83%</div>
  <div style="font-size:36px; font-weight:700; margin-top:20px; text-align:center;">
    GPT 5.4 Outscores Human Analysts
  </div>
  <div style="font-size:20px; color:#888; margin-top:16px;">
    on the GDPVal benchmark for knowledge work
  </div>
  <div style="position:absolute; bottom:30px; color:#555; font-size:14px;">
    thegeshwar | Source: TechCrunch
  </div>
</div>
"""


def _sample_story_with_html(account="personal") -> StoryContent:
    return StoryContent(
        hook="83%. That is GPT 5.4's score beating human experts.",
        headline="GPT 5.4 Outscores Human Analysts",
        body=["OpenAI's latest model scored 83% on GDPVal."],
        insight="We just entered the good enough to trust era.",
        source="TechCrunch", source_url="https://techcrunch.com",
        pillar="breaking-ai", account=account,
        html=SAMPLE_HTML,
    )


class TestRenderEngine:
    def test_renders_valid_png(self, tmp_path):
        story = _sample_story_with_html()
        path = render_story(story, output_dir=tmp_path)
        assert path.exists()
        assert path.suffix == ".png"
        img = Image.open(path)
        assert img.format == "PNG"

    def test_correct_dimensions(self, tmp_path):
        story = _sample_story_with_html()
        path = render_story(story, output_dir=tmp_path)
        img = Image.open(path)
        # 2x device scale factor
        assert img.size[0] == 1080 * 2
        assert img.size[1] == 1350 * 2

    def test_raises_without_html(self, tmp_path):
        import pytest
        story = StoryContent(
            hook="Hook", headline="Headline", body=["Body"], insight="Insight",
            source="Source", source_url="https://example.com",
            pillar="breaking-ai", account="personal",
        )
        with pytest.raises(ValueError, match="html is empty"):
            render_story(story, output_dir=tmp_path)

    def test_output_filename_from_headline(self, tmp_path):
        story = _sample_story_with_html()
        path = render_story(story, output_dir=tmp_path)
        assert "gpt-54-outscores-human-analysts" in path.name


class TestCLI:
    def test_render_from_json(self, tmp_path):
        story = _sample_story_with_html()
        json_path = tmp_path / "story.json"
        story.to_json(str(json_path))

        from click.testing import CliRunner
        from run import cli
        result = CliRunner().invoke(cli, [
            "render", str(json_path),
            "--output-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert "Saved" in result.output
