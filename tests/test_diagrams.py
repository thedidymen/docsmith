from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from docsmith.config import load_document_config
from docsmith.renderer.diagrams import (
    DiagramRenderError,
    build_managed_diagram_output_path,
    diagram_renderer_code_path,
    render_declared_diagrams,
)


def _create_document_with_declared_diagram(tmp_path: Path) -> tuple[Path, object]:
    document_root = tmp_path / "document"
    diagram_dir = document_root / "assets" / "diagrams"
    diagram_dir.mkdir(parents=True)
    (diagram_dir / "starter_procesdiagram.mmd").write_text("graph TD\nA-->B\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Diagram Build Example",
                "  author: Example Author",
                "diagrams:",
                "  - id: starter-procesdiagram",
                "    type: mermaid",
                "    source: assets/diagrams/starter_procesdiagram.mmd",
                "    output: assets/generated/starter_procesdiagram.png",
                "    format: png",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return document_root, load_document_config(document_root / "spec.yaml")


def test_build_managed_diagram_output_path_maps_declared_output_under_build_dir(
    tmp_path: Path,
) -> None:
    build_dir = tmp_path / "document" / "build"

    output_path = build_managed_diagram_output_path(
        build_dir,
        "assets/generated/starter_procesdiagram.png",
    )

    assert output_path == build_dir.resolve() / "assets" / "generated" / "starter_procesdiagram.png"


def test_build_managed_diagram_output_path_rejects_paths_outside_build_dir(
    tmp_path: Path,
) -> None:
    build_dir = tmp_path / "document" / "build"

    with pytest.raises(DiagramRenderError, match="must stay within the document build directory"):
        build_managed_diagram_output_path(build_dir, "../outside.png")


def test_render_declared_diagrams_invokes_mmdc_with_build_managed_output(tmp_path: Path) -> None:
    document_root, config = _create_document_with_declared_diagram(tmp_path)
    build_dir = document_root / "build"

    with (
        patch("docsmith.renderer.diagrams.shutil.which", return_value="/usr/local/bin/mmdc"),
        patch("docsmith.renderer.diagrams.subprocess.run") as mock_run,
    ):
        rendered = render_declared_diagrams(document_root, build_dir, config)

    assert len(rendered) == 1
    assert rendered[0].output_path == build_dir / "assets" / "generated" / "starter_procesdiagram.png"
    assert rendered[0].source_path == document_root / "assets" / "diagrams" / "starter_procesdiagram.mmd"
    mock_run.assert_called_once()
    command = mock_run.call_args.args[0]
    assert command == [
        "/usr/local/bin/mmdc",
        "-i",
        str(document_root / "assets" / "diagrams" / "starter_procesdiagram.mmd"),
        "-o",
        str(build_dir / "assets" / "generated" / "starter_procesdiagram.png"),
    ]


def test_render_declared_diagrams_skips_subprocess_when_no_diagrams(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    document_root.mkdir()
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: No Diagram Example",
                "  author: Example Author",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config = load_document_config(document_root / "spec.yaml")

    with patch("docsmith.renderer.diagrams.subprocess.run") as mock_run:
        rendered = render_declared_diagrams(document_root, document_root / "build", config)

    assert rendered == []
    mock_run.assert_not_called()


def test_render_declared_diagrams_fails_clearly_when_mmdc_is_missing(tmp_path: Path) -> None:
    document_root, config = _create_document_with_declared_diagram(tmp_path)

    with (
        patch("docsmith.renderer.diagrams.shutil.which", return_value=None),
        pytest.raises(DiagramRenderError, match="`mmdc` is not available on PATH"),
    ):
        render_declared_diagrams(document_root, document_root / "build", config)


def test_render_declared_diagrams_surfaces_renderer_failure_context(tmp_path: Path) -> None:
    document_root, config = _create_document_with_declared_diagram(tmp_path)

    with (
        patch("docsmith.renderer.diagrams.shutil.which", return_value="/usr/local/bin/mmdc"),
        patch(
            "docsmith.renderer.diagrams.subprocess.run",
            side_effect=subprocess.CalledProcessError(
                1,
                ["mmdc"],
                stderr="Parse error on line 2",
                output="Attempted Mermaid render",
            ),
        ),
        pytest.raises(DiagramRenderError, match="Parse error on line 2"),
    ):
        render_declared_diagrams(document_root, document_root / "build", config)


def test_diagram_renderer_code_path_points_to_engine_renderer() -> None:
    path = diagram_renderer_code_path()

    assert path.exists()
    assert path.name == "diagrams.py"
