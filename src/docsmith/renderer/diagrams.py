"""Build-managed diagram rendering helpers."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from docsmith.config import DiagramConfig, DocsmithConfig
from docsmith.core.paths import resolve_document_path


class DiagramRenderError(RuntimeError):
    """Raised when diagram rendering fails."""


@dataclass(frozen=True)
class RenderedDiagram:
    """A generated diagram asset produced during build."""

    diagram_id: str
    source_path: Path
    output_path: Path


def diagram_renderer_code_path() -> Path:
    """Return the engine-owned Mermaid renderer helper path."""
    return Path(__file__).resolve()


def build_managed_diagram_output_path(build_dir: Path, declared_output: str | Path) -> Path:
    """Map a declared output path to its build-managed location."""
    output_relative = Path(declared_output)
    if output_relative.is_absolute():
        raise DiagramRenderError(
            f"Diagram output path must be relative to the document build directory: {declared_output}"
        )

    build_root = build_dir.resolve()
    output_path = (build_root / output_relative).resolve()
    if not output_path.is_relative_to(build_root):
        raise DiagramRenderError(
            f"Diagram output path must stay within the document build directory: {declared_output}"
        )

    return output_path


def _render_mermaid_diagram(
    document_root: Path,
    build_dir: Path,
    diagram: DiagramConfig,
) -> RenderedDiagram:
    """Render one Mermaid diagram declaration with Mermaid CLI."""
    mmdc_path = shutil.which("mmdc")
    if mmdc_path is None:
        raise DiagramRenderError(
            "Mermaid diagrams are declared, but `mmdc` is not available on PATH. "
            "Install Mermaid CLI to build documents with declared Mermaid diagrams."
        )

    source_path = resolve_document_path(diagram.source, document_root)
    output_path = build_managed_diagram_output_path(build_dir, diagram.output)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DiagramRenderError(
            f"Could not create the build-managed diagram output directory: {output_path.parent}"
        ) from exc

    command = [
        mmdc_path,
        "-i",
        str(source_path),
        "-o",
        str(output_path),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        details: list[str] = [f"Mermaid rendering failed for diagram `{diagram.id}`."]
        if exc.stderr and exc.stderr.strip():
            details.append(f"stderr: {exc.stderr.strip()}")
        if exc.stdout and exc.stdout.strip():
            details.append(f"stdout: {exc.stdout.strip()}")
        raise DiagramRenderError(" ".join(details)) from exc
    except FileNotFoundError as exc:
        raise DiagramRenderError(
            "Could not start Mermaid CLI (`mmdc`). Install Mermaid CLI and ensure it is on PATH."
        ) from exc

    return RenderedDiagram(
        diagram_id=diagram.id,
        source_path=source_path,
        output_path=output_path,
    )


def render_declared_diagrams(
    document_root: Path,
    build_dir: Path,
    config: DocsmithConfig,
) -> list[RenderedDiagram]:
    """Render all declared diagrams into the build directory."""
    rendered: list[RenderedDiagram] = []

    for diagram in config.diagrams:
        if diagram.type != "mermaid":
            raise DiagramRenderError(f"Unsupported declared diagram type during build: {diagram.type}")
        if diagram.format != "png":
            raise DiagramRenderError(
                f"Unsupported declared Mermaid output format during build: {diagram.format}"
            )
        rendered.append(_render_mermaid_diagram(document_root, build_dir, diagram))

    return rendered
