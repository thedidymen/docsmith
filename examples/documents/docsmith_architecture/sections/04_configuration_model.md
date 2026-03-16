# Configuration Model

Docsmith currently uses a small YAML configuration model with these main sections:

- `project`
- `metadata`
- `document`
- `citations`
- `output`
- `versioning`

For architecture-style documents, the most relevant fields are often:

- `project.template`
- `document.include`
- `output.directory`
- `output.basename`
- `versioning.initial_version`

The current template architecture is path-based. A document points at a template directory
relative to its own root, for example `templates/technical_report`.

