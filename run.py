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
