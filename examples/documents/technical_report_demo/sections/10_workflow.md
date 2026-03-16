# Build Workflow

Docsmith expects a document directory with a `spec.yaml` file, ordered or discoverable
Markdown inputs, and a document-local template selection. During a build it validates inputs,
assembles source Markdown, writes runtime metadata, resolves an output version, and then
invokes Pandoc for PDF rendering.

```{=latex}
\begin{figure}[htbp]
\centering
\fbox{
  \parbox{0.82\textwidth}{
    \centering
    \textbf{Docsmith MVP build flow}\\[0.75em]
    spec.yaml + sections + template + citations\\
    $\downarrow$\\
    validation + assembly + version resolution\\
    $\downarrow$\\
    Pandoc + document-local academic thesis template\\
    $\downarrow$\\
    versioned PDF output
  }
}
\caption{Conceptual build flow shown as a simple figure rendered through raw LaTeX.}
\label{fig:docsmith-workflow}
\end{figure}
```

The generated title page exposes runtime version metadata automatically. When git hash
support is enabled, the build can also show short revision traceability alongside the
semantic version.
