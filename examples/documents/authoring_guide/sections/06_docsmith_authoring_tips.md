# Docsmith Authoring Tips

This guide is intentionally compact, but it reflects a few practical habits that fit the
current MVP well.

## Recommended Workflow

1. Keep document source in small ordered files.
2. Put reusable assets in `assets/`.
3. Validate the document before building.
4. Treat `build/` and `output/` as generated state.

## Keep the Example Readable

- prefer ordinary Markdown over raw LaTeX unless the feature genuinely needs it
- reserve raw LaTeX for cases like custom figure layout in the current PDF-only flow
- keep bibliography and CSL files close to the document so validation stays clear

## Try It

```bash
docsmith validate examples/docsmith_authoring_guide
docsmith build examples/docsmith_authoring_guide
```

If the document content is unchanged, the semantic version stays the same. If you edit a
section, bibliography file, or `spec.yaml`, the next build will normally bump the patch
version.

