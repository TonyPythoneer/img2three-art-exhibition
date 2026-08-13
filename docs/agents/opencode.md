# opencode — the execution end for non-visual work

> **Dispatching here is no longer automatic.** The standing rule that sent all non-visual work to
> opencode has been revoked; see [AGENTS.md](../../AGENTS.md) § _Work split_. Nothing in this file
> may be acted on without an explicit user order. It is kept as a reference for when the user does
> ask for a dispatch.

## Model

`opencode.json` at the project root pins the default:

```json
{ "model": "opencode/mimo-v2.5-free" }
```

`orca orchestration worker-start` has no `--model` flag, so the model can only come from that
config — **do not delete it**. `openrouter/xiaomi/mimo-v2.5` is the paid equivalent, used only when
the free tier's quota runs out.

Changing the model affects **subsequently** started workers only; a running worker keeps the model
it started with.

## Dispatch commands

```bash
orca orchestration run-create  --objective "<what this round is doing>" --json
orca orchestration task-create --spec "<one smallest reasonable unit of work>" --json
orca orchestration worker-start --task <task_id> --worktree current --agent opencode --json
orca orchestration check --wait --types worker_done,escalation,question --timeout-ms 600000 --json
```

A `check --wait` timeout or `{count:0}` is a checkpoint, not a failure; 15–60 minutes is normal for
long work, so keep rolling the wait. There are only three real failure signals: an `escalation`
arrives, the terminal disappears, or the user calls a halt.

## Dispatch contract

- One smallest reasonable unit at a time: one part, one script, one gate. That keeps the blast
  radius small when a dispatch dies mid-run.
- opencode executes a dispatched task as a **subagent**, not a long-lived session.
- While a dispatch is in flight the main agent healthchecks every 60s; three consecutive misses
  means the dispatch has failed — **create and dispatch a new task**, never resume the stalled one.
- The deliverable is **files plus a rerunnable command**. "I looked at it and it's fine" is not a
  deliverable.

## Known failure mode: a self-contradictory task spec spins forever

Observed 2026-08-12: a task spec demanded both "the face must be smooth" and "angle between
adjacent face normals ≥18° (hard faceting)". The worker stayed in one reasoning loop for
**50 minutes** with zero files produced, repeatedly re-deriving the normal angles of the smooth
control sphere. It will not point out the contradiction itself and it will not escalate — it just
circles.

**So read your own task spec before sending it and ask: are any two requirements in here mutually
exclusive?** State the direction of every assertion explicitly — `>= X` (make it faceted) or
`<= X` (make it smooth), never just a bare number.

If you see it spinning, run
`orca terminal read --terminal <handle> --limit 60 --json` to see where it is stuck, fix the
contradiction, and **dispatch a new task**; do not resume the stalled one.

## What does not happen here

No reading of reference images, no judging renders, no deciding
`continue`/`refine-spec`/`refine-code`. Anything that needs eyes goes back to the main agent, with
the paths of the images produced.

## Environment traps

- The global `~/.config/opencode/opencode.json` sets `bash`/`glob`/`grep`/`read` to `deny`. A
  dispatch prompt must either go through the lean-ctx MCP tools or say explicitly which of those
  needs to be allowed.
- The default reply language is Traditional Chinese (`instructions` in that same config).
