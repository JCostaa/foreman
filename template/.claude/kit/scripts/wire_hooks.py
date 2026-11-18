#!/usr/bin/env python3
"""Wires the kit's hooks into a Claude Code settings.json, keeping every other hook.

Usage: wire_hooks.py <settings.json>     (called by install.sh; idempotent)

Matched per (event, matcher), not per event: a repo that already runs flow.py on
PreToolUse "*" still needs the AskUserQuestion hold, which is a separate entry with its own
timeout. The repo's own .claude/settings.json is what this produces from itself, and
test_kit.py asserts it, so the kit and the repo cannot drift.
"""
import json
import os
import re
import sys

FLOW = "python3 \"$CLAUDE_PROJECT_DIR/.claude/kit/hooks/flow.py\""
HOLD = "python3 \"$CLAUDE_PROJECT_DIR/.claude/kit/hooks/attention.py\" hold"
# Permission dialogs and the main session's turn, answered from the page while it is open.
PERMISSION = "python3 \"$CLAUDE_PROJECT_DIR/.claude/kit/hooks/attention.py\" permission"
TURN = "python3 \"$CLAUDE_PROJECT_DIR/.claude/kit/hooks/attention.py\" turn"
CLEANUP = "python3 \"$CLAUDE_PROJECT_DIR/.claude/kit/scripts/dashboard.py\" hook \"$CLAUDE_PROJECT_DIR\""
# Scripts an older kit wired that no longer exist: their entries would fail on every event.
GONE = ("cleanup.py",)

# The holds wait for the page as long as it stays open and in view (they let go 30 s after it
# closes or hides), so their hook timeout is an hour, 30 s over the 3570 s hold. Measured on
# Claude Code 2.1.326: a 3600 s timeout held a PreToolUse, a Stop and a SessionStart hook for 660
# to 700 s without a kill (no run went longer), and a 15 s timeout killed its 45 s hook at 15 s
# (the control). PermissionRequest was not measured on its own: it runs through the same runner.
HOLD_TIMEOUT = 3600
# (event, matcher or None, command, timeout). The rest return in milliseconds.
HOOKS = [
    ("PreToolUse", "*", FLOW, 10),
    ("PreToolUse", "AskUserQuestion", HOLD, HOLD_TIMEOUT),
    ("PostToolUse", "AskUserQuestion", FLOW, 10),
    # A decision taken on the page reaches the working main session after its next tool call.
    ("PostToolUse", "*", FLOW, 10),
    ("PermissionRequest", None, FLOW, 10),
    ("PermissionRequest", None, PERMISSION, HOLD_TIMEOUT),
    ("Notification", "permission_prompt", FLOW, 10),
    ("SubagentStart", None, FLOW, 10),
    ("SubagentStop", None, FLOW, 10),
    ("Stop", None, FLOW, 10),
    ("Stop", None, TURN, HOLD_TIMEOUT),
    ("UserPromptSubmit", None, FLOW, 10),
    ("SessionStart", None, FLOW, 10),
    ("SessionStart", None, CLEANUP, 10),
    ("SessionEnd", None, FLOW, 10),
]


SCRIPT_RX = re.compile(r'/([\w-]+\.py)"?\s*(\S*)')


def same_script(installed, wanted):
    """An older install may quote the path differently; the script and its first argument decide."""
    got, want = SCRIPT_RX.search(installed.strip()), SCRIPT_RX.search(wanted.strip())
    return bool(got and want) and (got[1], got[2].strip()) == (want[1], want[2].strip())


def wire(settings):
    hooks = settings.setdefault("hooks", {})
    for groups in hooks.values():
        for g in groups:
            g["hooks"] = [h for h in g.get("hooks", [])
                          if not (SCRIPT_RX.search(h.get("command", "")) or [None, ""])[1] in GONE]
        groups[:] = [g for g in groups if g["hooks"]]
    for event, matcher, command, timeout in HOOKS:
        groups = hooks.setdefault(event, [])
        mine = [h for g in groups if g.get("matcher") == matcher for h in g.get("hooks", [])
                if same_script(h.get("command", ""), command)]
        if mine:
            # The kit owns its own entries' command and timeout: an older install's 600 s hold
            # would be killed long before the hold lets go.
            for h in mine:
                h["command"], h["timeout"] = command, timeout
            continue
        groups.append({**({"matcher": matcher} if matcher else {}),
                       "hooks": [{"type": "command", "command": command, "timeout": timeout}]})
    return settings


def render(settings):
    return json.dumps(settings, indent=2) + "\n"


def main(path):
    settings = {}
    if os.path.exists(path):
        with open(path) as f:
            settings = json.load(f)
    out = render(wire(settings))
    with open(path, "w") as f:
        f.write(out)


if __name__ == "__main__":
    main(sys.argv[1])
