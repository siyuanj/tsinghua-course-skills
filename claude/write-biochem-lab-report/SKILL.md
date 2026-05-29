---
name: write-biochem-lab-report
description: Create, format, revise, and validate biochemistry laboratory reports using an ElegantPaper-based LaTeX template, teacher-feedback formatting rules, and clean publication-style scientific figures. Use when the user asks for a biochemical experiment report, English lab report, ELISA/WB/GF/BCA/UV protein assay report, standard curve or elution curve figure, three-line table formatting, result/discussion writing, or conversion of experiment data into a polished PDF report.
---

# Write Biochem Lab Report

## Overview

Use this skill to produce polished biochemistry lab reports with correct academic figure/table formatting, formal English scientific prose, and reproducible data plots. Default to short report metadata only: title, name, student ID, class, and date; do not add an abstract unless the user requests one.

## Workflow

1. Collect the report requirements, experiment type, language, personal metadata, and available data files.
2. Read `references/format_checklist.md` before writing or revising the report.
3. Protect user files before editing. When revising an existing report or plot, create a clearly named copy such as `*_revised.tex`, `*_teacher_revised.tex`, or a new dated output folder; do not overwrite the original source/PDF unless the user explicitly asks for replacement.
4. Create a report project when the user needs a new report:

```powershell
python "$env:USERPROFILE\.claude\skills\write-biochem-lab-report\scripts\create_report_project.py" "D:\path\to\report" --title "Protein Quantification Report" --name "Name" --student-id "2023000000" --class-name "Class" --date "May 28, 2026"
```

5. Put raw CSV files in the project `data/` directory and generated figures in `figures/`.
6. Generate plots with `scripts/plot_biochem.py` when possible; keep calculations reproducible instead of hand-copying values. The project generator and plotting script refuse to overwrite existing generated files by default; choose a new output name for revisions, or pass `--overwrite` only after the user explicitly wants replacement.
7. Write or revise `report.tex` using connected prose, complete figure/table captions, table notes when data processing needs explanation, and explicit data-processing details.
8. Run the TeX structure checker before compiling when a report source is available:

```powershell
python "$env:USERPROFILE\.claude\skills\write-biochem-lab-report\scripts\check_report_tex.py" .\report.tex
```

9. Compile with XeLaTeX. `latexmk` automatically runs multiple passes so that `\ref{...}` cross-references resolve; a single `xelatex` pass leaves them as `??`:

```powershell
latexmk -pdfxe -interaction=nonstopmode -halt-on-error report.tex
```

If `report.pdf` is locked by an open viewer, compile to an alternate name and swap: `xelatex -jobname=report_new report.tex` then `mv -f report_new.pdf report.pdf`. Run `latexmk` once more after the swap if any reference still shows `??`.

10. Render the PDF pages with Poppler and visually inspect layout, figure/table placement, labels, captions, and text overflow. Verify the text layer with `pdftotext -enc UTF-8 report.pdf -` — without `-enc UTF-8`, CJK characters can be stripped from the extracted text and falsely suggest a font-rendering bug.

## Plotting

Use the bundled plotting script for default clean report charts: white background, no grid, left and bottom axes only, outward major ticks, no top/right ticks, clear markers, fitted line for standard curves, and legends placed in empty plot regions. Omit in-plot titles for report figures; the LaTeX caption provides the figure title and legend.

Elution curve:

```powershell
python .\scripts\plot_biochem.py elution .\data\gf_elution.csv .\figures\gf_elution_curve.pdf --x volume_ml --y a280 --xlabel 'Elution volume (mL)' --ylabel 'Absorbance at 280 nm, $A_{280}$'
```

GF standard curve:

```powershell
python .\scripts\plot_biochem.py standard .\data\gf_standard.csv .\figures\gf_standard_curve.pdf --x kav --y log_mw --unknown-x 0.55 --xlabel 'Partition coefficient, $K_{av}$' --ylabel '$\log_{10}(\mathrm{MW})$' --results .\data\gf_fit.txt
```

BCA standard curve:

```powershell
python .\scripts\plot_biochem.py bca .\data\bca_standard.csv .\figures\bca_standard_curve.pdf --unknown-y 0.612 --xlabel 'Protein concentration (mg mL$^{-1}$)' --ylabel 'Absorbance at 562 nm, $A_{562}$' --results .\data\bca_fit.txt
```

In PowerShell examples, use single quotes around labels containing `$...$` so math text is passed to Python unchanged.

If a user provides Excel files, first extract or save the relevant sheets as CSV before plotting. If a plot needs special experimental conventions, adapt the script but preserve the clean report style unless the user asks otherwise.

## Writing Rules

