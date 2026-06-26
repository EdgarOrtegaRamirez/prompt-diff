"""Prompt model and diff engine for AI prompt versioning."""

from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class DiffFormat(str, Enum):
    """Output format for diff results."""
    UNIFIED = "unified"
    CONTEXT = "context"
    STATS = "stats"
    JSON = "json"


@dataclass
class PromptVersion:
    """Represents a single version of a prompt."""
    id: str
    name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptVersion:
        return cls(**data)

    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]


@dataclass
class DiffResult:
    """Result of comparing two prompt versions."""
    base: str
    target: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    modified: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def format_unified(self) -> str:
        """Format as unified diff."""
        base_lines = self.base.splitlines()
        target_lines = self.target.splitlines()
        return "\n".join(
            difflib.unified_diff(
                base_lines, target_lines,
                fromfile=f"v{self.base}",
                tofile=f"v{self.target}",
            )
        )

    def format_stats(self) -> str:
        """Format as statistics summary."""
        stats = self.stats
        lines = [
            f"Prompt Diff: {self.base} -> {self.target}",
            f"  Lines added:    {stats.get('added', 0)}",
            f"  Lines removed:  {stats.get('removed', 0)}",
            f"  Lines changed:  {stats.get('changed', 0)}",
            f"  Lines unchanged: {stats.get('unchanged', 0)}",
        ]
        return "\n".join(lines)

    def format_json(self) -> str:
        """Format as JSON."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class PromptRegistry:
    """Registry of prompt versions with versioning support."""
    name: str
    versions: list[PromptVersion] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_version(self, version: PromptVersion) -> None:
        self.versions.append(version)
        self.versions.sort(key=lambda v: v.created_at)

    def get_version(self, version_id: str) -> PromptVersion | None:
        for v in self.versions:
            if v.id == version_id:
                return v
        return None

    def get_latest(self) -> PromptVersion | None:
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.created_at)

    def get_versions_by_tag(self, tag: str) -> list[PromptVersion]:
        return [v for v in self.versions if tag in v.tags]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "versions": [v.to_dict() for v in self.versions],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptRegistry:
        versions = [PromptVersion.from_dict(v) for v in data.get("versions", [])]
        return cls(name=data.get("name", ""), versions=versions, created_at=data.get("created_at", ""))

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: str | Path) -> PromptRegistry:
        path = Path(path)
        text = path.read_text().strip()
        if not text:
            return cls(name="")
        data = json.loads(text)
        return cls.from_dict(data)


def compute_diff(
    base_content: str,
    target_content: str,
    base_name: str = "base",
    target_name: str = "target",
) -> DiffResult:
    """Compute a diff between two prompt versions."""
    base_lines = base_content.splitlines()
    target_lines = target_content.splitlines()

    added = []
    removed = []
    modified = []
    stats = {"added": 0, "removed": 0, "changed": 0, "unchanged": 0}

    matcher = difflib.SequenceMatcher(None, base_lines, target_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            stats["unchanged"] += 1
        elif tag == "replace":
            stats["changed"] += 1
            base_slice = base_lines[i1:i2]
            target_slice = target_lines[j1:j2]
            stats["removed"] += len(base_slice)
            stats["added"] += len(target_slice)
            removed.extend(base_slice)
            added.extend(target_slice)
            # Pair up modified lines
            max_len = max(len(base_slice), len(target_slice))
            for k in range(max_len):
                modified.append({
                    "base": base_slice[k] if k < len(base_slice) else "",
                    "target": target_slice[k] if k < len(target_slice) else "",
                })
        elif tag == "insert":
            stats["added"] += 1
            added.extend(target_lines[j1:j2])
        elif tag == "delete":
            stats["removed"] += 1
            removed.extend(base_lines[i1:i2])

    return DiffResult(
        base=base_name,
        target=target_name,
        added=added,
        removed=removed,
        modified=modified,
        stats=stats,
    )
