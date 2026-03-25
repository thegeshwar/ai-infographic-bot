#!/usr/bin/env python3
"""CLI entrypoint for the AI Infographic Bot."""

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click

from src.config import ROOT_DIR, DATA_DIR, SCHEDULE_HOUR
from src.logging_config import setup_logging

setup_logging()

from src.pipeline import run_pipeline  # noqa: E402 — must come after logging setup

VALID_STAGES = ["discover", "curate", "generate", "post"]
PLIST_NAME = "com.infographicbot.daily.plist"
PLIST_SRC = ROOT_DIR / "scripts" / PLIST_NAME
PLIST_DST = Path.home() / "Library" / "LaunchAgents" / PLIST_NAME


@click.group()
def cli():
    """AI Infographic Bot — run pipeline or manage scheduling."""
    pass


@cli.command("run")
@click.argument("stages", nargs=-1, type=click.Choice(VALID_STAGES))
def run_cmd(stages: tuple[str, ...]):
    """Run the pipeline. Optionally specify stages: discover, curate, generate, post."""
    stage_list = list(stages) if stages else None
    run_pipeline(stage_list)


@cli.command()
def install():
    """Install the launchd schedule for daily runs."""
    if not PLIST_SRC.exists():
        click.echo(f"Error: plist not found at {PLIST_SRC}")
        sys.exit(1)

    PLIST_DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(PLIST_SRC), str(PLIST_DST))
    click.echo(f"Copied plist to {PLIST_DST}")

    subprocess.run(["launchctl", "load", str(PLIST_DST)], check=False)
    click.echo(f"Loaded launchd job. Pipeline will run daily at hour {SCHEDULE_HOUR}.")


@cli.command()
def uninstall():
    """Remove the launchd schedule."""
    if PLIST_DST.exists():
        subprocess.run(["launchctl", "unload", str(PLIST_DST)], check=False)
        PLIST_DST.unlink()
        click.echo("Unloaded and removed launchd job.")
    else:
        click.echo("No launchd job installed.")


@cli.command()
def status():
    """Show pipeline status: last run, schedule, recent errors."""
    click.echo(f"Schedule: daily at hour {SCHEDULE_HOUR:02d}:00")

    # Check if launchd job is installed
    if PLIST_DST.exists():
        click.echo(f"Launchd: installed ({PLIST_DST})")
    else:
        click.echo("Launchd: not installed")

    # Show most recent log
    logs_dir = DATA_DIR / "logs"
    if logs_dir.exists():
        logs = sorted(logs_dir.glob("pipeline_*.log"), reverse=True)
        if logs:
            latest = logs[0]
            click.echo(f"Last log: {latest.name}")
            # Show last 5 lines
            lines = latest.read_text().strip().split("\n")
            for line in lines[-5:]:
                click.echo(f"  {line}")
        else:
            click.echo("No log files found.")
    else:
        click.echo("No logs directory found.")

    # Show recent errors from latest log
    if logs_dir.exists():
        logs = sorted(logs_dir.glob("pipeline_*.log"), reverse=True)
        if logs:
            errors = [l for l in logs[0].read_text().split("\n") if "ERROR" in l]
            if errors:
                click.echo(f"\nRecent errors ({len(errors)}):")
                for err in errors[-5:]:
                    click.echo(f"  {err}")


@cli.command()
def history():
    """Show posting history."""
    from src.history import get_history

    entries = get_history()
    if not entries:
        click.echo("No posting history yet.")
        return

    click.echo(f"Total posts: {len(entries)}\n")
    for entry in entries[-20:]:  # Show last 20
        ts = entry.get("timestamp", "unknown")
        click.echo(f"  [{ts}] {entry.get('platform', '?')} -- {entry.get('title', '?')}")
        click.echo(f"    URL: {entry.get('url', '?')}")


if __name__ == "__main__":
    cli()
