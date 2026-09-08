from pathlib import Path
import shutil
from unittest.mock import patch

import pytest
import yaml

from docsmith.core.builder import build_document
from docsmith.renderer.pandoc import (
    build_pandoc_command,
    cross_reference_filter_path,
    table_column_widths_filter_path,
)
from docsmith.versioning.state import load_build_state


def _write_document_spec(
    document_root: Path,
    *,
    template: str = "templates/technical_report",
    bibliography: str | None = None,
    csl: str | None = None,
    diagrams: list[dict[str, str]] | None = None,
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

    if diagrams:
        lines.append("diagrams:")
        for diagram in diagrams:
            lines.extend(
                [
                    f"  - id: {diagram['id']}",
                    f"    type: {diagram['type']}",
                    f"    source: {diagram['source']}",
                    f"    output: {diagram['output']}",
                    f"    format: {diagram['format']}",
                ]
            )

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


def _create_document_with_declared_diagram(document_root: Path) -> None:
    _create_document(document_root)
    diagram_dir = document_root / "assets" / "diagrams"
    diagram_dir.mkdir(parents=True, exist_ok=True)
    (diagram_dir / "starter_procesdiagram.mmd").write_text("graph TD\nA-->B\n", encoding="utf-8")
    _write_document_spec(
        document_root,
        diagrams=[
            {
                "id": "starter-procesdiagram",
                "type": "mermaid",
                "source": "assets/diagrams/starter_procesdiagram.mmd",
                "output": "assets/generated/starter_procesdiagram.png",
                "format": "png",
            }
        ],
    )


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


def test_build_document_renders_declared_diagrams_before_pandoc(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document_with_declared_diagram(document_root)
    call_order: list[str] = []

    def _record_diagrams(*args: object, **kwargs: object) -> list[object]:
        call_order.append("diagrams")
        return []

    def _record_pdf(*args: object, **kwargs: object) -> Path:
        call_order.append("pdf")
        return Path(kwargs.get("output_file", args[1]))  # pragma: no cover - defensive fallback

    with (
        patch("docsmith.core.builder.render_declared_diagrams", side_effect=_record_diagrams),
        patch("docsmith.core.builder.render_pdf", side_effect=_record_pdf),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        build_document(document_root)

    assert call_order == ["diagrams", "pdf"]


def test_build_document_passes_build_dir_to_declared_diagram_rendering(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    _create_document_with_declared_diagram(document_root)

    with (
        patch("docsmith.core.builder.render_declared_diagrams") as mock_render_diagrams,
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        build_document(document_root)

    assert mock_render_diagrams.call_args.args[0] == document_root.resolve()
    assert mock_render_diagrams.call_args.args[1] == document_root.resolve() / "build"


def test_build_document_skips_declared_diagram_rendering_when_none_are_configured(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    _create_document(document_root)

    with (
        patch("docsmith.core.builder.render_declared_diagrams") as mock_render_diagrams,
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        build_document(document_root)

    mock_render_diagrams.assert_not_called()


def test_build_document_merges_user_metadata_into_runtime_metadata(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    _create_template(document_root)
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Example Document",
                "  author: Example Author",
                '  student_number: "123456"',
                "  reviewer:",
                "    name: Dr. Example",
                "  version: user-defined-version",
                "document:",
                "  include:",
                "    - 00_intro.md",
                "output:",
                "  directory: output",
                "  basename: example_document",
                "versioning:",
                "  strategy: semver",
                "  initial_version: 0.1.0",
                "  include_git_hash: true",
            ]
        ),
        encoding="utf-8",
    )

    with (
        patch("docsmith.core.builder.render_pdf"),
        patch("docsmith.core.builder.get_git_short_hash", return_value="abc1234"),
    ):
        result = build_document(document_root)

    metadata = yaml.safe_load(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["title"] == "Example Document"
    assert metadata["student_number"] == "123456"
    assert metadata["reviewer"]["name"] == "Dr. Example"
    assert metadata["version"] == "0.1.0"
    assert metadata["git_hash"] == "abc1234"


def test_build_document_passes_extensible_metadata_to_renderer(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    sections_dir.mkdir(parents=True)
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    _create_template(document_root)
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Integration Metadata Example",
                "  author: Example Author",
                '  student_number: "123456"',
                "document:",
                "  include:",
                "    - 00_intro.md",
                "output:",
                "  directory: output",
                "  basename: example_document",
                "versioning:",
                "  strategy: semver",
                "  initial_version: 0.1.0",
                "  include_git_hash: false",
            ]
        ),
        encoding="utf-8",
    )

    def fake_render_pdf(input_file: Path, output_file: Path, **kwargs: object) -> Path:
        metadata_file = kwargs["metadata_file"]
        metadata = yaml.safe_load(Path(metadata_file).read_text(encoding="utf-8"))
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            f'{metadata["title"]}\n{metadata["student_number"]}\n',
            encoding="utf-8",
        )
        return output_file

    with (
        patch("docsmith.core.builder.render_pdf", side_effect=fake_render_pdf),
        patch("docsmith.core.builder.get_git_short_hash", return_value=None),
    ):
        result = build_document(document_root)

    output_content = result.output_path.read_text(encoding="utf-8")
    assert "Integration Metadata Example" in output_content
    assert "123456" in output_content


def test_build_document_allows_real_template_to_consume_arbitrary_metadata(
    tmp_path: Path,
) -> None:
    if shutil.which("pandoc") is None or shutil.which("xelatex") is None:
        pytest.skip("pandoc and xelatex are required for the real metadata integration test")

    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    template_root = document_root / "templates" / "metadata_probe"
    sections_dir.mkdir(parents=True)
    template_root.mkdir(parents=True)

    (sections_dir / "00_intro.md").write_text("# Intro\n\nRendered through a real template.\n", encoding="utf-8")
    (template_root / "defaults.yaml").write_text(
        "\n".join(
            [
                "from: markdown",
                "pdf-engine: xelatex",
                "standalone: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (template_root / "template.tex").write_text(
        "\n".join(
            [
                r"\documentclass{article}",
                r"\def\studentnumber{$student_number$}",
                r"\def\expectedstudentnumber{123456}",
                r"\ifx\studentnumber\expectedstudentnumber\else",
                r"\errmessage{student_number metadata was not passed to the template}",
                r"\fi",
                r"\begin{document}",
                r"Student: \studentnumber",
                r"",
                r"$body$",
                r"\end{document}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/metadata_probe",
                "metadata:",
                "  title: Real Metadata Integration Example",
                "  author: Example Author",
                '  student_number: "123456"',
                "document:",
                "  include:",
                "    - 00_intro.md",
                "output:",
                "  directory: output",
                "  basename: metadata_integration",
                "versioning:",
                "  strategy: semver",
                "  initial_version: 0.1.0",
                "  include_git_hash: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = build_document(document_root)

    assert result.output_path.exists()
    assert result.output_path.suffix == ".pdf"


def test_build_document_runs_real_pdf_cross_reference_path_with_lua_filter(
    tmp_path: Path,
) -> None:
    if shutil.which("pandoc") is None or shutil.which("xelatex") is None:
        pytest.skip("pandoc and xelatex are required for the real cross-reference integration test")

    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    template_root = document_root / "templates" / "crossref_probe"
    assets_dir = document_root / "assets" / "generated"
    sections_dir.mkdir(parents=True)
    template_root.mkdir(parents=True)
    assets_dir.mkdir(parents=True)

    (sections_dir / "00_intro.md").write_text(
        "\n".join(
            [
                "# Intro",
                "",
                "Zie @fig:registratieproces en @tbl:validatie.",
                "",
                "![Procesdiagram van het registratieproces](assets/generated/registratieproces.png){#fig:registratieproces width=40%}",
                "",
                "| ID | Requirement | MoSCoW | Imp. | Nec. | Prio. |",
                "|---|---|---:|---:|---:|---:|",
                "| FN-ETM-01 | Create sign-up events | Must | 5 | 5 | 25 |",
                "| FN-ETM-07 | Configure registration opening and closing | Should | 5 | 4 | 20 |",
                "",
                ': Prioritisation of requirements {#tbl:validatie column-widths="14,56,10,7,7,6"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    shutil.copyfile(
        Path("examples/documents/authoring_guide/assets/docsmith-diagram.png"),
        assets_dir / "registratieproces.png",
    )
    (template_root / "defaults.yaml").write_text(
        "\n".join(
            [
                "from: markdown+link_attributes+citations+pipe_tables+table_captions",
                "pdf-engine: xelatex",
                "standalone: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (template_root / "template.tex").write_text(
        "\n".join(
            [
                r"\documentclass{article}",
                r"\usepackage{graphicx}",
                r"\usepackage{longtable}",
                r"\usepackage{booktabs}",
                r"\usepackage{array}",
                r"\usepackage{calc}",
                r"\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}",
                r"\providecommand{\pandocbounded}[1]{#1}",
                r"\begin{document}",
                r"$body$",
                r"\end{document}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/crossref_probe",
                "metadata:",
                "  title: Real Cross Reference Integration Example",
                "  author: Example Author",
                "document:",
                "  include:",
                "    - 00_intro.md",
                "output:",
                "  directory: output",
                "  basename: crossref_integration",
                "versioning:",
                "  strategy: semver",
                "  initial_version: 0.1.0",
                "  include_git_hash: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    captured_commands: list[list[str]] = []

    def _capturing_build_pandoc_command(*args: object, **kwargs: object) -> list[str]:
        command = build_pandoc_command(*args, **kwargs)
        captured_commands.append(command)
        return command

    with patch(
        "docsmith.renderer.pandoc.build_pandoc_command",
        side_effect=_capturing_build_pandoc_command,
    ):
        result = build_document(document_root)

    assert result.output_path.exists()
    assert result.output_path.suffix == ".pdf"
    assert captured_commands, "Expected the real Pandoc command to be captured"
    command = captured_commands[-1]
    assert "--lua-filter" in command
    assert str(cross_reference_filter_path()) in command
    assert str(table_column_widths_filter_path()) in command


def test_build_document_runs_real_mermaid_rendering_path(
    tmp_path: Path,
) -> None:
    if (
        shutil.which("mmdc") is None
        or shutil.which("pandoc") is None
        or shutil.which("xelatex") is None
    ):
        pytest.skip(
            "mmdc, pandoc, and xelatex are required for the real Mermaid integration test"
        )

    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    template_root = document_root / "templates" / "mermaid_probe"
    diagram_source_dir = document_root / "assets" / "diagrams"
    sections_dir.mkdir(parents=True)
    template_root.mkdir(parents=True)
    diagram_source_dir.mkdir(parents=True)

    (sections_dir / "00_intro.md").write_text(
        "\n".join(
            [
                "# Intro",
                "",
                "Hieronder staat een build-managed Mermaid-diagram.",
                "",
                "![Procesdiagram](assets/generated/starter_procesdiagram.png){width=40%}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (diagram_source_dir / "starter_procesdiagram.mmd").write_text(
        "\n".join(
            [
                "flowchart TD",
                "    Start --> Controle",
                "    Controle --> Einde",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (template_root / "defaults.yaml").write_text(
        "\n".join(
            [
                "from: markdown+link_attributes",
                "pdf-engine: xelatex",
                "standalone: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (template_root / "template.tex").write_text(
        "\n".join(
            [
                r"\documentclass{article}",
                r"\usepackage{graphicx}",
                r"\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}",
                r"\providecommand{\pandocbounded}[1]{#1}",
                r"\begin{document}",
                r"$body$",
                r"\end{document}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/mermaid_probe",
                "metadata:",
                "  title: Real Mermaid Integration Example",
                "  author: Example Author",
                "document:",
                "  include:",
                "    - 00_intro.md",
                "diagrams:",
                "  - id: starter-procesdiagram",
                "    type: mermaid",
                "    source: assets/diagrams/starter_procesdiagram.mmd",
                "    output: assets/generated/starter_procesdiagram.png",
                "    format: png",
                "output:",
                "  directory: output",
                "  basename: mermaid_integration",
                "versioning:",
                "  strategy: semver",
                "  initial_version: 0.1.0",
                "  include_git_hash: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = build_document(document_root)

    assert result.output_path.exists()
    assert result.output_path.suffix == ".pdf"
    assert (
        result.build_dir / "assets" / "generated" / "starter_procesdiagram.png"
    ).exists()
