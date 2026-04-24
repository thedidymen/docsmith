from pathlib import Path

import pytest

from docsmith.config import load_document_config
from docsmith.scaffold import (
    ScaffoldError,
    initialize_document_scaffold,
    initialize_template_scaffold,
)
from docsmith.templates.registry import validate_template


def test_initialize_document_scaffold_creates_expected_structure(tmp_path: Path) -> None:
    target_dir = tmp_path / "starter-document"

    result = initialize_document_scaffold(target_dir)

    assert result.kind == "document"
    assert (target_dir / "spec.yaml").exists()
    assert (target_dir / "references.bib").exists()
    assert (target_dir / "csl" / "apa.csl").exists()
    assert (target_dir / "assets" / "images").is_dir()
    assert (target_dir / "sections" / "00_intro.md").exists()
    assert (target_dir / "sections" / "01_body.md").exists()
    assert (target_dir / "sections" / "30_appendix.md").exists()
    assert (target_dir / "README.md").exists()


def test_initialize_document_scaffold_generates_loadable_spec(tmp_path: Path) -> None:
    target_dir = tmp_path / "neutral-project"
    initialize_document_scaffold(target_dir)

    config = load_document_config(target_dir / "spec.yaml")

    assert config.project.slug == "neutral_project"
    assert config.project.template == "templates/default"
    assert config.document.include == []
    assert config.document.front_matter[0].generated == "toc"
    assert config.document.front_matter[0].title == "Contents"
    assert config.document.front_matter[0].numbered is False
    assert config.document.front_matter[0].listed is True
    assert [item.file for item in config.document.main_matter] == [
        "00_intro.md",
        "01_body.md",
    ]
    assert [item.file for item in config.document.appendices] == ["30_appendix.md"]
    assert config.output.formats == ["pdf"]
    assert config.versioning.initial_version == "0.1.0"


def test_initialize_template_scaffold_creates_expected_structure(tmp_path: Path) -> None:
    target_dir = tmp_path / "starter-template"

    result = initialize_template_scaffold(target_dir)

    assert result.kind == "template"
    assert (target_dir / "template.tex").exists()
    assert (target_dir / "defaults.yaml").exists()
    assert (target_dir / "metadata.yaml").exists()
    assert (target_dir / "README.md").exists()
    assert (target_dir / "partials" / "titlepage.tex").exists()
    assert (target_dir / "partials" / "before-body.tex").exists()
    assert (target_dir / "partials" / "after-body.tex").exists()


def test_initialize_template_scaffold_creates_valid_template_root(tmp_path: Path) -> None:
    target_dir = tmp_path / "starter-template"
    initialize_template_scaffold(target_dir)

    validated = validate_template(".", target_dir)

    assert validated == target_dir.resolve()
    defaults = (target_dir / "defaults.yaml").read_text(encoding="utf-8")
    assert "toc: false" in defaults


@pytest.mark.parametrize(
    "creator",
    [initialize_document_scaffold, initialize_template_scaffold],
)
def test_initialize_scaffold_rejects_non_empty_target_directory(
    tmp_path: Path,
    creator,
) -> None:
    target_dir = tmp_path / "existing"
    target_dir.mkdir()
    (target_dir / "existing.txt").write_text("present\n", encoding="utf-8")

    with pytest.raises(ScaffoldError, match="already exists and is not empty"):
        creator(target_dir)


def test_initialize_scaffold_rejects_target_file(tmp_path: Path) -> None:
    target_path = tmp_path / "existing.txt"
    target_path.write_text("present\n", encoding="utf-8")

    with pytest.raises(ScaffoldError, match="is not a directory"):
        initialize_document_scaffold(target_path)
