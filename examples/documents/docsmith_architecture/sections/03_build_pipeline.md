# Build Pipeline

The build pipeline is intentionally linear and deterministic:

1. load and validate configuration
2. discover ordered Markdown inputs
3. compute a build fingerprint
4. resolve semantic version and output path
5. assemble Markdown into `build/combined.md`
6. write runtime metadata to `build/runtime-metadata.yaml`
7. invoke Pandoc with the selected template
8. persist build state to `build/.docsmith-state.json`

This structure makes it easier to debug failures and reason about version changes. It also
keeps the CLI thin because the orchestration logic lives in the engine layers rather than
in command parsing code.

