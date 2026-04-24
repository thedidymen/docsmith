# Docsmith Cross-References Design

## Status

This document defines the Docsmith engine design for automatic figure and table numbering plus cross-references.

Implemented today:

- validation of duplicate figure or table IDs
- validation of invalid figure or table IDs
- validation of missing figure or table reference targets
- minimal PDF rendering support for `@fig:...` and `@tbl:...` through an engine-owned Pandoc Lua filter

Not implemented:

- section or appendix cross-references
- DOCX cross-reference rendering
- configurable label language
- stricter optional warning modes such as unused IDs

The purpose of this document is to make the first implementation small, explicit, and compatible with Docsmith's neutral engine role.

## Goals

Docsmith should support:

- automatic figure numbering
- automatic table numbering
- references from text to figures and tables
- validation of duplicate IDs, invalid IDs, and missing reference targets
- gradual migration without breaking existing documents

Docsmith should not use this feature to smuggle presentation policy into Markdown. Numbering and references are engine concepts; caption layout and typography remain template concerns.

## Proposed Authoring Syntax

### Figures

Use ordinary Markdown image syntax with a caption plus an explicit attribute ID:

```md
![Procesdiagram van het registratieproces](assets/generated/registratieproces.png){#fig:registratieproces width=80%}
```

Proposed convention:

- figures that participate in cross-references should use an explicit ID
- figure IDs must start with `fig:`
- the part after `fig:` should be lowercase kebab-case or snake-case ASCII text with digits allowed
- recommended pattern: `fig:[a-z0-9][a-z0-9_-]*`

Examples:

- `fig:registratieproces`
- `fig:context_overview`
- `fig:api-flow-01`

### Tables

Use a normal Markdown table followed by a caption line with an explicit attribute ID:

```md
| Scenario | Verwacht resultaat |
|---|---|
| Geldige invoer | Inschrijving wordt vastgelegd |

Table: Resultaten van validatiescenario's {#tbl:validatie}
```

Proposed convention:

- tables that participate in cross-references should use an explicit ID
- table IDs must start with `tbl:`
- the part after `tbl:` follows the same pattern as figures
- recommended pattern: `tbl:[a-z0-9][a-z0-9_-]*`

Examples:

- `tbl:validatie`
- `tbl:acceptatiecriteria`
- `tbl:api-status-codes`

### References in text

Use citation-like target syntax in Markdown prose:

```md
Zie @fig:registratieproces.
Zie @tbl:validatie.
```

This keeps references short, readable, and consistent with Pandoc-style source conventions.

## Authoring Rules

### Prefixes

`fig:` and `tbl:` are required.

Reasoning:

- they make target type explicit
- they avoid collisions between figures and tables
- they make validation simpler and clearer
- they leave room for future namespaces such as `sec:` or `app:`

### Caption without ID

Allowed.

Effect:

- the figure or table renders normally according to the existing document flow
- it is not cross-referenceable through the planned Docsmith feature
- no numbering guarantee is promised by this design unless the chosen output pipeline numbers all captioned items consistently

This preserves backward compatibility for existing documents and supports gradual migration.

### ID without references

Allowed.

First implementation behavior:

- no build failure
- no warning in the first implementation

Possible later enhancement:

- optional warning for unused IDs

### Reference target does not exist

Should be an error in the first implementation.

Reasoning:

- a dangling cross-reference is a broken document contract, not a style issue
- silent fallback would make versioned outputs look complete while containing invalid references
- document authors need deterministic feedback before rendering

### Invalid ID format

Should be an error.

Reasoning:

- invalid IDs create ambiguity in parsing and future extensibility
- the format needs to remain stable across templates and renderer options

## Engine Responsibilities

Docsmith should own the document-level contract and validation behavior, not the caption styling.

Docsmith responsibilities:

- parse the assembled Markdown for figure IDs, table IDs, and `@fig:` or `@tbl:` references
- validate duplicate figure and table IDs
- validate ID format
- validate that each reference target exists
- surface clear error messages with source-file context when possible
- preserve source boundaries through assembly so diagnostics can still point back to authored files
- pass the required Pandoc or filter arguments once the implementation approach is chosen
- keep cross-reference support opt-in and backward compatible
- include any new cross-reference configuration and helper files in the build fingerprint once they exist

### Validation ownership

Planned validation rules:

- duplicate `fig:` IDs: error
- duplicate `tbl:` IDs: error
- invalid `fig:` or `tbl:` ID format: error
- reference to a missing `fig:` or `tbl:` target: error
- caption without ID: allowed
- unused IDs: no warning in first implementation

### Error behavior

