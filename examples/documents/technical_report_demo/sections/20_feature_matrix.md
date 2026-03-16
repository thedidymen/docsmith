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
