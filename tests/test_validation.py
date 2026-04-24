from pathlib import Path
from unittest.mock import patch

from docsmith.core.validation import format_validation_report, validate_document


def _create_template(document_root: Path, template_name: str = "technical_report") -> None:
    template_root = document_root / "templates" / template_name
    template_root.mkdir(parents=True, exist_ok=True)
    (template_root / "template.tex").write_text(
        "\\documentclass{article}\n\\begin{document}\n$body$\n\\end{document}\n",
        encoding="utf-8",
    )
    (template_root / "defaults.yaml").write_text(
        "from: markdown\npdf-engine: xelatex\n",
        encoding="utf-8",
    )


def test_validate_document_reports_success_for_example() -> None:
    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(Path("examples/documents/technical_report_demo"))

    assert report.ok is True
    assert len(report.checks) == 10
    assert all(check.ok for check in report.checks)


def test_validate_document_reports_success_for_authoring_guide_example() -> None:
    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(Path("examples/documents/authoring_guide"))

    assert report.ok is True
    assert all(check.ok for check in report.checks)


def test_validate_document_reports_success_for_architecture_example() -> None:
    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(Path("examples/documents/docsmith_architecture"))

    assert report.ok is True
    assert all(check.ok for check in report.checks)


def test_validate_document_checks_missing_output_directory_without_creating_it(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Output Directory Example",
                "  author: Example Author",
                "output:",
                "  directory: build/output",
            ]
        ),
        encoding="utf-8",
    )

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is True
    assert not (document_root / "build" / "output").exists()


def test_validate_document_reports_missing_include_file(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Missing Include Example",
                "  author: Example Author",
                "document:",
                "  include:",
                "    - missing.md",
            ]
        ),
        encoding="utf-8",
    )

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is False
    markdown_check = next(
        check for check in report.checks if check.label == "included markdown files existence"
    )
    assert markdown_check.ok is False
    assert "missing.md" in markdown_check.detail


def test_validate_document_reports_output_directory_path_conflict(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    output_file = document_root / "output"
    output_file.write_text("not a directory\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Output Path Conflict Example",
                "  author: Example Author",
            ]
        ),
        encoding="utf-8",
    )

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is False
    output_check = next(
        check
        for check in report.checks
        if check.label == "output directory resolution/creatability"
    )
    assert output_check.ok is False
    assert "not a directory" in output_check.detail.lower()


def test_format_validation_report_includes_status_lines() -> None:
    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(Path("examples/documents/technical_report_demo"))

    rendered = format_validation_report(report)

    assert "Validation results for" in rendered
    assert "[PASS] spec.yaml loading:" in rendered
    assert "Validation succeeded." in rendered


def test_validate_document_reports_missing_pdf_dependencies(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Dependency Example",
                "  author: Example Author",
            ]
        ),
        encoding="utf-8",
    )

    with patch(
        "docsmith.core.validation.validate_pdf_dependencies",
        return_value=["pandoc", "xelatex"],
    ):
        report = validate_document(document_root)

    dependency_check = next(
        check for check in report.checks if check.label == "external PDF build dependencies"
    )
    assert dependency_check.ok is False
    assert "pandoc" in dependency_check.detail
    assert "xelatex" in dependency_check.detail


def test_validate_document_reports_non_mapping_metadata(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  - invalid",
            ]
        ),
        encoding="utf-8",
    )

    report = validate_document(document_root)

    assert report.ok is False
    spec_check = next(check for check in report.checks if check.label == "spec.yaml loading")
    assert spec_check.ok is False
    assert "metadata" in spec_check.detail


def test_validate_document_reports_duplicate_zone_references(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
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

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is False
    markdown_check = next(
        check for check in report.checks if check.label == "included markdown files existence"
    )
    assert "Duplicate markdown source across document zones" in markdown_check.detail


def test_validate_document_reports_duplicate_appendix_references(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "30_appendix_a.md").write_text("# Appendix A\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
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

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is False
    markdown_check = next(
        check for check in report.checks if check.label == "included markdown files existence"
    )
    assert "Duplicate markdown source across document zones" in markdown_check.detail


def test_validate_document_accepts_structural_bibliography_in_back_matter(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "10_body.md").write_text("# Body\n\nCite [@ref].\n", encoding="utf-8")
    (document_root / "references.bib").write_text(
        "@book{ref,\n  title = {Book}\n}\n",
        encoding="utf-8",
    )
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Structural Bibliography Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
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

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is True


def test_validate_document_rejects_structural_bibliography_without_bib_file(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Invalid Structural Bibliography Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
                "  bibliography:",
                "    enabled: true",
                "    zone: back_matter",
            ]
        ),
        encoding="utf-8",
    )

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is False
    bibliography_check = next(
        check for check in report.checks if check.label == "structural bibliography placement"
    )
    assert "citations.bibliography" in bibliography_check.detail


