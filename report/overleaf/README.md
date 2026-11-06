# Batch 18 IEEE report: Overleaf source

This folder contains the editable IEEEtran journal-paper source, bibliography, figures, and the compiled PDF.

## Open in Overleaf

1. Upload Batch18_IEEE_Overleaf_Source.zip as a new Overleaf project.
2. Set Batch18_IEEE_Report.tex as the Main document.
3. Select pdfLaTeX; Overleaf will run BibTeX for the references.

The ZIP is self-contained: all referenced figures and the bibliography are inside it. Batch18_IEEE_Report.pdf is also provided for direct review.

## Local build

From this directory, run:

    latexmk -pdf -interaction=nonstopmode Batch18_IEEE_Report.tex

The report summarizes the saved project radial calculation and CSV outputs. The live demonstration notebook is an educational solver and does not generate the 120-by-600 result set described in the report.
