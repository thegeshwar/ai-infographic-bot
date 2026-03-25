"""Tests for the single-story renderer."""
from src.render.model import StoryContent
from src.render.templates import get_template, list_templates


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
