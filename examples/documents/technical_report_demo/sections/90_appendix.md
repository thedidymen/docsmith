# Supporting Notes

The main body ends here. The next marker switches the active document template into
appendix mode.

<!-- APPENDIX -->

# Appendix A: Example Build Artifacts

After a successful build, Docsmith writes intermediate files to `build/` and final PDF
artifacts to `output/`. The build state file keeps track of the last semantic version
and fingerprint so repeated builds can decide whether the version should stay the same
or bump automatically.
