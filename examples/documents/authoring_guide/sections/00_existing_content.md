# Overview

This example document is the main Docsmith MVP showcase. It demonstrates the current
build flow with:

- ordered Markdown section assembly
- title page metadata from `spec.yaml`
- automatic table of contents generation from the document-local `academic_thesis` template
- citation processing with bibliography and CSL files
- a figure, a table, and appendix content
- visible build version metadata on the generated title page

The document is intentionally small enough to read in the repository, while still
exercising the features that currently matter for real builds.

The goal of the project is a generic Markdown-to-document engine. A practical framing
for that goal is to keep document content declarative and push rendering concerns into
templates and build tooling [@wilson2021].

# Build Workflow

Docsmith expects a document directory with a `spec.yaml` file, ordered or discoverable
Markdown inputs, and a document-local template selection. During a build it validates inputs,
assembles source Markdown, writes runtime metadata, resolves an output version, and then
invokes Pandoc for PDF rendering.

```{=latex}
\begin{figure}[htbp]
\centering
\fbox{
  \parbox{0.82\textwidth}{
    \centering
    \textbf{Docsmith MVP build flow}\\[0.75em]
    spec.yaml + sections + template + citations\\
    $\downarrow$\\
    validation + assembly + version resolution\\
    $\downarrow$\\
    Pandoc + document-local academic thesis template\\
    $\downarrow$\\
    versioned PDF output
  }
}
\caption{Conceptual build flow shown as a simple figure rendered through raw LaTeX.}
\label{fig:docsmith-workflow}
\end{figure}
```

The generated title page exposes runtime version metadata automatically. When git hash
support is enabled, the build can also show short revision traceability alongside the
semantic version.

# Feature Matrix

The table below summarizes what this example is deliberately exercising.

| Area | Demonstrated in this example | Notes |
| --- | --- | --- |
| Ordered sections | Yes | Explicit `document.include` order in `spec.yaml` |
| Title page metadata | Yes | Title, subtitle, author, and date |
| Table of contents | Yes | Enabled by the document-local template defaults |
| Figure support | Yes | Raw LaTeX figure block in the workflow section |
| Tables | Yes | Native Markdown table in this section |
| Citations | Yes | Bibliography entry rendered with a local CSL file |
| Appendix handling | Yes | `<!-- APPENDIX -->` marker switches to appendix mode |
| Version metadata | Yes | Version appears on the template title page |

For a first real project, the current MVP is most useful when the document structure is
stable, the template is known up front, and PDF is the required output format.

# Citations and Rendering Notes

This section demonstrates citation handling with a local BibTeX file and CSL style.
Pandoc citeproc resolves inline citations such as [@wilson2021] during PDF generation.

In practical use, the combination of structured Markdown, a small YAML specification,
and deterministic output naming makes the build easier to automate in scripts and CI.
That is especially useful for documents that need repeatable output and visible version
metadata for review cycles.
