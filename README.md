<p align="center">
<img 
  width="200" 
  height="200" 
  src="https://raw.githubusercontent.com/alexruco/caveman-mcp/refs/heads/main/images/caveman-mcp.png" 
  alt="hammer"
>
</p>
<div class="install-box">

### Install caveman-mcp

<pre><code class="bash">
pip install caveman-mcp
</code></pre>

</div>

<p class="install-alt">
  or run without installing: <code>uvx caveman-mcp</code>
</p>
<h1 align="center">caveman-mcp</h1>

<p align="center">
  <strong>MCP server that cuts 65% of tokens by compressing markdown files and activating caveman speak.</strong><br/>
  Thinner and simpler than the original — no file distribution, no sync. No API key. Works everywhere.
</p>

<p align="center">
  <a href="https://pypi.org/project/caveman-mcp"><img src="https://img.shields.io/pypi/v/caveman-mcp?style=flat&color=blue" alt="PyPI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat" alt="License"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-green?style=flat" alt="MCP"></a>
</p>

---

## Why

Every token you send costs money and fills context. Long markdown files — `CLAUDE.md`, memory files, notes, docs — get read on every session. Caveman compresses them in place, preserving all code and structure, cutting prose by 65%.

| Without caveman (69 tokens) | With caveman (19 tokens) |
|----------------------------------|------------------------------|
| "The reason your React component is re-rendering is likely because you're creating a new object reference on each render cycle. When you pass an inline object as a prop, React's shallow comparison sees it as a different object every time, which triggers a re-render. I'd recommend using useMemo to memoize the object." | "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`." |

**Same fix. 75% fewer tokens.**

## Why MCP

Caveman prompts used to require a file in every project. With MCP:

- **Register once** — works across all projects, all agents
- **No file to sync** — no copy-pasting prompts into repos
- **Tools included** — compress any markdown file directly from the agent
- **Any client** — Claude Code, Cursor, Windsurf, Cline, or any MCP-compatible host

## Install

```bash
pip install caveman-mcp
```

Or run without installing:

```bash
uvx caveman-mcp
```

## Connect

**Claude Code** (global — recommended):

Edit `~/.claude/settings.json`:
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

Or per-project via CLI:
```bash
claude mcp add caveman-mcp uvx -- caveman-mcp
```

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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

> **Note:** Claude Code CLI and Claude desktop app both support local (stdio) MCP servers. Claude.ai web app only supports remote (HTTP/SSE) connectors.

**Without uvx** (local clone):
```json
{
  "command": "/path/to/.venv/bin/python",
  "args": ["-m", "caveman_mcp.server"]
}
```

## Prompts

Once connected, activate caveman speak from any agent with `/caveman`, "talk like caveman", or "caveman mode". Stop with "stop caveman" or "normal mode".

| Prompt | What it does |
|--------|--------------|
| `caveman` | Activate caveman compression |
| `caveman-commit` | Terse commit message style |
| `caveman-review` | One-line code review comments |
| `caveman-help` | Quick-reference card |

### Intensity levels

| Mode | Effect |
|------|--------|
| `lite` | Drop filler, keep full sentences and articles |
| `full` | Default — drop articles, fragments OK, short synonyms |
| `ultra` | Abbreviate (DB/auth/req/res/fn), strip conjunctions, X→Y causality |
| `wenyan-lite` | Semi-classical Chinese register |
| `wenyan-full` | Full 文言文, 80–90% character reduction |
| `wenyan-ultra` | Extreme, ancient scholar feel |

## Compress Tools

Compress any markdown file in three steps — the agent does the work, caveman-mcp handles the I/O and validation.

### `compress_prepare(filepath)`

Reads the file, returns content + compression instructions. The agent compresses the prose, then calls `compress_write`.

```
compress_prepare("CLAUDE.md")
→ { filepath, original_content, instructions }
```

Refuses: sensitive files (`~/.ssh/`, `.env`, credentials), existing backups, non-text formats, files > 500 KB.

### `compress_write(filepath, compressed_content)`

Writes compressed content. Auto-creates a `.original.md` backup on first call. Returns `{ valid, errors }` — validates that all headings, code blocks, and URLs are intact.

### `compress_restore(filepath)`

Restores from `.original.md` backup. Call if something goes wrong.

**Flow:**

```
compress_prepare("CLAUDE.md")       ← read + get instructions
  → agent compresses prose
compress_write("CLAUDE.md", result) ← write + validate
  → { valid: true, errors: [] }
```

The result:

```
CLAUDE.md          ← compressed (65% fewer tokens every session)
CLAUDE.original.md ← full backup (edit this, re-compress anytime)
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

**Toggle:** run `python3 ~/bin/caveman-toggle` to turn auto-compress on or off. To use as a bare command, add `~/bin` to PATH via `~/.zprofile` (not `.zshrc`):

```bash
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zprofile
```

Files with an existing `.original.md` backup are skipped automatically.

## Attribution

Fork of [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) — MIT licence, copyright © 2026 Julius Brussee. Original prompt design and caveman concept by Julius Brussee. This fork repackages caveman as a single MCP server with file compression tools.

## License

MIT
