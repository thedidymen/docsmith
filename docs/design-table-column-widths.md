# Relative Table Column Widths

## Contract

Docsmith supports optional relative column weights for normal Pandoc Markdown
tables through a caption attribute:

```md
| ID | Description | Status |
|---|---|---|
| R-01 | Descriptive content | Must |

: Requirements {#tbl:requirements column-widths="15,70,15"}
```

The comma-separated values are positive, finite numbers. Their count must equal
the table's column count; their sum is unrestricted. Absolute physical units are
outside this contract.

## Pipeline ownership

The engine-owned `table_column_widths.lua` filter runs for every Pandoc build.
It returns tables without the attribute untouched. For annotated tables it
validates against Pandoc's parsed column count, normalizes the weights to a sum
of one, preserves each column's alignment, assigns Pandoc-native `ColWidth`
values, and removes the consumed authoring attribute.

This is separate from figure/table cross-reference resolution. The table
caption and identifier remain on the AST node, so the existing `@tbl:` path
continues to use the template and writer's normal caption numbering.

## Rendering

The contract is writer-independent: the filter emits no raw LaTeX. Pandoc's PDF
writer maps explicit widths to wrapping table columns within the available
table width and retains its normal multi-page table behavior. Other future
writers may use the native widths when supported or fall back gracefully.

Because the filter always participates in rendering, its source is always a
build-fingerprint input. This keeps version changes aligned with effective
rendering behavior.
