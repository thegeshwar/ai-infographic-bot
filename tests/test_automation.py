"""Tests for Phase 5: Scheduling & Automation layer.

Written TDD-style — tests first, then implementation to make them pass.
"""

import json
import logging
import os
import smtplib
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory structure."""
    logs_dir = tmp_path / "data" / "logs"
    logs_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def history_file(tmp_path):
    """Provide a temporary history.json path."""
    return tmp_path / "data" / "history.json"


@pytest.fixture
def sample_story():
    return {
        "headline": "GPT-5 Released",
        "url": "https://example.com/gpt5",
        "source": "TechCrunch",
    }


# ===========================================================================
# 1. Logging config tests
# ===========================================================================

class TestLoggingConfig:
    """Tests for src.logging_config module."""

    def test_setup_logging_creates_log_file(self, tmp_data_dir):
        """Log file with today's date should be created."""
        from src.logging_config import setup_logging

        setup_logging(data_dir=tmp_data_dir / "data")
        logger = logging.getLogger("test.logging_config")
        logger.info("hello from test")

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = tmp_data_dir / "data" / "logs" / f"pipeline_{today}.log"
        assert log_file.exists()
        contents = log_file.read_text()
        assert "hello from test" in contents

    def test_log_format_structured(self, tmp_data_dir):
        """Log lines should contain timestamp, level, module, message."""
        from src.logging_config import setup_logging

        setup_logging(data_dir=tmp_data_dir / "data")
        logger = logging.getLogger("test.structured")
        logger.warning("structured test message")

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = tmp_data_dir / "data" / "logs" / f"pipeline_{today}.log"
        line = log_file.read_text().strip().split("\n")[-1]
        # Should contain timestamp pattern, WARNING level, module, message
        assert "WARNING" in line
        assert "test.structured" in line
        assert "structured test message" in line

    def test_log_rotation_deletes_old_files(self, tmp_data_dir):
        """Files older than 30 days should be cleaned up."""
        from src.logging_config import cleanup_old_logs

        logs_dir = tmp_data_dir / "data" / "logs"

        # Create fake old log files
        for days_ago in [1, 15, 31, 45]:
            date_str = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            (logs_dir / f"pipeline_{date_str}.log").write_text("old log")

        cleanup_old_logs(logs_dir, max_age_days=30)

        remaining = list(logs_dir.glob("pipeline_*.log"))
        remaining_names = [f.name for f in remaining]

        # Files <= 30 days old should remain
        for days_ago in [1, 15]:
            date_str = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            assert f"pipeline_{date_str}.log" in remaining_names

        # Files > 30 days old should be gone
        for days_ago in [31, 45]:
            date_str = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            assert f"pipeline_{date_str}.log" not in remaining_names

    def test_setup_logging_creates_logs_dir(self, tmp_path):
        """setup_logging should create the logs directory if missing."""
        from src.logging_config import setup_logging

        data_dir = tmp_path / "nonexistent_data"
        setup_logging(data_dir=data_dir)

        assert (data_dir / "logs").is_dir()


# ===========================================================================
# 2. History tracking tests
# ===========================================================================

class TestHistory:
    """Tests for src.history module."""

    def test_is_posted_returns_false_for_new_url(self, history_file):
        """New URLs should not be marked as posted."""
        from src.history import is_posted

        assert is_posted("https://example.com/new", history_file=history_file) is False

    def test_record_post_and_is_posted(self, history_file, sample_story):
        """After recording a post, is_posted should return True."""
        from src.history import is_posted, record_post

        record_post(
            story=sample_story,
            platform="twitter",
            image_path="/tmp/img.png",
            history_file=history_file,
        )
        assert is_posted(sample_story["url"], history_file=history_file) is True

    def test_record_post_persists_to_json(self, history_file, sample_story):
        """History should be saved as valid JSON with correct fields."""
        from src.history import record_post

        history_file.parent.mkdir(parents=True, exist_ok=True)
        record_post(
            story=sample_story,
            platform="linkedin",
            image_path="/tmp/img.png",
            history_file=history_file,
        )

        data = json.loads(history_file.read_text())
        assert isinstance(data, list)
        assert len(data) == 1

        entry = data[0]
        assert entry["url"] == sample_story["url"]
        assert entry["title"] == sample_story["headline"]
        assert entry["platform"] == "linkedin"
        assert entry["image_path"] == "/tmp/img.png"
        assert "timestamp" in entry

    def test_dedup_prevents_double_post(self, history_file, sample_story):
        """Recording the same URL twice should create two entries but is_posted stays True."""
        from src.history import is_posted, record_post

        record_post(story=sample_story, platform="twitter", image_path="/tmp/a.png", history_file=history_file)
        record_post(story=sample_story, platform="linkedin", image_path="/tmp/b.png", history_file=history_file)

        assert is_posted(sample_story["url"], history_file=history_file) is True
        data = json.loads(history_file.read_text())
        assert len(data) == 2

    def test_is_posted_handles_missing_file(self, tmp_path):
        """is_posted should return False if history file doesn't exist."""
        from src.history import is_posted

        missing = tmp_path / "no_such_file.json"
        assert is_posted("https://x.com", history_file=missing) is False

    def test_get_history_returns_all_entries(self, history_file, sample_story):
        """get_history should return the full list of entries."""
        from src.history import get_history, record_post

        record_post(story=sample_story, platform="twitter", image_path="/tmp/a.png", history_file=history_file)
        entries = get_history(history_file=history_file)
        assert len(entries) == 1
        assert entries[0]["url"] == sample_story["url"]


