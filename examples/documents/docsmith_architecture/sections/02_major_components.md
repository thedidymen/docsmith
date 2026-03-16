# Major Components

The current implementation is organized around a few main responsibilities.

| Component Area | Purpose | Typical Modules |
| --- | --- | --- |
| CLI | parse commands and print results | `src/docsmith/cli.py` |
| Config | load and validate `spec.yaml` | `src/docsmith/config.py` |
| Core | discover content, assemble Markdown, orchestrate builds | `src/docsmith/core/` |
| Renderer | write runtime metadata and invoke Pandoc | `src/docsmith/renderer/` |
| Versioning | fingerprint inputs, resolve semantic versions, persist build state | `src/docsmith/versioning/` |
| Templates | validate document-local template directories | `src/docsmith/templates/registry.py` |

This separation is deliberate. The engine should remain neutral while document repositories
own their templates and content structure.

