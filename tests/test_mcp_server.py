"""Tests for caveman_mcp.server — no API key, no MCP transport needed."""
import pytest
from pathlib import Path

from caveman_mcp.server import (
    caveman_prompt,
    caveman_commit_prompt,
    caveman_review_prompt,
    caveman_help_prompt,
    compress_prepare,
    compress_write,
    compress_restore,
    _is_sensitive,
)

# ── Prompts ───────────────────────────────────────────────────────────────────

def test_all_prompts_return_text():
    assert len(caveman_prompt()) > 100
    assert len(caveman_commit_prompt()) > 100
    assert len(caveman_review_prompt()) > 100
    assert len(caveman_help_prompt()) > 50

def test_caveman_mode_injected():
    assert "ultra" in caveman_prompt("ultra")
    assert "wenyan-full" in caveman_prompt("wenyan-full")
    assert "lite" in caveman_prompt("lite")

# ── Sensitive-file guard ─────────────────────────────────────────────────────

@pytest.mark.parametrize("path", [
    "/home/user/.ssh/id_rsa",
    "/home/user/.aws/credentials",
    "/tmp/secrets.md",
    "/tmp/passwords.txt",
    "/tmp/cert.pem",
    "/tmp/.env.local",
])
def test_sensitive_paths_refused(path):
    assert _is_sensitive(Path(path)), f"Expected {path} to be flagged sensitive"

def test_compress_prepare_refuses_sensitive(tmp_path):
    f = tmp_path / "secrets.md"
    f.write_text("top secret stuff")
    with pytest.raises(ValueError, match="Refusing sensitive"):
        compress_prepare(str(f))

# ── compress_prepare ─────────────────────────────────────────────────────────

def test_compress_prepare_returns_content(tmp_path):
    f = tmp_path / "notes.md"
    content = "# Hello\n\nThis is a test document with some natural language content."
    f.write_text(content)
    result = compress_prepare(str(f))
    assert result["original_content"] == content
    assert "instructions" in result
    assert result["filepath"] == str(f.resolve())

def test_compress_prepare_refuses_backup(tmp_path):
    f = tmp_path / "notes.original.md"
    f.write_text("backup")
    with pytest.raises(ValueError, match="backup"):
        compress_prepare(str(f))

def test_compress_prepare_refuses_non_compressible(tmp_path):
    f = tmp_path / "script.py"
    f.write_text("print('hello')")
    with pytest.raises(ValueError, match="Not compressible"):
        compress_prepare(str(f))

def test_compress_prepare_refuses_existing_backup(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("content")
    backup = tmp_path / "notes.original.md"
    backup.write_text("old backup")
    with pytest.raises(FileExistsError, match="Backup already exists"):
        compress_prepare(str(f))

# ── compress_write ────────────────────────────────────────────────────────────

def test_compress_write_creates_backup(tmp_path):
    f = tmp_path / "doc.md"
    orig = "# Title\n\nThis is original content."
    f.write_text(orig)
    compress_write(str(f), "# Title\n\nOriginal content.")
    backup = tmp_path / "doc.original.md"
    assert backup.exists()
    assert backup.read_text() == orig

def test_compress_write_validates_urls(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nSee https://example.com for details.")
    result = compress_write(str(f), "# Title\n\nSee details.")  # URL dropped
    assert not result["valid"]
    assert any("URL" in e for e in result["errors"])

def test_compress_write_validates_code_blocks(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\n```python\nprint('hello')\n```")
    result = compress_write(str(f), "# Title\n\nCode removed.")  # block dropped
    assert not result["valid"]
    assert any("Code" in e for e in result["errors"])

def test_compress_write_valid(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nThis is a long sentence that describes something in detail.")
    result = compress_write(str(f), "# Title\n\nLong sentence describe something.")
    assert result["valid"]
    assert result["errors"] == []

def test_compress_write_retry_uses_backup_as_orig(tmp_path):
    f = tmp_path / "doc.md"
    orig = "# Title\n\nOriginal content."
    f.write_text(orig)
    # First write (creates backup)
    compress_write(str(f), "# Title\n\nFirst attempt.")
    # Second write (retry) — backup still holds original
    compress_write(str(f), "# Title\n\nSecond attempt.")
    assert (tmp_path / "doc.original.md").read_text() == orig

# ── compress_restore ──────────────────────────────────────────────────────────

def test_compress_restore(tmp_path):
    f = tmp_path / "doc.md"
    orig = "# Title\n\nOriginal content."
    f.write_text(orig)
    compress_write(str(f), "# Title\n\nCompressed.")
    compress_restore(str(f))
    assert f.read_text() == orig
    assert not (tmp_path / "doc.original.md").exists()

def test_compress_restore_no_backup(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("content")
    with pytest.raises(FileNotFoundError, match="No backup"):
        compress_restore(str(f))
