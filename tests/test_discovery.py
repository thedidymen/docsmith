from pathlib import Path

from docsmith.config import load_document_config
from docsmith.core.discovery import discover_markdown_files


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
