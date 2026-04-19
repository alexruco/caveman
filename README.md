<p align="center">
  <img src="https://em-content.zobj.net/source/apple/391/rock_1faa8.png" width="120" />
</p>

<h1 align="center">caveman-mcp</h1>

<p align="center">
  <strong>why use many token when few do trick</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat" alt="License"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-green?style=flat" alt="MCP"></a>
</p>

---

MCP server exposing [caveman](https://github.com/JuliusBrussee/caveman) prompts + compress tool to any MCP-compatible agent — one registration, no file distribution, no sync.

## Before / After

| Normal (69 tokens) | Caveman (19 tokens) |
|--------------------|---------------------|
| "The reason your React component is re-rendering is likely because you're creating a new object reference on each render cycle. When you pass an inline object as a prop, React's shallow comparison sees it as a different object every time, which triggers a re-render. I'd recommend using useMemo to memoize the object." | "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`." |

**Same fix. 75% less word.**

## Install

```bash
pip install caveman-mcp
```

Or run directly without installing:

```bash
uvx caveman-mcp
```

## MCP Config

**Claude Code** (CLI — recommended):
```bash
claude mcp add caveman-mcp uvx -- caveman-mcp
```

Global install across all projects — edit `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "caveman-mcp": {
      "command": "uvx",
      "args": ["caveman-mcp"]
    }
  }
}
```

> **Note:** Claude Code CLI and Claude desktop app both support local (stdio) MCP servers. Claude.ai web app only supports remote (HTTP/SSE) connectors.

**Cursor** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "caveman-mcp": {
      "command": "uvx",
      "args": ["caveman-mcp"]
    }
  }
}
```

**Windsurf** (`~/.codeium/windsurf/mcp_settings.json`):
```json
{
  "mcpServers": {
    "caveman-mcp": {
      "command": "uvx",
      "args": ["caveman-mcp"]
    }
  }
}
```

**Cline** (MCP settings panel → Add Server):
```json
{
  "command": "uvx",
  "args": ["caveman-mcp"]
}
```

**Without uvx** (local clone):
```json
{
  "command": "/path/to/.venv/bin/python",
  "args": ["-m", "caveman_mcp.server"]
}
```

## Prompts

| Name | Description | Parameters |
|------|-------------|------------|
| `caveman` | Activate caveman compression | `mode` (optional) |
| `caveman-commit` | Terse commit message style | — |
| `caveman-review` | One-line code review style | — |
| `caveman-help` | Quick-reference card | — |

### Intensity levels (`mode` parameter)

| Mode | Effect |
|------|--------|
| `lite` | Drop filler, keep full sentences and articles |
| `full` | Default. Drop articles, fragments OK, short synonyms |
| `ultra` | Abbreviate (DB/auth/req/res/fn), strip conjunctions, X→Y causality |
| `wenyan-lite` | Semi-classical Chinese register |
| `wenyan-full` | Full 文言文, 80–90% character reduction |
| `wenyan-ultra` | Extreme, ancient scholar feel |

Activate with `/caveman`, "talk like caveman", or "caveman mode". Stop with "stop caveman" or "normal mode".

## Tools

### `compress_prepare(filepath)`

Reads markdown/text file, returns content + compression instructions. Agent compresses prose, passes result to `compress_write`.

```
compress_prepare("CLAUDE.md")
→ { filepath, original_content, instructions }
```

Refuses: sensitive files (`~/.ssh/`, `.env`, credentials), backup files (`.original.md`), non-text formats, files > 500 KB.

### `compress_write(filepath, compressed_content)`

Writes compressed content. Creates `.original.md` backup on first call (idempotent on retry). Returns `{ valid, errors }` — validates headings, code blocks, URLs preserved.

### `compress_restore(filepath)`

Restores from `.original.md` backup and deletes it. Call if validation keeps failing.

**Typical compress flow:**

```
compress_prepare("CLAUDE.md")           ← agent reads original
  → agent compresses prose
compress_write("CLAUDE.md", result)     ← write + validate
  → { valid: true, errors: [] }
```

```
CLAUDE.md          ← compressed (Claude reads this every session)
CLAUDE.original.md ← human-readable backup (you edit this)
```

## Auto-compress with Claude Code hook

Compress files automatically whenever Claude reads them — no manual invocation needed.

**1. Create the hook script** (`~/bin/caveman-hook`):

```python
#!/usr/bin/env python3
"""PostToolUse hook: compress .md files via caveman MCP when auto mode is on."""
import json, os, sys

flag = os.path.expanduser("~/.claude/caveman-auto")
if not os.path.exists(flag):
    sys.exit(0)

data = json.load(sys.stdin)
filepath = data.get("tool_input", {}).get("file_path", "")

if not filepath.endswith(".md"):
    sys.exit(0)

backup = filepath.replace(".md", ".original.md")
if os.path.exists(backup):
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": (
            f"caveman-auto is ON. Compress {filepath} now using the three-step workflow: "
            "compress_prepare → compress the prose → compress_write. "
            "Do this silently without announcing it."
        )
    }
}))
```

```bash
chmod +x ~/bin/caveman-hook
```

**2. Create the toggle script** (`~/bin/caveman-toggle`):

```python
#!/usr/bin/env python3
import os

flag = os.path.expanduser("~/.claude/caveman-auto")
if os.path.exists(flag):
    os.remove(flag)
    print("caveman: OFF")
else:
    open(flag, "w").close()
    print("caveman: ON")
```

```bash
chmod +x ~/bin/caveman-toggle
```

**3. Register the hook** in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /Users/you/bin/caveman-hook",
            "statusMessage": "caveman check..."
          }
        ]
      }
    ]
  }
}
```

**Usage:** run `python3 ~/bin/caveman-toggle` to turn auto-compress on or off. To use as bare command, add `~/bin` to PATH via `~/.zprofile` (not `.zshrc`):

```bash
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zprofile
```

Files with existing `.original.md` backup are skipped.

## Attribution

Fork of [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) — MIT licence, copyright © 2026 Julius Brussee. Original prompt design and caveman concept by Julius Brussee. This fork strips the file-distribution system and repackages caveman as a single MCP server.

## License

MIT
