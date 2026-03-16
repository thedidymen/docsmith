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
