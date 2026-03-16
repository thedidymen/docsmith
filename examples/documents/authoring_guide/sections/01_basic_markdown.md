# Basic Markdown Authoring

This section demonstrates everyday authoring patterns that Docsmith already supports
because the current MVP passes standard Markdown through Pandoc.

## Headings and Hierarchy

Use normal heading levels to produce a readable document structure:

### Third-Level Heading

This paragraph includes **bold text**, *italic text*, and `inline code` for short
references to filenames, commands, or markers such as `<!-- APPENDIX -->`.

## Lists

Unordered list:

- write content in small, focused sections
- keep filenames ordered when sequence matters
- store figures and other reusable assets under `assets/`

Ordered list:

1. Write or update `spec.yaml`.
2. Add or revise Markdown section files.
3. Run `docsmith validate`.
4. Run `docsmith build`.

## Block Quotes

> Keep the source document readable first. The current Docsmith MVP is strongest when
> authors can review the Markdown directly without needing a complex preprocessor.

