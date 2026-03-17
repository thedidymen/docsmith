# Docsmith Project Status

## Snapshot

Docsmith is currently a working Python CLI for building structured Markdown document directories into PDF via Pandoc, using document-local LaTeX templates and YAML configuration. The repository is beyond a scaffold: config loading, document discovery, validation, assembly, runtime metadata generation, versioned output naming, automatic semantic version bumping, and a tested build flow are implemented.

At the same time, it is still an early MVP. The public story is narrower than the project goals suggest: DOCX output is configured in the model but not actually built, template handling is intentionally simple, and the current template reuse story is still example-driven rather than package-driven. The repository is now explicitly organization-neutral: Docsmith is the engine, while document repositories and example projects own their templates and content.

## Current Phase

Docsmith has completed the first structural milestone set for the document model. Metadata, zones, appendices, bibliography placement, and table-of-contents placement are now explicit engine concepts. The next architectural work is to tighten the authoring model so document content, metadata, templates, and engine responsibilities remain clearly separated.

## Architectural Direction

The engine direction is to model stable document concepts in a neutral way and let templates consume those concepts through clear contracts. That includes metadata, document structure, appendices, bibliography placement, and other layout-relevant zones that should become explicit parts of the build model over time. The engine should keep handling orchestration and reproducibility, while templates remain outside the engine and decide how those concepts are rendered.

## Next Milestone

The next milestone is declarative front matter and title page support so document repositories no longer need layout-oriented workarounds in Markdown content. The current phase is still incremental: explicit structure first, then cleaner authoring contracts built on top of it.

## Schema Evolution Notes

Because Docsmith is still in the `0.x` phase, config and spec evolution is acceptable when it improves the document model. That evolution should be explicit, documented, and paired with implementation updates, tests, and README or status documentation changes. Backward compatibility is valuable, but clarity in the emerging document contract is more important than freezing an immature schema too early.

## Current Implemented Features

### Configuration and document model

- `spec.yaml` loading and validation are implemented in `src/docsmith/config.py`.
- The config model is structured into `project`, `metadata`, `document`, `citations`, `output`, and `versioning`.
- `metadata` is now an extensible top-level mapping rather than a fixed field schema.
- Arbitrary metadata keys and nested metadata structures are preserved and passed through the build pipeline for template consumption.
- `document` now supports minimal explicit zones: `front_matter`, `main_matter`, and `back_matter`.
- `document.appendices` now provides first-class appendix structure distinct from generic back matter.
- `document.bibliography` now provides first-class bibliography placement distinct from hand-authored Markdown sections.
- `document.toc` now provides first-class table-of-contents placement distinct from hand-authored front-matter sections.
- Legacy `document.include` remains supported during the transition.
- When explicit structure fields and `document.include` are present, explicit structure takes precedence.
- Template resolution now uses filesystem paths declared in `spec.yaml`, typically relative to the document root.
- Backward-compatible normalization exists for both top-level `template` forms and legacy `versioning.current_version`.
- Pydantic is used when available, with a fallback minimal validator/parser for bare environments.

### Structural milestone status

- The current structural milestone set is complete for the present engine phase:
  - extensible metadata
  - explicit document zones
  - first-class appendices
  - first-class bibliography placement
  - first-class table-of-contents placement
- The remaining gap is no longer basic structure, but the authoring model used inside Markdown sources.

## Authoring Model Issues

The main architectural issue now is that some Markdown documents still contain raw LaTeX for layout purposes, such as title-page logic or formatting hacks. That is considered a violation of the intended Docsmith design.

Target separation of concerns:

- Markdown = content only
- Metadata = document structure and data
- Templates = layout
- Engine = glue

Future direction:

- eliminate LaTeX from document content wherever it is being used for layout
- replace layout-oriented Markdown hacks with metadata-driven rendering and template behavior
- add declarative front matter and title page support as the next focused milestone

### Document discovery and assembly

