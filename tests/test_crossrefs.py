from pathlib import Path

from docsmith.config import load_document_config
from docsmith.core.crossrefs import (
    scan_markdown_cross_references,
    validate_markdown_cross_references,
)


def _create_document(document_root: Path, markdown_lines: list[str]) -> None:
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "10_body.md").write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Cross Reference Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )


def test_scan_markdown_cross_references_discovers_figure_table_and_references(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    _create_document(
        document_root,
        [
            "Zie @fig:registratieproces.",
            "",
            "![Procesdiagram](assets/generated/registratieproces.png){#fig:registratieproces width=80%}",
            "",
            "| Scenario | Resultaat |",
            "|---|---|",
            "| Geldige invoer | Vastgelegd |",
            "",
            "Table: Resultaten van validatiescenario's {#tbl:validatie}",
            "",
            "Zie @tbl:validatie.",
        ],
    )
    config = load_document_config(document_root / "spec.yaml")

    scan_result = scan_markdown_cross_references(document_root, config)

    assert [target.kind for target in scan_result.targets] == ["figure", "table"]
    assert [target.target_id for target in scan_result.targets] == [
        "fig:registratieproces",
        "tbl:validatie",
    ]
    assert [reference.target_id for reference in scan_result.references] == [
        "fig:registratieproces",
        "tbl:validatie",
    ]


def test_validate_markdown_cross_references_accepts_caption_without_id(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(
        document_root,
        [
            "![Procesdiagram](assets/generated/registratieproces.png){width=80%}",
            "",
            "| Scenario | Resultaat |",
            "|---|---|",
            "| Geldige invoer | Vastgelegd |",
            "",
            "Table: Resultaten van validatiescenario's",
        ],
    )
    config = load_document_config(document_root / "spec.yaml")

    detail = validate_markdown_cross_references(document_root, config)

    assert detail == "No figure/table cross-reference authoring detected"


def test_validate_markdown_cross_references_rejects_duplicate_ids(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(
        document_root,
        [
            "![Procesdiagram A](a.png){#fig:registratieproces}",
            "![Procesdiagram B](b.png){#fig:registratieproces}",
        ],
    )
    config = load_document_config(document_root / "spec.yaml")

    try:
        validate_markdown_cross_references(document_root, config)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected duplicate cross-reference IDs to fail validation")

    assert "Duplicate cross-reference ID `fig:registratieproces`" in message


def test_validate_markdown_cross_references_rejects_invalid_target_ids(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(
        document_root,
        [
            "![Procesdiagram](a.png){#figure:registratieproces}",
            "",
            "Table: Resultaten van validatiescenario's {#tbl:Validatie}",
        ],
    )
    config = load_document_config(document_root / "spec.yaml")

    try:
        validate_markdown_cross_references(document_root, config)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected invalid cross-reference IDs to fail validation")

    assert "Invalid figure ID `figure:registratieproces`" in message
    assert "Invalid table ID `tbl:Validatie`" in message


def test_validate_markdown_cross_references_rejects_missing_targets(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(
        document_root,
        [
            "Zie @fig:registratieproces.",
            "Zie @tbl:validatie.",
            "",
            "![Procesdiagram](a.png){#fig:ander-doel}",
        ],
    )
    config = load_document_config(document_root / "spec.yaml")

    try:
        validate_markdown_cross_references(document_root, config)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected missing cross-reference targets to fail validation")

    assert "Missing cross-reference target `fig:registratieproces`" in message
    assert "Missing cross-reference target `tbl:validatie`" in message
