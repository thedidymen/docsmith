from pathlib import Path
from subprocess import CalledProcessError
import json
import shutil
import subprocess
from unittest.mock import patch
import os
import yaml

import pytest

from docsmith.config import load_document_config
from docsmith.renderer.metadata import write_runtime_metadata
from docsmith.renderer.pandoc import (
    PandocRenderError,
    build_pandoc_command,
    cross_reference_filter_path,
    render_pdf,
    table_column_widths_filter_path,
)


def test_build_pandoc_command_returns_pdf_invocation() -> None:
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))
    command = build_pandoc_command(
        Path("input.md"),
        Path("output.pdf"),
        document_root=Path("examples/documents/technical_report_demo"),
        config=config,
        template_name="../../templates/technical_report",
    )

    assert command[0] == "pandoc"
    assert command[1] == "input.md"
    assert "--defaults" in command
    assert "--resource-path" in command
    resource_path = command[command.index("--resource-path") + 1]
    resource_segments = resource_path.split(os.pathsep)
    assert str(Path("input.md").parent.resolve()) in resource_segments
    assert str(Path("examples/documents/technical_report_demo").resolve()) in resource_segments
    assert "--template" in command
    assert "-o" in command
    assert "output.pdf" in command


def test_build_pandoc_command_includes_metadata_file() -> None:
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))
    command = build_pandoc_command(
        Path("input.md"),
        Path("output.pdf"),
        document_root=Path("examples/documents/technical_report_demo"),
        config=config,
        template_name="../../templates/technical_report",
        metadata_file=Path("runtime-metadata.yaml"),
    )

    assert "--metadata-file" in command
    assert "runtime-metadata.yaml" in command


def test_build_pandoc_command_includes_bibliography_and_csl() -> None:
    config = load_document_config(Path("tests/fixtures/minimal_spec.yaml"))
    command = build_pandoc_command(
        Path("input.md"),
        Path("output.pdf"),
        document_root=Path("tests/fixtures"),
        config=config,
        template_name=str(
            Path("examples/templates/academic_thesis").resolve()
        ),
    )

    assert "--bibliography" in command
    assert str(Path("tests/fixtures/references.bib").resolve()) in command
    assert "--csl" in command
    assert str(Path("tests/fixtures/csl/apa.csl").resolve()) in command


def test_build_pandoc_command_disables_template_level_toc_for_structural_toc(
    tmp_path: Path,
) -> None:
    template_root = tmp_path / "templates" / "technical_report"
    template_root.mkdir(parents=True)
    (template_root / "template.tex").write_text(
        "\\documentclass{article}\n\\begin{document}\n$body$\n\\end{document}\n",
        encoding="utf-8",
    )
    (template_root / "defaults.yaml").write_text(
        "from: markdown\npdf-engine: xelatex\ntoc: true\n",
        encoding="utf-8",
    )
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: TOC Command Example",
                "document:",
                "  toc:",
                "    enabled: true",
                "    zone: front_matter",
            ]
        ),
        encoding="utf-8",
    )
    config = load_document_config(spec_path)

    command = build_pandoc_command(
        Path("input.md"),
        Path("output.pdf"),
        document_root=tmp_path,
        config=config,
        template_name="templates/technical_report",
    )

    assert "-M" in command
    assert "toc=false" in command


def test_build_pandoc_command_disables_template_level_toc_for_ordered_generated_toc(
    tmp_path: Path,
) -> None:
    template_root = tmp_path / "templates" / "technical_report"
    template_root.mkdir(parents=True)
    (template_root / "template.tex").write_text(
        "\\documentclass{article}\n\\begin{document}\n$body$\n\\end{document}\n",
        encoding="utf-8",
    )
    (template_root / "defaults.yaml").write_text(
        "from: markdown\npdf-engine: xelatex\ntoc: true\n",
        encoding="utf-8",
    )
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Ordered TOC Command Example",
                "document:",
                "  front_matter:",
                "    - generated: toc",
            ]
        ),
        encoding="utf-8",
    )
    config = load_document_config(spec_path)

    command = build_pandoc_command(
        Path("input.md"),
        Path("output.pdf"),
        document_root=tmp_path,
        config=config,
        template_name="templates/technical_report",
    )

    assert "-M" in command
    assert "toc=false" in command