- Input root resolution is implemented.
- Explicit include ordering is supported via `document.include`.
- Explicit zone ordering is now supported via `document.front_matter`, `document.main_matter`, and `document.back_matter`.
- Explicit appendix ordering is now supported via `document.appendices`.
- Explicit bibliography placement is now supported via `document.bibliography`.
- Explicit table-of-contents placement is now supported via `document.toc`.
- If no include list is configured, Markdown files are discovered recursively and sorted.
- If any explicit structure is configured, discovery resolves files in order: front matter, main matter, back matter, then appendices.
- Assembly concatenates Markdown files into `build/combined.md`.
- Assembly now emits explicit zone boundary comments in the intermediate combined Markdown.
- Explicit appendices trigger a first-class appendix boundary during assembly.
- Structural bibliography placement emits a Pandoc-native bibliography placeholder in the configured zone.
- Structural TOC placement emits a TOC block in the configured zone and suppresses template-level auto-TOC for that document.
- The older appendix marker remains supported for non-migrated documents during transition.
- Assembly inserts source boundary comments like `<!-- begin:path -->` into the combined file.
- Resource handling is build-aware: the renderer passes Pandoc a `--resource-path` including both the build directory and the original document root so images and other assets still resolve after Markdown assembly.

### Build validation

- `docsmith validate <document_dir>` is implemented.
- Validation covers:
  - `spec.yaml` loading
  - input root existence
  - included Markdown file existence
  - document-local template existence and required files
  - external PDF build dependencies
  - bibliography and CSL path existence
  - output directory resolution and creatability
- Validation output is human-readable and returns a non-zero exit code on failure.

### Rendering

- PDF rendering through Pandoc is implemented.
- The Pandoc command includes:
  - document-local template defaults
  - document-local LaTeX template
  - `--resource-path` covering both the build directory and the source document root
  - runtime metadata file
  - bibliography and CSL arguments when configured
- Runtime metadata is written as YAML rather than hand-built scalar lines.
- Runtime metadata merges user-defined metadata from `spec.yaml` with runtime values such as `version` and optional `git_hash`.
- On metadata key collisions, runtime values win.
- Example templates now include compatibility shims for Pandoc-generated constructs such as `\tightlist`, `\pandocbounded`, Pandoc table output, code block environments, and CSL bibliography output.
- Clear runtime errors are raised for:
  - missing Pandoc executable
  - missing PDF engine dependencies such as `xelatex`
  - Pandoc command failure

### Example documents

The repository now includes multiple neutral example document projects that double as system demonstrations:

- `examples/templates`
  - shared repository-level neutral templates reused by multiple example documents
- `examples/documents/technical_report_demo`
  - smaller showcase document using the shared `technical_report` template
- `examples/documents/authoring_guide`
  - richer authoring guide covering Markdown, assets, citations, appendices, and versioning
- `examples/documents/docsmith_architecture`
  - architecture-style report that documents the Docsmith system itself using a neutral report template

These examples are now the primary place where template usage is demonstrated. The engine repository no longer ships organization-specific or bundled templates, and the shared `examples/templates/` layout shows how several documents in the same repository can reuse one template set without duplication.

### Versioning and output naming

- Output filenames include semantic version metadata.
- Optional git short hash metadata is supported when enabled and available.
- Non-overwrite behavior is implemented via collision suffixes such as `_01`, `_02`.
- Automatic semantic version bumping is implemented for semver builds.
- Build state is persisted to `build/.docsmith-state.json`.
- Fingerprints are computed from effective build inputs:
  - `spec.yaml`
  - included Markdown files
  - active document-local template files
  - bibliography and CSL files when configured

## Current CLI Commands

### `docsmith build <document_dir>`

Current behavior:

- Loads `spec.yaml`
- Computes the document fingerprint
- Loads prior build state from `build/.docsmith-state.json` if present
- Resolves the semantic version
- Assembles Markdown into `build/combined.md`
- Writes runtime metadata to `build/runtime-metadata.yaml`
- Renders a PDF
- Persists updated build state after a successful render
- Prints status lines such as:
  - whether content changes were detected
  - whether the semantic version was kept or bumped
  - git hash if present
  - final output path

Supported flags:

- `--bump patch`
- `--bump minor`
- `--bump major`
- `--no-bump`

Important limitation:

- The build command currently produces only PDF output, even though `output.formats` allows `pdf` and `docx` in config.

### `docsmith validate <document_dir>`

Current behavior:

