"""Configuration loading and validation for Docsmith."""

from __future__ import annotations

from dataclasses import MISSING, dataclass, field, fields
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, get_args, get_origin, get_type_hints

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only in bare environments.
    yaml = None

try:
    from pydantic import BaseModel, ConfigDict, Field
except ModuleNotFoundError:  # pragma: no cover - exercised only in bare environments.
    class BaseModel:
        """Minimal fallback for environments without Pydantic."""

        def __init_subclass__(cls, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            dataclass(cls)

        @classmethod
        def model_validate(cls, data: dict[str, Any]) -> "BaseModel":
            values: dict[str, Any] = {}
            type_hints = get_type_hints(cls)
            for item in fields(cls):
                if item.name in data:
                    raw_value = data[item.name]
                elif item.default is not MISSING:
                    raw_value = item.default
                elif item.default_factory is not MISSING:  # type: ignore[attr-defined]
                    raw_value = item.default_factory()  # type: ignore[misc]
                else:
                    raise ValueError(f"Missing required field: {item.name}")

                field_type = type_hints.get(item.name, item.type)
                origin = get_origin(field_type)
                if origin is Literal:
                    allowed_values = get_args(field_type)
                    if raw_value not in allowed_values:
                        raise ValueError(
                            f"Invalid value for {item.name}: {raw_value!r}. "
                            f"Expected one of {allowed_values!r}."
                        )
                    values[item.name] = raw_value
                elif origin is list and isinstance(raw_value, list):
                    inner_type = get_args(field_type)[0]
                    if get_origin(inner_type) is Literal:
                        allowed_values = get_args(inner_type)
                        invalid_values = [
                            value for value in raw_value if value not in allowed_values
                        ]
                        if invalid_values:
                            raise ValueError(
                                f"Invalid values for {item.name}: {invalid_values!r}. "
                                f"Expected values from {allowed_values!r}."
                            )
                    elif hasattr(inner_type, "model_validate"):
                        values[item.name] = [
                            inner_type.model_validate(value) if isinstance(value, dict) else value
                            for value in raw_value
                        ]
                    else:
                        values[item.name] = raw_value
                elif hasattr(field_type, "model_validate") and isinstance(raw_value, dict):
                    values[item.name] = field_type.model_validate(raw_value)
                else:
                    values[item.name] = raw_value

            return cls(**values)

    def Field(  # type: ignore[misc]
        default: Any = MISSING,
        *,
        default_factory: Any = MISSING,
    ) -> Any:
        """Minimal fallback for Pydantic's Field helper."""
        if default_factory is not MISSING:
            return field(default_factory=default_factory)
        if default is not MISSING:
            return field(default=default)
        return field()

    ConfigDict = dict  # type: ignore[assignment]


class ProjectConfig(BaseModel):
    """Top-level project settings."""

    if "ConfigDict" in globals():
        model_config = ConfigDict(extra="forbid")

    slug: str = "document"
    template: str = "templates/academic_thesis"


def default_metadata() -> dict[str, Any]:
    """Return backwards-compatible default metadata."""
    return {
        "title": "Untitled Document",
        "subtitle": None,
        "author": "Unknown Author",
        "date": None,
    }


class DocumentConfig(BaseModel):
    """Document source configuration."""

    if "ConfigDict" in globals():
        model_config = ConfigDict(extra="forbid")

    input_root: str = "sections"
    include: list[str] = Field(default_factory=list)
    front_matter: list["DocumentZoneItemConfig"] = Field(default_factory=list)
    main_matter: list["DocumentZoneItemConfig"] = Field(default_factory=list)
    back_matter: list["DocumentZoneItemConfig"] = Field(default_factory=list)
    appendices: list["DocumentZoneItemConfig"] = Field(default_factory=list)
    bibliography: "DocumentBibliographyConfig" = Field(
        default_factory=lambda: DocumentBibliographyConfig()
    )
    toc: "DocumentTocConfig" = Field(default_factory=lambda: DocumentTocConfig())
    appendix_marker: str = "<!-- APPENDIX -->"


class DocumentBibliographyConfig(BaseModel):
    """Bibliography placement configuration."""

    if "ConfigDict" in globals():
        model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    title: str = "Bibliography"
    zone: str = "back_matter"


class DocumentZoneItemConfig(BaseModel):
    """Ordered structural item inside a document zone."""

    if "ConfigDict" in globals():
        model_config = ConfigDict(extra="forbid")

    file: str | None = None
    generated: Literal["toc"] | None = None
    title: str = "Contents"
    numbered: bool = False
    listed: bool = True


class DocumentTocConfig(BaseModel):
    """Table-of-contents placement configuration."""

    if "ConfigDict" in globals():
        model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    title: str = "Contents"
    zone: str = "front_matter"


class CitationsConfig(BaseModel):
    """Citation-related configuration for Pandoc."""

    if "ConfigDict" in globals():
        model_config = ConfigDict(extra="forbid")

    bibliography: str | None = None
    csl: str | None = None


class DiagramConfig(BaseModel):
    """Diagram rendering declaration."""

    if "ConfigDict" in globals():
        model_config = ConfigDict(extra="forbid")

    id: str
    type: Literal["mermaid"]
    source: str
    output: str
    format: Literal["png"]


class OutputConfig(BaseModel):
    """Output configuration."""

    if "ConfigDict" in globals():
        model_config = ConfigDict(extra="forbid")

    directory: str = "output"
    basename: str = "document"
    formats: list[Literal["pdf", "docx"]] = Field(default_factory=lambda: ["pdf"])


class VersioningConfig(BaseModel):
    """Output versioning configuration."""

    if "ConfigDict" in globals():
        model_config = ConfigDict(extra="forbid")

    strategy: Literal["semver", "timestamp"] = "semver"
    initial_version: str = "0.1.0"
    include_git_hash: bool = True


class DocsmithConfig(BaseModel):
    """Validated Docsmith document specification."""

    if "ConfigDict" in globals():
        model_config = ConfigDict(extra="forbid")

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    metadata: dict[str, Any] = Field(default_factory=default_metadata)
    document: DocumentConfig = Field(default_factory=DocumentConfig)
    citations: CitationsConfig = Field(default_factory=CitationsConfig)
    diagrams: list[DiagramConfig] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)
    versioning: VersioningConfig = Field(default_factory=VersioningConfig)


