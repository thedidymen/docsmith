"""Conservative figure and table cross-reference scanning for Markdown sources."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from docsmith.config import DocsmithConfig
from docsmith.core.discovery import resolve_document_structure

ID_NAME_PATTERN = r"[a-z0-9][a-z0-9_-]*"
FIGURE_ID_PATTERN = re.compile(rf"^fig:{ID_NAME_PATTERN}$")
TABLE_ID_PATTERN = re.compile(rf"^tbl:{ID_NAME_PATTERN}$")
REFERENCE_PATTERN = re.compile(r"@(?P<raw>(?:fig|tbl):[A-Za-z0-9_-]+)")
IMAGE_WITH_ATTRIBUTES_PATTERN = re.compile(r"!\[[^\]]*]\([^)]+\)\{(?P<attrs>[^}]*)\}")
ATTRIBUTE_ID_PATTERN = re.compile(r"#(?P<raw>[^\s}]+)")
TABLE_CAPTION_PATTERN = re.compile(r"^Table:\s+.*\{(?P<attrs>[^}]*)\}\s*$")


@dataclass(frozen=True)
class CrossReferenceTarget:
    """A discovered figure or table target in source Markdown."""

    kind: str
    target_id: str
    path: Path
    line_number: int


@dataclass(frozen=True)
class CrossReferenceUsage:
    """A discovered figure or table reference in source Markdown."""

    target_id: str
    path: Path
    line_number: int


@dataclass(frozen=True)
class CrossReferenceScanResult:
    """Discovered cross-reference targets and usages for a document."""

    targets: tuple[CrossReferenceTarget, ...]
    references: tuple[CrossReferenceUsage, ...]


def _extract_attribute_id(attributes: str) -> str | None:
    """Return the first attribute ID in a Pandoc-style attribute block."""
    match = ATTRIBUTE_ID_PATTERN.search(attributes)
    if match is None:
        return None
    return match.group("raw")


def scan_markdown_cross_references(
    document_root: Path,
    config: DocsmithConfig,
) -> CrossReferenceScanResult:
    """Scan resolved Markdown sources for figure/table IDs and references.

    The scanner is intentionally conservative. It supports only the authoring
    patterns documented in ``docs/design-cross-references.md``:

    - figures on a single line using Markdown image syntax plus attributes
    - tables using a single-line ``Table: ... {#tbl:...}`` caption
    - text references using ``@fig:...`` or ``@tbl:...``
    """
    structure = resolve_document_structure(document_root, config)
    targets: list[CrossReferenceTarget] = []
    references: list[CrossReferenceUsage] = []

    for markdown_path in structure.files:
        content = markdown_path.read_text(encoding="utf-8")
        for line_number, line in enumerate(content.splitlines(), start=1):
            for image_match in IMAGE_WITH_ATTRIBUTES_PATTERN.finditer(line):
                raw_id = _extract_attribute_id(image_match.group("attrs"))
                if raw_id is None:
                    continue
                targets.append(
                    CrossReferenceTarget(
                        kind="figure",
                        target_id=raw_id,
                        path=markdown_path,
                        line_number=line_number,
                    )
                )

            table_match = TABLE_CAPTION_PATTERN.match(line.strip())
            if table_match is not None:
                raw_id = _extract_attribute_id(table_match.group("attrs"))
                if raw_id is not None:
                    targets.append(
                        CrossReferenceTarget(
                            kind="table",
                            target_id=raw_id,
                            path=markdown_path,
                            line_number=line_number,
                        )
                    )

            for reference_match in REFERENCE_PATTERN.finditer(line):
                references.append(
                    CrossReferenceUsage(
                        target_id=reference_match.group("raw"),
                        path=markdown_path,
                        line_number=line_number,
                    )
                )

    return CrossReferenceScanResult(targets=tuple(targets), references=tuple(references))


def validate_markdown_cross_references(
    document_root: Path,
    config: DocsmithConfig,
) -> str:
    """Validate figure/table cross-reference authoring in Markdown sources."""
    scan_result = scan_markdown_cross_references(document_root, config)

    target_index: dict[str, CrossReferenceTarget] = {}
    errors: list[str] = []

    for target in scan_result.targets:
        is_valid = (
            FIGURE_ID_PATTERN.match(target.target_id)
            if target.kind == "figure"
            else TABLE_ID_PATTERN.match(target.target_id)
        )
        expected_prefix = "fig:" if target.kind == "figure" else "tbl:"

        if is_valid is None:
            errors.append(
                (
                    f"Invalid {target.kind} ID `{target.target_id}` at "
                    f"{target.path}:{target.line_number}. "
                    f"{target.kind.capitalize()} IDs must start with `{expected_prefix}` "
                    "and use lowercase ASCII letters, digits, `_`, or `-` after the prefix."
                )
            )
            continue

        if target.target_id in target_index:
            original = target_index[target.target_id]
            errors.append(
                (
                    f"Duplicate cross-reference ID `{target.target_id}` at "
                    f"{target.path}:{target.line_number}; first defined at "
                    f"{original.path}:{original.line_number}."
                )
            )
            continue

        target_index[target.target_id] = target

    for reference in scan_result.references:
        pattern = FIGURE_ID_PATTERN if reference.target_id.startswith("fig:") else TABLE_ID_PATTERN
        if pattern.match(reference.target_id) is None:
            errors.append(
                (
                    f"Invalid cross-reference target `{reference.target_id}` at "
                    f"{reference.path}:{reference.line_number}."
                )
            )
            continue

        if reference.target_id not in target_index:
            errors.append(
                (
                    f"Missing cross-reference target `{reference.target_id}` referenced at "
                    f"{reference.path}:{reference.line_number}."
                )
            )

    if errors:
        raise ValueError(" ".join(errors))

    if not scan_result.targets and not scan_result.references:
        return "No figure/table cross-reference authoring detected"

    return (
        f"Validated {len(scan_result.targets)} cross-reference target(s) and "
        f"{len(scan_result.references)} reference(s)"
    )