When implemented, Docsmith should fail validation and build for structural cross-reference errors instead of trying to degrade silently.

Expected error categories:

- duplicate target ID
- invalid target ID format
- unresolved cross-reference target
- invalid target type prefix

The preferred reporting model is one clear issue per offending target or reference, with authored file paths and enough local context to fix the problem quickly.

### Fingerprinting and versioning

Cross-reference support should not change the current fingerprinting model conceptually.

Once implemented, the fingerprint should continue to include:

- `spec.yaml`
- Markdown source files
- active template files
- any cross-reference helper scripts or filter files if Docsmith starts shipping them

Rationale:

- changing IDs or references changes document meaning and should affect build versioning through the Markdown source fingerprint
- changing the cross-reference resolution mechanism should affect versioning if that mechanism is part of the effective output pipeline

## Template Responsibilities

Templates should continue to own presentation, not cross-reference correctness.

Template responsibilities:

- visual styling of figure captions
- visual styling of table captions
- placement of figure captions below figures
- placement of table captions above tables
- label language such as `Figure`, `Figuur`, `Table`, or `Tabel`, unless a later design deliberately moves that into engine config
- PDF typography, spacing, alignment, and layout details

Template non-responsibilities:

- discovering duplicate IDs
- validating broken references
- deciding whether a figure or table is logically referenceable
- inventing ad hoc numbering rules that contradict the engine contract

## Implementation Options

### Option A: Pandoc-native behavior only

Interpretation:

- rely only on Pandoc's built-in parsing and writer behavior
- avoid extra tools or filters

Pros:

- lowest dependency impact
- simplest runtime story
- best portability on paper

Cons:

- Pandoc alone does not provide a complete generic figure and table cross-reference system for the target authoring contract
- table references are especially awkward without additional machinery
- validation of missing targets and duplicate IDs would still require Docsmith-side parsing
- output behavior may vary by format and template assumptions

Dependency impact:

- no new external dependency

Template impact:

- templates may still need writer-specific assumptions to achieve good results

Portability impact:

- good in theory, but functionality is incomplete for Docsmith's goals

Complexity:

- deceptively low; the missing capabilities push complexity back into Docsmith or author workarounds

Fit with Docsmith architecture:

- weak for the first implementation because it does not give a complete, stable contract

### Option B: pandoc-crossref

Interpretation:

- depend on `pandoc-crossref` for numbering and reference resolution

Pros:

- mature, purpose-built solution
- supports figures, tables, equations, and more
- familiar in Pandoc ecosystems

Cons:

- introduces an extra external dependency beyond Pandoc
- increases setup and compatibility burden for users
- makes Docsmith less predictable across environments unless installation is tightly managed
- couples the engine more strongly to one external cross-reference tool

Dependency impact:

- significant; new required executable or packaging story needed

Template impact:

- moderate; templates may need to align with generated labels or writer output conventions

Portability impact:

- weaker than Pandoc-only because all build environments must install and support the extra tool

Complexity:

- medium operational complexity even if implementation code is smaller

Fit with Docsmith architecture:

- acceptable technically, but weaker strategically because Docsmith is trying to keep the engine surface lean and predictable

### Option C: Custom lightweight Docsmith Pandoc Lua filter

Interpretation:

- ship a Docsmith-owned Pandoc Lua filter to resolve figure and table numbering plus references

Pros:

- no new non-Pandoc dependency
- keeps logic close to the renderer pipeline
- Docsmith can shape behavior to its own contract
- easier portability than `pandoc-crossref`

Cons:

- Docsmith must own and maintain filter logic
- testing burden increases
- AST-level behavior may become renderer-specific if not designed carefully
- validation still needs a clean engine-side contract, not just filter behavior

Dependency impact:

- no extra executable dependency, but does add shipped filter logic

Template impact:

- moderate; templates still need to render the resulting numbered elements well

Portability impact:

- better than `pandoc-crossref`, assuming Pandoc Lua filters are available

Complexity:

- medium implementation complexity

Fit with Docsmith architecture:

- good if the contract is documented first and the filter remains narrow and neutral

### Option D: Hybrid approach

Interpretation:

- Docsmith validates and prepares the authoring contract
- Pandoc plus a Docsmith-owned output-stage mechanism resolves numbering and final references
- the first implementation may use a lightweight Docsmith Lua filter, but the validation and contract stay engine-owned

Pros:

- clean separation of concerns
- Docsmith owns document correctness and migration behavior
- output resolution remains in the rendering pipeline where numbering belongs
- validation can fail early before expensive rendering
- preserves room to change the rendering mechanism later without changing author syntax

Cons:

