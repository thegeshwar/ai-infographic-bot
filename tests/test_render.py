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
