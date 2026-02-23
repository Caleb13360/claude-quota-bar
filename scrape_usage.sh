#!/bin/bash
# Scrapes claude /usage and writes JSON to data/usage_cache.json
# Run this in the background (e.g. via Claude Code Stop hook).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE_FILE="$SCRIPT_DIR/data/usage_cache.json"
LOCK_FILE="$SCRIPT_DIR/data/scrape.lock"

# Only one scrape at a time
if [ -f "$LOCK_FILE" ]; then
    lock_age=$(( $(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0) ))
    if [ "$lock_age" -lt 30 ]; then
        exit 0
    fi
    rm -f "$LOCK_FILE"
fi

touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# Find a trusted project directory (most recently modified jsonl)
TRUSTED_DIR=$(find ~/.claude/projects -name '*.jsonl' -printf '%T@ %h\n' 2>/dev/null | sort -rn | head -1 | awk '{print $2}')
if [ -n "$TRUSTED_DIR" ]; then
    REAL_PATH=$(tail -1 "$(ls -t "$TRUSTED_DIR"/*.jsonl 2>/dev/null | head -1)" 2>/dev/null | python3 -c "import sys,json; print(json.loads(sys.stdin.readline()).get('cwd',''))" 2>/dev/null)
    if [ -d "$REAL_PATH" ]; then
        cd "$REAL_PATH"
    fi
fi

mkdir -p "$SCRIPT_DIR/data"

# Capture claude /usage output via PTY
TMPFILE=$(mktemp /tmp/claude_usage_XXXXXX.txt)
env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT TERM=xterm-256color timeout 15 script -qc "claude /usage" "$TMPFILE" >/dev/null 2>&1

# Parse output — only overwrite cache if we got real data
python3 -c "
import re, json, time, sys

with open('$TMPFILE', 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8', errors='ignore')
text = re.sub(r'\x1b\[(\d+)C', lambda m: ' ' * int(m.group(1)), text)
text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
text = re.sub(r'\x1b\].*?\x07', '', text)
text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

lines = [l.strip() for l in text.splitlines() if l.strip()]

result = {'scraped_at': time.time()}
i = 0
while i < len(lines):
    ll = lines[i].lower()
    section = None
    if 'current session' in ll: section = 'session'
    elif 'current week' in ll and 'all model' in ll: section = 'weekly_all'
    elif 'current week' in ll and 'opus' in ll: section = 'weekly_opus'
    elif 'current week' in ll and 'sonnet' in ll: section = 'weekly_sonnet'

    if section:
        for j in range(i, min(i+8, len(lines))):
            m = re.search(r'(\d{1,3})\s*%\s*(used|left)', lines[j])
            if m:
                val = int(m.group(1))
                if m.group(2) == 'left': val = 100 - val
                result[section + '_pct'] = val
                break
        for j in range(i, min(i+10, len(lines))):
            m = re.search(r'[Rr]ese\s*t?s?\s+(.*)', lines[j])
            if m:
                result[section + '_reset'] = m.group(1).strip()
                break
    i += 1

# Only write cache if we actually parsed usage data
if any(k.endswith('_pct') for k in result):
    with open('$CACHE_FILE', 'w') as f:
        json.dump(result, f)
"

rm -f "$TMPFILE"
