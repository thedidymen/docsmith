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
    assert len(report.checks) == 7
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
