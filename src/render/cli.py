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
    out.mkdir(parents=True, exist_ok=True)
    path = render_story(story, template=template, output_dir=out)
    click.echo(f"Saved: {path}")
