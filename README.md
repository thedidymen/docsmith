# Docsmith

Docsmith is a Python CLI for building structured Markdown document directories into versioned PDF files using Pandoc and document-local LaTeX templates.

## Current MVP

What works today:

- load document configuration from `spec.yaml`
- discover and order Markdown source files
- assemble sources into a combined Markdown build artifact
- validate document inputs before building
- render PDF with Pandoc and document-local templates
- support bibliography and CSL paths when configured
- write versioned output filenames
- automatically bump semantic versions when effective build inputs change
- include optional git short hash metadata in output filenames
- avoid overwriting existing outputs with collision suffixes

What does not work yet:

- DOCX output
- multi-format builds

## Supported Output Formats

Current supported build output:

- PDF

The config model already contains `output.formats`, but the implemented build flow currently renders PDF only.

## Installation

### 1. Install Python

Docsmith requires Python 3.11 or newer.

Check your version:

```bash
python3 --version
```

### 2. Install external PDF build dependencies

PDF builds require:

- `pandoc`
- a LaTeX engine compatible with the document template defaults
- `xelatex` available on `PATH`

#### macOS

Install Pandoc:

```bash
brew install pandoc
```

Install a LaTeX distribution that provides `xelatex`:

```bash
brew install --cask mactex-no-gui
```

If `xelatex` is still not found after installation, restart the shell or ensure the TeX binary directory is on `PATH`.

#### Linux

Install Pandoc and a TeX distribution with `xelatex`.

Debian/Ubuntu example:

```bash
sudo apt update
sudo apt install pandoc texlive-xetex
```

Fedora example:

```bash
sudo dnf install pandoc texlive-xetex
```

#### Windows

Install:

- Python 3.11+
- Pandoc
- a TeX distribution with `xelatex`, such as MiKTeX or TeX Live

Common approach:

1. Install Python from python.org
2. Install Pandoc from pandoc.org
3. Install MiKTeX or TeX Live
4. Open a new terminal so `pandoc` and `xelatex` are available on `PATH`

Check both tools:

```powershell
pandoc --version
xelatex --version
```

## Python Environment Setup

Create and activate a virtual environment, then install Docsmith in editable mode.

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Quickstart

List shared example templates:

```bash
cd examples
docsmith templates
```

Validate the authoring guide example:

```bash
docsmith validate examples/documents/authoring_guide
```

Build the authoring guide example:

```bash
docsmith build examples/documents/authoring_guide
```

Run tests:

```bash
pytest
```

## Example Document

Docsmith includes a shared example repository layout under `examples/`:

- `examples/templates/`
- `examples/documents/authoring_guide/`
- `examples/documents/docsmith_architecture/`
- `examples/documents/technical_report_demo/`

This keeps the repository self-contained while avoiding template duplication across
multiple documents.

The main feature-complete authoring example lives at
`examples/documents/authoring_guide`.

The shared example template set includes:

- `examples/templates/academic_thesis`
- `examples/templates/technical_report`

It demonstrates:

- title page metadata
- automatic table of contents
- ordered Markdown sections
- basic Markdown authoring patterns
- a repository-local image asset
- a Markdown table
- a bibliography-backed citation with a local CSL file
- appendix handling via `<!-- APPENDIX -->`
- visible version metadata on the generated title page
- document-local template paths in `spec.yaml`

Validate it:

```bash
docsmith validate examples/documents/authoring_guide
```

Build it:

```bash
docsmith build examples/documents/authoring_guide
```

Expected behavior:

- validation prints a `PASS` or `FAIL` line per check
- build prints whether content changes were detected
- build prints whether the semantic version was kept or bumped
- build prints the final output path

The smaller shared-template demo remains available at
`examples/documents/technical_report_demo`, but the authoring guide is the better first
example for new users.

To try the alternate layout, change `project.template` in the authoring guide `spec.yaml`
from `../../templates/academic_thesis` to `../../templates/technical_report` and rebuild.

## Architecture Example

Docsmith also includes an architecture-style example document at
`examples/documents/docsmith_architecture`.

It demonstrates:

- a neutral report template
- architecture-oriented section structure
- a repository-local diagram image
- a component table
- an appendix
- version-aware build output

Validate it:

```bash
docsmith validate examples/documents/docsmith_architecture
```

Build it:

```bash
docsmith build examples/documents/docsmith_architecture
```

This example doubles as lightweight high-level architecture documentation for the current
Docsmith system.

## Versioning Behavior

Docsmith separates semantic version from build identity.

### Semantic version

- `spec.yaml` defines `versioning.initial_version`
- the evolving build version is stored in `build/.docsmith-state.json`
- `spec.yaml` is not rewritten during builds

### Automatic bumping

For `semver` documents:

- first build uses `initial_version`
- if the build fingerprint is unchanged, the semantic version stays the same
- if the fingerprint changed, Docsmith bumps `PATCH`

Fingerprint inputs currently include:

- `spec.yaml`
- included Markdown source files
- active document-local template files
- bibliography and CSL files when configured

### Build identity metadata

- if `versioning.include_git_hash` is enabled and git is available, the short git hash is added to the output filename
- if git is unavailable, builds still work normally

### Collision suffixes

If an output file already exists, Docsmith avoids overwriting it by adding suffixes such as:

- `_01`
- `_02`

### CLI overrides

The build command supports:

```bash
docsmith build <document_dir> --bump patch
docsmith build <document_dir> --bump minor
docsmith build <document_dir> --bump major
docsmith build <document_dir> --no-bump
```

## Build Artifacts

Docsmith writes two main artifact areas inside a document directory.

### `build/`

Internal build artifacts:

- `combined.md`
- `runtime-metadata.yaml`
- `.docsmith-state.json`

Purpose:

- assembled Markdown for rendering
- runtime metadata passed to Pandoc
- persisted version/fingerprint state for future builds

### `output/`

Final rendered files:

- versioned PDF output, for example:
  - `technical_report_demo_v0.1.0.pdf`
  - `technical_report_demo_v0.1.1_ab12cd3.pdf`
  - `technical_report_demo_v0.1.1_ab12cd3_01.pdf`

## CLI Commands

### `docsmith build <document_dir>`

Builds the document and prints:

- change detection status
- semantic version result
- git hash if available
- final output path

### `docsmith validate <document_dir>`

Validates the document configuration and inputs without rendering.

Checks:

- `spec.yaml` loading
- input root existence
- included Markdown existence
- template existence and required files
- bibliography and CSL path existence
- output directory resolution and creatability

### `docsmith templates`

Lists template directories under `./templates` in the current working tree.

## Minimal Config Example

```yaml
project:
  template: ../../templates/academic_thesis

metadata:
  title: Docsmith Example Document
  author: Docsmith Contributors

document:
  input_root: sections

output:
  directory: output
  basename: technical_report_demo
  formats:
    - pdf

versioning:
  strategy: semver
  initial_version: 0.1.0
  include_git_hash: false
```

## Troubleshooting

### `Pandoc executable not found`

Cause:

- `pandoc` is not installed
- `pandoc` is installed but not on `PATH`

Check:

```bash
pandoc --version
```

### `xelatex` not found or PDF build fails in LaTeX

Cause:

- no TeX distribution is installed
- `xelatex` is not on `PATH`
- the installed TeX packages are incomplete

Check:

```bash
xelatex --version
```

If needed, install or repair your TeX distribution, then retry the build.

## Status

Docsmith is currently a real but narrow MVP:

- PDF build flow is implemented
- validation is implemented
- semantic version bumping is implemented
- document-local templates are implemented
- broader roadmap items such as DOCX output are not yet available
