#!/usr/bin/env python3
"""Merge order of the branches (MRs) open at the same time, computed from git alone.

Usage: merge-order.py [--base <remote/branch>] [--json] [branch ...]
       (default base: the remote's default branch, origin/HEAD, else origin/main)

Without branches it takes the ones checked out in the worktrees of this repository that
have commits the base does not. For each pair it says why one goes before the other:

  stacked   B was cut from A (A's tip is in B): A merges first, or B's MR carries A's diff.
  overlap   both change the same file and neither contains the other: merge the one that
            started first, then rebase the other on the base and re-run its pipeline.

A branch with neither is independent and merges in any order. The order is printed as a
numbered list, the same text that goes into the "Merge order" section of each PR or MR.
"""
import argparse
import json
import subprocess
import sys


def git(*args, check=True):
    run = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and run.returncode != 0:
        raise SystemExit(f"git {' '.join(args)}: {run.stderr.strip()}")
    return run


def worktree_branches():
    out, found = git("worktree", "list", "--porcelain").stdout, []
    for line in out.splitlines():
        if line.startswith("branch "):
            found.append(line[len("branch "):].removeprefix("refs/heads/"))
    return found


def ahead(base, branch):
    return int(git("rev-list", "--count", f"{base}..{branch}").stdout.strip() or 0)


def first_commit_time(base, branch):
    times = git("log", "--format=%ct", "--reverse", f"{base}..{branch}").stdout.split()
    return int(times[0]) if times else 0


def changed_files(base, branch):
    return set(git("diff", "--name-only", f"{base}...{branch}").stdout.split())


def is_ancestor(a, b):
    return git("merge-base", "--is-ancestor", a, b, check=False).returncode == 0


def plan(base, branches):
    """Returns (order, edges, independent): order is the merge list, edges the reasons."""
    live = [b for b in dict.fromkeys(branches) if ahead(base, b) > 0]
    started = {b: first_commit_time(base, b) for b in live}
    # Sorted, so the answer does not depend on the order the branches were named in.
    live.sort(key=lambda x: (started[x], x))
    files = {b: changed_files(base, b) for b in live}
    edges = []  # (first, then, kind, detail)
    for i, a in enumerate(live):
        for b in live[i + 1:]:
            if is_ancestor(a, b) and not is_ancestor(b, a):
                edges.append((a, b, "stacked", f"{b} was cut from {a}"))
            elif is_ancestor(b, a) and not is_ancestor(a, b):
                edges.append((b, a, "stacked", f"{a} was cut from {b}"))
            else:
                common = sorted(files[a] & files[b])
                if common:
                    first, then = sorted((a, b), key=lambda x: (started[x], x))
                    shown = ", ".join(common[:5]) + (f" (+{len(common) - 5})" if len(common) > 5 else "")
                    edges.append((first, then, "overlap", f"both change {shown}; rebase {then} after {first} merges"))
    # Kahn's sort, ties broken by the branch that started first.
    before = {b: set() for b in live}
    for first, then, _, _ in edges:
        before[then].add(first)
    order, left = [], set(live)
    while left:
        ready = sorted((b for b in left if not (before[b] & left)), key=lambda x: (started[x], x))
        if not ready:  # a cycle cannot come from ancestry; overlap edges follow start time
            ready = sorted(left, key=lambda x: (started[x], x))
        order.append(ready[0])
        left.discard(ready[0])
    linked = {b for e in edges for b in e[:2]}
    return order, edges, [b for b in order if b not in linked]


def default_base():
    ref = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False).stdout.strip()
    return ref or "origin/main"


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--base", default=None)
    p.add_argument("--json", action="store_true")
    p.add_argument("branches", nargs="*")
    args = p.parse_args()
    args.base = args.base or default_base()
    branches = args.branches or [b for b in worktree_branches() if b != args.base.split("/")[-1]]
    order, edges, independent = plan(args.base, branches)
    if args.json:
        print(json.dumps({"base": args.base, "order": order, "independent": independent,
                          "edges": [dict(zip(("first", "then", "kind", "detail"), e)) for e in edges]}, indent=2))
        return 0
    if not order:
        print(f"no branch ahead of {args.base}")
        return 0
    print(f"Merge order into {args.base}:")
    for n, b in enumerate(order, 1):
        why = [f"after {f} ({k}: {d})" for f, t, k, d in edges if t == b]
        print(f"  {n}. {b}" + ("  independent, any order" if b in independent else "")
              + "".join(f"\n       {w}" for w in why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
