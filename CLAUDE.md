# CLAUDE.md

## Project Overview

Claude Code status line extension that displays real usage quota data scraped from `claude /usage`. Three files: `status_line.py`, `scrape_usage.sh`, and `install.py`. No external dependencies — stdlib Python 3.10+ only.

## How It Works

1. `scrape_usage.sh` runs `claude /usage` in a PTY, strips ANSI codes, parses usage percentages into `data/usage_cache.json`
2. `status_line.py` reads that cache (triggers background re-scrape if >30s old), gets git info via subprocess, reads model/cwd from Claude Code's stdin JSON, prints the formatted status line
3. `install.py` sets the `statusLine` command in `~/.claude/settings.json`

## Status Line Format

```
📁 /path | 🌿 branch*? | 🤖 Model | ⚡ session% | 📅 weekly% | 🔄 reset time
```

## Key Files

- `status_line.py` — main script called by Claude Code (all logic in one file)
- `scrape_usage.sh` — background scraper for `claude /usage`
- `install.py` — hooks status line into Claude Code settings
- `data/usage_cache.json` — auto-generated, gitignored
