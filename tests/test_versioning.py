import json
from pathlib import Path
from unittest.mock import patch

from docsmith.config import load_document_config
from docsmith.renderer.diagrams import diagram_renderer_code_path
from docsmith.versioning.fingerprint import collect_fingerprint_inputs, compute_build_fingerprint
from docsmith.versioning.git import get_git_short_hash
from docsmith.versioning.resolver import (
    build_output_filename,
    bump_semantic_version,
    resolve_output_filename,
    resolve_output_path,
    resolve_semantic_version,
    resolve_version_string,
)
from docsmith.versioning.state import load_build_state, save_build_state, state_file_path


def test_build_output_filename_without_git_hash() -> None:
    filename = build_output_filename("report", "0.1.0", "pdf")

    assert filename == "report_v0.1.0.pdf"


def test_build_output_filename_with_git_hash_and_collision_suffix() -> None:
    filename = build_output_filename(
        "report",
        "0.1.0",
        ".pdf",
        git_hash="abc1234",
        collision_index=2,
    )

    assert filename == "report_v0.1.0_abc1234_02.pdf"


def test_resolve_version_string_for_semver_uses_initial_version() -> None:
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))

    assert resolve_version_string(config) == "0.1.0"


def test_bump_semantic_version_supports_patch_minor_and_major() -> None:
    assert bump_semantic_version("1.2.3", "patch") == "1.2.4"
    assert bump_semantic_version("1.2.3", "minor") == "1.3.0"
    assert bump_semantic_version("1.2.3", "major") == "2.0.0"


def test_resolve_semantic_version_keeps_version_when_fingerprint_is_unchanged(
    tmp_path: Path,
) -> None:
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))
    build_dir = tmp_path / "build"
    save_build_state(
        build_dir,
        current_version="0.1.0",
        fingerprint="same-fingerprint",
        git_hash="abc1234",
    )

    state = load_build_state(build_dir)
    resolution = resolve_semantic_version(
        config,
        fingerprint="same-fingerprint",
        prior_state=state,
    )

    assert resolution.semantic_version == "0.1.0"
    assert resolution.bump_applied is None
    assert resolution.fingerprint_changed is False


def test_resolve_semantic_version_auto_bumps_patch_when_fingerprint_changes(
    tmp_path: Path,
) -> None:
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))
    build_dir = tmp_path / "build"
    save_build_state(
        build_dir,
        current_version="0.1.0",
        fingerprint="old-fingerprint",
        git_hash=None,
    )

    state = load_build_state(build_dir)
    resolution = resolve_semantic_version(
        config,
        fingerprint="new-fingerprint",
        prior_state=state,
    )

    assert resolution.semantic_version == "0.1.1"
    assert resolution.bump_applied == "patch"
    assert resolution.fingerprint_changed is True


def test_resolve_semantic_version_supports_explicit_override_and_no_bump(
    tmp_path: Path,
) -> None:
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))
    build_dir = tmp_path / "build"
    save_build_state(
        build_dir,
        current_version="0.1.0",
        fingerprint="old-fingerprint",
        git_hash=None,
    )
    state = load_build_state(build_dir)

    explicit = resolve_semantic_version(
        config,
        fingerprint="new-fingerprint",
        prior_state=state,
        bump="minor",
    )
    disabled = resolve_semantic_version(
        config,
        fingerprint="new-fingerprint",
        prior_state=state,
        no_bump=True,
    )

    assert explicit.semantic_version == "0.2.0"
    assert explicit.bump_applied == "minor"
    assert disabled.semantic_version == "0.1.0"
    assert disabled.bump_applied is None


def test_resolve_output_filename_includes_git_hash_when_available() -> None:
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))
    config.versioning.include_git_hash = True

    filename = resolve_output_filename(
        Path("."),
        config,
        "pdf",
        version="0.1.0",
        git_hash="abc1234",
    )

    assert filename == "technical_report_demo_v0.1.0_abc1234.pdf"


def test_resolve_output_filename_falls_back_outside_git() -> None:
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))
    config.versioning.include_git_hash = True

    with patch("docsmith.versioning.resolver.get_git_short_hash", return_value=None):
        filename = resolve_output_filename(
            Path("."),
            config,
            "pdf",
            version="0.1.0",
        )

    assert filename == "technical_report_demo_v0.1.0.pdf"


