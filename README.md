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

MCP server that exposes [caveman](https://github.com/JuliusBrussee/caveman) prompts and the compress tool to any MCP-compatible agent — one registration, no file distribution, no sync workflows.

## Before / After

| Normal (69 tokens) | Caveman (19 tokens) |
|--------------------|---------------------|
| "The reason your React component is re-rendering is likely because you're creating a new object reference on each render cycle. When you pass an inline object as a prop, React's shallow comparison sees it as a different object every time, which triggers a re-render. I'd recommend using useMemo to memoize the object." | "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`." |

**Same fix. 75% less word.**

## Install

```bash
uvx caveman-mcp
```

Or add to your MCP config and let the agent launch it on demand.

## MCP Config

**Claude Code** (CLI command — recommended):
```bash
claude mcp add caveman-mcp uvx -- caveman-mcp
```

This adds it to the project-local config. For global installation across all projects, edit `~/.claude/settings.json`:
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

> **Note:** The Claude.app desktop UI only supports remote (HTTP/SSE) connectors — use the CLI command above instead.

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

Reads a markdown/text file and returns its content with compression instructions. The calling agent compresses the prose, then passes the result to `compress_write`.

```
compress_prepare("CLAUDE.md")
→ { filepath, original_content, instructions }
```

Refuses: sensitive files (`~/.ssh/`, `.env`, credentials), backup files (`.original.md`), non-text formats, files > 500 KB.

### `compress_write(filepath, compressed_content)`

Writes compressed content. Creates a `.original.md` backup on first call (idempotent on retry). Returns `{ valid, errors }` — validates that headings, code blocks, and URLs are preserved.

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

## Attribution

Fork of [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) — MIT licence, copyright © 2026 Julius Brussee. Original prompt design and caveman concept by Julius Brussee. This fork strips the file-distribution system and repackages caveman as a single MCP server.

## License

MIT
