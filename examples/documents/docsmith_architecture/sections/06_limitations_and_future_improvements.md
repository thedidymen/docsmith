# Limitations and Future Improvements

The current architecture is intentionally narrow.

Current limitations:

- PDF is the only implemented render output
- template validation checks required files but not full template semantics
- most tests are unit or mocked-service tests rather than full render integrations

Likely improvements:

- add stronger integration testing around real Pandoc builds
- expand template packaging and reuse beyond copy-based example repositories
- model multi-format build results more explicitly when DOCX support is added

This example document is useful partly because it makes those tradeoffs visible in a format
that is close to the eventual user-facing documentation style.

