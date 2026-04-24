# Docsmith Agent Instructions

Docsmith is a neutral document build engine that builds structured Markdown documents into versioned outputs.

Repository Role:
- Docsmith is the engine layer for structured document builds
- this repository should define reusable build concepts and orchestration, not organization-specific document products
- templates, branding, and document programs belong in document repositories or external template packs

Development Philosophy:
- evolve the engine through explicit document concepts rather than ad hoc one-off features
- prefer small, documented schema and architecture steps over big-bang redesigns
- keep engine behavior inspectable and predictable for both document authors and template authors
- avoid hidden coupling between engine internals and template implementation details

Current implemented output:
- PDF

Important repository stance:
- Docsmith is the engine, not the template pack
- templates belong in document repositories or external template packs
- example documents are demonstrations of the engine and lightweight documentation artifacts
- the core repository must remain organization-neutral
- do not introduce organization-specific templates, branding, or assumptions into the engine

Project goals:
- generic Markdown -> document engine
- Python-based CLI
- Pandoc for rendering
- document-local LaTeX templates for PDF
- YAML specification files
- reusable templates
- support for citations via BibTeX and CSL
- support for figures, tables, appendices, and title pages
- output filenames with version metadata and optional git hash

Architecture rules:
- keep CLI, core logic, rendering, and versioning separated
- document-specific logic must not be hardcoded
- templates belong in document repositories or external template packs, not in the engine
- keep engine logic separate from document content and example content
- keep the repository organization-neutral
- configuration loading belongs in `src/docsmith/config.py`
- Pandoc orchestration belongs in `src/docsmith/renderer/`
- builder logic belongs in `src/docsmith/core/`
- prefer clean, modular Python
- use `pyproject.toml`
- prefer Typer for CLI
- prefer Pydantic for config models
- add tests for important behavior
- write clear docstrings and readable code
- when extending document behavior, prefer explicit concepts such as metadata, document zones, appendices, bibliography placement, and template contracts
- structural features should be introduced incrementally with clear config and pipeline changes
- do not rely on implicit template behavior when an engine-level concept should be modeled explicitly
- avoid engine-template coupling that only works for one example template family
- do not introduce LaTeX into markdown documents for layout purposes
- prefer metadata, explicit document structure, or template changes over markdown-level LaTeX layout hacks
- new media, diagram, figure, table, or cross-reference features should be designed as explicit engine or template-contract concepts before implementation
- avoid ad hoc renderer-specific behavior for media or cross-references unless the engine-template contract is documented clearly first
- future figure or table cross-reference work must follow `docs/design-cross-references.md` before implementation changes are made
- future diagram rendering work must follow `docs/design-diagram-rendering.md` before implementation changes are made
- future document scaffolding or profile work must follow `docs/design-document-scaffolding.md` before implementation changes are made
- do not add consumer-side Mermaid or diagram workarounds in the engine; keep renderer behavior explicit, neutral, and build-managed
- keep engine scaffolds neutral; do not turn `docsmith init` into a repository-specific or organization-specific starter generator

Current architecture assumptions:
- `project.template` resolves to a filesystem path, typically relative to the document root
- validation, fingerprinting, and rendering all operate on document-local template paths
- Pandoc resource handling must continue to support assembled Markdown plus source-document assets
- build state lives in `build/.docsmith-state.json`
- semantic versioning is fingerprint-based and separate from optional git-hash traceability

Example repository guidance:
- examples should demonstrate the engine, not special-case product behavior
- keep examples neutral, educational, and repository-relevant
- example documents may double as lightweight documentation, such as authoring guides or architecture reports
- if an example includes templates, those templates live inside that example document repository
- when several example documents in the same repository can reuse one neutral template set, prefer a shared repository-level templates directory rather than duplicating templates per document
- preserve existing examples unless a task explicitly calls for replacing them

Documentation guidance:
- keep README, project status, and agent guidance synchronized with implementation changes
- when architecture changes, update the narrative, not just code snippets
- avoid documenting unsupported features as available
- remove outdated organization-specific references when the implementation becomes more generic

Working style:
- first propose repository structure
- then implement an MVP
- keep changes small and coherent
- do not invent features beyond the stated requirements unless clearly useful
- when evolving the document model, document the contract change in README and project status alongside the code change
