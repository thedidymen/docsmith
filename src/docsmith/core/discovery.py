"""Markdown source discovery for Docsmith documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from docsmith.config import (
    DocsmithConfig,
    DocumentZoneItemConfig,
    document_has_explicit_generated_toc,
    load_document_config,
)
from docsmith.core.paths import resolve_document_path

ZONE_NAMES = ("front_matter", "main_matter", "back_matter", "appendices")


@dataclass(frozen=True)
class ResolvedDocumentFileItem:
    """Resolved authored Markdown file inside a document zone."""

    kind: str
    path: Path


@dataclass(frozen=True)
class ResolvedGeneratedTocItem:
    """Resolved table-of-contents placement inside a document zone."""

    kind: str
    generated: str
    zone: str
    title: str
    numbered: bool
    listed: bool


ResolvedDocumentZoneItem = Union[ResolvedDocumentFileItem, ResolvedGeneratedTocItem]


@dataclass(frozen=True)
class ResolvedDocumentZone:
    """Resolved ordered structural items for a logical document zone."""

    name: str
    items: tuple[ResolvedDocumentZoneItem, ...]

    @property
    def files(self) -> tuple[Path, ...]:
        """Return authored Markdown files in this zone."""
        return tuple(
            item.path for item in self.items if isinstance(item, ResolvedDocumentFileItem)
        )


@dataclass(frozen=True)
class ResolvedDocumentStructure:
    """Resolved ordered document structure used by the build pipeline."""

    zones: tuple[ResolvedDocumentZone, ...]
    bibliography: "ResolvedBibliographyPlacement | None" = None

    @property
    def files(self) -> list[Path]:
        """Return all zone files as a single ordered list."""
        return [path for zone in self.zones for path in zone.files]

    @property
    def toc(self) -> ResolvedGeneratedTocItem | None:
        """Return the resolved TOC item when configured."""
        for zone in self.zones:
            for item in zone.items:
                if isinstance(item, ResolvedGeneratedTocItem):
                    return item
        return None


@dataclass(frozen=True)
class ResolvedBibliographyPlacement:
    """Resolved bibliography placement in the document structure."""

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


def _resolve_zone_item(
    input_root: Path,
    zone_name: str,
    item: DocumentZoneItemConfig,
) -> ResolvedDocumentZoneItem:
    """Resolve one configured structural zone item."""
    if item.file:
        return ResolvedDocumentFileItem(
            kind="file",
            path=_validate_markdown_file(resolve_document_path(item.file, input_root)),
        )

    return ResolvedGeneratedTocItem(
        kind="generated",
        generated="toc",
        zone=zone_name,
        title=item.title,
        numbered=item.numbered,
        listed=item.listed,
    )


def _legacy_toc_item(config: DocsmithConfig) -> ResolvedGeneratedTocItem | None:
    """Resolve the legacy TOC config into the new ordered item model when needed."""
    if not config.document.toc.enabled or document_has_explicit_generated_toc(config):
        return None

    return ResolvedGeneratedTocItem(
        kind="generated",
        generated="toc",
        zone=config.document.toc.zone,
        title=config.document.toc.title,
        numbered=False,
        listed=True,
    )


def _resolve_zone_structure(
    input_root: Path,
    config: DocsmithConfig,
) -> ResolvedDocumentStructure:
    zones: list[ResolvedDocumentZone] = []
    seen_relative_paths: set[str] = set()
    legacy_toc_item = _legacy_toc_item(config)

    for zone_name in ZONE_NAMES:
        configured_items = list(getattr(config.document, zone_name))
        resolved_items: list[ResolvedDocumentZoneItem] = []
        if zone_name == "front_matter" and legacy_toc_item is not None:
            resolved_items.append(legacy_toc_item)

        for configured_item in configured_items:
            resolved_item = _resolve_zone_item(input_root, zone_name, configured_item)
            if isinstance(resolved_item, ResolvedDocumentFileItem):
                relative_path = resolved_item.path.relative_to(input_root).as_posix()
                if relative_path in seen_relative_paths:
                    raise ValueError(
                        f"Duplicate markdown source across document zones: {relative_path}"
                    )
                seen_relative_paths.add(relative_path)
            resolved_items.append(resolved_item)

        zones.append(ResolvedDocumentZone(name=zone_name, items=tuple(resolved_items)))

    if not seen_relative_paths:
        raise FileNotFoundError("No Markdown files configured in document zones")

    bibliography = None
    if config.document.bibliography.enabled:
        bibliography = ResolvedBibliographyPlacement(
            title=config.document.bibliography.title,
            zone=config.document.bibliography.zone,
        )
    return ResolvedDocumentStructure(
        zones=tuple(zones),
        bibliography=bibliography,
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
        zones=(
            ResolvedDocumentZone(
                name="main_matter",
                items=tuple(
                    ResolvedDocumentFileItem(kind="file", path=path) for path in files
                ),
            ),
        )
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
                    items=tuple(
                        ResolvedDocumentFileItem(kind="file", path=path)
                        for path in _resolve_explicit_paths(
                            input_root,
                            config.document.include,
                            label="document.include",
                        )
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
        )

    discovered = _discover_from_input_root(input_root)
    if config.document.bibliography.enabled or _legacy_toc_item(config) is not None:
        legacy_toc_item = _legacy_toc_item(config)
        zones = list(discovered.zones)
        if legacy_toc_item is not None:
            zones.insert(
                0,
                ResolvedDocumentZone(name="front_matter", items=(legacy_toc_item,)),
            )
        return ResolvedDocumentStructure(
            zones=tuple(zones),
            bibliography=(
                ResolvedBibliographyPlacement(
                    title=config.document.bibliography.title,
                    zone=config.document.bibliography.zone,
                )
                if config.document.bibliography.enabled
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