- Use formal, concise scientific English for English reports.
- First mention the full term followed by abbreviation, such as gel filtration (GF) or enzyme-linked immunosorbent assay (ELISA).
- Avoid abstract and keywords for ordinary homework reports.
- Default to five main sections: Introduction, Methods, Results, Discussion, and References.
- Do not create a standalone `Experiment Principle` section for ordinary ELISA/WB/GF reports. Put conceptual background, general principle, and experiment aim in Introduction; put the actual experimental design, assay mechanism when tied to execution, antibody/reagent concentrations, incubation conditions, controls, workflow, procedure, and detection settings in Methods.
- In Methods, include Materials and Reagents, Equipment, Workflow, and Experimental Procedure when the report needs explicit organization. Use connected prose for procedure text unless the assignment explicitly requires numbered steps.
- In Results, describe what each figure/table shows and explain data processing. Never rely on captions alone.
- In Discussion, analyze errors, controls, model choice, discrepancy between methods or groups, and possible improvements. Add a concise final takeaway at the end of Discussion when useful, but do not create a separate Conclusion unless the assignment asks for it.
- Use enough references for non-original statements in Introduction and Discussion, especially general method principles and applications. In report prose, format citation numbers as superscript square brackets, such as `\upcite{1}` or `\textsuperscript{[1,2]}`; keep the References list itself as normal numbered entries.
- Match claim strength to what the assay can support. Pull-down/WB show association under the conditions tested, not direct interaction. Avoid superlatives ("cleanest", "best", "perfect", "only"); hedge with "often", "generally", "when well validated".
- Do not fabricate biological identities for test proteins. If the user supplies "protein A, B, C" without saying what they are, write the report at that level of abstraction; speculation about identity is worse than not naming.
- For experimentally failed panels (no signal across the cohort), write "data not shown" in the figure caption and describe the negative result in the Results subsection — do not draw empty placeholder schematics.
- For inline arithmetic in body prose, keep digits upright and put only the operator in math mode: `0.8~$\times$~48~$=$~38.4~mA`. Wrapping the whole expression in `$...$` produces italic math digits that clash with sans-serif body text.
- For an English `lang=en` document with Chinese in the metadata (e.g., the author line), add `\usepackage{xeCJK}` + `\setCJKmainfont{Microsoft YaHei}` to the preamble; do not switch to `lang=cn`.
- For WB/pull-down reports, before annotating the blot confirm the lane-loading direction with the user (lane 1 may be on the right rather than the left). Disclose any brightness/contrast adjustment in the figure caption ("Brightness and contrast were linearly adjusted across the entire image for display purposes; no other manipulations were performed.").

## Formatting Rules

- Put figure titles and legends below figures; keep figure and caption on the same page. Configure captions without a colon after `Figure N` or `Table N` when using LaTeX, preferably `\captionsetup{labelsep=period}` for `Figure 1. Title...`.
- Put table titles above tables; use three-line tables with notes below when the table includes averages, SD, CV, blank correction, removed outliers, excluded points, or other processing details.
- Keep old and new deliverables distinguishable in file names and final messages. State which path is the original and which path is the revised copy.
- Put units in table headers; left-align text and right-align numbers.
- Avoid duplicating the same item in both the materials/reagents table and equipment paragraph. Consumables such as 96-well plates usually belong in materials; instruments such as microplate readers belong in equipment.
- Write antibody dilutions as the actual dilution used whenever possible. Avoid vague ranges such as `1:40000 to 1:20000` unless the protocol genuinely allowed a range; if a range is unavoidable, explain why in the note or methods text.
- In prose, write a space between numbers and units and prefer forms such as `0.80 mg mL$^{-1}$`.
- In figure/table labels, use either slash or parentheses for units consistently, such as `Concentration / mg mL$^{-1}$` or `Concentration (mg mL$^{-1}$)`.
- Use correct subscripts and superscripts: `$A_{280}$`, `$A_{490}$`, `Na$_2$CO$_3$`, and `mL$^{-1}$`.
- Write dilution ratios as `1:400`, not `1/400`.

## Resources

- `assets/report_template.tex`: ElegantPaper-based LaTeX report template.
- `assets/elegantpaper.cls`: bundled class file copied into generated projects.
- `scripts/create_report_project.py`: creates a report folder with template, class file, scripts, `data/`, and `figures/`.
- `scripts/check_report_tex.py`: checks TeX sources for the expected report structure, forbidden old headings, extra default cover fields, caption separator issues, table-note presence, and basic three-line-table markers.
- `scripts/plot_biochem.py`: clean plotting utility for elution curves, standard curves, and BCA curves.
- `references/format_checklist.md`: distilled teacher-feedback checklist; read before substantial report writing or revision.
