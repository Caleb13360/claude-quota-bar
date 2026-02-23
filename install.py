#!/usr/bin/env python3
"""
Installer for claude-quota-bar.
Hooks status_line.py and scrape_usage.sh into Claude Code's settings.
"""

import json
import shutil
import sys
from pathlib import Path


def main():
    project_dir = Path(__file__).parent.resolve()
    claude_settings = Path.home() / ".claude" / "settings.json"

    if sys.version_info < (3, 10):
        print("Python 3.10+ is required.")
        sys.exit(1)

    # Load existing settings (or start fresh)
    if claude_settings.exists():
        backup = claude_settings.with_suffix(".json.backup")
        shutil.copy2(claude_settings, backup)
        print(f"Backed up settings to {backup}")
        with open(claude_settings) as f:
            settings = json.load(f)
    else:
        settings = {}

    scrape_cmd = f'bash "{project_dir / "scrape_usage.sh"}"'

    # Wire up the status line
    settings["statusLine"] = {
        "type": "command",
        "command": f'python3 "{project_dir / "status_line.py"}"',
    }

    # Wire up Stop hook to refresh usage data after each response
    stop_hook = {
        "hooks": [
            {
                "type": "command",
                "command": scrape_cmd,
                "async": True,
            }
        ]
    }

    # Preserve existing hooks, append ours
    hooks = settings.get("hooks", {})
    stop_hooks = hooks.get("Stop", [])

    # Remove any existing scrape hook we installed previously
    stop_hooks = [h for h in stop_hooks if scrape_cmd not in json.dumps(h)]
    stop_hooks.append(stop_hook)

    hooks["Stop"] = stop_hooks
    settings["hooks"] = hooks

    claude_settings.parent.mkdir(exist_ok=True)
    with open(claude_settings, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"Updated {claude_settings}")
    print("Installed:")
    print(f"  - Status line: python3 {project_dir / 'status_line.py'}")
    print(f"  - Stop hook:   {scrape_cmd}")
    print("Restart Claude Code to activate.")


if __name__ == "__main__":
    main()
