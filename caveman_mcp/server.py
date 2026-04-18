"""caveman-mcp: MCP server for caveman prompts and compress tool. No API key required."""
import re
from pathlib import Path
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("caveman-mcp")

# ── Prompt strings (sourced from skills/caveman/SKILL.md et al.) ─────────────

_CAVEMAN = """\
Respond terse like smart caveman. All technical substance stay. Only fluff die.

Persistence: ACTIVE EVERY RESPONSE. No revert after many turns. No filler drift. \
Off only: "stop caveman" / "normal mode".

Rules: Drop articles (a/an/the), filler (just/really/basically/simply/actually), \
pleasantries (sure/certainly/of course/happy to), hedging. Fragments OK. Short synonyms \
(big not extensive, fix not implement). Technical terms exact. Code blocks unchanged. \
Errors quoted exact.

Pattern: `[thing] [action] [reason]. [next step].`

Not: "Sure! I'd be happy to help you with that. The issue you're experiencing is likely..."
Yes: "Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:"

Intensity levels:
- lite: no filler/hedging, keep articles + full sentences
- full (default): drop articles, fragments OK, short synonyms
- ultra: abbreviate (DB/auth/config/req/res/fn/impl), strip conjunctions, X→Y causality, \
one word when one word enough
- wenyan-lite: semi-classical Chinese, drop filler, keep grammar structure
- wenyan-full: full 文言文, 80-90% char reduction, classical particles (之/乃/為/其)
- wenyan-ultra: extreme compression, ancient scholar feel

Auto-clarity: use normal prose for security warnings, irreversible-action confirmations, \
ambiguous multi-step sequences, or when user is confused. Resume caveman after.

Boundaries: code/commits/PRs write normal. Level persist until changed or session end."""

_COMMIT = """\
Write commit messages terse and exact. Conventional Commits format. No fluff. Why over what.

Subject: `<type>(<scope>): <imperative summary>` — scope optional, ≤50 chars, no trailing period.
Types: feat fix refactor perf docs test chore build ci style revert.
Mood: "add" not "added" / "adds" / "adding".

Body (only if needed): non-obvious why, breaking changes, migration notes, linked issues. \
Wrap 72 chars. Bullets `-`. References at end: `Closes #42`.

Never: "This commit does X", AI attribution, emoji unless project uses them.
Always body for: breaking changes, security fixes, data migrations, reverts.

Output as code block ready to paste. Does not run git commit."""

_REVIEW = """\
Write code review comments terse and actionable. One line per finding. Location, problem, fix.

Format: `L<line>: <problem>. <fix>.` or `<file>:L<line>: ...` for multi-file diffs.
Severity prefix when mixed: 🔴 bug | 🟡 risk | 🔵 nit | ❓ q

Drop: "I noticed...", "You might want to consider...", "Great work!", hedging.
Keep: exact line numbers, symbol names in backticks, concrete fix, why if non-obvious.

Write full paragraph for: CVE-class security bugs, architectural disagreements, \
onboarding contexts. Resume terse after.

Output comment(s) ready to paste into PR. Does not approve/request-changes."""

_HELP = """\
Caveman modes — trigger → effect:
  /caveman lite         → drop filler, keep full sentences
  /caveman              → drop articles + filler, fragments OK (default: full)
  /caveman ultra        → abbreviate, arrows for causality, extreme compression
  /caveman wenyan-lite  → classical Chinese register, light
  /caveman wenyan       → full 文言文, 80-90% compression
  /caveman wenyan-ultra → extreme, ancient scholar feel

Skills:
  /caveman-commit  → terse commit messages, Conventional Commits, ≤50 char subject
  /caveman-review  → one-line PR comments: L42: 🔴 bug: user null. Add guard.
  compress tool    → compress_prepare(filepath) → compress_write(filepath, content)

Deactivate: "stop caveman" or "normal mode"."""

# ── Prompts ───────────────────────────────────────────────────────────────────

@mcp.prompt(name="caveman")
def caveman_prompt(mode: str = "full") -> str:
    """Activate caveman compression at a given intensity level."""
    return f"Active mode: **{mode}**\n\n{_CAVEMAN}"

@mcp.prompt(name="caveman-commit")
def caveman_commit_prompt() -> str:
    """Activate caveman commit message style."""
    return _COMMIT

@mcp.prompt(name="caveman-review")
def caveman_review_prompt() -> str:
    """Activate caveman code review style."""
    return _REVIEW

@mcp.prompt(name="caveman-help")
def caveman_help_prompt() -> str:
    """Display caveman quick-reference card."""
    return _HELP

# ── Sensitive-file guard ─────────────────────────────────────────────────────

