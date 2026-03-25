"""Comprehensive tests for the content curation system."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.discover.scraper import Story


# ---------------------------------------------------------------------------
# Helpers — sample stories used across tests
# ---------------------------------------------------------------------------

def _make_story(title="Test Story", source="ArXiv AI", summary="A summary", url="https://example.com",
                published=None, tags=None):
    return Story(
        title=title,
        url=url,
        summary=summary,
        source=source,
        published=published or datetime.now(),
        tags=tags or [],
    )


SAMPLE_STORIES = [
    _make_story("GPT-5 Released", source="TechCrunch AI", summary="OpenAI releases GPT-5 with reasoning"),
    _make_story("New RL Paper", source="ArXiv AI", summary="Reinforcement learning breakthrough"),
    _make_story("AI Startup Raises $1B", source="Hacker News AI", summary="Funding round details"),
    _make_story("Google Gemini Update", source="The Verge AI", summary="Google upgrades Gemini"),
    _make_story("MIT Robotics", source="MIT Tech Review AI", summary="New robot from MIT"),
    _make_story("Random Blog Post", source="Unknown Blog", summary="Some random AI thoughts"),
]


# ===========================================================================
# 1. Source credibility scoring — src.curate.scorer
# ===========================================================================

class TestCredibilityScoring:
    """Test that source credibility weights are correctly applied."""

    def test_known_sources_have_weights(self):
        from src.curate.scorer import SOURCE_WEIGHTS
        assert "ArXiv AI" in SOURCE_WEIGHTS
        assert "TechCrunch AI" in SOURCE_WEIGHTS
        assert "Hacker News AI" in SOURCE_WEIGHTS

    def test_arxiv_has_highest_weight(self):
        from src.curate.scorer import SOURCE_WEIGHTS
        arxiv = SOURCE_WEIGHTS["ArXiv AI"]
        for name, weight in SOURCE_WEIGHTS.items():
            if name != "ArXiv AI":
                assert arxiv >= weight, f"ArXiv ({arxiv}) should be >= {name} ({weight})"

    def test_unknown_source_gets_default_weight(self):
        from src.curate.scorer import score_story
        story = _make_story(source="Unknown Blog", summary="something")
        score = score_story(story)
        assert score > 0, "Unknown source should still get a positive score"

    def test_score_story_returns_float(self):
        from src.curate.scorer import score_story
        story = _make_story(source="ArXiv AI")
        score = score_story(story)
        assert isinstance(score, float)

    def test_keyword_relevance_boosts_score(self):
        from src.curate.scorer import score_story
        generic = _make_story(source="Hacker News AI", title="Stuff happened", summary="Nothing special")
        relevant = _make_story(source="Hacker News AI", title="LLM breakthrough", summary="New transformer model released")
        assert score_story(relevant) > score_story(generic)

    def test_recency_boosts_score(self):
        from src.curate.scorer import score_story
        recent = _make_story(source="ArXiv AI", published=datetime.now())
        old = _make_story(source="ArXiv AI", published=datetime.now() - timedelta(days=7))
        assert score_story(recent) >= score_story(old)


# ===========================================================================
# 2. Story pre-sorting by score
# ===========================================================================

class TestStorySorting:
    """Test that stories are sorted by score (best first)."""

    def test_sort_stories_returns_sorted(self):
        from src.curate.scorer import sort_stories_by_score
        sorted_stories = sort_stories_by_score(SAMPLE_STORIES)
        scores = [s[1] for s in sorted_stories]
        assert scores == sorted(scores, reverse=True), "Stories should be sorted descending by score"

    def test_sort_stories_returns_tuples(self):
        from src.curate.scorer import sort_stories_by_score
        result = sort_stories_by_score(SAMPLE_STORIES)
        for item in result:
            assert isinstance(item, tuple)
            assert isinstance(item[0], Story)
            assert isinstance(item[1], float)

    def test_sort_empty_list(self):
        from src.curate.scorer import sort_stories_by_score
        assert sort_stories_by_score([]) == []


# ===========================================================================
# 3. Cache write / read / date-check
# ===========================================================================

class TestCurationCache:
    """Test caching curated results to JSON files."""

    @pytest.fixture(autouse=True)
    def _setup_cache_dir(self, tmp_path):
        """Patch DATA_DIR to use a temp directory for each test."""
        self.cache_dir = tmp_path / "data" / "curated"
        self.cache_dir.mkdir(parents=True)
        self._patcher = patch("src.curate.cache.CURATED_DIR", self.cache_dir)
        self._patcher.start()
        yield
        self._patcher.stop()

    def test_save_curated_creates_file(self):
        from src.curate.cache import save_curated
        data = [{"headline": "Test", "bullets": ["a"], "category": "research", "original_title": "T"}]
        save_curated(data)
        files = list(self.cache_dir.glob("*.json"))
        assert len(files) == 1

    def test_save_curated_filename_has_date(self):
        from src.curate.cache import save_curated
        data = [{"headline": "Test"}]
        save_curated(data)
        files = list(self.cache_dir.glob("*.json"))
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in files[0].name

    def test_load_curated_returns_data(self):
        from src.curate.cache import save_curated, load_curated
        data = [{"headline": "Cached Story", "bullets": ["b1"], "category": "product", "original_title": "CS"}]
        save_curated(data)
        loaded = load_curated()
        assert loaded == data

    def test_load_curated_returns_none_when_no_cache(self):
        from src.curate.cache import load_curated
        assert load_curated() is None

    def test_load_curated_returns_none_for_different_date(self):
        from src.curate.cache import save_curated, load_curated
        data = [{"headline": "Old"}]
        # Manually write a file with yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        filepath = self.cache_dir / f"curated_{yesterday}.json"
        filepath.write_text(json.dumps(data))
        # Today's cache should not exist
        assert load_curated() is None

    def test_force_bypass_returns_none(self):
        from src.curate.cache import save_curated, load_curated
        data = [{"headline": "Cached"}]
        save_curated(data)
        # force=True should bypass cache
        assert load_curated(force=True) is None


# ===========================================================================
# 4. Claude integration with mocked API
# ===========================================================================

class TestCurateStories:
    """Test the main curate_stories function with mocked Claude API."""

    def _mock_claude_response(self, curated_data):
        """Build a mock Anthropic message response."""
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=json.dumps(curated_data))]
        return mock_msg

    @patch("src.curate.ranker.save_curated")
    @patch("src.curate.ranker.load_curated", return_value=None)
    @patch("src.curate.ranker.anthropic.Anthropic")
    @patch("src.curate.ranker.ANTHROPIC_API_KEY", "test-key")
    def test_curate_stories_calls_claude(self, mock_anthropic_cls, _mock_load, _mock_save):
        from src.curate.ranker import curate_stories
        curated = [{"headline": "AI News", "bullets": ["b1"], "category": "breakthrough", "original_title": "T"}]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = self._mock_claude_response(curated)
        mock_anthropic_cls.return_value = mock_client

        result = curate_stories(SAMPLE_STORIES)
        assert len(result) > 0
        mock_client.messages.create.assert_called_once()

    @patch("src.curate.ranker.save_curated")
    @patch("src.curate.ranker.load_curated", return_value=None)
    @patch("src.curate.ranker.anthropic.Anthropic")
    @patch("src.curate.ranker.ANTHROPIC_API_KEY", "test-key")
    def test_curate_stories_returns_parsed_json(self, mock_anthropic_cls, _mock_load, _mock_save):
        from src.curate.ranker import curate_stories
        curated = [
            {"headline": "Story A", "bullets": ["b1", "b2"], "category": "research", "original_title": "A"},
            {"headline": "Story B", "bullets": ["b3"], "category": "product", "original_title": "B"},
        ]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = self._mock_claude_response(curated)
        mock_anthropic_cls.return_value = mock_client

        result = curate_stories(SAMPLE_STORIES)
        assert result == curated

    def test_curate_stories_empty_input(self):
        from src.curate.ranker import curate_stories
        assert curate_stories([]) == []


# ===========================================================================
# 5. Fallback curation
# ===========================================================================

class TestFallbackCuration:
    """Test that curation gracefully degrades without API key."""

    @patch("src.curate.ranker.save_curated")
    @patch("src.curate.ranker.load_curated", return_value=None)
    @patch("src.curate.ranker.ANTHROPIC_API_KEY", "")
    def test_falls_back_without_api_key(self, _mock_load, _mock_save):
        from src.curate.ranker import curate_stories
        result = curate_stories(SAMPLE_STORIES)
        assert len(result) > 0
        # Fallback should use original titles (from pre-sorted stories)
        all_titles = {s.title for s in SAMPLE_STORIES}
        for item in result:
            assert item["original_title"] in all_titles

    @patch("src.curate.ranker.save_curated")
    @patch("src.curate.ranker.load_curated", return_value=None)
    @patch("src.curate.ranker.ANTHROPIC_API_KEY", "")
    def test_fallback_category_is_industry(self, _mock_load, _mock_save):
        from src.curate.ranker import curate_stories
        result = curate_stories(SAMPLE_STORIES)
        for item in result:
            assert item["category"] == "industry"

    @patch("src.curate.ranker.save_curated")
    @patch("src.curate.ranker.load_curated", return_value=None)
    @patch("src.curate.ranker.anthropic.Anthropic")
    @patch("src.curate.ranker.ANTHROPIC_API_KEY", "test-key")
    def test_falls_back_on_api_error(self, mock_anthropic_cls, _mock_load, _mock_save):
        from src.curate.ranker import curate_stories
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error")
        mock_anthropic_cls.return_value = mock_client

        result = curate_stories(SAMPLE_STORIES)
        assert len(result) > 0  # Should still return results via fallback


# ===========================================================================
# 6. Integration — scoring + caching in curate_stories
# ===========================================================================

class TestIntegration:
    """Test that curate_stories integrates scoring and caching."""

    @pytest.fixture(autouse=True)
    def _setup_cache_dir(self, tmp_path):
        self.cache_dir = tmp_path / "data" / "curated"
        self.cache_dir.mkdir(parents=True)
        self._patcher = patch("src.curate.cache.CURATED_DIR", self.cache_dir)
        self._patcher.start()
        yield
        self._patcher.stop()

    @patch("src.curate.ranker.anthropic.Anthropic")
    @patch("src.curate.ranker.ANTHROPIC_API_KEY", "test-key")
    def test_curate_stories_uses_cache(self, mock_anthropic_cls):
        from src.curate.cache import save_curated
        from src.curate.ranker import curate_stories
        cached = [{"headline": "Cached", "bullets": ["b"], "category": "research", "original_title": "C"}]
        save_curated(cached)

        result = curate_stories(SAMPLE_STORIES)
        # Should return cached data without calling Claude
        assert result == cached
        mock_anthropic_cls.return_value.messages.create.assert_not_called()

    @patch("src.curate.ranker.anthropic.Anthropic")
    @patch("src.curate.ranker.ANTHROPIC_API_KEY", "test-key")
    def test_curate_stories_force_bypasses_cache(self, mock_anthropic_cls):
        from src.curate.cache import save_curated
        from src.curate.ranker import curate_stories
        cached = [{"headline": "Cached", "bullets": ["b"], "category": "research", "original_title": "C"}]
        save_curated(cached)

        curated = [{"headline": "Fresh", "bullets": ["b"], "category": "product", "original_title": "F"}]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = self._mock_claude_response(curated)
        mock_anthropic_cls.return_value = mock_client

        result = curate_stories(SAMPLE_STORIES, force=True)
        assert result == curated
        mock_client.messages.create.assert_called_once()

    @patch("src.curate.ranker.anthropic.Anthropic")
    @patch("src.curate.ranker.ANTHROPIC_API_KEY", "test-key")
    def test_curate_stories_saves_to_cache(self, mock_anthropic_cls):
        from src.curate.ranker import curate_stories
        curated = [{"headline": "New", "bullets": ["b"], "category": "breakthrough", "original_title": "N"}]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = self._mock_claude_response(curated)
        mock_anthropic_cls.return_value = mock_client

        curate_stories(SAMPLE_STORIES)
        files = list(self.cache_dir.glob("*.json"))
        assert len(files) == 1

    def _mock_claude_response(self, curated_data):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=json.dumps(curated_data))]
        return mock_msg

    @patch("src.curate.ranker.ANTHROPIC_API_KEY", "")
    def test_stories_are_pre_sorted_before_curation(self):
        """Verify that stories passed to _simple_curate are pre-sorted by score."""
        from src.curate.ranker import curate_stories
        from src.curate.scorer import score_story

        result = curate_stories(SAMPLE_STORIES)
        # The fallback curate uses the sorted order, so the first result
        # should come from the highest-scored story
        scores = [(s, score_story(s)) for s in SAMPLE_STORIES]
        scores.sort(key=lambda x: x[1], reverse=True)
        best_title = scores[0][0].title
        assert result[0]["original_title"] == best_title
