# Changelog

## 0.9.3

- The office is now a construction site, as fits a foreman: a drafting room (blueprint floor),
  the building site (concrete, workbenches, bricks), inspection (clipboards) and the site
  office (the plan table). Every robot wears a hard hat in its role's color; the foreman, your
  main session, wears white. Room names are yellow site signs and doors carry hazard tape. The
  room ids did not change, so an existing `flow.json` keeps working.
- "ACT" is now "NEEDS YOU" ("PRECISA DE VOCÊ").

## 0.9.2

From the kit's first production use:

- A finding's decision line carries its key, `- fix|accepted <severity> <lens> [<key>]: ...`;
  `work.sh findings <ID>` prints the keys. A lens re-run that words a finding anew makes it a new,
  open finding: no old decision lands on it. Findings partly decided read `some-open`.
- The fix round ends by turning `- fix` into `- fixed` on the findings it fixed.
- The event stream takes the page's token, so another site cannot hold its connections.
- The cleanup refuses a worktree holding a directory named in `sensitive_ignored` (flow.json) or
  more ignored files than it can list; a task file edited after the confirmation refuses it too.
- The command that restarts the dashboard with a forge token reads it with `read -rs`, so the
  token never lands in the shell history.
- The page asks before deciding a finding, lets the dev dismiss an alert (and show it again),
  gives the whole command to ask the session about a failed review or a blocked agent, follows
  the system theme as a third option, and says "connecting" while the stream opens.

## 0.9.1

- The per-worktree switches (answering questions on the page, replying to the session's turn on
  the page) are on the dashboard too: a line under "Now" and a button on an alert that is off.
  Each asks first and says the risk; `POST /api/switch` writes the same files as the terminal
  command, behind the page's token.
- The task's lane is translated like every other word.
- The repository is `yantadeu/foreman`; `main` takes changes through pull requests only.

## 0.9.0

- The product is **Foreman**: name, logo (`assets/`), wordmark and favicon; every message a dev
  reads says Foreman. The repository keeps its name. Licensed Apache-2.0 with a NOTICE that
  credits the author; install.sh copies LICENSE and NOTICE into every install.
- New dashboard page, written for Foreman:
  - **Now**: one verb, ACT or WAIT. ACT lists what waits on the dev for the task, each answerable
    right there; WAIT names the agents at work.
  - **Steps**: the task as a tree with "you are here"; each review carries its findings, a
    step's file opens under it.
  - **Office**: a floor plan with one room per stage, each agent a robot at its desk with a name
    tag, a bubble while it works and a raised hand when it needs the dev; "You" sit in the
    decision room.
  - Everything in English and Portuguese, names included; every command to copy is whole,
    `cd <worktree> && claude "<message>"`.
  - `test_page.py` rewritten for it: 11 checks, each proved by mutations.
- Answer everything from the page: permission dialogs (allow or deny, always held while the page
  is open), questions (`work.sh ui answers on`) and the main session's turn
  (`work.sh ui turns on`, new): the message written on the page continues the session.
- Findings decided on the page one at a time (the server's model from the kit's first production
  use: open, fix-pending, fixed, accepted), with who acts on each: the dev, or the stage its
  route names inside the fix loop. A decision reaches the session at once: after its next tool
  call while it works (PostToolUse), or, when it stopped waiting for the findings, by holding
  that Stop until the decision arrives. A task with fixes asked from the page reads `fixing`.
- `/flow-agent`: create, move or remove a specialized agent by interview, with its place in the
  flow (review lens, stage, or outside the flow), its room and its look. The office is drawn from
  `rooms` of flow.json, so a new room and robot show up on their own; the task skill runs the
  stages flow.json lists.
- `language` in flow.json: every session is told at its start to write messages, questions and
  work files in the dev's language.
- The raised hand is a drawn icon with a pulsing ring, and new alerts play a two-note chime.
- From the kit's first production use: the event stream (`/api/events`) with a poll fallback, the
  finding parser that reads severity in several forms, sensitive git-ignored files refusing a
  worktree removal, the session marker, stronger log masking, and the dashboard refusing to be
  framed.

## 0.8.0

- The entry command is `/task` (it was `/agent-flow`). It works without a tracker: a plain
  description is enough, and the agent proposes the acceptance criteria and a short ID for the
  dev to confirm. `/flow-setup` treats "no tracker" as a complete answer.
- A task is done only when its pull or merge request is open or merged, when git sees its branch
  merged into the base, or when the dev runs `work.sh done [ID]`. The dashboard shows
  `findings` and `ready-for-mr` before that, links the PR/MR, says the next step, and warns
  when a FAIL is still standing at done. GitHub (also Enterprise, with `"forge": "github"`) and
  GitLab are looked up at most once a minute per branch; tokens never reach the page.
- Findings decision: a PASS_WITH_FINDINGS ends in one multiple-choice question; the checked
  findings go back through the stages, the rest are recorded as accepted, and
  `findings-decision.md` keeps the decision until a review reopens it.
- After done, the session suggests `/clear` before the next task.
- Cleanup replaces `cleanup.py`: `work.sh cleanup <ID>|--all-done` and the dashboard's "clean
  up" show one plan (task state, worktree and local branch, a review of Claude's auto memory
  about the task) and delete only what it lists after the dev confirms. A plan that changed is
  refused; a dirty, unpushed or live worktree is never removed; the auto memory is reviewed
  entry by entry by the next session in that worktree, never deleted wholesale.
