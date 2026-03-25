"""Logging configuration with file rotation for the pipeline."""

import logging
from datetime import datetime, timedelta
from pathlib import Path


def setup_logging(data_dir: Path | None = None, level: int = logging.INFO) -> None:
    """Configure logging to both console and a dated log file.

    Args:
        data_dir: Base data directory. Logs go to data_dir/logs/.
                  Defaults to <project_root>/data.
        level: Logging level (default INFO).
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"

    logs_dir = data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"pipeline_{today}.log"

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # Clear any existing handlers on root logger to avoid duplicates
    root = logging.getLogger()
    root.setLevel(level)

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    root.addHandler(fh)

    # Console handler (only add if none exists)
    has_console = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in root.handlers
    )
    if not has_console:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
        root.addHandler(ch)

    # Clean up old logs
    cleanup_old_logs(logs_dir)


def cleanup_old_logs(logs_dir: Path, max_age_days: int = 30) -> None:
    """Delete pipeline log files older than max_age_days.

    Args:
        logs_dir: Directory containing pipeline_YYYY-MM-DD.log files.
        max_age_days: Maximum age in days to keep.
    """
    cutoff = datetime.now() - timedelta(days=max_age_days)

    for log_file in logs_dir.glob("pipeline_*.log"):
        # Extract date from filename: pipeline_YYYY-MM-DD.log
        try:
            date_str = log_file.stem.replace("pipeline_", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                log_file.unlink()
        except ValueError:
            continue  # Skip files with unexpected names
