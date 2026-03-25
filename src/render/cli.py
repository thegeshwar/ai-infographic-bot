"""CLI for rendering stories from JSON files."""

import click
from pathlib import Path
from src.render.model import StoryContent
from src.render.engine import render_story


@click.command("render")
@click.argument("story_json", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="output", help="Output directory")
def render_cmd(story_json: str, output_dir: str):
    """Render a story JSON file into an infographic PNG.

    The JSON must include an 'html' field with the infographic HTML/CSS.
    """
    story = StoryContent.from_json(story_json)
    if not story.html:
        raise click.ClickException("Story JSON has no 'html' field. Claude must design the HTML first.")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = render_story(story, output_dir=out)
    click.echo(f"Saved: {path}")