- Runs structured validation checks without rendering
- Prints one `PASS` or `FAIL` line per check
- Exits with status code `1` when validation fails

Important detail:

- Validation checks whether the output directory already exists and is writable, or whether it can be created under a writable parent, without creating it.

### `docsmith templates`

Current behavior:

- Lists template directory names under `./templates` in the current working tree
- This is now a convenience command for document repositories and example projects, not for engine-bundled templates

## What Is Already Production-Like

- Clear separation between CLI, core build logic, rendering, configuration, templates, and versioning.
- Clean separation between engine logic and document-owned templates/content.
- Extensible metadata pass-through from `spec.yaml` into Pandoc template variables.
- Deterministic fingerprint-based semantic version bumping.
- Persisted build state rather than rewriting declarative config.
- Non-overwriting output naming.
- Graceful behavior both with and without git.
- Human-readable validation output with non-zero exit behavior.
- Good unit and service-level test coverage for current behavior.
- Reasonable failure messages for missing files, missing Pandoc, and missing PDF build dependencies.

## What Is Still Placeholder or Incomplete

- DOCX rendering is not implemented in the build flow.
- Multi-format builds are not implemented despite config support for multiple formats.
- Template support is intentionally simple and path-based; there is no template packaging workflow yet.
- The `docsmith templates` command only lists `./templates` under the current working tree; it is not a full template discovery mechanism.
- Template metadata conventions are not formalized beyond required file presence.
- There is no end-to-end test that runs real Pandoc against a real template and verifies produced artifacts.
- No packaging/release guidance is documented for external users.
- No clean story exists yet for first-time template authoring or custom template extension.
- No build manifest, artifact summary, or machine-readable CLI output exists.
- No plugin or extension mechanism exists.

## Current Template Capabilities

Example shared repository-level templates:

- `academic_thesis`
- `technical_report`

Supported today:

- Template discovery by path relative to a document root
- Validation that a template has `template.tex` and `defaults.yaml`
- Template files are included in the build fingerprint
- Example templates can include additional partials and metadata assets
- Example templates can support common Pandoc LaTeX constructs for lists, bounded images, tables, code blocks, and citeproc bibliography output

What this means in practice:

- `academic_thesis` demonstrates a title-page-oriented thesis layout
- `technical_report` demonstrates a simpler report-style layout
- Templates can live beside a set of documents in the same repository, which keeps the engine neutral while avoiding duplication across related documents

Not yet supported:

- template inheritance/composition
- template schema validation
- format-specific template selection
- structured template capability metadata

## Current Versioning Behavior

### Semantic version source of truth

- `spec.yaml` provides `versioning.initial_version`
- actual evolving semantic version lives in `build/.docsmith-state.json`
- `spec.yaml` is not rewritten during builds

### Automatic bump rules

- first build with no prior state uses `initial_version`
- unchanged fingerprint keeps the same semantic version
- changed fingerprint bumps `PATCH`
- explicit `--bump` overrides automatic behavior
- `--no-bump` disables automatic bumping for that build

### Build identity vs semantic version

- semantic version is human meaningful
- optional git hash adds traceability
- collision suffixes only prevent overwrites

### Limitations

- only semver is meaningfully integrated with the build-state flow
- `timestamp` remains in the config model, but the current build resolution path is semver-centric
- change classification is coarse: any effective input change becomes a patch bump unless overridden

## Current Test Coverage Areas

The repository currently has 68 passing tests covering these areas:

- config loading, defaults, validation, and legacy field compatibility
- Markdown discovery and include ordering
- Markdown assembly and appendix marker replacement
- CLI build and validate command behavior
- validation reporting and failure modes
- Pandoc command construction and error handling
- template registry behavior
- semantic version bumping logic
- fingerprint-sensitive rebuild behavior
- state file persistence and reload
- no-git behavior
- non-overwrite output naming
- example document config/discovery/validation coverage for the technical report demo, authoring guide, and architecture report

Coverage strengths:

- good behavioral coverage for the currently implemented Python logic
- strong isolation of side-effect-heavy code through mocking

Coverage gaps:

- no real subprocess integration test with Pandoc
- no test that actually confirms produced PDF contents or layout
- no dedicated integration test suite around switching one example document between multiple templates
- no regression coverage yet for multiple output formats because they are not implemented

