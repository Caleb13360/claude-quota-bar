#!/usr/bin/env python3
"""
Status line generator for Claude Code integration.
Uses real usage data scraped from `claude /usage`.
Reads session context (cwd, model) from stdin JSON provided by Claude Code.
"""

import json
import re
import sys

from git_info import GitInfo
from usage_scraper import get_usage


def _color(r, g, b, text):
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def _pct_color(pct):
    if pct < 50:
        return (0, 255, 0)
    elif pct < 75:
        return (255, 255, 0)
    else:
        return (255, 150, 150)


def _reset_countdown(reset_str: str) -> str | None:
    """Convert a reset time string like '7 m (Australia/Hobart)' into 'Xh Ym'."""
    from datetime import datetime, timedelta
    import zoneinfo

    tz_match = re.search(r'\(([^)]+)\)', reset_str)
    tz_name = tz_match.group(1).strip() if tz_match else None

    clean = re.sub(r'\s*\([^)]*\)\s*', ' ', reset_str).strip()
    clean = re.sub(r'(\d+)\s+m\b', r'\1am', clean)
    clean = re.sub(r'(\d+)\s+pm\b', r'\1pm', clean)

    try:
        tz = zoneinfo.ZoneInfo(tz_name) if tz_name else None
    except Exception:
        tz = None

    now = datetime.now(tz)

    for fmt in ('%I%p', '%I:%M%p', '%b %d, %I%p', '%b %d, %I:%M%p'):
        try:
            parsed = datetime.strptime(clean, fmt)
            if '%b' in fmt:
                target = parsed.replace(year=now.year, tzinfo=tz)
            else:
                target = now.replace(
                    hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
                )
            if target <= now:
                target += timedelta(days=1)
            diff = target - now
            total_mins = int(diff.total_seconds() // 60)
            hours = total_mins // 60
            mins = total_mins % 60
            if hours > 0:
                return f"{hours}h {mins}m"
            return f"{mins}m"
        except ValueError:
            continue

    if re.match(r'\d+[dhm]', clean):
        return clean

    return clean


def generate_status_line():
    # Read context from stdin (provided by Claude Code)
    ctx = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            ctx = json.loads(raw)
    except Exception:
        pass

    project_path = ctx.get('cwd', '')

    # Model from stdin context
    model_info = ctx.get('model', {})
    if isinstance(model_info, dict):
        model_name = model_info.get('display_name', '')
        model_id = model_info.get('id', '')
        current_model = model_name or model_id or "Unknown"
    else:
        current_model = "Unknown"

    git_info = GitInfo(cache_duration=5)
    usage = get_usage()

    parts = []

    # Current working directory
    parts.append(f"📁 {project_path}")

    # Git branch
    if project_path:
        git_status = git_info.get_git_status(project_path)
        git_display = git_info.format_git_info(git_status)
        if git_display:
            parts.append(git_display)

    # Model
    parts.append(f"🤖 {current_model}")

    if usage:
        s_pct = usage.get('session_pct')
        if s_pct is not None:
            r, g, b = _pct_color(s_pct)
            parts.append(_color(r, g, b, f"⚡ {s_pct}%"))

        w_pct = usage.get('weekly_all_pct')
        if w_pct is not None:
            r, g, b = _pct_color(w_pct)
            parts.append(_color(r, g, b, f"📅 {w_pct}%"))

        s_reset = usage.get('session_reset')
        if s_reset:
            countdown = _reset_countdown(s_reset)
            if countdown:
                parts.append(f"🔄 {countdown}")
    else:
        parts.append("⚡ --")

    print(" | ".join(parts))


if __name__ == "__main__":
    generate_status_line()
