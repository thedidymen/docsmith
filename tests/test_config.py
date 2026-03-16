from pathlib import Path

from docsmith.config import load_document_config


def test_load_document_config_from_example() -> None:
    spec_path = Path("examples/documents/technical_report_demo/spec.yaml")
    config = load_document_config(spec_path)

    assert config.project.template == "../../templates/technical_report"
    assert config.output.basename == "technical_report_demo"


def test_load_document_config_from_authoring_guide_example() -> None:
    spec_path = Path("examples/documents/authoring_guide/spec.yaml")
    config = load_document_config(spec_path)

    assert config.project.template == "../../templates/academic_thesis"
    assert config.output.basename == "docsmith_authoring_guide"
    assert config.document.include[0] == "00_existing_content.md"


def test_load_document_config_from_architecture_example() -> None:
    spec_path = Path("examples/documents/docsmith_architecture/spec.yaml")
    config = load_document_config(spec_path)

    assert config.project.template == "../../templates/technical_report"
    assert config.output.basename == "docsmith_architecture"
    assert config.document.include[0] == "00_scope_and_goals.md"


def test_load_document_config_for_mvp_sections() -> None:
    spec_path = Path("tests/fixtures/minimal_spec.yaml")
    config = load_document_config(spec_path)

    assert config.metadata.subtitle == "MVP Config Fixture"
    assert config.document.include == ["00_intro.md", "10_body.md"]
    assert config.document.appendix_marker == "<!-- APPENDIX -->"
    assert config.citations.bibliography == "references.bib"
    assert config.citations.csl == "csl/apa.csl"
    assert config.output.formats == ["pdf", "docx"]
    assert config.versioning.strategy == "semver"
    assert config.versioning.initial_version == "0.2.0"


def test_load_document_config_uses_defaults_for_missing_sections(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Defaults Example",
                "  author: Example Author",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(spec_path)

    assert config.document.input_root == "sections"
    assert config.output.formats == ["pdf"]
    assert config.versioning.include_git_hash is True


def test_load_document_config_accepts_legacy_current_version_field(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Legacy Version Example",
                "  author: Example Author",
                "versioning:",
                "  current_version: 1.2.3",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(spec_path)

    assert config.versioning.initial_version == "1.2.3"


def test_load_document_config_accepts_top_level_template_path_mapping(
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "template:",
                "  path: templates/academic_thesis",
                "metadata:",
                "  title: Template Path Example",
                "  author: Example Author",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(spec_path)

    assert config.project.template == "templates/academic_thesis"


def test_load_document_config_rejects_unsupported_output_format(
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Invalid Format Example",
                "  author: Example Author",
                "output:",
                "  formats:",
                "    - html",
            ]
        ),
        encoding="utf-8",
    )

    try:
        load_document_config(spec_path)
    except Exception as exc:
        message = str(exc)
        assert "formats" in message or "html" in message
    else:
        raise AssertionError("Expected invalid output format to fail validation")
