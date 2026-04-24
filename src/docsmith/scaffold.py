"""Project and template scaffolding for Docsmith."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent


class ScaffoldError(RuntimeError):
    """Raised when a scaffold target cannot be created safely."""


@dataclass(frozen=True)
class ScaffoldResult:
    """Information about a generated scaffold."""

    kind: str
    target_dir: Path
    created_paths: tuple[Path, ...]


def initialize_document_scaffold(target_dir: Path) -> ScaffoldResult:
    """Create a generic document project scaffold."""
    target_dir = _prepare_target_dir(target_dir)
    slug = _slugify(target_dir.name or "document")

    files = {
        "spec.yaml": _document_spec(slug),
        "references.bib": _references_bib(),
        "csl/apa.csl": _apa_csl(),
        "sections/00_intro.md": _section_intro(),
        "sections/01_body.md": _section_body(),
        "sections/30_appendix.md": _section_appendix(),
        "README.md": _document_readme(target_dir.name),
    }
    created_paths = _write_files(target_dir, files, directories=("assets/images",))
    return ScaffoldResult(kind="document", target_dir=target_dir, created_paths=created_paths)


def initialize_template_scaffold(target_dir: Path) -> ScaffoldResult:
    """Create a generic PDF template scaffold."""
    target_dir = _prepare_target_dir(target_dir)

    files = {
        "template.tex": _template_tex(),
        "defaults.yaml": _template_defaults(),
        "metadata.yaml": _template_metadata(),
        "partials/titlepage.tex": _partial_titlepage(),
        "partials/before-body.tex": _partial_before_body(),
        "partials/after-body.tex": _partial_after_body(),
        "README.md": _template_readme(target_dir.name),
    }
    created_paths = _write_files(target_dir, files)
    return ScaffoldResult(kind="template", target_dir=target_dir, created_paths=created_paths)


def _prepare_target_dir(target_dir: Path) -> Path:
    resolved_target = target_dir.resolve()

    if resolved_target.exists():
        if not resolved_target.is_dir():
            raise ScaffoldError(f"Target path exists and is not a directory: {resolved_target}")
        if any(resolved_target.iterdir()):
            raise ScaffoldError(f"Target directory already exists and is not empty: {resolved_target}")
    else:
        resolved_target.mkdir(parents=True, exist_ok=True)

    return resolved_target


def _write_files(
    target_dir: Path,
    files: dict[str, str],
    *,
    directories: tuple[str, ...] = (),
) -> tuple[Path, ...]:
    created_paths: list[Path] = []
    for relative_path, content in files.items():
        output_path = target_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        created_paths.append(output_path)

    for relative_path in directories:
        output_path = target_dir / relative_path
        output_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(output_path)

    return tuple(created_paths)


def _slugify(value: str) -> str:
    cleaned = [
        character.lower() if character.isalnum() else "_"
        for character in value.strip()
    ]
    slug = "".join(cleaned).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "document"


def _document_spec(slug: str) -> str:
    return dedent(
        f"""\
        project:
          slug: {slug}
          template: templates/default

        metadata:
          title: Example Document
          subtitle: Starter structure for a Docsmith project
          author: Example Author
          date: "2026-01-01"

        document:
          input_root: sections
          front_matter:
            - generated: toc
              title: Contents
              numbered: false
              listed: true
          main_matter:
            - file: 00_intro.md
            - file: 01_body.md
          appendices:
            - file: 30_appendix.md

        citations:
          bibliography: references.bib
          csl: csl/apa.csl

        output:
          directory: output
          basename: {slug}
          formats:
            - pdf

        versioning:
          strategy: semver
          initial_version: 0.1.0
          include_git_hash: true
        """
    )


def _references_bib() -> str:
    return dedent(
        """\
        @book{sample-reference,
          author = {Example, Avery},
          title = {Example Reference for Docsmith},
          year = {2024},
          publisher = {Neutral Press}
        }
        """
    )


def _apa_csl() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="utf-8"?>
        <style xmlns="http://purl.org/net/xbiblio/csl" version="1.0" class="in-text">
          <info>
            <title>Placeholder APA Style</title>
            <id>https://example.com/docsmith-placeholder-apa</id>
            <updated>2026-01-01T00:00:00+00:00</updated>
            <rights license="https://creativecommons.org/publicdomain/zero/1.0/">
              This placeholder CSL file should be replaced with a project-approved APA style.
            </rights>
          </info>
          <citation>
            <layout prefix="(" suffix=")" delimiter="; ">
              <text variable="author"/>
              <text variable="issued" prefix=", "/>
            </layout>
          </citation>
          <bibliography>
            <layout suffix=".">
              <text variable="author"/>
              <text variable="issued" prefix=" (" suffix=")."/>
              <text variable="title" prefix=" "/>
              <text variable="publisher" prefix=" "/>
            </layout>
          </bibliography>
        </style>
        """
    )