_SENSITIVE_RE = re.compile(
    r"(?ix)^(\.env(\..+)?|\.netrc|credentials(\..+)?|secrets?(\..+)?|passwords?(\..+)?"
    r"|id_(rsa|dsa|ecdsa|ed25519)(\.pub)?|authorized_keys|known_hosts"
    r"|.*\.(pem|key|p12|pfx|crt|cer|jks|keystore|asc|gpg))$"
)
_SENSITIVE_DIRS = frozenset({".ssh", ".aws", ".gnupg", ".kube", ".docker"})
_SENSITIVE_TOKENS = ("secret", "credential", "password", "passwd",
                     "apikey", "accesskey", "token", "privatekey")

def _is_sensitive(p: Path) -> bool:
    if _SENSITIVE_RE.match(p.name):
        return True
    if {part.lower() for part in p.parts} & _SENSITIVE_DIRS:
        return True
    norm = re.sub(r"[_\-\s.]", "", p.name.lower())
    return any(t in norm for t in _SENSITIVE_TOKENS)

# ── Validation (inlined from skills/compress/scripts/validate.py) ────────────

_URL_RE = re.compile(r"https?://[^\s)]+")
_FENCE_RE = re.compile(r"^(?:\s{0,3})(`{3,}|~{3,})(.*)$")
_HEAD_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)

def _code_blocks(text: str) -> list[str]:
    blocks, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        m = _FENCE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        fc, fl, blk = m.group(1)[0], len(m.group(1)), [lines[i]]
        i += 1
        while i < len(lines):
            c = _FENCE_RE.match(lines[i])
            if c and c.group(1)[0] == fc and len(c.group(1)) >= fl and not c.group(2).strip():
                blk.append(lines[i])
                i += 1
                blocks.append("\n".join(blk))
                break
            blk.append(lines[i])
            i += 1
    return blocks

def _validate(orig: str, comp: str) -> list[str]:
    errors = []
    oh, ch = len(_HEAD_RE.findall(orig)), len(_HEAD_RE.findall(comp))
    if oh != ch:
        errors.append(f"Heading count: {oh} → {ch}")
    if _code_blocks(orig) != _code_blocks(comp):
        errors.append("Code blocks not preserved exactly")
    lost_urls = set(_URL_RE.findall(orig)) - set(_URL_RE.findall(comp))
    if lost_urls:
        errors.append(f"URLs lost: {lost_urls}")
    return errors

# ── Compress tools ─────────────────────────────────────────────────────────────

_COMPRESS_INSTRUCTIONS = """\
Compress this markdown into caveman format.
- Do NOT modify anything inside ``` code blocks or inline backticks
- Preserve ALL URLs exactly
- Preserve ALL headings exactly
- Preserve file paths and commands
- Return ONLY the compressed markdown — no outer fence around the whole output
Only compress natural language prose."""

_COMPRESSIBLE = {".md", ".txt", ".markdown", ".rst"}

@mcp.tool()
def compress_prepare(filepath: str) -> dict[str, Any]:
    """Read a file and return its content with compression instructions.
    No API key needed — the calling agent compresses the returned content,
    then passes it to compress_write."""
    p = Path(filepath).expanduser().resolve()
    if _is_sensitive(p):
        raise ValueError(
            f"Refusing sensitive file: {p.name}. "
            "Compression sends content to the agent context. Rename file if false positive."
        )
    if not p.exists():
        raise FileNotFoundError(f"Not found: {p}")
    if p.stat().st_size > 500_000:
        raise ValueError("File too large (max 500 KB)")
    if p.name.endswith(".original.md"):
        raise ValueError("Refusing backup file")
    if p.suffix.lower() not in _COMPRESSIBLE:
        raise ValueError(f"Not compressible: {p.suffix}. Supported: {_COMPRESSIBLE}")
    backup = p.with_name(p.stem + ".original.md")
    if backup.exists():
        raise FileExistsError(f"Backup already exists: {backup}. Remove it or call compress_restore first.")
    return {
        "filepath": str(p),
        "original_content": p.read_text(errors="ignore"),
        "instructions": _COMPRESS_INSTRUCTIONS,
    }

@mcp.tool()
def compress_write(filepath: str, compressed_content: str) -> dict[str, Any]:
    """Write compressed content to file. Creates backup on first call; overwrites on retry.
    Returns {valid, errors}. If errors persist after retries, call compress_restore."""
    p = Path(filepath).expanduser().resolve()
    backup = p.with_name(p.stem + ".original.md")
    if not backup.exists():
        orig = p.read_text(errors="ignore")
        backup.write_text(orig)
    else:
        orig = backup.read_text(errors="ignore")
    p.write_text(compressed_content)
    errors = _validate(orig, compressed_content)
    return {"valid": not errors, "errors": errors}

@mcp.tool()
def compress_restore(filepath: str) -> str:
    """Restore file from its .original.md backup and delete the backup.
    Call this if compression validation keeps failing after retries."""
    p = Path(filepath).expanduser().resolve()
    backup = p.with_name(p.stem + ".original.md")
    if not backup.exists():
        raise FileNotFoundError(f"No backup found: {backup}")
    p.write_text(backup.read_text(errors="ignore"))
    backup.unlink()
    return f"Restored {p.name} from backup."

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    mcp.run()

if __name__ == "__main__":
    main()
