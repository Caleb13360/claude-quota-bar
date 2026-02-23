#!/usr/bin/env python3
"""
Installer for claude-quota-bar.
Hooks status_line.py into Claude Code's settings.
"""

import json
import shutil
import sys
from pathlib import Path


def main():
    project_dir = Path(__file__).parent.resolve()
    claude_settings = Path.home() / ".claude" / "settings.json"

    # Require Python 3.10+ (for match/union types in status_line.py)
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

    # Wire up the status line command
    settings["statusLine"] = {
        "type": "command",
        "command": f"python3 {project_dir / 'status_line.py'}",
    }

    claude_settings.parent.mkdir(exist_ok=True)
    with open(claude_settings, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"Updated {claude_settings}")
    print("Done — restart Claude Code to see the status line.")


if __name__ == "__main__":
    main()
