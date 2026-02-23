# claude-quota-bar

A Claude Code status line that shows **real usage data** scraped from `claude /usage`.

```
📁 /home/user/project | 🌿 main*? | 🤖 Opus 4.6 | ⚡ 89% | 📅 57% | 🔄 2h 48m
```

| Section | Meaning |
|---------|---------|
| 📁 | Current working directory |
| 🌿 | Git branch + status (`*` modified, `?` untracked, `↑↓` ahead/behind) |
| 🤖 | Active model |
| ⚡ | Session usage % (green/yellow/red) |
| 📅 | Weekly usage % (green/yellow/red) |
| 🔄 | Time until session resets |

## Requirements

- Linux (uses `script` command for PTY emulation)
- Python 3.10+
- Claude Code CLI installed and authenticated

## Install

```bash
git clone https://github.com/Caleb13360/claude-quota-bar.git ~/claude-quota-bar
cd ~/claude-quota-bar
bash scrape_usage.sh        # populate initial cache (~15s)
python3 install.py          # hooks into ~/.claude/settings.json
```

Restart Claude Code. The status line appears at the bottom.

## How it works

1. **`scrape_usage.sh`** runs `claude /usage` in a PTY, strips ANSI codes, and parses usage percentages into `data/usage_cache.json`.
2. **`status_line.py`** reads the cache (triggering a background re-scrape if stale), grabs git info and model context from Claude Code's stdin JSON, and prints the formatted line.

## Files

```
claude-quota-bar/
├── status_line.py      # Main script (called by Claude Code)
├── scrape_usage.sh     # Scrapes claude /usage via PTY
├── install.py          # Hooks into ~/.claude/settings.json
└── data/
    └── usage_cache.json  # Auto-generated cache
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `⚡ --` | Run `bash scrape_usage.sh` to populate cache |
| Empty scrape | Make sure `claude /usage` works; needs a project in `~/.claude/projects/` |
| Model shows "Unknown" | Older Claude Code may not pass model info |
| No git branch | Directory must be a git repo |
| Status line missing | Restart Claude Code after install |
