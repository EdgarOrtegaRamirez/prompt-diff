"""Integration tests for prompt-diff CLI."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from prompt_diff.engine import PromptRegistry, PromptVersion


class TestCLIIntegration:
    """End-to-end CLI tests."""

    def _create_empty_registry(self):
        """Create a temporary empty registry file."""
        f = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        f.write("{}")
        f.close()
        return f.name

    def test_create_version(self):
        """Test creating a prompt version via CLI."""
        reg_path = self._create_empty_registry()

        try:
            result = subprocess.run(
                [
                    "python", "-m", "prompt_diff", "create",
                    "--name", "test prompt",
                    "--content", "You are a helpful assistant.",
                    "--tag", "test",
                    "--output", reg_path,
                ],
                capture_output=True,
                text=True,
                cwd="/root/workspace/prompt-diff",
            )
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert "Created version" in result.stdout

            # Verify registry was created
            reg = PromptRegistry.load(reg_path)
            assert len(reg.versions) == 1
            assert reg.versions[0].name == "test prompt"
            assert reg.versions[0].content == "You are a helpful assistant."
        finally:
            Path(reg_path).unlink(missing_ok=True)

    def test_show_version(self):
        """Test showing a prompt version."""
        reg_path = self._create_empty_registry()

        try:
            # Create first
            subprocess.run(
                [
                    "python", "-m", "prompt_diff", "create",
                    "--name", "test",
                    "--content", "hello world",
                    "--output", reg_path,
                ],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )

            # Show it
            result = subprocess.run(
                ["python", "-m", "prompt_diff", "show", reg_path, "v001"],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert "hello world" in result.stdout
        finally:
            Path(reg_path).unlink(missing_ok=True)

    def test_list_versions(self):
        """Test listing prompt versions."""
        reg_path = self._create_empty_registry()

        try:
            # Create two versions
            subprocess.run(
                ["python", "-m", "prompt_diff", "create",
                 "--name", "first", "--content", "a",
                 "--output", reg_path],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )
            subprocess.run(
                ["python", "-m", "prompt_diff", "create",
                 "--name", "second", "--content", "b",
                 "--output", reg_path],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )

            result = subprocess.run(
                ["python", "-m", "prompt_diff", "list-versions", reg_path],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert "v001" in result.stdout
            assert "v002" in result.stdout
        finally:
            Path(reg_path).unlink(missing_ok=True)

    def test_diff_command(self):
        """Test diffing two versions."""
        reg_path = self._create_empty_registry()

        try:
            subprocess.run(
                ["python", "-m", "prompt_diff", "create",
                 "--name", "v1", "--content", "hello\nworld",
                 "--output", reg_path],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )
            subprocess.run(
                ["python", "-m", "prompt_diff", "create",
                 "--name", "v2", "--content", "hello\nearth",
                 "--output", reg_path],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )

            result = subprocess.run(
                ["python", "-m", "prompt_diff", "diff", reg_path, "v001", "v002", "--format", "stats"],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert "v001" in result.stdout or "v002" in result.stdout
        finally:
            Path(reg_path).unlink(missing_ok=True)

    def test_info_command(self):
        """Test showing registry info."""
        reg_path = self._create_empty_registry()

        try:
            subprocess.run(
                ["python", "-m", "prompt_diff", "create",
                 "--name", "test", "--content", "hello",
                 "--tag", "prod",
                 "--output", reg_path],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )

            result = subprocess.run(
                ["python", "-m", "prompt_diff", "info", reg_path],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert "test" in result.stdout.lower()
        finally:
            Path(reg_path).unlink(missing_ok=True)

    def test_version_flag(self):
        """Test --version flag."""
        result = subprocess.run(
            ["python", "-m", "prompt_diff", "--version"],
            capture_output=True, text=True,
            cwd="/root/workspace/prompt-diff",
        )
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_sample_config(self):
        """Test sample-config command."""
        result = subprocess.run(
            ["python", "-m", "prompt_diff", "sample-config"],
            capture_output=True, text=True,
            cwd="/root/workspace/prompt-diff",
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        data = json.loads(result.stdout)
        assert "versions" in data
        assert len(data["versions"]) == 2

    def test_search_by_tag(self):
        """Test searching by tag."""
        reg_path = self._create_empty_registry()

        try:
            subprocess.run(
                ["python", "-m", "prompt_diff", "create",
                 "--name", "prod prompt", "--content", "a",
                 "--tag", "prod",
                 "--output", reg_path],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )
            subprocess.run(
                ["python", "-m", "prompt_diff", "create",
                 "--name", "dev prompt", "--content", "b",
                 "--tag", "dev",
                 "--output", reg_path],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )

            result = subprocess.run(
                ["python", "-m", "prompt_diff", "search", reg_path, "--tag", "prod"],
                capture_output=True, text=True,
                cwd="/root/workspace/prompt-diff",
            )
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert "prod prompt" in result.stdout
        finally:
            Path(reg_path).unlink(missing_ok=True)
