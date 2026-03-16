"""CLI entrypoint for Docsmith."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from docsmith.core.builder import build_document
from docsmith.core.validation import format_validation_report, validate_document
from docsmith.templates.registry import list_templates

app = typer.Typer(help="Build structured Markdown documents into PDF and DOCX.")


@app.command()
def build(
    document_path: Path,
    bump: Annotated[
        str | None,
        typer.Option(help="Force a semantic version bump: patch, minor, or major."),
    ] = None,
    no_bump: Annotated[
        bool,
        typer.Option(help="Disable automatic semantic version bumping for this build."),
    ] = False,
) -> None:
    """Build a document directory and print the final output path."""
    if bump is not None and bump not in {"patch", "minor", "major"}:
        raise typer.BadParameter("Bump must be one of: patch, minor, major.")

    result = build_document(document_path, bump=bump, no_bump=no_bump)
    version_info = result.version_info

    if version_info.fingerprint_changed:
        typer.echo("Detected content changes since last build.")
    else:
        typer.echo("No content changes detected since last build.")

    if version_info.bump_applied:
        previous = version_info.previous_version or result.version_info.semantic_version
        typer.echo(f"Version bumped: {previous} -> {version_info.semantic_version}")
    else:
        typer.echo(f"Version kept: {version_info.semantic_version}")

    if version_info.git_hash:
        typer.echo(f"Git hash: {version_info.git_hash}")

    typer.echo(f"Built: {result.output_path}")


@app.command()
def validate(document_path: Path) -> None:
    """Validate document configuration without running a build."""
    report = validate_document(document_path)
    typer.echo(format_validation_report(report))
    if not report.ok:
        raise typer.Exit(code=1)


@app.command()
def templates() -> None:
    """List template directories under the current working tree."""
    for template_name in list_templates(Path.cwd()):
        typer.echo(template_name)


if __name__ == "__main__":
    app()
