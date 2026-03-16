# Versioning Behavior

Docsmith separates semantic version from build identity.

## Semantic Version

`spec.yaml` defines `versioning.initial_version`. After the first successful build, the
active semantic version is tracked in `build/.docsmith-state.json` instead of being
written back to the source spec.

## Git Hash

If `include_git_hash` is enabled and the document lives inside a git repository, the
short git hash is added to the output filename as traceability metadata.

## Collision Suffixes

If a target output file already exists, Docsmith preserves the old artifact and writes a
new filename with a collision suffix such as `_01` or `_02`.

## Automatic Patch Bumps

When the build fingerprint changes, Docsmith bumps the patch version by default. The
fingerprint currently includes:

- `spec.yaml`
- included Markdown files
- active template files
- bibliography and CSL files when configured

This keeps semantic versioning deterministic without rewriting declarative source files.

