# Claude Status

A Claude Code status line extension that shows **real usage data** scraped directly from `claude /usage`. Unlike other trackers that estimate from local log files, this displays the actual percentages from Anthropic's servers.

```
📁 /home/user/project | 🌿 main*? | 🤖 Opus 4.6 | ⚡ 89% | 📅 57% | 🔄 2h 48m
```

## What it shows

| Section | Meaning |
|---------|---------|
| 📁 | Current working directory |
| 🌿 | Git branch + status (`*` modified, `?` untracked, `↑↓` ahead/behind) |
| 🤖 | Active model and version |
| ⚡ | Current session usage % (color-coded green/yellow/red) |
| 📅 | Weekly usage % across all models (color-coded) |
| 🔄 | Time until session resets |

### Git status indicators

- `*` — modified files
- `?` — untracked files
- `↑2` — 2 commits ahead of remote
- `↓3` — 3 commits behind remote

### Color coding

- **Green** — under 50% usage
- **Yellow** — 50-75% usage
- **Red** — over 75% usage

## Requirements

- **Linux** (uses `script` command for PTY emulation)
- **Python 3.10+**
- **[uv](https://github.com/astral-sh/uv)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Claude Code CLI** installed and authenticated

## Installation

### 1. Clone the repo

```bash
git clone <repo-url> ~/claude-status
cd ~/claude-status
```

### 2. Set up Python environment

```bash
uv venv
uv pip install numpy
```

### 3. Populate the initial usage cache

```bash
bash scrape_usage.sh
```

This takes ~15 seconds. It runs `claude /usage` in the background and caches the results.

### 4. Add to Claude Code settings

Edit `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "cd /home/YOUR_USER/claude-status && uv run python status_line.py"
  }
}
```

Replace `/home/YOUR_USER/claude-status` with the actual path where you cloned the repo.

### 5. Restart Claude Code

The status line will appear at the bottom of the CLI.

## How it works

1. **`scrape_usage.sh`** runs `claude /usage` inside a PTY (via the `script` command), captures the terminal output, strips ANSI escape codes, and parses the real usage percentages into a JSON cache file.

2. **`src/usage_scraper.py`** reads the cached JSON. If the cache is older than 30 seconds, it triggers a background re-scrape.

3. **`src/status_line.py`** reads session context (working directory, model) from stdin JSON provided by Claude Code, reads the usage cache, and prints the formatted status line.

The key insight is that `claude /usage` shows the **actual** usage data from Anthropic's servers. Other tools try to estimate usage by parsing local JSONL log files, which is always inaccurate because Anthropic's internal accounting works differently.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Status line shows `⚡ --` | Run `bash scrape_usage.sh` to populate the cache |
| Scrape returns empty data | Make sure `claude /usage` works inside Claude Code. The scrape needs a trusted project directory — it finds one from `~/.claude/projects/` |
| Model shows "Unknown" | Older Claude Code versions may not pass model info via stdin |
| Git branch not showing | Working directory must be a git repository |
| Status line not appearing | Restart Claude Code after editing `settings.json` |

## File structure

```
claude-status/
├── status_line.py          # Entry point (called by Claude Code)
├── scrape_usage.sh         # Scrapes claude /usage via PTY
├── src/
│   ├── status_line.py      # Status line formatter
│   ├── usage_scraper.py    # Cache reader + background scrape trigger
│   ├── git_info.py         # Git branch/status detection
│   ├── config.py           # Configuration management
│   └── tracker.py          # JSONL-based tracker (legacy)
├── config/
│   └── user_config.json    # User settings
└── data/
    └── usage_cache.json    # Cached usage data (auto-generated)
```
