# Images and Tables

This section demonstrates a repository-local image asset and a simple Markdown table.

![A small repository-local example image used by the authoring guide.](assets/docsmith-diagram.png)

The image above is intentionally simple. It shows the current pattern for document
assets: place the file under `assets/` and reference it from Markdown with a relative
path.

| Artifact | Produced by | Purpose |
| --- | --- | --- |
| `combined.md` | build flow | assembled Markdown source |
| `runtime-metadata.yaml` | build flow | metadata passed to Pandoc |
| `.docsmith-state.json` | versioning layer | persisted version and fingerprint state |
| `output/*.pdf` | Pandoc render | final document artifact |

For the current MVP, simple Markdown tables are the most maintainable choice unless the
template requires a more specialized LaTeX layout.

