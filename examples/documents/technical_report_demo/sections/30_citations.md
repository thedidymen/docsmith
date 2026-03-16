# Citations and Rendering Notes

This section demonstrates citation handling with a local BibTeX file and CSL style.
Pandoc citeproc resolves inline citations such as [@wilson2021] during PDF generation.

In practical use, the combination of structured Markdown, a small YAML specification,
and deterministic output naming makes the build easier to automate in scripts and CI.
That is especially useful for documents that need repeatable output and visible version
metadata for review cycles.

