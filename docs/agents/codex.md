# Codex

Project rules live in [AGENTS.md](../../AGENTS.md). Codex reads `AGENTS.md` natively; no extra
configuration is needed.

## One shared skill checkout

Keep exactly one img2threejs checkout and symlink each harness into it, so the two never end up
running different versions of the scripts:

```
~/.claude/skills/img2threejs -> <checkout>  (v1.5.1 @ dede590)
~/.codex/skills/img2threejs  -> <checkout>
.agents/skills/img2threejs   -> <checkout>
```

Always run the forge scripts from the skill root; never call them by relative path from the project
root.