def _section_intro() -> str:
    return dedent(
        """\
        # Introduction

        This section introduces the document scope, audience, and intent.

        Use explicit `front_matter`, `main_matter`, `back_matter`, and
        `appendices` zones in `spec.yaml` to keep the build structure
        explicit and reviewable.
        """
    )


def _section_body() -> str:
    return dedent(
        """\
        # Main Content

        Add the main analysis, narrative, or specification content here.

        This starter project keeps assets in `assets/images` and citations in
        `references.bib`. A sample citation looks like [@sample-reference].
        """
    )


def _section_appendix() -> str:
    return dedent(
        """\
        # Appendix

        Place supporting material, reference tables, or supplementary notes here.
        """
    )


def _document_readme(project_name: str) -> str:
    return dedent(
        f"""\
        # {project_name}

        This directory is a minimal Docsmith document scaffold.

        Included structure:

        - `spec.yaml` defines document metadata, explicit document zones, a structural
          front-matter TOC, PDF output, and semantic versioning.
        - `sections/` contains starter Markdown files for the main body and appendix.
        - `references.bib` and `csl/apa.csl` provide starter citation assets.
        - `assets/images/` is reserved for document-local figures.

        Next steps:

        1. Create or copy a local template pack and update `project.template` if needed.
        2. Replace the placeholder metadata, bibliography entries, and CSL file.
        3. Run `docsmith validate .` and then `docsmith build .`.
        """
    )


