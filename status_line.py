#!/usr/bin/env python3
"""
Status line for Claude Code — shows usage quota and git info.
Reads scraped usage data from cache, git info via subprocess,
and session context from stdin JSON.
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CACHE_PATH = SCRIPT_DIR / "data" / "usage_cache.json"


# ── usage cache ──────────────────────────────────────────────

def _get_usage() -> dict | None:
    """Load cached usage data. Scraping is handled by the Stop hook."""
    try:
        if CACHE_PATH.exists():
            with open(CACHE_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return None


# ── git info ─────────────────────────────────────────────────

def _run_git(cmd: list[str], cwd: str) -> str | None:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=3)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def _git_status(directory: str) -> str:
    """Return a compact colored git string like '🌿 main*?' or '' if not a repo."""
    if _run_git(["git", "rev-parse", "--is-inside-work-tree"], directory) != "true":
        return ""

    # Branch name
    branch = _run_git(["git", "symbolic-ref", "--short", "HEAD"], directory)
    if not branch:
        branch = _run_git(["git", "rev-parse", "--short", "HEAD"], directory)
        branch = f"({branch})" if branch else None
    if not branch:
        return ""

    if len(branch) > 20:
        branch = branch[:17] + "..."

    # Working tree indicators
    indicators = ""
    porcelain = _run_git(["git", "status", "--porcelain=v1"], directory) or ""
    has_changes = has_untracked = False
    for line in porcelain.splitlines():
        if len(line) >= 2:
            if line[0] not in " ?" or line[1] not in " ?":
                has_changes = True
            if line[0] == "?" or line[1] == "?":
                has_untracked = True
    if has_changes:
        indicators += "*"
    if has_untracked:
        indicators += "?"

    # Ahead/behind
    ab = _run_git(["git", "rev-list", "--left-right", "--count", "@{upstream}...HEAD"], directory)
    if ab:
        parts = ab.split()
        if len(parts) == 2:
            behind, ahead = int(parts[0]), int(parts[1])
            if ahead:
                indicators += f"\u2191{ahead}"
            if behind:
                indicators += f"\u2193{behind}"

    # Color: yellow if dirty, green if clean
    if has_changes or has_untracked:
        r, g, b = 255, 215, 0
    else:
        r, g, b = 0, 255, 0

    return f"\033[38;2;{r};{g};{b}m\U0001f33f {branch}{indicators}\033[0m"


# ── formatting helpers ───────────────────────────────────────

def _color(r: int, g: int, b: int, text: str) -> str:
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def _pct_color(pct: int) -> tuple[int, int, int]:
    if pct < 50:
        return (0, 255, 0)
    elif pct < 75:
        return (255, 255, 0)
    return (255, 150, 150)


def _reset_countdown(reset_str: str) -> str:
    """Convert a reset time string like '7 m (Australia/Hobart)' into 'Xh Ym'."""
    import zoneinfo

    tz_match = re.search(r"\(([^)]+)\)", reset_str)
    tz_name = tz_match.group(1).strip() if tz_match else None

    clean = re.sub(r"\s*\([^)]*\)\s*", " ", reset_str).strip()
    clean = re.sub(r"(\d+)\s+m\b", r"\1am", clean)
    clean = re.sub(r"(\d+)\s+pm\b", r"\1pm", clean)

    try:
        tz = zoneinfo.ZoneInfo(tz_name) if tz_name else None
    except Exception:
        tz = None

    now = datetime.now(tz)

    for fmt in ("%I%p", "%I:%M%p", "%b %d, %I%p", "%b %d, %I:%M%p"):
        try:
            parsed = datetime.strptime(clean, fmt)
            if "%b" in fmt:
                target = parsed.replace(year=now.year, tzinfo=tz)
            else:
                target = now.replace(
                    hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
                )
            if target <= now:
                target += timedelta(days=1)
            diff = target - now
            total_mins = int(diff.total_seconds() // 60)
            h, m = divmod(total_mins, 60)
            return f"{h}h {m}m" if h else f"{m}m"
        except ValueError:
            continue

    if re.match(r"\d+[dhm]", clean):
        return clean
    return clean


# ── main ─────────────────────────────────────────────────────

def generate_status_line():
    # Read context from stdin (Claude Code passes JSON)
    ctx = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            ctx = json.loads(raw)
    except Exception:
        pass

    project_path = ctx.get("cwd", "")

    # Model name from stdin context
    model_info = ctx.get("model", {})
    if isinstance(model_info, dict):
        current_model = model_info.get("display_name") or model_info.get("id") or "Unknown"
    else:
        current_model = "Unknown"

    usage = _get_usage()

    parts = []

    # Project
    parts.append(f"\U0001f4c1 {project_path}")

    # Git
    if project_path:
        git = _git_status(project_path)
        if git:
            parts.append(git)

    # Model
    parts.append(f"\U0001f916 {current_model}")

    # Usage
    if usage:
        s_pct = usage.get("session_pct")
        if s_pct is not None:
            r, g, b = _pct_color(s_pct)
            parts.append(_color(r, g, b, f"\u26a1 {s_pct}%"))

        w_pct = usage.get("weekly_all_pct")
        if w_pct is not None:
            r, g, b = _pct_color(w_pct)
            parts.append(_color(r, g, b, f"\U0001f4c5 {w_pct}%"))

        s_reset = usage.get("session_reset")
        if s_reset:
            countdown = _reset_countdown(s_reset)
            if countdown:
                parts.append(f"\U0001f504 {countdown}")
    else:
        parts.append("\u26a1 --")

    print(" | ".join(parts))


if __name__ == "__main__":
    generate_status_line()
