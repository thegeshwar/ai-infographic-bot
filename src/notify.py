"""Notification dispatch — macOS native, Slack webhook, email."""

import json
import logging
import smtplib
import subprocess
import urllib.request
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def notify_macos(title: str, message: str) -> None:
    """Send a macOS native notification via osascript.

    Args:
        title: Notification title.
        message: Notification body text.
    """
    safe_message = message.replace('\\', '\\\\').replace('"', '\\"')
    safe_title = title.replace('\\', '\\\\').replace('"', '\\"')
    script = f'display notification "{safe_message}" with title "{safe_title}"'
    try:
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True)
    except Exception as e:
        logger.warning(f"macOS notification failed: {e}")


def notify_slack(webhook_url: str, title: str, message: str) -> None:
    """Send a Slack notification via incoming webhook.

    Args:
        webhook_url: Slack webhook URL.
        title: Message title.
        message: Message body.
    """
    payload = json.dumps({"text": f"*{title}*\n{message}"}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except Exception as e:
        logger.warning(f"Slack notification failed: {e}")


def notify_email(
    host: str,
    from_addr: str,
    to_addr: str,
    password: str,
    title: str,
    message: str,
    port: int = 587,
) -> None:
    """Send an email notification via SMTP.

    Args:
        host: SMTP server hostname.
        from_addr: Sender email address.
        to_addr: Recipient email address.
        password: SMTP password.
        title: Email subject.
        message: Email body.
        port: SMTP port (default 587).
    """
    msg = MIMEText(message)
    msg["Subject"] = title
    msg["From"] = from_addr
    msg["To"] = to_addr

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(from_addr, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
    except Exception as e:
        logger.warning(f"Email notification failed: {e}")


def send_notification(title: str, message: str, level: str = "error") -> None:
    """Send notification to all configured channels.

    Always sends macOS notification. Additionally sends to Slack and/or
    email if the corresponding environment variables are set.

    Args:
        title: Notification title.
        message: Notification body.
        level: Severity level ('error', 'warning', 'info').
    """
    # Always send macOS notification
    notify_macos(title, message)

    # Slack (optional)
    from src.config import SLACK_WEBHOOK_URL, SMTP_HOST, SMTP_FROM, SMTP_TO, SMTP_PASSWORD
    if SLACK_WEBHOOK_URL:
        notify_slack(SLACK_WEBHOOK_URL, title, message)

    # Email (optional)
    if SMTP_HOST and SMTP_FROM and SMTP_TO:
        notify_email(SMTP_HOST, SMTP_FROM, SMTP_TO, SMTP_PASSWORD, title, message)
