from pathlib import Path

import pytest

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

    assert config.metadata["subtitle"] == "MVP Config Fixture"
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
    assert config.metadata["title"] == "Defaults Example"
    assert config.metadata["author"] == "Example Author"


def test_load_document_config_preserves_flat_arbitrary_metadata(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Extensible Metadata Example",
                "  author: Example Author",
                '  student_number: "123456"',
                "  program: HBO-ICT",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(spec_path)

    assert config.metadata["student_number"] == "123456"
    assert config.metadata["program"] == "HBO-ICT"


def test_load_document_config_preserves_nested_metadata(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Nested Metadata Example",
                "  reviewer:",
                "    name: Dr. Example",
                "    affiliation: Neutral Institute",
                "  contributors:",
                "    - Alex",
                "    - Sam",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(spec_path)

    assert config.metadata["reviewer"]["name"] == "Dr. Example"
    assert config.metadata["contributors"] == ["Alex", "Sam"]


def test_load_document_config_supports_document_zones(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Zoned Example",
                "document:",
                "  front_matter:",
                "    - 00_preface.md",
                "  main_matter:",
                "    - 10_body.md",
                "  back_matter:",
                "    - 90_notes.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(spec_path)

    assert config.document.front_matter[0].file == "00_preface.md"
    assert config.document.main_matter[0].file == "10_body.md"
    assert config.document.back_matter[0].file == "90_notes.md"


def test_load_document_config_supports_appendices(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Appendix Example",
                "document:",
                "  main_matter:",
                "    - 10_body.md",
                "  appendices:",
                "    - 30_appendix_a.md",
                "    - 31_appendix_b.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(spec_path)

    assert config.document.main_matter[0].file == "10_body.md"
    assert [item.file for item in config.document.appendices] == [
        "30_appendix_a.md",
        "31_appendix_b.md",
    ]


def test_load_document_config_supports_ordered_front_matter_generated_toc(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Ordered TOC Example",
                "document:",
                "  front_matter:",
                "    - file: 00_preface.md",
                "    - file: 01_summary.md",
                "    - generated: toc",
                "      title: Inhoudsopgave",
                "      numbered: false",
                "      listed: true",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(spec_path)

    assert config.document.front_matter[0].file == "00_preface.md"
    assert config.document.front_matter[1].file == "01_summary.md"
    assert config.document.front_matter[2].generated == "toc"
    assert config.document.front_matter[2].title == "Inhoudsopgave"
    assert config.document.front_matter[2].numbered is False
    assert config.document.front_matter[2].listed is True


def test_load_document_config_supports_structural_bibliography(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Bibliography Example",
                "document:",
                "  bibliography:",
                "    enabled: true",
                "    title: Literature",
                "    zone: back_matter",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(spec_path)

    assert config.document.bibliography.enabled is True
    assert config.document.bibliography.title == "Literature"
    assert config.document.bibliography.zone == "back_matter"


def test_load_document_config_supports_structural_toc(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: TOC Example",
                "document:",
                "  toc:",
                "    enabled: true",
                "    title: Inhoudsopgave",
                "    zone: front_matter",
            ]
        ),
        encoding="utf-8",
    )

    config = load_document_config(spec_path)

    assert config.document.toc.enabled is True
    assert config.document.toc.title == "Inhoudsopgave"
    assert config.document.toc.zone == "front_matter"


def test_load_document_config_rejects_generated_toc_outside_front_matter(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Invalid Generated TOC Example",
                "document:",
                "  back_matter:",
                "    - generated: toc",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="document.front_matter|currently supported only"):
        load_document_config(spec_path)


def test_load_document_config_rejects_unsupported_generated_item_type(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Invalid Generated Item Example",
                "document:",
                "  front_matter:",
                "    - generated: index",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(Exception):
        load_document_config(spec_path)


def test_load_document_config_rejects_titleless_listed_toc(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  title: Invalid TOC Semantics Example",
                "document:",
                "  front_matter:",
                "    - generated: toc",
                "      title: \"\"",
                "      listed: true",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="without a title"):
        load_document_config(spec_path)


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


def test_load_document_config_rejects_non_mapping_metadata(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "metadata:",
                "  - invalid",
            ]
        ),
        encoding="utf-8",
    )

    try:
        load_document_config(spec_path)
    except Exception as exc:
        assert "metadata" in str(exc)
    else:
        raise AssertionError("Expected non-mapping metadata to fail validation")
