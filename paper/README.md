# ALUCLU technical paper

The paper is distributed in two forms:

- `ALUCLU_paper.pdf`: compiled 47-page A4 paper.
- `ALUCLU_paper.tex`, `sections/`, and `references.bib`: complete LaTeX source.

The paper separates implemented behavior, measured evidence, and proposed
experiments. The current CPU numbers describe the portable correctness backend;
they are not fused-kernel or state-of-the-art claims.

## Build

[Tectonic](https://tectonic-typesetting.github.io/) 0.17 or later is
recommended:

```powershell
.\build.ps1
```

If `tectonic` is not on `PATH`, pass its executable explicitly:

```powershell
.\build.ps1 -TectonicPath C:\tools\tectonic.exe
```

The script writes intermediate files to `paper/build/` and copies the finished
PDF to `paper/ALUCLU_paper.pdf`.