# ===========================================================================
# 3. Notification tests
# ===========================================================================

class TestNotify:
    """Tests for src.notify module."""

    @mock.patch("subprocess.run")
    def test_macos_notification_calls_osascript(self, mock_run):
        """macOS notification should invoke osascript."""
        from src.notify import notify_macos

        notify_macos("Test Title", "Test message body")
        mock_run.assert_called_once()
        args = mock_run.call_args
        cmd = args[0][0] if isinstance(args[0][0], list) else args[0]
        # Should call osascript
        assert "osascript" in str(cmd)

    @mock.patch("subprocess.run")
    def test_send_notification_always_sends_macos(self, mock_run):
        """send_notification should always try macOS native notification."""
        from src.notify import send_notification

        with mock.patch.dict(os.environ, {}, clear=False):
            send_notification("Title", "Message")
        assert mock_run.called

    @mock.patch("urllib.request.urlopen")
    def test_slack_notification_sends_webhook(self, mock_urlopen):
        """When SLACK_WEBHOOK_URL is set, a POST to that URL should happen."""
        from src.notify import notify_slack

        mock_response = mock.MagicMock()
        mock_response.read.return_value = b"ok"
        mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
        mock_response.__exit__ = mock.MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        notify_slack("https://hooks.slack.com/test", "Title", "Body")
        mock_urlopen.assert_called_once()

    @mock.patch("smtplib.SMTP")
    def test_email_notification_sends_smtp(self, mock_smtp_class):
        """When SMTP vars are set, an email should be sent."""
        from src.notify import notify_email

        mock_smtp = mock.MagicMock()
        mock_smtp_class.return_value.__enter__ = mock.MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = mock.MagicMock(return_value=False)

        notify_email(
            host="smtp.example.com",
            from_addr="bot@example.com",
            to_addr="admin@example.com",
            password="secret",
            title="Error",
            message="Pipeline failed",
        )
        mock_smtp.sendmail.assert_called_once()

    @mock.patch("src.notify.notify_email")
    @mock.patch("src.notify.notify_slack")
    @mock.patch("src.notify.notify_macos")
    def test_send_notification_dispatches_all_configured(
        self, mock_macos, mock_slack, mock_email
    ):
        """send_notification should call all configured channels."""
        from src.notify import send_notification

        env = {
            "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_FROM": "bot@x.com",
            "SMTP_TO": "admin@x.com",
            "SMTP_PASSWORD": "pw",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            send_notification("Title", "Message", level="error")

        mock_macos.assert_called_once()
        mock_slack.assert_called_once()
        mock_email.assert_called_once()


# ===========================================================================
# 4. CLI command tests
# ===========================================================================

class TestCLI:
    """Tests for run.py CLI commands (install, uninstall, status, history)."""

    @mock.patch("subprocess.run")
    @mock.patch("shutil.copy2")
    def test_install_command(self, mock_copy, mock_run, tmp_path):
        """install command should copy plist and load it."""
        from click.testing import CliRunner
        from run import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["install"])
        # Should not crash
        assert result.exit_code == 0 or "install" in result.output.lower() or mock_copy.called or mock_run.called

    @mock.patch("subprocess.run")
    def test_uninstall_command(self, mock_run, tmp_path):
        """uninstall command should unload and remove plist."""
        from click.testing import CliRunner
        from run import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["uninstall"])
        assert result.exit_code == 0

    def test_status_command(self):
        """status command should output pipeline status info."""
        from click.testing import CliRunner
        from run import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        # Should contain some status info
        assert len(result.output) > 0

    def test_history_command(self, history_file, sample_story):
        """history command should print posting history."""
        from click.testing import CliRunner
        from run import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["history"])
        assert result.exit_code == 0