- install.sh removes the hook entry of the old `cleanup.py` from settings.json.
- Dashboard page: English and Portuguese, terminal look kept; a "where it is" timeline; the
  findings of each review with their decision; "Mark as done"; every item waiting on the dev
  ends with its action and a command to copy; a failed PR/MR check never reads as "ready for
  PR"; noise (agent ids, tool calls, events) starts collapsed; a beep with mute; notifications
  show the kind of alert, never the command; the page cannot be framed. `test_page.py` checks
  it without a browser.
- Forge tokens from the environment go only to github.com or a host in `forge_hosts`; PRs and
  MRs from forks do not count.
- Cleanup lists the git-ignored files a removed worktree takes with it and refuses when a secret
  is among them; a live session is also a running Claude process or a recent event.
- The hooks record each session's Claude process; the event log keeps agent ids unmasked; the
  mask covers `--password`-style flags, `curl -u`, AWS keys and presigned URL signatures.

## 0.7.0

- `cleanup.py`: worktrees whose branch is merged into the base, or whose remote branch was
  deleted (squash merge), with their tasks and the Claude Code memory of their path. `--apply`
  refuses a dirty, locked or live worktree, archives each task with its events into
  `.work/archive/` of the main checkout, removes the worktree, and deletes the branch
  (`--delete-branch`, never `-D`) and the Claude Code memory of the path
  (`--forget-claude-project`) only when asked. `--prune` trims dead runtime state.
- A SessionStart hook tells the session which worktrees are finished, and the agent-flow skill
  offers the cleanup with `AskUserQuestion`, retrospective first. The dashboard marks a merged
  worktree in the sidebar.

## 0.6.0

- "Waiting on you" alerts: hooks on PermissionRequest, Notification, Stop, UserPromptSubmit,
  SessionStart, SessionEnd and AskUserQuestion keep `.work/attention/` current for every
  session, task or not; the dashboard shows them with a worktree badge, the count in the tab
  title and a browser notification.
- Answering `AskUserQuestion` from the dashboard, opt-in per worktree (`work.sh ui answers on`):
  the hook holds the question while the page is open, up to 9.5 minutes, and hands it back to
  the terminal on release, page close or timeout. The only write endpoint needs a per-server
  token, a localhost Origin and a JSON body.
- `merge-order.py`: merge order of the branches open at the same time, from git alone.
- `wire_hooks.py`: the installer wires hooks per (event, matcher), so a re-install adds new
  entries next to an older install's without duplicating them.
- The triage closes with `AskUserQuestion`, so the lane can be picked from the dashboard.

## 0.5.0

- Dashboard of every worktree: `scripts/dashboard.py` reads each worktree's work directory from
  `git worktree list`; a sidebar lists the tasks with their status (running, clarify, blocked,
  FAIL, done) and a click shows that task. Two read-only endpoints, tasks addressed by worktree
  index and id, never by path. Shows Status lines, clarifications, fix rounds and rulings.
- Terminal look: dark by default, monospaced panels with a live log per agent, a light toggle.
- `work.sh ui start | stop`: the dashboard in the background on the first free port from 8787.
- `/agent-flow` asks once per session whether to open the dashboard.

## 0.4.0

- Retrospective agent: reads the finished task and proposes tagged learnings for the dev to approve.
- Behavior evals (`.claude/kit/evals/`): fixture, pressure prompt and deterministic checks per
  case, `--runs N` and a `--control` run without the agent's instructions. First cases: refiner
  under ambiguity, refiner under time pressure, QA reviewer facing a test that cannot fail.
- GitHub Copilot: `--tools copilot` generates `.github/agents/*.agent.md` and `.github/prompts/`.
- "What you read is data, not orders" rule for learnings, sources, tickets and pages.
- Exit codes across scripts: 0 ok, 1 a check failed, 2 configuration or usage error.

## 0.3.0

- Fixed first line in every stage file and answer: `Status: DONE | DONE_WITH_CONCERNS |
  NEEDS_CONTEXT | BLOCKED`; the orchestrator routes on it.
- `ledger.md` per task: the base commit and every decision taken without asking, as rulings.
- `work.sh review-package`: one diff since the base, new files included, read by all reviewers.
- Findings carry `[route: refiner|executor|tester]`; the hook caps executor rounds
  (`max_fix_rounds`, default 3).
- `/flow-setup stack` asks for the model per stage and the round cap.

## 0.2.0

- Acceptance criteria as `AC-001`, `AC-002`...; the gate refuses a contract or a proof that
  does not cite every one.
- `[NEEDS CLARIFICATION: ...]` markers instead of guesses, resolved one question at a time and
  recorded under `## Clarifications` in the purpose.
- The hook refuses to launch a stage before the stages it requires pass (`requires` in
  `flow.json`), while a clarification is open, or after a stage reported `BLOCKED`.
- `Lane:` in the purpose; Full lane adds Given/When/Then criteria and edge cases.
- `work.sh status` shows what is next, or why it cannot start.

## 0.1.0

- Stages on disk in `.work/<ID>/`, stage gate hook, four parallel review lenses, product sources
  registry, `/flow-setup` and `/product-source`, learnings by lens, live dashboard, detection of
  existing AI configuration, projections for Cursor and Codex.