def test_resolve_output_path_uses_collision_suffix_when_needed(tmp_path: Path) -> None:
    config = load_document_config(Path("examples/documents/technical_report_demo/spec.yaml"))
    document_root = tmp_path / "document"
    output_dir = document_root / "output"
    output_dir.mkdir(parents=True)
    (output_dir / "technical_report_demo_v0.1.0.pdf").write_text("existing\n", encoding="utf-8")

    output_path = resolve_output_path(
        document_root,
        config,
        "pdf",
        version="0.1.0",
        git_hash=None,
    )

    assert output_path.name == "technical_report_demo_v0.1.0_01.pdf"


def test_compute_build_fingerprint_changes_when_spec_or_template_changes(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    template_root = document_root / "templates"
    sections_dir.mkdir(parents=True)
    (template_root / "technical_report").mkdir(parents=True)
    (template_root / "technical_report" / "template.tex").write_text(
        "version one\n",
        encoding="utf-8",
    )
    (template_root / "technical_report" / "defaults.yaml").write_text(
        "pdf-engine: xelatex\n",
        encoding="utf-8",
    )
    (template_root / "academic_thesis").mkdir(parents=True)
    (template_root / "academic_thesis" / "template.tex").write_text(
        "version two\n",
        encoding="utf-8",
    )
    (template_root / "academic_thesis" / "defaults.yaml").write_text(
        "pdf-engine: xelatex\n",
        encoding="utf-8",
    )
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Example",
                "  author: Example Author",
            ]
        ),
        encoding="utf-8",
    )
    config = load_document_config(document_root / "spec.yaml")

    original = compute_build_fingerprint(document_root, config)

    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/academic_thesis",
                "metadata:",
                "  title: Example",
                "  author: Example Author",
            ]
        ),
        encoding="utf-8",
    )
    updated_config = load_document_config(document_root / "spec.yaml")
    changed = compute_build_fingerprint(document_root, updated_config)

    assert changed != original


def test_collect_fingerprint_inputs_includes_cross_reference_filter_when_used(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    template_root = document_root / "templates" / "technical_report"
    sections_dir.mkdir(parents=True)
    template_root.mkdir(parents=True)
    (template_root / "template.tex").write_text("template\n", encoding="utf-8")
    (template_root / "defaults.yaml").write_text("pdf-engine: xelatex\n", encoding="utf-8")
    (sections_dir / "10_body.md").write_text(
        "\n".join(
            [
                "Zie @fig:registratieproces.",
                "",
                "![Procesdiagram](diagram.png){#fig:registratieproces}",
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
                "  title: Cross Reference Fingerprint Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )
    config = load_document_config(document_root / "spec.yaml")

    inputs = collect_fingerprint_inputs(document_root, config)

    assert any(
        fingerprint_input.relative_key
        == "docsmith/renderer/filters/figure_table_crossrefs.lua"
        for fingerprint_input in inputs
    )


def test_collect_fingerprint_inputs_skips_cross_reference_filter_without_authoring(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    template_root = document_root / "templates" / "technical_report"
    sections_dir.mkdir(parents=True)
    template_root.mkdir(parents=True)
    (template_root / "template.tex").write_text("template\n", encoding="utf-8")
    (template_root / "defaults.yaml").write_text("pdf-engine: xelatex\n", encoding="utf-8")
    (sections_dir / "10_body.md").write_text("# Body\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Plain Fingerprint Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
            ]
        ),
        encoding="utf-8",
    )
    config = load_document_config(document_root / "spec.yaml")

    inputs = collect_fingerprint_inputs(document_root, config)

    assert all(
        fingerprint_input.relative_key
        != "docsmith/renderer/filters/figure_table_crossrefs.lua"
        for fingerprint_input in inputs
    )


def test_collect_fingerprint_inputs_includes_declared_diagram_sources(tmp_path: Path) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    diagram_dir = document_root / "assets" / "diagrams"
    template_root = document_root / "templates" / "technical_report"
    sections_dir.mkdir(parents=True)
    diagram_dir.mkdir(parents=True)
    template_root.mkdir(parents=True)
    (template_root / "template.tex").write_text("template\n", encoding="utf-8")
    (template_root / "defaults.yaml").write_text("pdf-engine: xelatex\n", encoding="utf-8")
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    (diagram_dir / "starter_procesdiagram.mmd").write_text("graph TD\nA-->B\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Diagram Fingerprint Example",
                "document:",
                "  include:",
                "    - 00_intro.md",
                "diagrams:",
                "  - id: starter-procesdiagram",
                "    type: mermaid",
                "    source: assets/diagrams/starter_procesdiagram.mmd",
                "    output: assets/generated/starter_procesdiagram.png",
                "    format: png",
            ]
        ),
        encoding="utf-8",
    )
    config = load_document_config(document_root / "spec.yaml")

    inputs = collect_fingerprint_inputs(document_root, config)

    assert any(
        fingerprint_input.label == "diagram_source"
        and fingerprint_input.relative_key == "assets/diagrams/starter_procesdiagram.mmd"
        for fingerprint_input in inputs
    )


def test_collect_fingerprint_inputs_includes_diagram_renderer_code_when_diagrams_are_declared(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    diagram_dir = document_root / "assets" / "diagrams"
    template_root = document_root / "templates" / "technical_report"
    sections_dir.mkdir(parents=True)
    diagram_dir.mkdir(parents=True)
    template_root.mkdir(parents=True)
    (template_root / "template.tex").write_text("template\n", encoding="utf-8")
    (template_root / "defaults.yaml").write_text("pdf-engine: xelatex\n", encoding="utf-8")
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    (diagram_dir / "starter_procesdiagram.mmd").write_text("graph TD\nA-->B\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Diagram Fingerprint Example",
                "document:",
                "  include:",
                "    - 00_intro.md",
                "diagrams:",
                "  - id: starter-procesdiagram",
                "    type: mermaid",
                "    source: assets/diagrams/starter_procesdiagram.mmd",
                "    output: assets/generated/starter_procesdiagram.png",
                "    format: png",
            ]
        ),
        encoding="utf-8",
    )
    config = load_document_config(document_root / "spec.yaml")

    inputs = collect_fingerprint_inputs(document_root, config)

    assert any(
        fingerprint_input.label == "diagram_renderer"
        and fingerprint_input.path == diagram_renderer_code_path()
        and fingerprint_input.relative_key == "docsmith/renderer/diagrams.py"
        for fingerprint_input in inputs
    )