def test_cross_reference_filter_file_exists() -> None:
    filter_path = cross_reference_filter_path()

    assert filter_path.exists()
    assert filter_path.name == "figure_table_crossrefs.lua"


def test_table_column_widths_filter_file_exists() -> None:
    filter_path = table_column_widths_filter_path()

    assert filter_path.exists()
    assert filter_path.name == "table_column_widths.lua"


def test_build_pandoc_command_includes_lua_filter_when_cross_references_are_present(
    tmp_path: Path,
) -> None:
    template_root = tmp_path / "templates" / "technical_report"
    template_root.mkdir(parents=True)
    (template_root / "template.tex").write_text(
        "\\documentclass{article}\n\\begin{document}\n$body$\n\\end{document}\n",
        encoding="utf-8",
    )
    (template_root / "defaults.yaml").write_text(
        "from: markdown\npdf-engine: xelatex\n",
        encoding="utf-8",
    )
    sections_dir = tmp_path / "sections"
    sections_dir.mkdir()
    (sections_dir / "10_body.md").write_text(
        "\n".join(
            [
                "Zie @fig:registratieproces.",
                "",
                "![Procesdiagram](assets/generated/registratieproces.png){#fig:registratieproces width=80%}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Cross Reference Command Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )
    config = load_document_config(spec_path)

    command = build_pandoc_command(
        Path("input.md"),
        Path("output.pdf"),
        document_root=tmp_path,
        config=config,
        template_name="templates/technical_report",
    )

    assert "--lua-filter" in command
    assert str(cross_reference_filter_path()) in command


def test_build_pandoc_command_only_uses_widths_filter_without_cross_reference_authoring(
    tmp_path: Path,
) -> None:
    template_root = tmp_path / "templates" / "technical_report"
    template_root.mkdir(parents=True)
    (template_root / "template.tex").write_text(
        "\\documentclass{article}\n\\begin{document}\n$body$\n\\end{document}\n",
        encoding="utf-8",
    )
    (template_root / "defaults.yaml").write_text(
        "from: markdown\npdf-engine: xelatex\n",
        encoding="utf-8",
    )
    sections_dir = tmp_path / "sections"
    sections_dir.mkdir()
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Plain Command Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )
    config = load_document_config(spec_path)

    command = build_pandoc_command(
        Path("input.md"),
        Path("output.pdf"),
        document_root=tmp_path,
        config=config,
        template_name="templates/technical_report",
    )

    filter_paths = [
        command[index + 1]
        for index, value in enumerate(command)
        if value == "--lua-filter"
    ]
    assert filter_paths == [str(table_column_widths_filter_path())]


def test_cross_reference_lua_filter_uses_latex_caption_names_and_refs(tmp_path: Path) -> None:
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc is required for the Lua filter LaTeX output test")

    input_file = tmp_path / "input.md"
    input_file.write_text(
        "\n".join(
            [
                "![Caption](examples/documents/authoring_guide/assets/docsmith-diagram.png){#fig:test width=40%}",
                "",
                "| A | B |",
                "|---|---|",
                "| 1 | 2 |",
                "",
                "Table: Tab cap {#tbl:test}",
                "",
                "See @fig:test and @tbl:test.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "pandoc",
            str(input_file),
            "-f",
            "markdown+link_attributes+citations+pipe_tables+table_captions",
            "-t",
            "latex",
            "--lua-filter",
            str(table_column_widths_filter_path()),
            "--lua-filter",
            str(cross_reference_filter_path()),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "\\caption{Caption}\\label{fig:test}" in result.stdout
    assert "\\caption{Tab cap}\\label{tbl:test}" in result.stdout
    assert "\\figurename~\\ref{fig:test}" in result.stdout
    assert "\\tablename~\\ref{tbl:test}" in result.stdout


def _pandoc_table_json(tmp_path: Path, markdown: str, *, filtered: bool = True) -> dict:
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc is required for the table column widths filter test")
    input_file = tmp_path / "table.md"
    input_file.write_text(markdown, encoding="utf-8")
    command = [
        "pandoc",
        str(input_file),
        "-f",
        "markdown+pipe_tables+table_captions",
        "-t",
        "json",
    ]
    if filtered:
        command.extend(["--lua-filter", str(table_column_widths_filter_path())])
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def _first_table(document: dict) -> dict:
    return next(block for block in document["blocks"] if block["t"] == "Table")


def test_table_without_column_widths_is_unchanged(tmp_path: Path) -> None:
    markdown = "| A | B |\n|---|---:|\n| one | 2 |\n"

    unfiltered = _pandoc_table_json(tmp_path, markdown, filtered=False)
    filtered = _pandoc_table_json(tmp_path, markdown)

    assert filtered == unfiltered


@pytest.mark.parametrize(
    ("raw_widths", "expected"),
    [
        ("20,60,20", [0.2, 0.6, 0.2]),
        ("2,8,1,1", [1 / 6, 4 / 6, 1 / 12, 1 / 12]),
        ("20,80,10,10", [1 / 6, 2 / 3, 1 / 12, 1 / 12]),
    ],
)
def test_relative_table_column_widths_are_normalized(
    tmp_path: Path,
    raw_widths: str,
    expected: list[float],
) -> None:
    columns = len(expected)
    headers = " | ".join(chr(ord("A") + index) for index in range(columns))
    markdown = (
        f"| {headers} |\n"
        f"| {' | '.join('---' for _ in range(columns))} |\n"
        f"| {' | '.join('value' for _ in range(columns))} |\n\n"
        f': Caption {{#tbl:widths column-widths="{raw_widths}"}}\n'
    )

    table = _first_table(_pandoc_table_json(tmp_path, markdown))
    attr, caption, colspecs = table["c"][:3]

    assert attr[0] == "tbl:widths"
    assert [item for item in attr[2] if item[0] == "column-widths"] == []
    assert caption is not None
    assert [spec[1]["c"] for spec in colspecs] == pytest.approx(expected)


@pytest.mark.parametrize(
    ("raw_widths", "message"),
    [
        ("20,80", "expected 3 values for 3 columns, but received 2"),
        ("20,0,80", "value 2 must be greater than zero"),
        ("20,-1,80", "value 2 must be greater than zero"),
        ("20,wide,80", "value 2 (`wide`) is not a finite number"),
        ("20,,80", "value 2 (``) is not a finite number"),
    ],
)
def test_invalid_table_column_widths_fail_clearly(
    tmp_path: Path,
    raw_widths: str,
    message: str,
) -> None:
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc is required for the table column widths filter test")
    input_file = tmp_path / "invalid.md"
    input_file.write_text(
        "| A | B | C |\n|---|---|---|\n| 1 | 2 | 3 |\n\n"
        f': Invalid {{#tbl:invalid column-widths="{raw_widths}"}}\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "pandoc",
            str(input_file),
            "-f",
            "markdown+pipe_tables+table_captions",
            "-t",
            "json",
            "--lua-filter",
            str(table_column_widths_filter_path()),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Table `tbl:invalid`: invalid `column-widths`" in result.stderr
    assert message in result.stderr


def test_width_table_keeps_caption_identifier_and_cross_reference(tmp_path: Path) -> None:
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc is required for the table column widths LaTeX test")
    input_file = tmp_path / "widths.md"
    input_file.write_text(
        "See @tbl:requirements.\n\n"
        "| ID | Requirement | Status |\n|---|---|---|\n"
        "| R-01 | A considerably longer description | Must |\n\n"
        ': Requirements {#tbl:requirements column-widths="15,70,15"}\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            "pandoc",
            str(input_file),
            "-f",
            "markdown+citations+pipe_tables+table_captions",
            "-t",
            "latex",
            "--lua-filter",
            str(table_column_widths_filter_path()),
            "--lua-filter",
            str(cross_reference_filter_path()),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "\\caption{Requirements}\\label{tbl:requirements}" in result.stdout
    assert "\\tablename~\\ref{tbl:requirements}" in result.stdout
    # Pandoc emits proportional p-columns; the descriptive column must dominate.
    assert result.stdout.count(r"\real{0.7000}") >= 1


def test_render_pdf_invokes_subprocess_with_document_local_template(tmp_path: Path) -> None:
    input_file = tmp_path / "combined.md"
    output_file = tmp_path / "output" / "report.pdf"
    input_file.write_text("# Example\n", encoding="utf-8")
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))

    with (
        patch("docsmith.renderer.pandoc.validate_pdf_dependencies", return_value=[]),
        patch("docsmith.renderer.pandoc.subprocess.run") as mock_run,
    ):
        rendered_path = render_pdf(
            input_file,
            output_file,
            config=config,
            document_root=Path("examples/documents/technical_report_demo"),
        )

    assert rendered_path == output_file
    invoked_command = mock_run.call_args.args[0]
    assert invoked_command[0] == "pandoc"
    assert str(output_file) in invoked_command
    assert mock_run.call_args.kwargs["check"] is True


def test_render_pdf_raises_clear_error_when_pandoc_is_missing(tmp_path: Path) -> None:
    input_file = tmp_path / "combined.md"
    output_file = tmp_path / "report.pdf"
    input_file.write_text("# Example\n", encoding="utf-8")
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))

    with (
        patch("docsmith.renderer.pandoc.validate_pdf_dependencies", return_value=[]),
        patch(
            "docsmith.renderer.pandoc.subprocess.run",
            side_effect=FileNotFoundError("pandoc"),
        ),
        ):
        try:
            render_pdf(
                input_file,
                output_file,
                config=config,
                document_root=Path("examples/documents/technical_report_demo"),
            )
        except PandocRenderError as exc:
            assert "Install pandoc" in str(exc)
        else:
            raise AssertionError("Expected missing pandoc executable to raise")


def test_render_pdf_raises_clear_error_on_pandoc_failure(tmp_path: Path) -> None:
    input_file = tmp_path / "combined.md"
    output_file = tmp_path / "report.pdf"
    input_file.write_text("# Example\n", encoding="utf-8")
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))

    with (
        patch("docsmith.renderer.pandoc.validate_pdf_dependencies", return_value=[]),
        patch(
            "docsmith.renderer.pandoc.subprocess.run",
            side_effect=CalledProcessError(
                returncode=1,
                cmd=["pandoc"],
                stderr="LaTeX Error",
            ),
        ),
        ):
        try:
            render_pdf(
                input_file,
                output_file,
                config=config,
                document_root=Path("examples/documents/technical_report_demo"),
            )
        except PandocRenderError as exc:
            assert "LaTeX Error" in str(exc)
        else:
            raise AssertionError("Expected pandoc failure to raise")


def test_render_pdf_raises_clear_error_when_pdf_dependencies_are_missing(tmp_path: Path) -> None:
    input_file = tmp_path / "combined.md"
    output_file = tmp_path / "report.pdf"
    input_file.write_text("# Example\n", encoding="utf-8")
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))

    with patch(
        "docsmith.renderer.pandoc.validate_pdf_dependencies",
        return_value=["pandoc", "xelatex"],
    ):
        try:
            render_pdf(
                input_file,
                output_file,
                config=config,
                document_root=Path("examples/documents/technical_report_demo"),
            )
        except PandocRenderError as exc:
            message = str(exc)
            assert "pandoc" in message
            assert "xelatex" in message
        else:
            raise AssertionError("Expected missing PDF dependencies to raise")


