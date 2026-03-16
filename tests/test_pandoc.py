from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import patch
import os

from docsmith.config import load_document_config
from docsmith.renderer.metadata import write_runtime_metadata
from docsmith.renderer.pandoc import (
    PandocRenderError,
    build_pandoc_command,
    render_pdf,
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
    config.metadata.title = 'Example: "Quoted"'
    config.metadata.subtitle = "Line one\nLine two"

    output_path = write_runtime_metadata(
        build_dir,
        tmp_path,
        config,
        version="0.1.0",
        git_hash="abc1234",
    )

    content = output_path.read_text(encoding="utf-8")
    assert "title:" in content
    assert "Line one" in content
    assert "git_hash: abc1234" in content