def test_validate_document_accepts_structural_toc_in_front_matter(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Structural TOC Example",
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

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is True


def test_validate_document_rejects_structural_toc_in_unsupported_zone(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Invalid Structural TOC Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
                "  toc:",
                "    enabled: true",
                "    zone: back_matter",
            ]
        ),
        encoding="utf-8",
    )

    report = validate_document(document_root)

    assert report.ok is False
    spec_check = next(check for check in report.checks if check.label == "spec.yaml loading")
    assert "front_matter" in spec_check.detail


def test_validate_document_accepts_ordered_front_matter_toc(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "00_preface.md").write_text("# Preface\n", encoding="utf-8")
    (sections_dir / "10_intro.md").write_text("# Inleiding\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Ordered Structural TOC Example",
                "document:",
                "  front_matter:",
                "    - file: 00_preface.md",
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

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is True
    toc_check = next(check for check in report.checks if check.label == "structural TOC placement")
    assert "ordered `document.front_matter`" in toc_check.detail


def test_validate_document_prefers_ordered_toc_over_legacy_toc_config(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "00_preface.md").write_text("# Preface\n", encoding="utf-8")
    (sections_dir / "10_intro.md").write_text("# Inleiding\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: TOC Precedence Validation Example",
                "document:",
                "  front_matter:",
                "    - file: 00_preface.md",
                "    - generated: toc",
                "      title: Ordered Contents",
                "  main_matter:",
                "    - 10_intro.md",
                "  toc:",
                "    enabled: true",
                "    title: Legacy Contents",
                "    zone: front_matter",
            ]
        ),
        encoding="utf-8",
    )

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is True
    toc_check = next(check for check in report.checks if check.label == "structural TOC placement")
    assert "legacy `document.toc` is ignored" in toc_check.detail


def test_validate_document_rejects_invalid_generated_toc_semantics(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "10_intro.md").write_text("# Inleiding\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Invalid Ordered TOC Example",
                "document:",
                "  front_matter:",
                "    - generated: toc",
                "      title: \"\"",
                "      listed: true",
                "  main_matter:",
                "    - 10_intro.md",
            ]
        ),
        encoding="utf-8",
    )

    report = validate_document(document_root)

    assert report.ok is False
    spec_check = next(check for check in report.checks if check.label == "spec.yaml loading")
    assert "without a title" in spec_check.detail


def test_validate_document_accepts_captioned_media_without_cross_reference_ids(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "10_body.md").write_text(
        "\n".join(
            [
                "![Procesdiagram](assets/generated/registratieproces.png){width=80%}",
                "",
                "| Scenario | Resultaat |",
                "|---|---|",
                "| Geldige invoer | Vastgelegd |",
                "",
                "Table: Resultaten van validatiescenario's",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Captioned Media Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is True
    crossref_check = next(
        check for check in report.checks if check.label == "figure/table cross-reference authoring"
    )
    assert crossref_check.ok is True
    assert "No figure/table cross-reference authoring detected" in crossref_check.detail


def test_validate_document_rejects_duplicate_cross_reference_ids(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "10_body.md").write_text(
        "\n".join(
            [
                "![Procesdiagram A](a.png){#fig:registratieproces}",
                "![Procesdiagram B](b.png){#fig:registratieproces}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Duplicate Cross Reference Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is False
    crossref_check = next(
        check for check in report.checks if check.label == "figure/table cross-reference authoring"
    )
    assert crossref_check.ok is False
    assert "Duplicate cross-reference ID `fig:registratieproces`" in crossref_check.detail


def test_validate_document_rejects_missing_cross_reference_targets(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "10_body.md").write_text(
        "\n".join(
            [
                "Zie @fig:registratieproces.",
                "",
                "![Procesdiagram](a.png){#fig:ander-doel}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Missing Cross Reference Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )

    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        report = validate_document(document_root)

    assert report.ok is False
    crossref_check = next(
        check for check in report.checks if check.label == "figure/table cross-reference authoring"
    )
    assert crossref_check.ok is False
    assert "Missing cross-reference target `fig:registratieproces`" in crossref_check.detail