def test_render_pdf_raises_actionable_message_for_missing_xelatex_in_stderr(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "combined.md"
    output_file = tmp_path / "report.pdf"
    input_file.write_text("# Example\n", encoding="utf-8")
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))

    with (
        patch("docsmith.renderer.pandoc.validate_pdf_dependencies", return_value=[]),
        patch(
            "docsmith.renderer.pandoc.subprocess.run",
            side_effect=CalledProcessError(
                returncode=1,
                cmd=["pandoc"],
                stderr="xelatex not found",
            ),
        ),
        ):
        try:
            render_pdf(
                input_file,
                output_file,
                config=config,
                document_root=Path("examples/documents/technical_report_demo"),
            )
        except PandocRenderError as exc:
            assert "xelatex" in str(exc)
            assert "Install a TeX distribution" in str(exc)
        else:
            raise AssertionError("Expected missing xelatex to raise")


def test_write_runtime_metadata_serializes_special_characters_safely(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))
    config.metadata["title"] = 'Example: "Quoted"'
    config.metadata["subtitle"] = "Line one\nLine two"
    config.metadata["student_number"] = "123456"
    config.metadata["reviewer"] = {"name": "Dr. Example"}
    config.metadata["version"] = "user-version"

    output_path = write_runtime_metadata(
        build_dir,
        tmp_path,
        config,
        version="0.1.0",
        git_hash="abc1234",
    )

    content = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert content["title"] == 'Example: "Quoted"'
    assert content["subtitle"] == "Line one\nLine two"
    assert content["student_number"] == "123456"
    assert content["reviewer"]["name"] == "Dr. Example"
    assert content["version"] == "0.1.0"
    assert content["git_hash"] == "abc1234"
