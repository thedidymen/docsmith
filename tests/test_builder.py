from pathlib import Path
from unittest.mock import patch

from docsmith.core.builder import build_document
from docsmith.versioning.state import load_build_state


def _write_document_spec(
    document_root: Path,
    *,
    template: str = "templates/technical_report",
    bibliography: str | None = None,
    csl: str | None = None,
) -> None:
    lines = [
        "project:",
        f"  template: {template}",
        "metadata:",
        "  title: Example Document",
        "  author: Example Author",
        "document:",
        "  input_root: sections",
        "output:",
        "  directory: output",
        "  basename: example_document",
        "versioning:",
        "  strategy: semver",
        "  initial_version: 0.1.0",
        "  include_git_hash: true",
    ]
    if bibliography or csl:
        lines.extend(["citations:"])
        if bibliography:
            lines.append(f"  bibliography: {bibliography}")
        if csl:
            lines.append(f"  csl: {csl}")

    (document_root / "spec.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def _create_document(document_root: Path) -> None:
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    _create_template(document_root)
    _write_document_spec(document_root)


def test_first_build_uses_initial_version_when_no_prior_state(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(document_root)

    with (
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        result = build_document(document_root)

    assert result.version_info.semantic_version == "0.1.0"
    assert result.output_path.name == "example_document_v0.1.0_abc1234.pdf"
    state = load_build_state(result.build_dir)
    assert state is not None
    assert state.current_version == "0.1.0"


def test_repeated_build_with_unchanged_fingerprint_keeps_same_version(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(document_root)

    with (
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        first = build_document(document_root)
        second = build_document(document_root)

    assert first.version_info.semantic_version == "0.1.0"
    assert second.version_info.semantic_version == "0.1.0"
    assert second.version_info.bump_applied is None


def test_repeated_build_with_changed_markdown_content_bumps_patch(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(document_root)

    with (
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        first = build_document(document_root)
        (document_root / "sections" / "00_intro.md").write_text("# Intro\nUpdated.\n", encoding="utf-8")
        second = build_document(document_root)

    assert first.version_info.semantic_version == "0.1.0"
    assert second.version_info.semantic_version == "0.1.1"
    assert second.version_info.bump_applied == "patch"


def test_repeated_build_with_changed_spec_bumps_patch(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(document_root)

    with (
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        build_document(document_root)
        _create_template(document_root, "academic_thesis")
        _write_document_spec(document_root, template="templates/academic_thesis")
        result = build_document(document_root)

    assert result.version_info.semantic_version == "0.1.1"


def test_repeated_build_with_changed_template_input_bumps_patch(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(document_root)
    template_root = tmp_path / "template"
    template_root.mkdir()
    (template_root / "template.tex").write_text("version one\n", encoding="utf-8")
    (template_root / "defaults.yaml").write_text("pdf-engine: xelatex\n", encoding="utf-8")

    with (
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
        patch("docsmith.versioning.fingerprint.validate_template", return_value=template_root),
    ):
        build_document(document_root)
        (template_root / "template.tex").write_text("version two\n", encoding="utf-8")
        result = build_document(document_root)

    assert result.version_info.semantic_version == "0.1.1"


def test_repeated_build_with_changed_bibliography_or_csl_bumps_patch(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    _create_template(document_root)
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    (document_root / "references.bib").write_text("@book{ref,\n  title = {Book}\n}\n", encoding="utf-8")
    csl_dir = document_root / "csl"
    csl_dir.mkdir()
    (csl_dir / "apa.csl").write_text("<style />\n", encoding="utf-8")
    _write_document_spec(
        document_root,
        bibliography="references.bib",
        csl="csl/apa.csl",
    )

    with (
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        build_document(document_root)
        (document_root / "references.bib").write_text(
            "@book{ref,\n  title = {Updated Book}\n}\n",
            encoding="utf-8",
        )
        changed_bibliography = build_document(document_root)
        (csl_dir / "apa.csl").write_text("<style updated=\"yes\" />\n", encoding="utf-8")
        changed_csl = build_document(document_root)

    assert changed_bibliography.version_info.semantic_version == "0.1.1"
    assert changed_csl.version_info.semantic_version == "0.1.2"


def test_explicit_patch_minor_and_major_bump_overrides_are_supported(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(document_root)

    with (
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        build_document(document_root)
        patch_result = build_document(document_root, bump="patch")
        minor_result = build_document(document_root, bump="minor")
        major_result = build_document(document_root, bump="major")

    assert patch_result.version_info.semantic_version == "0.1.1"
    assert minor_result.version_info.semantic_version == "0.2.0"
    assert major_result.version_info.semantic_version == "1.0.0"


def test_no_bump_disables_automatic_bumping_for_changed_content(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(document_root)

    with (
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        build_document(document_root)
        (document_root / "sections" / "00_intro.md").write_text("# Intro\nUpdated.\n", encoding="utf-8")
        result = build_document(document_root, no_bump=True)

    assert result.version_info.semantic_version == "0.1.0"
    assert result.version_info.bump_applied is None


def test_build_document_works_without_git(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(document_root)

    with (
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value=None),
    ):
        result = build_document(document_root)

    assert result.version_info.git_hash is None
    assert result.output_path.name == "example_document_v0.1.0.pdf"


def test_build_document_writes_intermediate_files_and_runtime_metadata(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document(document_root)

    with (
        patch("docsmith.core.builder.render_pdf") as mock_render_pdf,
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        result = build_document(document_root)

    assert result.assembled_markdown_path.exists()
    assert result.metadata_path.exists()
    assert result.state_path.exists()
    assert mock_render_pdf.call_args.kwargs["metadata_file"] == result.metadata_path
    metadata = result.metadata_path.read_text(encoding="utf-8")
    assert "title: Example Document" in metadata
    assert "version: 0.1.0" in metadata
    assert "git_hash: abc1234" in metadata