def _template_tex() -> str:
    return dedent(
        r"""\
        % Minimal neutral Pandoc template for Docsmith PDF builds.
        \documentclass[$if(fontsize)$$fontsize$,$endif$$if(papersize)$$papersize$paper,$endif$article]{article}
        \usepackage[T1]{fontenc}
        \usepackage[utf8]{inputenc}
        \usepackage{graphicx}
        \usepackage{geometry}
        \usepackage{longtable}
        \usepackage{booktabs}
        \usepackage{array}
        \usepackage{calc}
        \usepackage{hyperref}
        \usepackage{xcolor}
        \usepackage{fancyvrb}
        \newcounter{none}
        \providecommand{\tightlist}{%
          \setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
        \providecommand{\pandocbounded}[1]{#1}
        \DefineVerbatimEnvironment{Highlighting}{Verbatim}{commandchars=\\\{\}}
        \newenvironment{Shaded}{}{}
        \newcommand{\AlertTok}[1]{#1}
        \newcommand{\AnnotationTok}[1]{#1}
        \newcommand{\AttributeTok}[1]{#1}
        \newcommand{\BaseNTok}[1]{#1}
        \newcommand{\BuiltInTok}[1]{#1}
        \newcommand{\CharTok}[1]{#1}
        \newcommand{\CommentTok}[1]{#1}
        \newcommand{\ConstantTok}[1]{#1}
        \newcommand{\ControlFlowTok}[1]{#1}
        \newcommand{\DataTypeTok}[1]{#1}
        \newcommand{\DecValTok}[1]{#1}
        \newcommand{\DocumentationTok}[1]{#1}
        \newcommand{\DoubleTok}[1]{#1}
        \newcommand{\ErrorTok}[1]{#1}
        \newcommand{\ExtensionTok}[1]{#1}
        \newcommand{\FloatTok}[1]{#1}
        \newcommand{\FunctionTok}[1]{#1}
        \newcommand{\ImportTok}[1]{#1}
        \newcommand{\InformationTok}[1]{#1}
        \newcommand{\KeywordTok}[1]{#1}
        \newcommand{\NormalTok}[1]{#1}
        \newcommand{\OperatorTok}[1]{#1}
        \newcommand{\OtherTok}[1]{#1}
        \newcommand{\PreprocessorTok}[1]{#1}
        \newcommand{\RegionMarkerTok}[1]{#1}
        \newcommand{\SpecialCharTok}[1]{#1}
        \newcommand{\SpecialStringTok}[1]{#1}
        \newcommand{\StringTok}[1]{#1}
        \newcommand{\VariableTok}[1]{#1}
        \newcommand{\VerbatimStringTok}[1]{#1}
        \newcommand{\WarningTok}[1]{#1}
        \newcommand{\citeproctext}{}
        \newenvironment{CSLReferences}[2]
          {\begin{thebibliography}{99}}
          {\end{thebibliography}}
        \newcommand{\CSLBlock}[1]{#1\hfill\break}
        \newcommand{\CSLLeftMargin}[1]{#1}
        \newcommand{\CSLRightInline}[1]{#1\break}
        \newcommand{\CSLIndent}[1]{\hspace{1.5em}#1}

        $if(geometry)$
        \geometry{$for(geometry)$$geometry$$sep$,$endfor$}
        $endif$

        \hypersetup{
          colorlinks=true,
          linkcolor=black,
          urlcolor=blue
        }

        \begin{document}

        $if(title)$
        {\LARGE\bfseries $title$\par}
        $endif$
        $if(subtitle)$
        \vspace{0.5em}
        {\large $subtitle$\par}
        $endif$
        \vspace{1em}
        $if(author)$
        {\normalsize $author$\par}
        $endif$
        $if(date)$
        {\normalsize $date$\par}
        $endif$
        $if(version)$
        {\small Version $version$\par}
        $endif$
        $if(git_hash)$
        {\small Git $git_hash$\par}
        $endif$
        \vspace{1.5em}

        $if(toc)$
        \tableofcontents
        \clearpage
        $endif$

        $body$

        \end{document}
        """
    )


def _template_defaults() -> str:
    return dedent(
        """\
        from: markdown+raw_tex
        pdf-engine: xelatex
        toc: false
        number-sections: true
        citeproc: true
        standalone: true
        before-body:
          - partials/before-body.tex
        after-body:
          - partials/after-body.tex
        variables:
          papersize: a4
          geometry:
            - margin=2.5cm
        """
    )


def _template_metadata() -> str:
    return dedent(
        """\
        lang: en-US
        """
    )


def _partial_titlepage() -> str:
    return dedent(
        r"""\
        % Optional title page partial.
        % This file is not wired in by default. Use it when you want a dedicated
        % cover page or custom title block beyond the default template heading.
        """
    )


def _partial_before_body() -> str:
    return dedent(
        r"""\
        % Insert raw LaTeX here when the document needs material before the body.
        % Keep this neutral and document-specific rather than engine-specific.
        """
    )


def _partial_after_body() -> str:
    return dedent(
        r"""\
        % Insert raw LaTeX here when the document needs closing material after the body.
        """
    )


def _template_readme(template_name: str) -> str:
    return dedent(
        f"""\
        # {template_name}

        This directory is a minimal Docsmith template scaffold for PDF builds.

        Included structure:

        - `template.tex` is the main Pandoc LaTeX template.
        - `defaults.yaml` defines generic PDF defaults and partial hooks.
        - `metadata.yaml` holds template-level metadata defaults for future use.
        - `partials/` contains optional LaTeX fragments for body wrappers or a
          custom title page workflow.

        Usage:

        1. Point a document `project.template` setting at this directory.
        2. Adjust `defaults.yaml` for PDF engine, layout, or Pandoc flags.
        3. Extend `template.tex` and partials with document-repository-specific styling.
        """
    )
