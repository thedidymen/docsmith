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


def test_assemble_markdown_preserves_zone_boundaries_and_order(tmp_path: Path) -> None:
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
                "  title: Zoned Assembly Example",
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

    content = assemble_markdown(document_root)

    assert "<!-- zone:front_matter -->" in content
    assert "<!-- zone:main_matter -->" in content
    assert "<!-- zone:back_matter -->" in content
    assert content.index("# Preface") < content.index("# Body") < content.index("# Notes")


def test_assemble_markdown_uses_zones_when_both_models_are_present(tmp_path: Path) -> None:
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

    content = assemble_markdown(document_root)

    assert "# Ignored" not in content
    assert content.index("# Preface") < content.index("# Body")


def test_assemble_markdown_places_appendices_after_back_matter(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_preface.md").write_text("# Preface\n", encoding="utf-8")
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (sections_dir / "90_notes.md").write_text("# Notes\n", encoding="utf-8")
    (sections_dir / "30_appendix_a.md").write_text("# Appendix A\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Appendix Assembly Example",
                "document:",
                "  front_matter:",
                "    - 00_preface.md",
                "  main_matter:",
                "    - 10_body.md",
                "  back_matter:",
                "    - 90_notes.md",
                "  appendices:",
                "    - 30_appendix_a.md",
            ]
        ),
        encoding="utf-8",
    )

    content = assemble_markdown(document_root)

    assert "<!-- zone:appendices -->" in content
    assert "<!-- appendix-begin -->" in content
    assert "\\appendix" in content
    assert content.index("# Preface") < content.index("# Body") < content.index("# Notes")
    assert content.index("# Notes") < content.index("# Appendix A")


def test_assemble_markdown_strips_legacy_appendix_marker_for_explicit_appendices(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "30_appendix_a.md").write_text(
        "# Appendix A\n\n<!-- APPENDIX -->\n\nDetails.\n",
        encoding="utf-8",
    )
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Explicit Appendix Example",
                "document:",
                "  appendices:",
                "    - 30_appendix_a.md",
            ]
        ),
        encoding="utf-8",
    )

    content = assemble_markdown(document_root)

    assert content.count("\\appendix") == 1
    assert "<!-- APPENDIX -->" not in content


def test_assemble_markdown_places_bibliography_in_back_matter(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "10_body.md").write_text("# Body\n\nCite [@ref].\n", encoding="utf-8")
    (sections_dir / "90_notes.md").write_text("# Notes\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Bibliography Assembly Example",
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
    (document_root / "references.bib").write_text(
        "@book{ref,\n  title = {Book}\n}\n",
        encoding="utf-8",
    )

    content = assemble_markdown(document_root)

    assert "<!-- bibliography-begin -->" in content
    assert "# Literature" in content
    assert "::: {#refs}" in content
    assert content.index("# Notes") < content.index("# Literature")


def test_assemble_markdown_keeps_backward_compatibility_without_bibliography_config(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: No Bibliography Placement Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )

    content = assemble_markdown(document_root)

    assert "<!-- bibliography-begin -->" not in content
    assert "::: {#refs}" not in content


def test_assemble_markdown_places_toc_in_front_matter(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_preface.md").write_text("# Preface\n", encoding="utf-8")
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: TOC Assembly Example",
                "document:",
                "  front_matter:",
                "    - 00_preface.md",
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

    content = assemble_markdown(document_root)

    assert "<!-- toc-begin -->" in content
    assert "# Inhoudsopgave" in content
    assert "\\tableofcontents" in content
    assert content.index("# Inhoudsopgave") < content.index("# Preface") < content.index("# Body")


def test_assemble_markdown_places_ordered_front_matter_toc_after_authored_sections(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_preface.md").write_text("# Preface\n", encoding="utf-8")
    (sections_dir / "01_summary.md").write_text("# Summary\n", encoding="utf-8")
    (sections_dir / "10_intro.md").write_text("# Inleiding\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Ordered TOC Assembly Example",
                "document:",
                "  front_matter:",
                "    - file: 00_preface.md",
                "    - file: 01_summary.md",
                "    - generated: toc",
                "      title: Inhoudsopgave",
                "      numbered: false",
                "      listed: true",
                "  main_matter:",
                "    - 10_intro.md",
            ]
        ),
        encoding="utf-8",
    )

    content = assemble_markdown(document_root)

    assert content.index("# Preface") < content.index("# Summary") < content.index("# Inhoudsopgave")
    assert content.index("# Inhoudsopgave") < content.index("# Inleiding")
    assert "{.unnumbered}" in content
    assert "<!-- toc-config:numbered=false listed=true -->" in content


def test_assemble_markdown_renders_unlisted_toc_semantics(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_preface.md").write_text("# Preface\n", encoding="utf-8")
    (sections_dir / "10_intro.md").write_text("# Inleiding\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Unlisted TOC Assembly Example",
                "document:",
                "  front_matter:",
                "    - file: 00_preface.md",
                "    - generated: toc",
                "      title: Inhoudsopgave",
                "      numbered: false",
                "      listed: false",
                "  main_matter:",
                "    - 10_intro.md",
            ]
        ),
        encoding="utf-8",
    )

    content = assemble_markdown(document_root)

    assert "# Inhoudsopgave {.unnumbered .unlisted}" in content
    assert "<!-- toc-config:numbered=false listed=false -->" in content


def test_assemble_markdown_numbered_false_preserves_first_numbered_chapter_for_inleiding(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "10_intro.md").write_text("# Inleiding\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: TOC Numbering Example",
                "document:",
                "  front_matter:",
                "    - generated: toc",
                "      title: Inhoudsopgave",
                "      numbered: false",
                "      listed: true",
                "  main_matter:",
                "    - 10_intro.md",
            ]
        ),
        encoding="utf-8",
    )

    content = assemble_markdown(document_root)

    assert "# Inhoudsopgave {.unnumbered}" in content
    assert "# Inleiding" in content


def test_assemble_markdown_keeps_backward_compatibility_without_toc_config(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  title: No TOC Placement Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )

    content = assemble_markdown(document_root)

    assert "<!-- toc-begin -->" not in content
    assert "\\tableofcontents" not in content
