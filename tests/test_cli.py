from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("typer")
from typer.testing import CliRunner

from docsmith.cli import app
from docsmith.core.builder import BuildResult
from docsmith.versioning.resolver import VersionResolution


runner = CliRunner()


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


def test_build_command_prints_final_output_path() -> None:
    document_root = Path("examples/documents/technical_report_demo").resolve()
    build_dir = document_root / "build"
    output_path = document_root / "output" / "technical_report_demo_v0.1.0.pdf"
    result_payload = BuildResult(
        document_root=document_root,
        build_dir=build_dir,
        assembled_markdown_path=build_dir / "combined.md",
        metadata_path=build_dir / "runtime-metadata.yaml",
        output_path=output_path,
        version_info=VersionResolution(
            semantic_version="0.1.0",
            previous_version=None,
            fingerprint_changed=False,
            bump_applied=None,
            git_hash=None,
        ),
        state_path=build_dir / ".docsmith-state.json",
    )

    with patch("docsmith.cli.build_document", return_value=result_payload):
        result = runner.invoke(app, ["build", "examples/documents/technical_report_demo"])

    assert result.exit_code == 0
    assert "No content changes detected since last build." in result.stdout
    assert "Version kept: 0.1.0" in result.stdout
    assert f"Built: {output_path}" in result.stdout


def test_build_command_passes_bump_override_flags() -> None:
    document_root = Path("examples/documents/technical_report_demo").resolve()
    build_dir = document_root / "build"
    output_path = document_root / "output" / "technical_report_demo_v0.1.1.pdf"
    result_payload = BuildResult(
        document_root=document_root,
        build_dir=build_dir,
        assembled_markdown_path=build_dir / "combined.md",
        metadata_path=build_dir / "runtime-metadata.yaml",
        output_path=output_path,
        version_info=VersionResolution(
            semantic_version="0.1.1",
            previous_version="0.1.0",
            fingerprint_changed=True,
            bump_applied="patch",
            git_hash="abc1234",
        ),
        state_path=build_dir / ".docsmith-state.json",
    )

    with patch("docsmith.cli.build_document", return_value=result_payload) as mock_build:
        result = runner.invoke(
            app,
            ["build", "examples/documents/technical_report_demo", "--bump", "patch", "--no-bump"],
        )

    assert result.exit_code == 0
    assert mock_build.call_args.kwargs == {"bump": "patch", "no_bump": True}
    assert "Version bumped: 0.1.0 -> 0.1.1" in result.stdout
    assert "Git hash: abc1234" in result.stdout


def test_validate_command_prints_human_readable_success_report() -> None:
    with patch("docsmith.core.validation.validate_pdf_dependencies", return_value=[]):
        result = runner.invoke(app, ["validate", "examples/documents/technical_report_demo"])

    assert result.exit_code == 0
    assert "Validation results for" in result.stdout
    assert "[PASS] spec.yaml loading:" in result.stdout
    assert "Validation succeeded." in result.stdout


def test_validate_command_returns_non_zero_for_invalid_document(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    document_root.mkdir()
    _create_template(document_root)
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Invalid Document",
                "  author: Example Author",
                "document:",
                "  include:",
                "    - missing.md",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(document_root)])

    assert result.exit_code == 1
    assert "[FAIL] included markdown files existence:" in result.stdout
    assert "Validation failed." in result.stdout