## Likely Technical Debt or Weak Spots

1. Config and feature mismatch: `output.formats` supports `docx`, but the builder only renders PDF.
2. Template reuse across document repositories still relies on copy-based examples rather than a mature template-pack workflow.
3. The fallback YAML parser is intentionally narrow and may diverge from real YAML behavior in edge cases.
4. Template validation remains shallow and only checks required file presence, not full semantic compatibility with Pandoc output.
5. Fingerprinting uses raw file contents only and has no explicit normalization or manifest of included logical inputs.
6. Build flow assumes a single output artifact and does not model per-format results.
7. `timestamp` versioning remains partly modeled but is not the primary tested path.
8. Template capability boundaries are undocumented, which will make template authoring brittle.
9. Real example documents exist now, but the project still lacks a deeper long-running integration workflow in CI that actually exercises full PDF builds routinely.
10. The convenience `templates` command is intentionally narrow and may create expectations of a fuller template management workflow than currently exists.

## Top 10 Next Improvements

Ordered by likely impact:

1. Implement actual multi-format rendering so `output.formats` is honored, starting with DOCX.
2. Introduce a minimal structured document-zone model so concepts like body, appendix, and bibliography placement are explicit rather than purely template-driven.
3. Add a proper template-pack or reusable template distribution story so document repositories do not need to copy templates manually.
4. Document the current config schema, CLI usage, build artifacts, and versioning behavior in the README.
5. Add end-to-end integration tests that run real Pandoc in CI or in an opt-in test job.
6. Make build results format-aware, returning multiple output artifacts instead of assuming one PDF.
7. Add opt-in integration tests that build real PDFs in CI, since the current suite is mostly unit and mocked service coverage.
8. Strengthen template validation to cover referenced partials and required assets, not just `template.tex` and `defaults.yaml`.
9. Decide whether `timestamp` is a real supported strategy and either finish it or remove it for now.
10. Add a clear template contract story so document structure and template expectations evolve without hidden coupling.

## What Should Be Documented in the README Right Now

- installation and dependency prerequisites, especially Pandoc and LaTeX expectations
- current CLI commands and examples:
  - `build`
  - `validate`
  - `templates`
- actual supported build output today: PDF only
- the current `spec.yaml` structure with a minimal complete example
- how Markdown discovery and `document.include` ordering work
- appendix marker behavior
- citation support expectations for bibliography and CSL files
- document-local templates and their current status
- the example document set and what each example demonstrates
- resource-path behavior for images and other assembled-document assets
- versioning behavior:
  - `initial_version`
  - automatic patch bumping
  - build state file
  - optional git hash
  - collision suffixes
- build artifacts written under `build/` and `output/`
- current project limitations and non-goals for the MVP

## What Is Missing for a Good First Public MVP

- a truthful README that matches the implemented behavior
- a clear statement that PDF is the actual supported output today
- continued maintenance of the current example set so it stays representative of real usage
- either working DOCX support or removal of DOCX from the advertised MVP surface
- installation instructions for Pandoc and required LaTeX tooling
- basic end-to-end verification against a real render
- clearer template documentation for users who want to adopt or adapt a document-local template
- a small compatibility statement for supported Python and external tool expectations

## What Should Be Postponed Until After the First Real Document Repository Is Tested

- interactive version selection flows
- sophisticated change classification beyond patch bumps
- plugin architecture or templating extension APIs
- remote asset fetching
- watch mode and live rebuild workflows
- advanced template inheritance systems
- highly generalized template metadata contracts
- rich machine-readable CLI output formats
- build caching beyond the current fingerprint/state mechanism
- opinionated abstractions for figures, tables, or title pages that have not yet been validated against real document needs

## Overall Assessment

Docsmith is in a credible pre-public-MVP state. The repository already contains a real build pipeline, validation command, and a reasonably clean internal architecture. The main risk is not lack of code structure; it is the gap between the broader product promise and the narrower set of capabilities that are actually proven today.

The next step should not be adding more features indiscriminately. The highest-value move is to tighten the public contract around what already works, validate the tool against one realistic document repository, and then use that feedback to decide which abstractions are real requirements versus premature generalization.
