# Docsmith Diagram Rendering Design

## Status

This document defines the proposed Docsmith engine design for engine-managed diagram rendering, starting with Mermaid.

It is a design and documentation slice only.

Not implemented:

- engine-managed Mermaid rendering
- diagram declarations in `spec.yaml`
- Markdown rewriting for diagram sources
- renderer dependency management for Mermaid
- diagram-specific validation beyond current generic asset handling

The purpose of this document is to move diagram generation from consumer-side scripts toward a reproducible engine-owned build workflow without making Docsmith template-specific or repository-specific.

## Current State

The current workflow in consumer repositories such as `docsmith-demo` is:

- Mermaid source files are authored as `.mmd` files
- a repository-local script renders those sources into generated PNG assets
- Markdown references the generated PNG as an ordinary figure
- Pandoc and templates then see only a normal image asset

That works as a short-term consumer convention, but it is not a good long-term engine story.

Current drawbacks:

- it introduces an extra manual or repo-local pre-build step
- generated assets can become stale relative to their `.mmd` sources
- build reproducibility depends on a consumer-owned script outside Docsmith's build contract
- workflow quality and behavior can drift between consumer repositories
- fingerprinting and versioning currently see only the image asset path used in Markdown, not the real diagram source workflow

## Desired Engine Behavior

The future Docsmith workflow should make diagram rendering part of the build system rather than a sidecar convention.

Desired behavior:

- Mermaid source files are either declared explicitly or referenced through a supported authoring contract
- Docsmith validates diagram sources before rendering
- diagram rendering happens before Pandoc consumes the final Markdown
- generated image assets are written into a build-managed location
- Markdown or Pandoc sees stable image paths that resolve through Docsmith's resource-path handling
- diagram source files and renderer configuration affect the build fingerprint
- stale generated assets stop mattering because the build owns regeneration

## Authoring Model Options

### Option A: Authors still reference generated image paths

Interpretation:

- authors keep writing Markdown against `assets/generated/foo.png`
- Docsmith optionally regenerates that file from a known `.mmd` source

Pros:

- smallest disruption to existing Markdown
- best backward compatibility
- minimal Pandoc behavior change

Cons:

- source-of-truth remains ambiguous
- generated paths still look like consumer-managed assets
- Docsmith needs some other place to learn which `.mmd` source owns which generated image
- easier for stale generated files to remain conceptually normalized in authoring

Portability:

- high, because Pandoc still sees ordinary image paths

Pandoc compatibility:

- excellent

Template impact:

- none

Validation impact:

- validation must map generated assets back to source declarations elsewhere

Authoring simplicity:

- simple for authors, but hides important build semantics

Fit:

- acceptable for migration, weak as the long-term contract

### Option B: Authors reference `.mmd` files directly and Docsmith rewrites or links them

Interpretation:

- Markdown points to Mermaid source paths
- Docsmith turns those references into build-managed rendered image paths

Pros:

- source-of-truth is explicit in Markdown
- no duplicate image path convention in authored content
- build semantics become clearer

Cons:

- requires Markdown rewriting or AST/path transformation
- raw Markdown is no longer directly renderable outside Docsmith
- output format negotiation becomes more explicit because `.mmd` is not directly a Pandoc image

Portability:

- medium

Pandoc compatibility:

- depends on Docsmith rewriting before Pandoc

Template impact:

- none if rewritten to ordinary image paths before Pandoc

Validation impact:

- strong, because source paths are explicit

Authoring simplicity:

- good once documented

Fit:

- good for explicit engine ownership, but more invasive as a first implementation

### Option C: Authors use fenced Mermaid blocks in Markdown

Interpretation:

