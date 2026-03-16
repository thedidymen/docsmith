# Versioning and Outputs

Docsmith separates semantic version from build identity.

Semantic versioning behavior:

- `spec.yaml` provides the initial semantic version
- repeated builds keep the same version when the fingerprint is unchanged
- content changes bump the patch version by default

Output naming behavior:

- the semantic version is part of the filename
- an optional git hash can be included when enabled
- collision suffixes such as `_01` prevent overwriting prior artifacts

This report therefore serves as a useful architecture example because every successful build
also demonstrates the engine's version-aware output behavior.

