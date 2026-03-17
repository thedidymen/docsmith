# Metadata Audit

## Classification

Partially implemented.

The engine-side metadata milestone is functionally implemented in code and covered by targeted tests, but it is not yet fully closed as a repository milestone because:

- `docs/project-status.md` still describes extensible metadata as part of the next milestone rather than current capability.
- there is no real Pandoc end-to-end integration test that proves arbitrary metadata survives all the way into a real rendered artifact.

## Evidence

### 1. `spec.yaml` and config support

Status: implemented.

- Top-level `metadata:` is supported as a generic mapping in [src/docsmith/config.py](/Users/reijer/Repo/docsmith/src/docsmith/config.py).
  - `DocsmithConfig.metadata` is typed as `dict[str, Any]`.
  - `default_metadata()` provides backward-compatible defaults for `title`, `subtitle`, `author`, and `date`.
- Arbitrary keys are allowed.
  - No fixed metadata schema remains.
  - `load_document_config()` only checks that `metadata` is mapping-like.
- Nested metadata structures are preserved.
  - The config loader passes the mapping through unchanged.
  - Tests cover nested dicts and lists in [tests/test_config.py](/Users/reijer/Repo/docsmith/tests/test_config.py).

Concrete code evidence:

- [src/docsmith/config.py](/Users/reijer/Repo/docsmith/src/docsmith/config.py)
  - `metadata: dict[str, Any] = Field(default_factory=default_metadata)`
  - `if metadata is not None and not isinstance(metadata, Mapping): raise TypeError(...)`

Concrete test evidence:

- [tests/test_config.py](/Users/reijer/Repo/docsmith/tests/test_config.py)
  - `test_load_document_config_preserves_flat_arbitrary_metadata`
  - `test_load_document_config_preserves_nested_metadata`
  - `test_load_document_config_rejects_non_mapping_metadata`

### 2. Internal model

Status: implemented.

- The config model exposes metadata generically via `config.metadata`.
- Metadata is accessible throughout the build flow because the full `DocsmithConfig` is passed from config loading into builder, runtime metadata writing, and rendering.

Concrete code evidence:

- [src/docsmith/core/builder.py](/Users/reijer/Repo/docsmith/src/docsmith/core/builder.py)
  - loads `config = load_document_config(...)`
  - passes `config` into `write_runtime_metadata(...)`
  - passes `config` and `metadata_file` into `render_pdf(...)`
- [src/docsmith/renderer/metadata.py](/Users/reijer/Repo/docsmith/src/docsmith/renderer/metadata.py)
  - reads from `config.metadata`

### 3. Runtime metadata generation

Status: implemented.

- `build/runtime-metadata.yaml` is generated during normal builds.
- User metadata is merged with runtime metadata.
- On key collision, runtime metadata wins.

Concrete code evidence:

- [src/docsmith/core/builder.py](/Users/reijer/Repo/docsmith/src/docsmith/core/builder.py)
  - writes runtime metadata before rendering
- [src/docsmith/renderer/metadata.py](/Users/reijer/Repo/docsmith/src/docsmith/renderer/metadata.py)
  - starts with `metadata = dict(config.metadata)`
  - then sets `metadata["version"] = version`
  - then sets `metadata["git_hash"] = git_hash` when available

Collision behavior:

- Runtime keys overwrite user keys for `version` and `git_hash`.
- There is no logging of collisions in code, but the behavior is documented in the README.

Concrete test evidence:

- [tests/test_builder.py](/Users/reijer/Repo/docsmith/tests/test_builder.py)
  - `test_build_document_merges_user_metadata_into_runtime_metadata`
    - explicitly sets `metadata.version: user-defined-version`
    - asserts output metadata uses runtime `version: 0.1.0`
- [tests/test_pandoc.py](/Users/reijer/Repo/docsmith/tests/test_pandoc.py)
  - `test_write_runtime_metadata_serializes_special_characters_safely`
    - verifies arbitrary keys, nested metadata, and collision override for `version`

### 4. Pandoc integration

Status: implemented at the command/build level.

