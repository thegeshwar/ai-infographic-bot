#!/usr/bin/env python3
"""CLI entrypoint for the AI Infographic Bot."""

import logging
import sys

import click

from src.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

VALID_STAGES = ["discover", "curate", "generate", "post"]


@click.command()
@click.argument("stages", nargs=-1, type=click.Choice(VALID_STAGES))
def main(stages: tuple[str, ...]):
    """Run the AI Infographic Bot pipeline.

    With no arguments, runs the full pipeline.
    Specify stages to run only those: discover, curate, generate, post
    """
    stage_list = list(stages) if stages else None
    run_pipeline(stage_list)


if __name__ == "__main__":
    main()
