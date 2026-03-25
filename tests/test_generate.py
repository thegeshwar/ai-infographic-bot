"""Comprehensive tests for the infographic generation system."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from src.generate.templates import (
    TEMPLATE_STYLES,
    OUTPUT_FORMATS,
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    get_template,
    get_output_format,
)
from src.generate.renderer import generate_infographic, _draw_gradient, _wrap_text


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_stories():
    """Return a list of sample curated stories for testing."""
    return [
        {
            "headline": "OpenAI Releases GPT-5 With Unprecedented Reasoning",
            "category": "breakthrough",
            "bullets": [
                "New model achieves superhuman performance on math benchmarks",
                "Available to ChatGPT Plus subscribers immediately",
                "Enterprise API access rolling out next week",
            ],
        },
        {
            "headline": "Google DeepMind Publishes AlphaFold 3 Paper",
            "category": "research",
            "bullets": [
                "Predicts protein-ligand interactions with high accuracy",
                "Open-sourced weights for academic use",
            ],
        },
        {
            "headline": "Apple Integrates On-Device LLM Into iOS 19",
            "category": "product",
            "bullets": [
                "Runs entirely on the Neural Engine",
                "No cloud connection required for basic tasks",
                "Developers get access via new CoreML APIs",
            ],
        },
    ]


@pytest.fixture
def single_story():
    return [
        {
            "headline": "EU AI Act Enforcement Begins",
            "category": "policy",
            "bullets": ["Fines up to 7% of global revenue for violations"],
        }
    ]


@pytest.fixture
def five_stories(sample_stories):
    """Five stories to test denser layouts."""
    extra = [
        {
            "headline": "Anthropic Raises $5B Series D",
            "category": "industry",
            "bullets": [
                "Valuation reaches $60 billion",
                "Funding to accelerate safety research",
            ],
        },
        {
            "headline": "New Policy Framework for Autonomous Vehicles",
            "category": "policy",
            "bullets": [
                "Federal standards for Level 4 autonomy",
                "Effective January 2027",
            ],
        },
    ]
    return sample_stories + extra


@pytest.fixture
def output_dir(tmp_path):
    """Provide a temporary output directory and patch OUTPUT_DIR."""
    with patch("src.generate.renderer.OUTPUT_DIR", tmp_path):
        yield tmp_path


# ---------------------------------------------------------------------------
# Template tests
# ---------------------------------------------------------------------------

class TestTemplates:
    """Tests for the template system."""

    @pytest.mark.parametrize("style", ["dark", "light", "gradient", "minimal"])
    def test_template_style_exists(self, style):
        tmpl = get_template(style)
        assert tmpl is not None
        assert "background" in tmpl
        assert "text_primary" in tmpl
        assert "text_secondary" in tmpl
        assert "accent" in tmpl

    @pytest.mark.parametrize("style", ["dark", "light", "gradient", "minimal"])
    def test_template_has_layout_spacing(self, style):
        tmpl = get_template(style)
        assert "margin" in tmpl
        assert "card_padding" in tmpl
        assert "card_radius" in tmpl

    def test_all_styles_in_registry(self):
        assert set(TEMPLATE_STYLES.keys()) == {"dark", "light", "gradient", "minimal"}

    def test_gradient_template_has_gradient_colors(self):
        tmpl = get_template("gradient")
        assert "gradient_start" in tmpl
        assert "gradient_end" in tmpl

    def test_unknown_template_falls_back_to_dark(self):
        tmpl = get_template("nonexistent")
        dark = get_template("dark")
        assert tmpl == dark

    def test_category_colors_defined(self):
        for cat in ("breakthrough", "product", "research", "industry", "policy"):
            assert cat in CATEGORY_COLORS
            assert "primary" in CATEGORY_COLORS[cat]
            assert "accent" in CATEGORY_COLORS[cat]

    def test_category_icons_defined(self):
        for cat in ("breakthrough", "product", "research", "industry", "policy"):
            assert cat in CATEGORY_ICONS
            assert len(CATEGORY_ICONS[cat]) >= 1


# ---------------------------------------------------------------------------
# Output format tests
# ---------------------------------------------------------------------------

class TestOutputFormats:
    """Tests for output format / aspect ratio definitions."""

    @pytest.mark.parametrize(
        "fmt, expected_w, expected_h",
        [
            ("instagram", 1080, 1350),
            ("twitter", 1200, 675),
            ("linkedin", 1200, 627),
        ],
    )
    def test_format_dimensions(self, fmt, expected_w, expected_h):
        f = get_output_format(fmt)
        assert f["width"] == expected_w
        assert f["height"] == expected_h

    def test_unknown_format_falls_back_to_instagram(self):
        f = get_output_format("tiktok")
        insta = get_output_format("instagram")
        assert f == insta

    def test_all_formats_in_registry(self):
        assert set(OUTPUT_FORMATS.keys()) == {"instagram", "twitter", "linkedin"}


# ---------------------------------------------------------------------------
# Gradient rendering tests
# ---------------------------------------------------------------------------

class TestGradient:
    """Tests for gradient background generation."""

    def test_gradient_produces_image(self):
        img = _draw_gradient(400, 300, "#FF0000", "#0000FF")
        assert isinstance(img, Image.Image)
        assert img.size == (400, 300)

    def test_gradient_top_is_start_color(self):
        img = _draw_gradient(100, 100, "#FF0000", "#0000FF")
        r, g, b = img.getpixel((50, 0))
        # Top should be close to red
        assert r > 200
        assert b < 55

    def test_gradient_bottom_is_end_color(self):
        img = _draw_gradient(100, 100, "#FF0000", "#0000FF")
        r, g, b = img.getpixel((50, 99))
        # Bottom should be close to blue
        assert b > 200
        assert r < 55


# ---------------------------------------------------------------------------
# Text wrapping tests
# ---------------------------------------------------------------------------

class TestTextWrapping:
    """Tests for the text wrapping utility."""

    def test_short_text_unchanged(self):
        lines = _wrap_text("Hello world", max_chars=40)
        assert lines == ["Hello world"]

    def test_long_text_wraps(self):
        long = "This is a really long headline that should definitely be wrapped across multiple lines for display"
        lines = _wrap_text(long, max_chars=30)
        assert len(lines) > 1
        for line in lines:
            assert len(line) <= 35  # textwrap allows slight overflow on words

    def test_empty_text(self):
        lines = _wrap_text("", max_chars=40)
        assert lines == [""]


# ---------------------------------------------------------------------------
# Full infographic generation tests
# ---------------------------------------------------------------------------

class TestGenerateInfographic:
    """Integration tests for generate_infographic."""

    def test_default_generates_valid_png(self, sample_stories, output_dir):
        path = generate_infographic(sample_stories)
        assert path.exists()
        assert path.suffix == ".png"
        img = Image.open(path)
        assert img.format == "PNG"

    def test_default_dimensions_instagram(self, sample_stories, output_dir):
        path = generate_infographic(sample_stories)
        img = Image.open(path)
        assert img.size == (1080, 1350)

    @pytest.mark.parametrize("template", ["dark", "light", "gradient", "minimal"])
    def test_each_template_produces_valid_image(self, template, sample_stories, output_dir):
        path = generate_infographic(sample_stories, template=template)
        assert path.exists()
        img = Image.open(path)
        assert img.format == "PNG"
        assert img.size[0] > 0 and img.size[1] > 0

    @pytest.mark.parametrize(
        "fmt, expected_w, expected_h",
        [
            ("instagram", 1080, 1350),
            ("twitter", 1200, 675),
            ("linkedin", 1200, 627),
        ],
    )
    def test_each_format_produces_correct_dimensions(
        self, fmt, expected_w, expected_h, sample_stories, output_dir
    ):
        path = generate_infographic(sample_stories, format=fmt)
        img = Image.open(path)
        assert img.size == (expected_w, expected_h)

    def test_single_story(self, single_story, output_dir):
        path = generate_infographic(single_story)
        assert path.exists()
        img = Image.open(path)
        assert img.format == "PNG"

    def test_five_stories(self, five_stories, output_dir):
        path = generate_infographic(five_stories)
        assert path.exists()
        img = Image.open(path)
        assert img.format == "PNG"

    def test_output_file_saved_in_output_dir(self, sample_stories, output_dir):
        path = generate_infographic(sample_stories)
        assert path.parent == output_dir

    def test_gradient_template_uses_gradient_background(self, sample_stories, output_dir):
        path = generate_infographic(sample_stories, template="gradient")
        img = Image.open(path)
        # Gradient should have varying pixel values top vs bottom
        top_pixel = img.getpixel((540, 0))
        bottom_pixel = img.getpixel((540, img.height - 1))
        assert top_pixel != bottom_pixel

    def test_stories_with_long_content(self, output_dir):
        stories = [
            {
                "headline": "This is an extremely long headline that would overflow a single line and must be properly wrapped to fit within the infographic boundaries",
                "category": "breakthrough",
                "bullets": [
                    "This is a very long bullet point that contains detailed information about a breakthrough in artificial intelligence research and development",
                    "Another long bullet with extensive details about methodology and results of the experiment",
                    "Short bullet",
                ],
            }
        ]
        path = generate_infographic(stories)
        assert path.exists()
        img = Image.open(path)
        assert img.format == "PNG"

    def test_combined_template_and_format(self, sample_stories, output_dir):
        path = generate_infographic(sample_stories, template="light", format="twitter")
        img = Image.open(path)
        assert img.size == (1200, 675)
