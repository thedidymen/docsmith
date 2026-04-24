# Document Scaffolding Design

This document defines the next Docsmith design direction for document scaffolding.

It is a design document only. It does not change current CLI behavior.

## Current State

Docsmith already implements:

- `docsmith init document <target_dir>`
- `docsmith init template <target_dir>`

The current document scaffold is intentionally minimal and neutral. It creates:

- `spec.yaml`
- `references.bib`
- `csl/apa.csl`
- `assets/images/`
- `sections/00_intro.md`
- `sections/01_body.md`
- `sections/30_appendix.md`
- `README.md`

The current generated `spec.yaml` already reflects the present engine contract:

- explicit document zones
- an ordered front-matter generated TOC
- PDF as the only output format
- semantic versioning
- a relative `project.template` path

This is a good first baseline. The remaining design question is not whether Docsmith
should scaffold documents at all, but how far the engine should go beyond one neutral
starter structure.

## Goals

Docsmith scaffolding should:

- create a runnable, inspectable starting point for a new document directory
- reflect current engine concepts truthfully
- remain neutral across organizations and template families
- avoid bundling document-program assumptions into the engine
- leave room for richer consumer-side starter profiles without forcing them into Docsmith

Docsmith scaffolding should not:

- become an organization-specific document generator
- embed a branded or opinionated document program
- imply support for features that are not implemented
- replace consumer repositories such as `docsmith-demo`

## Main Design Questions

### What should `docsmith init document <path>` create?

Recommended first scaffold shape:

- `spec.yaml`
- `README.md`
- `sections/`
- `sections/00_intro.md`
- `sections/01_body.md`
- `sections/30_appendix.md`
- `assets/images/`
- `references.bib`
- `csl/apa.csl`

Recommended `spec.yaml` shape:

- explicit `front_matter`, `main_matter`, and `appendices`
- a generated front-matter TOC item
- `project.template` as a relative filesystem path
- `output.formats` containing only `pdf`
- fingerprint-based semantic versioning defaults

Reasoning:

- this keeps the scaffold immediately buildable once a template exists
- it demonstrates current structural concepts without overloading the starter
- it avoids legacy include-only structure in new projects

### Should it create a neutral minimal document only?

Yes, for the first-class engine scaffold.

Docsmith should continue to own one neutral minimal document scaffold only.

Why:

- the engine should define the minimal contract, not a family of document programs
- richer starters quickly become consumer- or template-specific
- one neutral scaffold is easier to keep synchronized with the real engine contract

Future profile support can exist later, but it should be additive and explicit rather
than replacing the neutral default.

### How should templates be referenced?

Recommended rule:

- `project.template` should remain a relative filesystem path from the document root

Recommended starter default:

- keep the current neutral placeholder style such as `templates/default`

Scaffolding should not:

- bundle an engine-owned template into the document scaffold
- fetch external templates
- assume a registry or template marketplace

Reasoning:

- this matches current engine behavior
- it keeps template ownership in document repositories or external template packs
- it avoids hidden coupling between scaffold shape and engine repository examples

### Should it support profiles later?

Yes, but not in the first scaffolding expansion.

Recommended later model:

- keep `docsmith init document <path>` as the neutral baseline
- add an explicit future form such as `docsmith init document <path> --profile <name>`
- constrain engine-owned profiles to neutral structural variations only

Possible future engine-owned profiles:

- `minimal`
- `report`
- `thesis-lite`

These should only be introduced if they differ by reusable engine-level concerns such as:

- starter zone layout
- starter file count
- starter citation assets
- whether appendix structure is pre-created

They should not encode:

- Hanze conventions
- program-specific metadata
- institution-specific title pages
- template branding

### Should it include example figure, table, and cross-references?

Not in the first neutral scaffold.

Recommended first behavior:

- include plain structural prose only
- reserve richer authoring examples for `examples/` and consumer repositories

Why:

- figure/table cross-reference examples add authoring complexity to the minimal starter
- they are useful as teaching material, but not required to understand the document shape
- examples belong better in documentation-oriented example documents than in every new scaffold

Possible later option:

- a future `--with-authoring-examples` flag, if there is strong evidence that users need it

### Should it include an example Mermaid diagram declaration?

No, not in the default scaffold.

Reasons:

- Mermaid requires an optional external dependency
- a default Mermaid declaration would make the starter look more complex than the neutral baseline
- diagram rendering is still a narrow engine feature, not a universal document requirement

If Docsmith later adds optional scaffolding enrichments, Mermaid should be opt-in only.

### Should it initialize git or never touch git?

Recommended rule:

- Docsmith scaffolding should never initialize git

Reasons:

- git initialization is repository policy, not document-structure policy
- some users scaffold inside existing repositories
- touching git would exceed the engine's document-build responsibility

If users want git initialization, they should run it themselves or use repository-level tooling.

### What belongs in Docsmith vs consumer repos?

Docsmith should own:

- one neutral starter document scaffold
- one neutral template scaffold
- truthful starter defaults that match current engine behavior
- future neutral profile mechanics, if they are justified

Consumer repositories should own:

- branded or domain-specific starter profiles
- institution/program metadata conventions
- template packs tied to one template family
- richer authoring guides and teaching-oriented starter content

## Recommended First Scaffold Contract

The first-class Docsmith scaffold should remain deliberately small:

1. A neutral document directory with explicit zones and a TOC.
2. Citation placeholders because bibliography and CSL are current first-class engine concepts.
3. An images directory because ordinary figures are common and low-cost to reserve.
4. No predeclared cross-references, Mermaid diagrams, or template-coupled content.
5. No git actions.

This keeps the scaffold aligned with the current engine contract while avoiding starter
content that looks like a product profile.

## Relationship to `docsmith-demo`

`docsmith-demo` should not be treated as the engine scaffold.

Recommended relationship:

- `docsmith init document` creates the smallest neutral engine-shaped starting point
- `docsmith-demo` remains the richer consumer-side reference for realistic authoring and workflow patterns
- future migrations from `docsmith-demo` ideas into Docsmith should happen only when a pattern has proved reusable and neutral

That means:

- the demo starter profile can inform future profile design
- the engine should not copy the demo starter profile directly
- Hanze-specific or report-program assumptions should stay outside Docsmith

## Backward Compatibility

Current scaffold behavior should remain valid.

If profile support is added later:

- the current neutral scaffold should remain the default
- existing `docsmith init document <path>` usage should not break
- richer profiles must be opt-in

## Explicitly Postponed

Not part of the first scaffold expansion:

- organization-specific starter profiles
- template downloading or template registries
- automatic template creation during `init document`
- example figure/table/cross-reference content by default
- example Mermaid declarations by default
- git initialization
- multi-document repository bootstrapping
- profile-specific metadata questionnaires

## Open Questions

Questions worth revisiting after the first scaffolding design is implemented:

1. Should Docsmith offer a combined workflow such as "create document and template together" without blurring ownership?
2. Should neutral profiles exist at all, or is one minimal scaffold enough?
3. Should citation assets stay in the default scaffold forever, or become optional?
4. Should a future profile mechanism be flag-based, subcommand-based, or config-driven?
5. Should `docsmith init` eventually support repository-level scaffolding separately from document-level scaffolding?

## Recommended Next Implementation Slice

The smallest coherent implementation slice after this design is:

1. Document the current scaffold contract more explicitly in CLI-facing docs.
2. Keep the current default scaffold behavior intact.
3. Add one small preparatory CLI/config design hook for future profiles, without changing the default scaffold shape yet.

That keeps the first follow-up change narrow and backward-compatible.
