# Appendices

Docsmith currently uses a simple appendix marker in source Markdown. The marker is
replaced during assembly so the rendered PDF switches into appendix mode.

The preserved appendix content from the earlier example follows verbatim:

# Supporting Notes

The main body ends here. The next marker switches the active document template into
appendix mode.

<!-- APPENDIX -->

# Appendix A: Example Build Artifacts

After a successful build, Docsmith writes intermediate files to `build/` and final PDF
artifacts to `output/`. The build state file keeps track of the last semantic version
and fingerprint so repeated builds can decide whether the version should stay the same
or bump automatically.

# Appendix B: Authoring Checklist

- confirm section ordering in `document.include`
- keep cited sources under version control
- validate before running a full build
- treat generated files under `build/` and `output/` as build artifacts, not source
