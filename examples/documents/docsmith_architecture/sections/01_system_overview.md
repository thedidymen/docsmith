# System Overview

Docsmith is a generic Markdown to document build engine. A document repository provides:

- a `spec.yaml` file
- ordered Markdown sections
- any document assets such as images or bibliography files
- one or more document-local templates

The engine validates inputs, assembles Markdown, resolves runtime version metadata, and
invokes Pandoc to render a final PDF.

![A small diagram placeholder representing the Docsmith engine and a document repository.](assets/docsmith-architecture-diagram.png)

The diagram is intentionally simple. It demonstrates the current asset model: images live
inside the document repository and are resolved through the same build pipeline as normal
content files.

