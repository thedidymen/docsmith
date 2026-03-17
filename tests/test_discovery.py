from pathlib import Path

from docsmith.config import load_document_config
from docsmith.core.discovery import discover_markdown_files, resolve_document_structure


def test_discover_markdown_files_from_example() -> None:
    files = discover_markdown_files(Path("examples/documents/technical_report_demo"))

    assert [path.name for path in files] == [
        "00_overview.md",
        "10_workflow.md",
        "20_feature_matrix.md",
        "30_citations.md",
        "90_appendix.md",
    ]


def test_discover_markdown_files_from_authoring_guide_example() -> None:
    files = discover_markdown_files(Path("examples/documents/authoring_guide"))

    assert [path.name for path in files] == [
        "00_existing_content.md",
        "01_basic_markdown.md",
        "02_images_and_tables.md",
        "03_citations.md",
        "04_appendices.md",
        "05_versioning_behavior.md",
        "06_docsmith_authoring_tips.md",
    ]


def test_discover_markdown_files_from_architecture_example() -> None:
    files = discover_markdown_files(Path("examples/documents/docsmith_architecture"))

    assert [path.name for path in files] == [
        "00_scope_and_goals.md",
        "01_system_overview.md",
        "02_major_components.md",
        "03_build_pipeline.md",
        "04_configuration_model.md",
        "05_versioning_and_outputs.md",
        "06_limitations_and_future_improvements.md",
        "90_appendix.md",
    ]


def test_discover_markdown_files_uses_explicit_include_order(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_first.md").write_text("# First\n", encoding="utf-8")
    (sections_dir / "10_second.md").write_text("# Second\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Ordered Example",
                "  author: Example Author",
                "document:",
                "  input_root: sections",
                "  include:",
                "    - 10_second.md",
                "    - 00_first.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(document_root / "spec.yaml")
    files = discover_markdown_files(document_root, config)

    assert [path.name for path in files] == ["10_second.md", "00_first.md"]


def test_discover_markdown_files_fails_for_missing_include_file(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Missing File Example",
                "  author: Example Author",
                "document:",
                "  input_root: sections",
                "  include:",
                "    - missing.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(document_root / "spec.yaml")

    try:
        discover_markdown_files(document_root, config)
    except FileNotFoundError as exc:
        assert "missing.md" in str(exc)
    else:
        raise AssertionError("Expected missing include file to fail discovery")


def test_resolve_document_structure_preserves_zone_order(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_preface.md").write_text("# Preface\n", encoding="utf-8")
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (sections_dir / "90_notes.md").write_text("# Notes\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Zoned Example",
                "document:",
                "  front_matter:",
                "    - 00_preface.md",
                "  main_matter:",
                "    - 10_body.md",
                "  back_matter:",
                "    - 90_notes.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(document_root / "spec.yaml")
    structure = resolve_document_structure(document_root, config)

    assert [zone.name for zone in structure.zones] == [
        "front_matter",
        "main_matter",
        "back_matter",
        "appendices",
    ]
    assert [path.name for path in structure.files] == [
        "00_preface.md",
        "10_body.md",
        "90_notes.md",
    ]


def test_discover_markdown_files_prefers_zones_over_legacy_include(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_preface.md").write_text("# Preface\n", encoding="utf-8")
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (sections_dir / "20_ignored.md").write_text("# Ignored\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Zoned Precedence Example",
                "document:",
                "  include:",
                "    - 20_ignored.md",
                "  front_matter:",
                "    - 00_preface.md",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(document_root / "spec.yaml")
    files = discover_markdown_files(document_root, config)

    assert [path.name for path in files] == ["00_preface.md", "10_body.md"]


def test_resolve_document_structure_rejects_duplicate_zone_references(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Duplicate Zone Example",
                "document:",
                "  front_matter:",
                "    - 10_body.md",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(document_root / "spec.yaml")

    try:
        resolve_document_structure(document_root, config)
    except ValueError as exc:
        assert "Duplicate markdown source across document zones" in str(exc)
    else:
        raise AssertionError("Expected duplicate zone references to fail discovery")


def test_resolve_document_structure_includes_appendices_after_back_matter(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_preface.md").write_text("# Preface\n", encoding="utf-8")
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (sections_dir / "90_notes.md").write_text("# Notes\n", encoding="utf-8")
    (sections_dir / "30_appendix_a.md").write_text("# Appendix A\n", encoding="utf-8")
    (sections_dir / "31_appendix_b.md").write_text("# Appendix B\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Appendix Structure Example",
                "document:",
                "  front_matter:",
                "    - 00_preface.md",
                "  main_matter:",
                "    - 10_body.md",
                "  back_matter:",
                "    - 90_notes.md",
                "  appendices:",
                "    - 30_appendix_a.md",
                "    - 31_appendix_b.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(document_root / "spec.yaml")
    structure = resolve_document_structure(document_root, config)

    assert [zone.name for zone in structure.zones] == [
        "front_matter",
        "main_matter",
        "back_matter",
        "appendices",
    ]
    assert [path.name for path in structure.files] == [
        "00_preface.md",
        "10_body.md",
        "90_notes.md",
        "30_appendix_a.md",
        "31_appendix_b.md",
    ]


def test_resolve_document_structure_rejects_duplicate_appendix_references(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "30_appendix_a.md").write_text("# Appendix A\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Duplicate Appendix Example",
                "document:",
                "  back_matter:",
                "    - 30_appendix_a.md",
                "  appendices:",
                "    - 30_appendix_a.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(document_root / "spec.yaml")

    try:
        resolve_document_structure(document_root, config)
    except ValueError as exc:
        assert "Duplicate markdown source across document zones" in str(exc)
    else:
        raise AssertionError("Expected duplicate appendix references to fail discovery")


def test_resolve_document_structure_includes_bibliography_placement(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (sections_dir / "90_notes.md").write_text("# Notes\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Bibliography Structure Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
                "  back_matter:",
                "    - 90_notes.md",
                "  bibliography:",
                "    enabled: true",
                "    title: Literature",
                "    zone: back_matter",
                "citations:",
                "  bibliography: references.bib",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(document_root / "spec.yaml")
    structure = resolve_document_structure(document_root, config)

    assert structure.bibliography is not None
    assert structure.bibliography.title == "Literature"
    assert structure.bibliography.zone == "back_matter"


def test_resolve_document_structure_includes_toc_placement(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: TOC Structure Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
                "  toc:",
                "    enabled: true",
                "    title: Inhoudsopgave",
                "    zone: front_matter",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(document_root / "spec.yaml")
    structure = resolve_document_structure(document_root, config)

    assert structure.toc is not None
    assert structure.toc.title == "Inhoudsopgave"
    assert structure.toc.zone == "front_matter"
