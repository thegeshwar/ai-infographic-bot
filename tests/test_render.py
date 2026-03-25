"""Tests for the single-story renderer."""
from src.render.model import StoryContent
from src.render.templates import get_template, list_templates
from src.render.fonts import load_font


class TestStoryContent:
    def test_create_minimal(self):
        story = StoryContent(
            hook="This changes everything.",
            headline="GPT-5 Scores 95% on ARC-AGI",
            body=["OpenAI's latest model just achieved what many thought impossible.", "The ARC-AGI benchmark tests genuine reasoning ability."],
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
            hook="Hook", headline="Headline", body=["Body"], insight="Insight",
            source="Source", source_url="https://example.com",
            pillar="industry-intel", account="company",
        )
        assert story.hashtags == []
        assert story.caption == ""
        assert story.strategy == {}

    def test_to_dict_roundtrip(self):
        story = StoryContent(
            hook="Hook", headline="Headline", body=["Line 1", "Line 2"],
            insight="Insight", source="Source", source_url="https://example.com",
            pillar="breaking-ai", account="personal",
            hashtags=["#AI", "#Tech"], caption="Great post about AI",
            strategy={"voice": "analyst", "format": "infographic"},
        )
        d = story.to_dict()
        restored = StoryContent.from_dict(d)
        assert restored.headline == story.headline
        assert restored.strategy == story.strategy
        assert restored.hashtags == story.hashtags


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

    def test_each_template_has_valid_colors(self):
        for name in list_templates("personal") + list_templates("company"):
            t = get_template(name)
            assert isinstance(t["bg"], (str, list))
            assert t["text_primary"].startswith("#")


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


from pathlib import Path
from PIL import Image
from src.render.engine import render_story


def _sample_story(account="personal") -> StoryContent:
    if account == "personal":
        return StoryContent(
            hook="This changes everything.",
            headline="GPT-5 Scores 95% on ARC-AGI",
            body=[
                "OpenAI's latest model achieved what many thought impossible — a 95% score on ARC-AGI, testing genuine reasoning.",
                "Previous SOTA peaked at 55%. The jump represents a qualitative shift in AI capability.",
                "The model uses chain-of-thought with self-verification loops.",
            ],
            insight="This isn't incremental. It's a phase change — the gap between 55% and 95% is the gap between autocomplete and reasoning.",
            source="TechCrunch", source_url="https://techcrunch.com/gpt5",
            pillar="breaking-ai", account="personal",
            hashtags=["#AI", "#GPT5", "#AGI", "#MachineLearning", "#Tech"],
        )
    return StoryContent(
        hook="Your via placement is costing you $2 per board.",
        headline="5 Via Mistakes That Inflate Your PCB Cost",
        body=[
            "Most engineers don't think about via costs during schematic capture. But by the time Gerbers hit the fab, those decisions are locked in.",
            "The biggest offender: through-hole vias where blind vias would work. Each unnecessary through-hole adds drilling time.",
            "Other mistakes: via-in-pad without filling, excessive via counts, wrong annular ring sizes.",
        ],
        insight="Run a DFM check before sending to fab. A 10-minute review saves $2/board — at 1000 units that's $2,000.",
        source="CU Circuits Engineering", source_url="https://cucircuits.com",
        pillar="dfm-tips", account="company",
        hashtags=["#PCB", "#DFM", "#Electronics", "#Manufacturing", "#MadeInIndia"],
    )


class TestRenderEngine:
    def test_renders_valid_png(self, tmp_path):
        path = render_story(_sample_story(), template="dark-glassmorphism", output_dir=tmp_path)
        assert path.exists() and path.suffix == ".png"
        assert Image.open(path).format == "PNG"

    def test_linkedin_dimensions(self, tmp_path):
        path = render_story(_sample_story(), template="dark-glassmorphism", output_dir=tmp_path)
        assert Image.open(path).size == (1080, 1350)

    def test_each_personal_template(self, tmp_path):
        for tmpl in list_templates("personal"):
            path = render_story(_sample_story("personal"), template=tmpl, output_dir=tmp_path)
            assert path.exists()

    def test_each_company_template(self, tmp_path):
        for tmpl in list_templates("company"):
            path = render_story(_sample_story("company"), template=tmpl, output_dir=tmp_path)
            assert path.exists()

    def test_long_body_wraps(self, tmp_path):
        story = _sample_story()
        story.body = ["A" * 500]
        path = render_story(story, template="dark-glassmorphism", output_dir=tmp_path)
        assert path.exists()

    def test_gradient_template(self, tmp_path):
        path = render_story(_sample_story(), template="neon-gradient", output_dir=tmp_path)
        assert Image.open(path).size == (1080, 1350)

    def test_company_with_logo(self, tmp_path):
        path = render_story(_sample_story("company"), template="circuit-board-dark", output_dir=tmp_path)
        assert Image.open(path).size == (1080, 1350)

    def test_tricolor_accent(self, tmp_path):
        path = render_story(_sample_story("company"), template="india-tech-gradient", output_dir=tmp_path)
        assert path.exists()

    def test_grid_pattern(self, tmp_path):
        path = render_story(_sample_story("company"), template="clean-fabrication", output_dir=tmp_path)
        assert path.exists()
