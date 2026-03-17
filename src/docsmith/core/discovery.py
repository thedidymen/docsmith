"""Markdown source discovery for Docsmith documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docsmith.config import DocsmithConfig, load_document_config
from docsmith.core.paths import resolve_document_path

ZONE_NAMES = ("front_matter", "main_matter", "back_matter", "appendices")


@dataclass(frozen=True)
class ResolvedDocumentZone:
    """Resolved Markdown files for a logical document zone."""

    name: str
    files: tuple[Path, ...]


@dataclass(frozen=True)
class ResolvedDocumentStructure:
    """Resolved ordered document structure used by the build pipeline."""

    zones: tuple[ResolvedDocumentZone, ...]
    bibliography: "ResolvedBibliographyPlacement | None" = None
    toc: "ResolvedTocPlacement | None" = None

    @property
    def files(self) -> list[Path]:
        """Return all zone files as a single ordered list."""
        return [path for zone in self.zones for path in zone.files]


@dataclass(frozen=True)
class ResolvedBibliographyPlacement:
    """Resolved bibliography placement in the document structure."""

    title: str
    zone: str


@dataclass(frozen=True)
class ResolvedTocPlacement:
    """Resolved table-of-contents placement in the document structure."""

    title: str
    zone: str


def _validate_markdown_file(path: Path) -> Path:
    """Validate that a discovered input exists and is a Markdown file."""
    if not path.exists():
        raise FileNotFoundError(f"Markdown source not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Markdown source is not a file: {path}")
    if path.suffix.lower() != ".md":
        raise ValueError(f"Markdown source must use a .md extension: {path}")
    return path


def _resolve_explicit_paths(
    input_root: Path,
    relative_paths: list[str],
    *,
    label: str,
) -> tuple[Path, ...]:
    files = [
        _validate_markdown_file(resolve_document_path(relative_path, input_root))
        for relative_path in relative_paths
    ]
    seen_relative_paths: set[str] = set()
    for path in files:
        relative_path = path.relative_to(input_root).as_posix()
        if relative_path in seen_relative_paths:
            raise ValueError(f"Duplicate markdown source in {label}: {relative_path}")
        seen_relative_paths.add(relative_path)
    return tuple(files)


def _resolve_zone_structure(
    input_root: Path,
    config: DocsmithConfig,
) -> ResolvedDocumentStructure:
    zones: list[ResolvedDocumentZone] = []
    seen_relative_paths: set[str] = set()

    for zone_name in ZONE_NAMES:
        relative_paths = getattr(config.document, zone_name)
        files = _resolve_explicit_paths(input_root, relative_paths, label=zone_name)
        for path in files:
            relative_path = path.relative_to(input_root).as_posix()
            if relative_path in seen_relative_paths:
                raise ValueError(f"Duplicate markdown source across document zones: {relative_path}")
            seen_relative_paths.add(relative_path)
        zones.append(ResolvedDocumentZone(name=zone_name, files=files))

    if not seen_relative_paths:
        raise FileNotFoundError("No Markdown files configured in document zones")

    bibliography = None
    if config.document.bibliography.enabled:
        bibliography = ResolvedBibliographyPlacement(
            title=config.document.bibliography.title,
            zone=config.document.bibliography.zone,
        )
    toc = None
    if config.document.toc.enabled:
        toc = ResolvedTocPlacement(
            title=config.document.toc.title,
            zone=config.document.toc.zone,
        )

    return ResolvedDocumentStructure(
        zones=tuple(zones),
        bibliography=bibliography,
        toc=toc,
    )


def _discover_from_input_root(input_root: Path) -> ResolvedDocumentStructure:
    files = tuple(
        sorted(
            _validate_markdown_file(path)
            for path in input_root.rglob("*.md")
            if path.is_file()
        )
    )
    if not files:
        raise FileNotFoundError(f"No Markdown files found under: {input_root}")
    return ResolvedDocumentStructure(
        zones=(ResolvedDocumentZone(name="main_matter", files=files),)
    )


def resolve_document_structure(
    document_root: Path,
    config: DocsmithConfig | None = None,
) -> ResolvedDocumentStructure:
    """Resolve the explicit document structure used by discovery and assembly."""
    document_root = document_root.resolve()
    config = config or load_document_config(document_root / "spec.yaml")

    input_root = resolve_document_path(config.document.input_root, document_root)
    if not input_root.exists():
        raise FileNotFoundError(f"Document input root not found: {input_root}")
    if not input_root.is_dir():
        raise NotADirectoryError(f"Document input root is not a directory: {input_root}")

    if any(getattr(config.document, zone_name) for zone_name in ZONE_NAMES):
        return _resolve_zone_structure(input_root, config)

    if config.document.include:
        return ResolvedDocumentStructure(
            zones=(
                ResolvedDocumentZone(
                    name="main_matter",
                    files=_resolve_explicit_paths(
                        input_root,
                        config.document.include,
                        label="document.include",
                    ),
                ),
            ),
            bibliography=(
                ResolvedBibliographyPlacement(
                    title=config.document.bibliography.title,
                    zone=config.document.bibliography.zone,
                )
                if config.document.bibliography.enabled
                else None
            ),
            toc=(
                ResolvedTocPlacement(
                    title=config.document.toc.title,
                    zone=config.document.toc.zone,
                )
                if config.document.toc.enabled
                else None
            ),
        )

    discovered = _discover_from_input_root(input_root)
    if config.document.bibliography.enabled or config.document.toc.enabled:
        return ResolvedDocumentStructure(
            zones=discovered.zones,
            bibliography=(
                ResolvedBibliographyPlacement(
                    title=config.document.bibliography.title,
                    zone=config.document.bibliography.zone,
                )
                if config.document.bibliography.enabled
                else None
            ),
            toc=(
                ResolvedTocPlacement(
                    title=config.document.toc.title,
                    zone=config.document.toc.zone,
                )
                if config.document.toc.enabled
                else None
            ),
        )

    return discovered


def discover_markdown_files(
    document_root: Path,
    config: DocsmithConfig | None = None,
) -> list[Path]:
    """Resolve ordered Markdown sources for a document."""
    return resolve_document_structure(document_root, config).files