- requires both engine-side validation design and output-side resolution design
- slightly more moving parts than a pure external-tool solution
- needs disciplined documentation to avoid hidden coupling

Dependency impact:

- low if implemented with a shipped Docsmith Lua filter later
- avoids introducing a new external tool initially

Template impact:

- controlled and limited; templates keep layout ownership

Portability impact:

- good if the output mechanism stays within standard Pandoc capabilities

Complexity:

- medium, but with clearer boundaries than the other options

Fit with Docsmith architecture:

- strongest fit
- preserves Docsmith as the owner of authoring contracts, validation, and orchestration without pushing everything into templates or external tools

## Recommended First Implementation Approach

Recommended approach: Option D, the hybrid model, with these boundaries:

- Docsmith defines the authoring syntax and validation rules
- Docsmith validates IDs and references before rendering
- Docsmith preserves authored source boundaries through assembly for diagnostics
- Docsmith passes a Docsmith-owned, lightweight Pandoc Lua filter to resolve numbering and references in output
- templates remain responsible for layout and styling only

Why this is the best first implementation:

- it matches Docsmith's architecture better than a hard dependency on `pandoc-crossref`
- it keeps the authoring contract stable even if the output mechanism changes later
- it lets validation happen independently from the final rendering mechanics
- it avoids overloading templates with semantic correctness rules
- it keeps the engine neutral and reusable across consumer repositories

## Validation Model

This validation model is now implemented for figures and tables.

### Rule set for first implementation

- duplicate figure IDs should be errors
- duplicate table IDs should be errors
- invalid figure ID formats should be errors
- invalid table ID formats should be errors
- references to missing targets should be errors
- captions without IDs should be allowed
- unused IDs should not produce warnings in the first implementation

### Why missing targets are errors

Missing targets should be errors rather than warnings because:

- they indicate a broken document contract
- they produce misleading final output if allowed through
- they are usually cheap for authors to fix once surfaced precisely

### Possible later strictness controls

Possible future configuration, not part of the first implementation:

- strict mode for warning on captioned figures or tables without IDs
- warning mode for unused IDs
- future controls for section or appendix cross-reference namespaces

## Backward Compatibility and Migration

### Compatibility guarantees

- existing documents without figure or table IDs continue to build
- existing documents without cross-references continue to build
- existing figure and table Markdown syntax does not break
- cross-reference support is opt-in through added IDs and `@fig:` or `@tbl:` references

### Gradual migration

Consumer repositories should be able to migrate incrementally:

1. keep existing figures and tables unchanged
2. add IDs only to figures or tables that need stable references
3. replace manual prose such as `see the figure below` with explicit `@fig:` or `@tbl:` references
4. tighten validation later if the project wants stricter authoring discipline

This avoids forcing a repository-wide rewrite and keeps adoption low-risk.

### Mermaid and generated diagrams

Mermaid-generated diagrams should be treated as ordinary figures once they exist as image assets in the document repository or build workspace.

That means:

- the cross-reference model does not need a separate diagram concept
- figure numbering applies to generated diagrams the same way it applies to hand-created images
- any source-to-image workflow remains separate from the cross-reference design unless a later diagram-rendering design explicitly adds that capability

## Future Scope Boundaries

This design intentionally covers only:

- figures
- tables
- text references to figures and tables

Not part of this first design:

- section cross-references
- appendix cross-references
- equation references
- bibliography citation behavior
- automatic diagram generation
- template localization config

## Open Questions

1. Should Docsmith later support cross-references for sections and appendices through additional prefixes such as `sec:` and `app:`?
2. Should label language such as `Figure` versus `Figuur` remain template-controlled, or should Docsmith eventually expose a config-level language contract?
3. Should cross-reference strictness become configurable, for example warning on captioned figures or tables without IDs?
4. Should Docsmith later expose a machine-readable manifest of discovered IDs and resolved references for editor tooling or CI reporting?
5. Is a single generic attribute-based authoring contract sufficient across future output formats, especially DOCX?
6. Should Docsmith validate reference usage only in prose, or also in metadata and generated content if those surfaces later become referenceable?

## Current Implementation Boundary

The current implementation stays intentionally narrow:

1. validation enforces the figure/table authoring contract
2. assembly preserves the cross-reference syntax unchanged
3. PDF rendering uses a Docsmith-owned Lua filter to resolve `@fig:` and `@tbl:` references to simple English labels such as `Figure 1` and `Table 1`

Still out of scope:

- section or appendix references
- output-format parity beyond PDF
- localization of reference labels
- richer cross-reference formatting such as prefixes, suffixes, or grouped references
