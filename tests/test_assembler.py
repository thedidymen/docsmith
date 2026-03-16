from pathlib import Path

from docsmith.core.assembler import assemble_markdown


def test_assemble_markdown_combines_example_sections_in_order() -> None:
    content = assemble_markdown(Path("examples/documents/technical_report_demo"))

    assert "<!-- begin:sections/00_overview.md -->" in content
    assert "<!-- begin:sections/90_appendix.md -->" in content
    assert content.index("# Overview") < content.index("# Supporting Notes")


def test_assemble_markdown_uses_explicit_include_order(tmp_path: Path) -> None:
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

    content = assemble_markdown(document_root)

    assert content.index("# Second") < content.index("# First")


def test_assemble_markdown_replaces_appendix_marker(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_body.md").write_text(
        "# Body\n\n<!-- APPENDIX -->\n\n# Appendix A\n",
        encoding="utf-8",
    )
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Appendix Example",
                "  author: Example Author",
                "document:",
                "  input_root: sections",
            ]
        ),
        encoding="utf-8",
    )

    content = assemble_markdown(document_root)

    assert "\\appendix" in content
