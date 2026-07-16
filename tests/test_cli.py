"""Integration tests for prompt-diff CLI."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from prompt_diff.cli import main
from prompt_diff.engine import PromptRegistry


class TestCLIIntegration:
    """End-to-end CLI tests using Click's CliRunner."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def _create_empty_registry(self):
        """Create a temporary empty registry file."""
        f = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        f.write("{}")
        f.close()
        return f.name

    def test_create_version(self, runner):
        """Test creating a prompt version via CLI."""
        reg_path = self._create_empty_registry()

        try:
            result = runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    "test prompt",
                    "--content",
                    "You are a helpful assistant.",
                    "--tag",
                    "test",
                    "--output",
                    reg_path,
                ],
            )
            assert result.exit_code == 0, f"CLI failed: {result.output}"
            assert "Created version" in result.output

            # Verify registry was created
            reg = PromptRegistry.load(reg_path)
            assert len(reg.versions) == 1
            assert reg.versions[0].name == "test prompt"
            assert reg.versions[0].content == "You are a helpful assistant."
        finally:
            Path(reg_path).unlink(missing_ok=True)

    def test_show_version(self, runner):
        """Test showing a prompt version."""
        reg_path = self._create_empty_registry()

        try:
            # Create first
            runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    "test",
                    "--content",
                    "hello world",
                    "--output",
                    reg_path,
                ],
            )

            # Show it
            result = runner.invoke(main, ["show", reg_path, "v001"])
            assert result.exit_code == 0, f"CLI failed: {result.output}"
            assert "hello world" in result.output
        finally:
            Path(reg_path).unlink(missing_ok=True)

    def test_list_versions(self, runner):
        """Test listing prompt versions."""
        reg_path = self._create_empty_registry()

        try:
            # Create two versions
            runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    "first",
                    "--content",
                    "a",
                    "--output",
                    reg_path,
                ],
            )
            runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    "second",
                    "--content",
                    "b",
                    "--output",
                    reg_path,
                ],
            )

            result = runner.invoke(main, ["list-versions", reg_path])
            assert result.exit_code == 0, f"CLI failed: {result.output}"
            assert "v001" in result.output
            assert "v002" in result.output
        finally:
            Path(reg_path).unlink(missing_ok=True)

    def test_diff_command(self, runner):
        """Test diffing two versions."""
        reg_path = self._create_empty_registry()

        try:
            runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    "v1",
                    "--content",
                    "hello\nworld",
                    "--output",
                    reg_path,
                ],
            )
            runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    "v2",
                    "--content",
                    "hello\nearth",
                    "--output",
                    reg_path,
                ],
            )

            result = runner.invoke(
                main,
                [
                    "diff",
                    reg_path,
                    "v001",
                    "v002",
                    "--format",
                    "stats",
                ],
            )
            assert result.exit_code == 0, f"CLI failed: {result.output}"
            assert "v001" in result.output or "v002" in result.output
        finally:
            Path(reg_path).unlink(missing_ok=True)

    def test_info_command(self, runner):
        """Test showing registry info."""
        reg_path = self._create_empty_registry()

        try:
            runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    "test",
                    "--content",
                    "hello",
                    "--tag",
                    "prod",
                    "--output",
                    reg_path,
                ],
            )

            result = runner.invoke(main, ["info", reg_path])
            assert result.exit_code == 0, f"CLI failed: {result.output}"
            assert "test" in result.output.lower()
        finally:
            Path(reg_path).unlink(missing_ok=True)

    def test_version_flag(self, runner):
        """Test --version flag."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_sample_config(self, runner):
        """Test sample-config command."""
        result = runner.invoke(main, ["sample-config"])
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        data = json.loads(result.output)
        assert "versions" in data
        assert len(data["versions"]) == 2

    def test_search_by_tag(self, runner):
        """Test searching by tag."""
        reg_path = self._create_empty_registry()

        try:
            runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    "prod prompt",
                    "--content",
                    "a",
                    "--tag",
                    "prod",
                    "--output",
                    reg_path,
                ],
            )
            runner.invoke(
                main,
                [
                    "create",
                    "--name",
                    "dev prompt",
                    "--content",
                    "b",
                    "--tag",
                    "dev",
                    "--output",
                    reg_path,
                ],
            )

            result = runner.invoke(main, ["search", reg_path, "--tag", "prod"])
            assert result.exit_code == 0, f"CLI failed: {result.output}"
            assert "prod prompt" in result.output
        finally:
            Path(reg_path).unlink(missing_ok=True)
