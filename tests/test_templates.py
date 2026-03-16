from pathlib import Path

from docsmith.templates.registry import (
    get_template_path,
    list_templates,
    validate_template,
)


EXAMPLES_ROOT = Path("examples")
DOCUMENT_ROOT = Path("examples/documents/authoring_guide")


def test_list_templates_includes_document_local_examples() -> None:
    templates = list_templates(EXAMPLES_ROOT)

    assert templates == ["academic_thesis", "technical_report"]


def test_get_template_path_resolves_document_local_template_directory() -> None:
    template_path = get_template_path(
        "../../templates/academic_thesis",
        DOCUMENT_ROOT,
    )

    assert template_path == (EXAMPLES_ROOT / "templates" / "academic_thesis").resolve()


def test_validate_template_accepts_academic_thesis() -> None:
    template_path = validate_template(
        "../../templates/academic_thesis",
        DOCUMENT_ROOT,
    )

    assert (template_path / "template.tex").exists()
    assert (template_path / "defaults.yaml").exists()


def test_academic_thesis_template_defines_tightlist() -> None:
    template_path = get_template_path(
        "../../templates/academic_thesis",
        DOCUMENT_ROOT,
    )
    content = (template_path / "template.tex").read_text(encoding="utf-8")

    assert "\\providecommand{\\tightlist}" in content


def test_academic_thesis_template_defines_pandocbounded() -> None:
    template_path = get_template_path(
        "../../templates/academic_thesis",
        DOCUMENT_ROOT,
    )
    content = (template_path / "template.tex").read_text(encoding="utf-8")

    assert "\\providecommand{\\pandocbounded}" in content


def test_academic_thesis_template_supports_pandoc_code_blocks() -> None:
    template_path = get_template_path(
        "../../templates/academic_thesis",
        DOCUMENT_ROOT,
    )
    content = (template_path / "template.tex").read_text(encoding="utf-8")

    assert "\\DefineVerbatimEnvironment{Highlighting}{Verbatim}" in content
    assert "\\newenvironment{Shaded}{}{}" in content


def test_academic_thesis_template_supports_pandoc_citations() -> None:
    template_path = get_template_path(
        "../../templates/academic_thesis",
        DOCUMENT_ROOT,
    )
    content = (template_path / "template.tex").read_text(encoding="utf-8")

    assert "\\newenvironment{CSLReferences}" in content
    assert "\\newcommand{\\CSLBlock}" in content


def test_validate_template_rejects_missing_template_files(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    template_root = document_root / "templates" / "broken_template"
    template_root.mkdir(parents=True)

    try:
        validate_template("templates/broken_template", document_root)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing template files to fail validation")