def test_compute_build_fingerprint_changes_when_declared_diagram_source_changes(
    tmp_path: Path,
) -> None:
    document_root = tmp_path / "document"
    sections_dir = document_root / "sections"
    diagram_dir = document_root / "assets" / "diagrams"
    template_root = document_root / "templates" / "technical_report"
    sections_dir.mkdir(parents=True)
    diagram_dir.mkdir(parents=True)
    template_root.mkdir(parents=True)
    (template_root / "template.tex").write_text("template\n", encoding="utf-8")
    (template_root / "defaults.yaml").write_text("pdf-engine: xelatex\n", encoding="utf-8")
    (sections_dir / "00_intro.md").write_text("# Intro\n", encoding="utf-8")
    diagram_path = diagram_dir / "starter_procesdiagram.mmd"
    diagram_path.write_text("graph TD\nA-->B\n", encoding="utf-8")
    (document_root / "spec.yaml").write_text(
        "\n".join(
            [
                "project:",
                "  template: templates/technical_report",
                "metadata:",
                "  title: Diagram Fingerprint Change Example",
                "document:",
                "  include:",
                "    - 00_intro.md",
                "diagrams:",
                "  - id: starter-procesdiagram",
                "    type: mermaid",
                "    source: assets/diagrams/starter_procesdiagram.mmd",
                "    output: assets/generated/starter_procesdiagram.png",
                "    format: png",
            ]
        ),
        encoding="utf-8",
    )
    config = load_document_config(document_root / "spec.yaml")

    original = compute_build_fingerprint(document_root, config)
    diagram_path.write_text("graph TD\nA-->C\n", encoding="utf-8")
    changed = compute_build_fingerprint(document_root, config)

    assert changed != original


def test_state_file_persistence_and_reload(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    path = save_build_state(
        build_dir,
        current_version="0.1.2",
        fingerprint="fingerprint",
        git_hash=None,
    )

    loaded = load_build_state(build_dir)

    assert path == state_file_path(build_dir)
    assert loaded is not None
    assert loaded.current_version == "0.1.2"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["last_fingerprint"] == "fingerprint"


def test_get_git_short_hash_returns_none_when_git_is_unavailable() -> None:
    with patch("docsmith.versioning.git.subprocess.run", side_effect=FileNotFoundError):
        git_hash = get_git_short_hash(Path("."))

    assert git_hash is None