- diagrams live inline as fenced code blocks such as ```` ```mermaid ````
- Docsmith renders those blocks into image assets before Pandoc

Pros:

- very author-friendly
- keeps source close to narrative context
- no separate asset declaration needed for simple diagrams

Cons:

- requires Markdown parsing and transformation, not just path management
- harder asset naming and caching story
- inline diagram source may be awkward for larger diagrams
- makes it harder to reuse one diagram across sections or documents

Portability:

- medium to low without Docsmith preprocessing

Pandoc compatibility:

- requires transformation before final rendering

Template impact:

- none if transformed cleanly into normal figures

Validation impact:

- higher complexity because source is embedded in Markdown

Authoring simplicity:

- high for small diagrams

Fit:

- attractive later, but too broad for the first engine-owned implementation

### Option D: Explicit diagram declarations in `spec.yaml`

Interpretation:

- diagrams are declared in config with source path, output format, and optional rendering settings
- Markdown references a stable rendered output path or a declared logical name

Pros:

- explicit and inspectable engine contract
- diagram sources, output names, and rendering settings are centralized
- validation is straightforward
- fingerprinting can be precise
- good fit for Docsmith's incremental schema-driven design

Cons:

- adds config overhead
- authors must keep Markdown and config aligned
- may feel heavier than direct Markdown-based authoring for small documents

Portability:

- high once rendered assets are exposed as normal image paths to Pandoc

Pandoc compatibility:

- excellent after Docsmith renders assets before Pandoc

Template impact:

- none

Validation impact:

- strong and explicit

Authoring simplicity:

- medium, but predictable

Fit:

- strongest fit for the first implementation

## Recommended First Authoring Model

Recommended first path: Option D, explicit diagram declarations in `spec.yaml`, while keeping existing Markdown image references in place.

Recommended shape:

- document repositories declare Mermaid diagrams in config
- each declaration maps a source `.mmd` file to a build-managed rendered asset name
- authored Markdown continues to reference an ordinary image path
- Docsmith ensures that rendered image exists at the expected build-managed location before Pandoc runs

Why this is the best first step:

- it keeps Docsmith explicit and inspectable
- it avoids introducing Markdown rewriting as part of the first engine-owned diagram feature
- it matches Docsmith's existing preference for schema-driven structure over implicit behavior
- it preserves template neutrality because Pandoc still sees ordinary images
- it allows gradual migration from consumer-generated PNG assets to engine-generated build assets

This also leaves room for later support of inline Mermaid blocks or direct `.mmd` references without locking the first implementation to those more invasive models.

## Rendering Backend Options

### Mermaid CLI (`mmdc`)

Interpretation:

- Docsmith invokes Mermaid CLI directly

Pros:

- purpose-built for Mermaid
- common workflow in documentation ecosystems
- straightforward CLI invocation

Cons:

- adds a Node-based external dependency
- local setup burden is non-trivial
- CLI behavior depends on browser/runtime support under the hood

Dependency impact:

- moderate

Reproducibility:

- good if version-pinned and documented

CI suitability:

- good once installed explicitly

Local setup burden:

- moderate to high

Security considerations:

- rendering untrusted diagram sources still requires care because browser-backed tooling is involved

Fit:

- strongest first backend choice because it is direct and predictable enough without overbuilding infrastructure

### Playwright/browser-based rendering

Interpretation:

- Docsmith orchestrates rendering through browser automation directly

Pros:

- flexible
- could support richer rendering control later

Cons:

- large implementation and dependency burden
- significantly more moving parts than Docsmith should own first

Dependency impact:

- high

Reproducibility:

- potentially good, but operationally heavy

CI suitability:

- acceptable, but expensive to maintain

Local setup burden:

- high

Security considerations:

- broad browser execution surface

Fit:

- poor for a first implementation

### Dockerized renderer

Interpretation:

- Docsmith shells out to a containerized Mermaid renderer

Pros:

- stronger environment control
- easier version pinning in some CI environments

Cons:

- assumes Docker availability
- poor local ergonomics for many users
- makes builds heavier and less portable

Dependency impact:

- high

Reproducibility:

- high when available

CI suitability:

- good in Docker-friendly CI

Local setup burden:

- high

Security considerations:

- better isolation, but broader operational complexity

Fit:

- useful only as a later optional backend, not the first default path

### External pre-build command hook

Interpretation:

- Docsmith exposes a hook and leaves rendering to a user-provided command

Pros:

- flexible
- avoids immediate backend ownership

Cons:

- weakens reproducibility
- pushes the hard problem back to consumer repos
- creates inconsistent behavior across users and repositories

Dependency impact:

- unspecified and user-dependent

Reproducibility:

- weak

CI suitability:

- variable

Local setup burden:

- variable

Security considerations:

- potentially broad and hard to reason about

Fit:

- poor if the goal is to move away from consumer-side scripts

### Pluggable renderer interface

Interpretation:

- Docsmith defines an abstract renderer contract with interchangeable backends

Pros:

- architecturally flexible
- future-proof in theory

Cons:

- overdesigned for the first supported diagram type
- creates plugin/extension surface area before the base workflow is proven

Dependency impact:

- depends on chosen implementations

Reproducibility:

- potentially good, but only with disciplined implementation

CI suitability:

- depends on concrete backend

Local setup burden:

- depends on concrete backend

Security considerations:

- wider surface area

Fit:

- not appropriate for the first implementation

## Recommended First Backend

Recommended first backend: Mermaid CLI (`mmdc`).

Why:

- it is the narrowest engine-owned backend that still makes Mermaid rendering reproducible
- it matches the immediate user need without requiring a generalized renderer framework
- it allows clear dependency checks and clear error reporting
- it preserves room to add optional backends later if real consumer pressure justifies them

Docsmith should not expose a pluggable rendering backend yet. It should first prove one explicit Mermaid workflow well.

## Engine Responsibilities

Docsmith should own:

- validating declared Mermaid source paths
- validating supported diagram type declarations
- invoking the Mermaid renderer before Pandoc
- writing rendered assets into a build-managed directory
- ensuring Pandoc `--resource-path` includes those generated assets
- including Mermaid source files and renderer configuration in the build fingerprint
- surfacing clear errors for missing renderer dependencies
- making stale generated output irrelevant by regenerating build-managed assets
- keeping the workflow neutral and generic rather than Hanze-specific

Docsmith should not own:

- document-specific diagram content
- template-specific figure styling
- hardcoded organization themes
- arbitrary consumer-side build scripting behavior

## Consumer and Template Responsibilities

Document repositories and templates should continue to own:

- Mermaid diagram content
- diagram themes or style inputs if Docsmith exposes them as explicit config later
- placement of diagrams in Markdown narrative flow
- figure captions and cross-reference IDs
- template styling of figures in rendered output

This keeps the engine focused on build orchestration while templates and documents keep presentation ownership.

## Build Lifecycle

Recommended lifecycle:

1. Load `spec.yaml`
2. Validate diagram declarations and source paths
3. Render diagrams into a build-managed directory before Markdown assembly completes for rendering
4. Assemble Markdown with image references that point to the rendered output paths Docsmith expects
5. Pass Pandoc a resource path that includes both build-managed assets and source-document assets
6. Render PDF normally

Recommended timing:

- diagram rendering should happen before Pandoc
- for the first implementation, it should happen before or during build preparation, prior to invoking Pandoc
- it does not need to happen before logical document discovery

Why this timing works:

- Pandoc still sees ordinary image references
- generated diagrams are available for layout and figure handling
- cross-references continue to work because diagrams remain ordinary figures from Pandoc's perspective

## Validation Model

Conceptual validation rules for the first implementation:

- missing declared diagram source: error
- unsupported diagram type: error
- renderer unavailable: validation warning, build error
- invalid Mermaid syntax: build error surfaced clearly from renderer output
- stale generated output: irrelevant because build-managed rendering regenerates assets

### Why renderer unavailability should be a validation warning but a build error

Validation should warn rather than fail hard for missing Mermaid tooling because:

- `docsmith validate` should continue to provide useful structural feedback in environments that do not have optional diagram tooling installed
- some documents may not declare diagrams at all, or may be validated before full build tooling is ready

Build should fail if Mermaid rendering is required and unavailable because:

- the output would be incomplete or incorrect
- reproducibility depends on the renderer actually running

## Fingerprinting and Versioning

The build fingerprint should include:

- Mermaid source `.mmd` files
- diagram declarations in `spec.yaml`
- diagram renderer configuration such as output format, theme, or scaling if Docsmith later exposes those fields
- engine-owned diagram-rendering code or helper files when they affect output

The build fingerprint should not treat generated diagram images as the source of truth.

Rationale:

- the source diagram and renderer settings are the meaningful inputs
- generated assets are build products and should be replaceable
- version bumps should track semantic input changes, not leftover generated files

## Backward Compatibility and Migration

Compatibility rules:

- the existing image-based Mermaid workflow must keep working
- engine-supported Mermaid rendering should be opt-in
- existing documents that reference committed PNG assets must not break
- consumer repositories can migrate gradually

Recommended migration path:

1. keep existing PNG-based diagrams as they are
2. add explicit diagram declarations for selected Mermaid sources
3. move those diagrams to build-managed rendering while keeping ordinary Markdown figure usage
4. stop committing generated assets once the engine-managed path is trusted

This avoids a breaking change and keeps document repositories in control of migration timing.

## Open Questions

1. Should the first engine-owned diagram feature support only Mermaid, or should the schema already anticipate more diagram types?
2. Should rendered outputs be build-only artifacts, or should some repositories still commit them for preview workflows?
3. Should Mermaid theme settings be configured globally, per document, or per diagram?
4. Should future DOCX support prefer PNG, SVG, or format-dependent output choices?
5. Should diagrams be declared in `spec.yaml`, discovered from Markdown, or both?
6. How much sandboxing or execution isolation should Docsmith require when invoking Mermaid rendering tools?

## Recommended Next Implementation Slice

The next implementation slice should stay narrow:

1. Add a minimal `spec.yaml` design for explicit Mermaid diagram declarations.
2. Add validation for declared Mermaid source paths and renderer availability.
3. Add a build-managed Mermaid rendering step using `mmdc`.
4. Write rendered outputs into the build directory and integrate those paths with Pandoc resource handling.
5. Add focused tests for dependency checks, path resolution, fingerprinting, and build-managed asset generation.

That path keeps the feature explicit, reproducible, and neutral without introducing plugin infrastructure or consumer-side workarounds.