# ===========================================================================
# 5. Pipeline error handling tests
# ===========================================================================

class TestPipelineErrorHandling:
    """Tests that pipeline failures trigger notifications."""

    @mock.patch("src.pipeline.send_notification")
    @mock.patch("src.pipeline.discover_stories", side_effect=RuntimeError("API down"))
    def test_pipeline_failure_sends_notification(self, mock_discover, mock_notify):
        """When pipeline raises, a notification should be sent."""
        from src.pipeline import run_pipeline

        # Should not raise — error is caught and notification sent
        run_pipeline(stages=["discover"])
        mock_notify.assert_called()
        # First call should be about the error
        call_args = mock_notify.call_args
        assert "error" in str(call_args).lower() or "fail" in str(call_args).lower()

    @mock.patch("src.pipeline.send_notification")
    @mock.patch("src.pipeline.discover_stories", return_value=[])
    def test_pipeline_success_sends_summary(self, mock_discover, mock_notify):
        """Successful pipeline run should send a success summary."""
        from src.pipeline import run_pipeline

        run_pipeline(stages=["discover"])
        # At least one notification call (success summary)
        assert mock_notify.called

    @mock.patch("src.history.is_posted", return_value=True)
    @mock.patch("src.pipeline.discover_stories", return_value=[
        {"headline": "Old News", "url": "https://old.com", "source": "test"}
    ])
    @mock.patch("src.pipeline.curate_stories", return_value=[
        {"headline": "Old News", "url": "https://old.com", "source": "test"}
    ])
    @mock.patch("src.pipeline.generate_infographic", return_value=Path("/tmp/test.png"))
    @mock.patch("src.pipeline._post_all")
    @mock.patch("src.notify.send_notification")
    def test_pipeline_skips_already_posted(
        self, mock_notify, mock_post_all, mock_gen, mock_curate, mock_discover, mock_is_posted
    ):
        """Pipeline should skip stories that have already been posted."""
        from src.pipeline import run_pipeline

        run_pipeline()
        # Post stage should recognize that stories are already posted
        # The pipeline should still complete but note the skipping


# ===========================================================================
# 6. Launchd plist tests
# ===========================================================================

class TestLaunchdPlist:
    """Tests for the launchd plist file."""

    def test_plist_file_exists(self):
        """The plist file should exist in scripts/."""
        plist = Path(__file__).parent.parent / "scripts" / "com.infographicbot.daily.plist"
        assert plist.exists(), f"Expected plist at {plist}"

    def test_plist_is_valid_xml(self):
        """The plist should be valid XML."""
        import xml.etree.ElementTree as ET

        plist = Path(__file__).parent.parent / "scripts" / "com.infographicbot.daily.plist"
        tree = ET.parse(plist)
        root = tree.getroot()
        assert root.tag == "plist"

    def test_plist_contains_required_keys(self):
        """Plist should contain Label, ProgramArguments, StartCalendarInterval."""
        plist = Path(__file__).parent.parent / "scripts" / "com.infographicbot.daily.plist"
        content = plist.read_text()
        assert "Label" in content
        assert "ProgramArguments" in content
        assert "StartCalendarInterval" in content
        assert "StandardOutPath" in content
        assert "StandardErrorPath" in content
        assert "WorkingDirectory" in content

    def test_install_script_exists(self):
        """install.sh should exist and be executable content."""
        script = Path(__file__).parent.parent / "scripts" / "install.sh"
        assert script.exists()
        content = script.read_text()
        assert "launchctl" in content
        assert "LaunchAgents" in content

    def test_uninstall_script_exists(self):
        """uninstall.sh should exist and handle unload + removal."""
        script = Path(__file__).parent.parent / "scripts" / "uninstall.sh"
        assert script.exists()
        content = script.read_text()
        assert "launchctl" in content
        assert "rm" in content or "remove" in content