def _parse_scalar(value: str) -> Any:
    """Parse a minimal YAML scalar."""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"

    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _simple_yaml_load(text: str) -> dict[str, Any]:
    """Parse a restricted YAML subset used by the MVP example files."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any] | list[Any]]] = [(-1, root)]
    pending_key: str | None = None

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        while indent <= stack[-1][0] and len(stack) > 1:
            stack.pop()

        current = stack[-1][1]

        if line.startswith("- "):
            item_text = line[2:].strip()
            if not isinstance(current, list):
                if not isinstance(stack[-2][1], dict) or pending_key is None:
                    raise ValueError("Invalid YAML structure")
                current_list: list[Any] = []
                stack[-2][1][pending_key] = current_list
                stack[-1] = (stack[-1][0], current_list)
                current = current_list

            if ": " in item_text:
                item_key, _, item_value = item_text.partition(":")
                item = {item_key.strip(): _parse_scalar(item_value.strip())}
                current.append(item)
                pending_key = item_key.strip()
                stack.append((indent + 2, item))
            else:
                current.append(_parse_scalar(item_text))
            continue

        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        if not isinstance(current, dict):
            raise ValueError("Invalid YAML mapping structure")

        if value == "":
            current[key] = {}
            pending_key = key
            stack.append((indent, current[key]))
            continue

        current[key] = _parse_scalar(value)
        pending_key = key

    return root


ZONE_NAMES = ("front_matter", "main_matter", "back_matter", "appendices")


def _normalize_zone_items(raw_config: dict[str, Any]) -> None:
    """Normalize zone items so authored files and generated items share one shape."""
    document = raw_config.get("document")
    if not isinstance(document, dict):
        return

    for zone_name in ZONE_NAMES:
        items = document.get(zone_name)
        if not isinstance(items, list):
            continue

        normalized_items: list[dict[str, Any]] = []
        for item in items:
            if isinstance(item, str):
                normalized_items.append({"file": item})
                continue
            if isinstance(item, Mapping):
                normalized_items.append(dict(item))
                continue
            raise TypeError(
                f"`document.{zone_name}` items must be file paths or mappings, got {type(item).__name__}."
            )

        document[zone_name] = normalized_items


def _validate_zone_item_config(config: DocsmithConfig) -> None:
    """Validate mixed zone items and legacy/new TOC combinations."""
    generated_toc_count = 0

    for zone_name in ZONE_NAMES:
        zone_items = getattr(config.document, zone_name)
        for item in zone_items:
            if item.file and item.generated:
                raise ValueError(
                    f"`document.{zone_name}` items must define either `file` or `generated`, not both."
                )
            if not item.file and not item.generated:
                raise ValueError(
                    f"`document.{zone_name}` items must define either `file` or `generated`."
                )
            if item.file:
                if (
                    item.generated
                    or item.title != "Contents"
                    or item.numbered is not False
                    or item.listed is not True
                ):
                    raise ValueError(
                        f"File item in `document.{zone_name}` cannot include generated TOC fields."
                    )
                continue

            if item.generated != "toc":
                raise ValueError(
                    f"Unsupported generated item in `document.{zone_name}`: {item.generated!r}."
                )
            if zone_name != "front_matter":
                raise ValueError(
                    "Generated TOC items are currently supported only in `document.front_matter`."
                )
            if item.title.strip() == "" and (item.numbered or item.listed):
                raise ValueError(
                    "A generated TOC item without a title cannot be numbered or listed."
                )
            generated_toc_count += 1

    if generated_toc_count > 1:
        raise ValueError("Only one generated TOC item is currently supported per document.")

    if config.document.toc.enabled and config.document.toc.zone != "front_matter":
        raise ValueError("Document TOC placement currently supports only `front_matter`.")


def document_has_explicit_generated_toc(config: DocsmithConfig) -> bool:
    """Return whether the ordered zone model already contains an explicit TOC item."""
    return any(item.generated == "toc" for item in config.document.front_matter)


def document_has_structural_toc(config: DocsmithConfig) -> bool:
    """Return whether any structural TOC should be emitted by the engine."""
    return document_has_explicit_generated_toc(config) or config.document.toc.enabled


def load_document_config(spec_path: Path) -> DocsmithConfig:
    """Load and validate a document spec from YAML."""
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    with spec_path.open("r", encoding="utf-8") as handle:
        raw_text = handle.read()

    if yaml is not None:
        raw_config: dict[str, Any] = yaml.safe_load(raw_text) or {}
    else:
        raw_config = _simple_yaml_load(raw_text)

    metadata = raw_config.get("metadata")
    if metadata is not None and not isinstance(metadata, Mapping):
        raise TypeError("`metadata` must be a mapping in spec.yaml")

    if "template" in raw_config:
        project = raw_config.setdefault("project", {})
        if isinstance(project, dict) and "template" not in project:
            project["template"] = raw_config.pop("template")

    project = raw_config.get("project")
    if isinstance(project, dict):
        template = project.get("template")
        if isinstance(template, dict) and "path" in template:
            project["template"] = template["path"]

    versioning = raw_config.get("versioning")
    if (
        isinstance(versioning, dict)
        and "current_version" in versioning
        and "initial_version" not in versioning
    ):
        versioning["initial_version"] = versioning.pop("current_version")

    _normalize_zone_items(raw_config)
    config = DocsmithConfig.model_validate(raw_config)
    _validate_zone_item_config(config)
    return config