- Metadata is passed via `--metadata-file`.
- The engine does not inline metadata into assembled Markdown.
- Templates can access arbitrary metadata fields through Pandoc variables without engine changes.

Concrete code evidence:

- [src/docsmith/renderer/pandoc.py](/Users/reijer/Repo/docsmith/src/docsmith/renderer/pandoc.py)
  - `command.extend(["--metadata-file", str(metadata_file)])`
- [src/docsmith/core/builder.py](/Users/reijer/Repo/docsmith/src/docsmith/core/builder.py)
  - passes `metadata_file=metadata_path` into `render_pdf(...)`

Concrete test evidence:

- [tests/test_pandoc.py](/Users/reijer/Repo/docsmith/tests/test_pandoc.py)
  - `test_build_pandoc_command_includes_metadata_file`
- [tests/test_builder.py](/Users/reijer/Repo/docsmith/tests/test_builder.py)
  - `test_build_document_passes_extensible_metadata_to_renderer`
    - simulates renderer consumption of arbitrary metadata fields from the runtime metadata file

Limitation:

- There is no real Pandoc integration test that renders a real template and verifies an arbitrary metadata field in a produced artifact. Current coverage proves command construction and build-path handoff, but the final Pandoc/template round-trip is still mocked or simulated.

### 5. Validation

Status: implemented.

- Metadata is optional.
  - `DocsmithConfig.metadata` has a default factory.
- Validation only requires metadata to be mapping-like.
  - There is no validation of individual metadata keys.

Concrete code evidence:

- [src/docsmith/config.py](/Users/reijer/Repo/docsmith/src/docsmith/config.py)
  - default metadata mapping exists even when `metadata:` is absent
  - only mapping-shape validation is enforced
- [src/docsmith/core/validation.py](/Users/reijer/Repo/docsmith/src/docsmith/core/validation.py)
  - validation relies on `load_document_config()` for metadata shape checks

Concrete test evidence:

- [tests/test_config.py](/Users/reijer/Repo/docsmith/tests/test_config.py)
  - `test_load_document_config_uses_defaults_for_missing_sections`
  - `test_load_document_config_rejects_non_mapping_metadata`
- [tests/test_validation.py](/Users/reijer/Repo/docsmith/tests/test_validation.py)
  - `test_validate_document_reports_non_mapping_metadata`

### 6. Tests

Status: mostly implemented.

Existing metadata-related coverage:

- config loading for default, flat, and nested metadata structures
- rejection of non-mapping metadata
- runtime metadata file creation
- merged metadata contents
- collision override behavior for runtime keys
- Pandoc command inclusion of `--metadata-file`
- simulated renderer consumption of arbitrary metadata fields

What is missing:

- a real end-to-end Pandoc test that renders a template using an arbitrary metadata field and verifies the produced artifact

### 7. Documentation

Status: mostly implemented, but not fully aligned.

README:

- [README.md](/Users/reijer/Repo/docsmith/README.md) correctly documents:
  - arbitrary metadata in `spec.yaml`
  - pass-through to `build/runtime-metadata.yaml`
  - template access via Pandoc variables
  - runtime collision precedence

AGENTS:

- [AGENTS.md](/Users/reijer/Repo/docsmith/AGENTS.md) reflects metadata as an explicit engine concept and warns against hidden engine-template coupling.

Project status:

- [docs/project-status.md](/Users/reijer/Repo/docsmith/docs/project-status.md) mentions runtime metadata as implemented.
- But it is not fully aligned with the current state because `## Next Milestone` still says the next milestone is "extensible metadata + minimal document zones".

## Missing Pieces

Only the following pieces appear to remain:

- update [docs/project-status.md](/Users/reijer/Repo/docsmith/docs/project-status.md) so extensible metadata is described as implemented, and the next milestone shifts to the next structured-document concept after metadata
- add one real Pandoc integration test proving an arbitrary metadata field can be consumed by a real template without engine changes

## Recommendation

Treat extensible metadata as effectively implemented in the engine, but not fully closed as a milestone until the status documentation is updated and a real end-to-end metadata render test exists.

The next milestone should be minimal document zones or other explicit structured document concepts, not extensible metadata itself.
