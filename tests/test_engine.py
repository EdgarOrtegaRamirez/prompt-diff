"""Tests for prompt-diff engine module."""

import json
import tempfile
from pathlib import Path


from prompt_diff.engine import (
    PromptVersion,
    DiffResult,
    PromptRegistry,
    compute_diff,
)


class TestPromptVersion:
    """Tests for PromptVersion dataclass."""

    def test_create_version(self):
        v = PromptVersion(id="v001", name="test", content="hello")
        assert v.id == "v001"
        assert v.name == "test"
        assert v.content == "hello"
        assert v.content_hash() is not None
        assert len(v.content_hash()) == 16

    def test_to_dict(self):
        v = PromptVersion(id="v001", name="test", content="hello", tags=["a", "b"])
        d = v.to_dict()
        assert d["id"] == "v001"
        assert d["tags"] == ["a", "b"]

    def test_from_dict(self):
        data = {
            "id": "v001",
            "name": "test",
            "content": "hello",
            "metadata": {"author": "alice"},
            "tags": ["test"],
        }
        v = PromptVersion.from_dict(data)
        assert v.id == "v001"
        assert v.metadata["author"] == "alice"

    def test_content_hash_deterministic(self):
        v1 = PromptVersion(id="v001", name="test", content="same")
        v2 = PromptVersion(id="v002", name="other", content="same")
        assert v1.content_hash() == v2.content_hash()

    def test_content_hash_different(self):
        v1 = PromptVersion(id="v001", name="test", content="hello")
        v2 = PromptVersion(id="v002", name="other", content="world")
        assert v1.content_hash() != v2.content_hash()


class TestDiffResult:
    """Tests for DiffResult formatting."""

    def test_format_stats(self):
        result = DiffResult(
            base="v1", target="v2",
            added=["line2"],
            removed=["line1"],
            stats={"added": 1, "removed": 1, "changed": 0, "unchanged": 5},
        )
        output = result.format_stats()
        assert "v1 -> v2" in output
        assert "Lines added:    1" in output
        assert "Lines removed:  1" in output

    def test_format_json(self):
        result = DiffResult(base="v1", target="v2", added=["a"], removed=["b"])
        data = json.loads(result.format_json())
        assert data["base"] == "v1"
        assert data["target"] == "v2"
        assert data["added"] == ["a"]

    def test_format_unified(self):
        result = DiffResult(
            base="v1", target="v2",
            added=["new line"],
            removed=["old line"],
        )
        output = result.format_unified()
        assert "+" in output
        assert "-" in output

    def test_to_dict(self):
        result = DiffResult(base="v1", target="v2", added=["a"])
        d = result.to_dict()
        assert d["base"] == "v1"
        assert d["added"] == ["a"]


class TestPromptRegistry:
    """Tests for PromptRegistry."""

    def test_add_and_get_version(self):
        reg = PromptRegistry(name="test")
        v = PromptVersion(id="v001", name="test", content="hello")
        reg.add_version(v)
        assert len(reg.versions) == 1
        assert reg.get_version("v001") is v

    def test_get_nonexistent_version(self):
        reg = PromptRegistry(name="test")
        assert reg.get_version("v999") is None

    def test_get_latest(self):
        reg = PromptRegistry(name="test")
        v1 = PromptVersion(id="v001", name="first", content="a")
        v2 = PromptVersion(id="v002", name="second", content="b")
        reg.add_version(v1)
        reg.add_version(v2)
        assert reg.get_latest() == v2

    def test_get_versions_by_tag(self):
        reg = PromptRegistry(name="test")
        v1 = PromptVersion(id="v001", name="a", content="x", tags=["prod"])
        v2 = PromptVersion(id="v002", name="b", content="y", tags=["dev"])
        v3 = PromptVersion(id="v003", name="c", content="z", tags=["prod"])
        reg.add_version(v1)
        reg.add_version(v2)
        reg.add_version(v3)
        prod = reg.get_versions_by_tag("prod")
        assert len(prod) == 2
        assert all("prod" in v.tags for v in prod)

    def test_empty_latest(self):
        reg = PromptRegistry(name="test")
        assert reg.get_latest() is None

    def test_save_and_load(self):
        reg = PromptRegistry(name="test")
        v = PromptVersion(id="v001", name="test", content="hello", tags=["a"])
        reg.add_version(v)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            reg.save(path)
            loaded = PromptRegistry.load(path)
            assert loaded.name == "test"
            assert len(loaded.versions) == 1
            assert loaded.versions[0].id == "v001"
            assert loaded.versions[0].content == "hello"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_to_dict(self):
        reg = PromptRegistry(name="test")
        v = PromptVersion(id="v001", name="test", content="hello")
        reg.add_version(v)
        d = reg.to_dict()
        assert d["name"] == "test"
        assert len(d["versions"]) == 1

    def test_from_dict(self):
        data = {
            "name": "test",
            "versions": [
                {"id": "v001", "name": "test", "content": "hello", "tags": []}
            ],
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        reg = PromptRegistry.from_dict(data)
        assert reg.name == "test"
        assert len(reg.versions) == 1


class TestComputeDiff:
    """Tests for compute_diff function."""

    def test_identical_content(self):
        result = compute_diff("hello world", "hello world", "v1", "v2")
        assert result.stats["added"] == 0
        assert result.stats["removed"] == 0
        assert result.stats["unchanged"] == 1

    def test_completely_different(self):
        result = compute_diff("line1\nline2", "line3\nline4\nline5", "v1", "v2")
        assert result.stats["added"] > 0
        assert result.stats["removed"] > 0

    def test_single_line_addition(self):
        result = compute_diff("hello", "hello\nworld", "v1", "v2")
        assert result.stats["added"] > 0

    def test_single_line_removal(self):
        result = compute_diff("hello\nworld", "hello", "v1", "v2")
        assert result.stats["removed"] > 0

    def test_diff_result_has_stats(self):
        result = compute_diff("a\nb\nc", "a\nx\nc", "v1", "v2")
        assert "changed" in result.stats
        assert "unchanged" in result.stats

    def test_diff_modified_lines(self):
        result = compute_diff("hello\nworld", "hello\nearth", "v1", "v2")
        assert len(result.modified) > 0
