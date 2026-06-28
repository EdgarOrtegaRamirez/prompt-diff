"""CLI interface for prompt-diff."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from prompt_diff.__init__ import __version__
from prompt_diff.engine import (
    PromptRegistry,
    PromptVersion,
    compute_diff,
)

console = Console()


def _validate_path(ctx, param, value):
    """Validate that a file path exists."""
    if value:
        p = Path(value)
        if not p.exists():
            raise click.BadParameter(f"File not found: {value}")
    return value


@click.group()
@click.version_option(version=__version__, prog_name="prompt-diff")
def main():
    """Prompt Diff - Version, diff, and evaluate AI prompts."""
    pass


@main.command()
@click.argument("registry_path", callback=_validate_path)
@click.argument("version_id")
def show(registry_path, version_id):
    """Show a specific prompt version."""
    registry = PromptRegistry.load(registry_path)
    version = registry.get_version(version_id)
    if not version:
        console.print(f"[red]Version '{version_id}' not found in '{registry_path}'[/red]")
        sys.exit(1)

    console.print(f"[bold]Name:[/bold] {version.name}")
    console.print(f"[bold]ID:[/bold] {version.id}")
    console.print(f"[bold]Created:[/bold] {version.created_at}")
    console.print(f"[bold]Hash:[/bold] {version.content_hash()}")
    if version.tags:
        console.print(f"[bold]Tags:[/bold] {', '.join(version.tags)}")
    console.print(f"[bold]Metadata:[/bold] {json.dumps(version.metadata, indent=2)}")
    console.print()
    console.print(version.content)


@main.command()
@click.argument("registry_path", callback=_validate_path)
@click.argument("version1")
@click.argument("version2")
@click.option("--format", "fmt", default="unified", type=click.Choice(["unified", "stats", "json"]),
              help="Output format for diff")
def diff(registry_path, version1, version2, fmt):
    """Diff two prompt versions."""
    registry = PromptRegistry.load(registry_path)

    v1 = registry.get_version(version1)
    v2 = registry.get_version(version2)

    if not v1:
        console.print(f"[red]Version '{version1}' not found[/red]")
        sys.exit(1)
    if not v2:
        console.print(f"[red]Version '{version2}' not found[/red]")
        sys.exit(1)

    result = compute_diff(v1.content, v2.content, v1.id, v2.id)

    if fmt == "unified":
        console.print(result.format_unified())
    elif fmt == "stats":
        console.print(result.format_stats())
    elif fmt == "json":
        console.print(result.format_json())


@main.command()
@click.argument("registry_path", callback=_validate_path)
def list_versions(registry_path):
    """List all versions in a prompt registry."""
    registry = PromptRegistry.load(registry_path)

    table = Table(title=f"Prompt Versions: {registry.name}")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Created", style="white")
    table.add_column("Hash", style="magenta")
    table.add_column("Tags", style="yellow")

    for v in registry.versions:
        table.add_row(
            v.id,
            v.name,
            v.created_at[:19],
            v.content_hash(),
            ", ".join(v.tags) or "-",
        )

    console.print(table)


@main.command()
@click.argument("registry_path", callback=_validate_path)
@click.option("--search", "-s", help="Search versions by name or tag")
@click.option("--tag", "-t", help="Filter by tag")
def search(registry_path, search, tag):
    """Search prompt versions."""
    registry = PromptRegistry.load(registry_path)

    results = registry.versions

    if tag:
        results = registry.get_versions_by_tag(tag)

    if search:
        results = [
            v for v in results
            if search.lower() in v.name.lower()
            or any(search.lower() in t.lower() for t in v.tags)
        ]

    if not results:
        console.print("[yellow]No matching versions found[/yellow]")
        return

    for v in results:
        console.print(f"  [cyan]{v.id}[/cyan]  [green]{v.name}[/green]  "
                       f"[white]{v.created_at[:19]}[/white]  [{', '.join(v.tags)}]")


@main.command()
@click.option("--name", "-n", required=True, help="Name for the prompt version")
@click.option("--content", "-c", help="Prompt content (or pipe from stdin)")
@click.option("--file", "-f", type=click.Path(exists=True), help="File containing prompt content")
@click.option("--tag", "-t", multiple=True, help="Tags for the version (repeatable)")
@click.option("--metadata", "-m", help="JSON metadata (key=value pairs)")
@click.option("--output", "-o", required=True, help="Output registry file path")
def create(name, content, file, tag, metadata, output):
    """Create a new prompt version in a registry."""
    if content:
        prompt_content = content
    elif file:
        prompt_content = Path(file).read_text()
    else:
        prompt_content = click.get_text_stream("stdin").read()

    meta = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError:
            # Try key=value format
            for pair in metadata.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    meta[k.strip()] = v.strip()

    # Load existing registry or create new one
    output_path = Path(output)
    if output_path.exists():
        registry = PromptRegistry.load(output)
    else:
        registry = PromptRegistry(name=name)

    version = PromptVersion(
        id=f"v{len(registry.versions) + 1:03d}" if registry.versions else "v001",
        name=name,
        content=prompt_content,
        metadata=meta,
        tags=list(tag),
    )

    registry.add_version(version)
    registry.save(output)
    console.print(f"[green]Created version '{version.id}' ({name})[/green]")
    console.print(f"  Hash: {version.content_hash()}")
    console.print(f"  Saved to: {output}")


@main.command()
@click.argument("registry_path", callback=_validate_path)
def info(registry_path):
    """Show registry information."""
    registry = PromptRegistry.load(registry_path)

    table = Table(title=f"Registry: {registry.name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total versions", str(len(registry.versions)))
    if registry.versions:
        latest = registry.get_latest()
        table.add_row("Latest version", latest.id)
        table.add_row("Latest created", latest.created_at[:19])

        all_tags = set()
        for v in registry.versions:
            all_tags.update(v.tags)
        table.add_row("Tags", ", ".join(sorted(all_tags)) if all_tags else "none")

        total_content = sum(len(v.content) for v in registry.versions)
        table.add_row("Total content chars", f"{total_content:,}")

    console.print(table)


@main.command()
@click.option("--config", "-c", help="Path to sample config file")
def sample_config(config):
    """Print a sample registry configuration."""
    sample = {
        "name": "my-prompts",
        "versions": [
            {
                "id": "v001",
                "name": "Initial prompt",
                "content": "You are a helpful assistant.",
                "metadata": {"author": "alice", "model": "gpt-4"},
                "tags": ["initial", "assistant"],
                "created_at": "2026-01-01T00:00:00+00:00",
            },
            {
                "id": "v002",
                "name": "Enhanced with examples",
                "content": "You are a helpful assistant.\\n\\nExamples:\\n- Q: What is AI?\\n- A: Artificial Intelligence...",
                "metadata": {"author": "alice", "model": "gpt-4", "temperature": 0.7},
                "tags": ["enhanced", "with-examples"],
                "created_at": "2026-01-15T00:00:00+00:00",
            },
        ],
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    click.echo(json.dumps(sample, indent=2))


if __name__ == "__main__":
    main()
