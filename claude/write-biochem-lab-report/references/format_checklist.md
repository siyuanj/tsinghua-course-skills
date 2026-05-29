# Biochemistry Lab Report Checklist

Use this checklist as general guidance, not as a rigid assignment-specific rubric.

## Academic Integrity

- Write independently. Do not copy another student's figures, tables, wording, or references.
- If using a non-original image, cite the source in the figure caption.
- Add references for non-original statements in Introduction and Discussion, including textbook material.
- In the body text, format citation numbers as superscript square brackets, such as `\upcite{1}` or `\textsuperscript{[1,2]}`. Keep the References section as a normal numbered list.

## File Safety

- Treat user-provided reports, source files, figures, and PDFs as originals. Do not overwrite them while revising unless the user explicitly asks for replacement.
- Save revised versions with clear suffixes such as `_revised`, `_teacher_revised`, `_v2`, or in a new dated output folder.
- In the final response, identify the original path and the revised path so the user can tell which file is which.
- If accidental overwrite is suspected, stop and restore from backup, TeX auxiliary files, version history, or the most recent copy before making further edits.

## Report Structure

- For short homework-style reports, use only title, name, student ID, class, date, and the required sections. Do not add an abstract unless requested.
- For formal reports such as ELISA or WB, default to five main sections: Introduction, Methods, Results, Discussion, and References. Do not add a separate Conclusion unless the assignment asks for it.
- In Introduction, define first-use abbreviations such as gel filtration (GF), enzyme-linked immunosorbent assay (ELISA), and western blot (WB), give only the necessary background, state the aim, and cite general principle/application statements.
- Do not put `Experiment Principle` as a separate section after Introduction. If the paragraph is broad background or general principle, fold it into Introduction; if it describes the actual assay mechanism, controls, concentrations, workflow, procedure, or detection design, fold it into Methods.
- In Methods, include Materials and Reagents, Equipment, Workflow, and Experimental Procedure when useful. Write connected prose adapted to the actual experiment. Do not paste protocol text. Include experimental design, reagent composition, antibody/sample concentrations or dilution ratios, controls, incubation conditions, detection wavelength, and instrument settings when relevant.
- For assays with a workflow figure (ELISA, WB, pull-down), do not split Methods into a figure-only `Workflow` subsection and a text-only `Experimental Procedure` subsection. Combine them into one `Experimental Procedure` subsection where the workflow figure and any sample/lane table are embedded inside the prose, and every step shown in the diagram also appears in connected sentences. The workflow figure summarises; the prose specifies.
- In Results, describe the experimental design and data processing in prose. State regression model choice, fitted equation or parameters, replicate handling, average, standard deviation, coefficient of variation, blank correction, and outlier handling when applicable.
- In Discussion, analyze error sources, controls, regression model reasonableness, large discrepancies, and possible improvements.

## Figures

- Every figure needs a concise title and a legend/caption below the figure.
- Figure captions should read like `Figure 1. Linear standard curve...` rather than `Figure 1: ...`; configure LaTeX captions with `labelsep=period` when needed.
- Keep the figure and its caption together on the same page.
- Prefer `justification=raggedright,singlelinecheck=false` over `justification=centering` for figure and table captions. Multi-line captions read better left-aligned, and this matches journal practice; rubrics that say 居中 typically refer to the figure itself being centered, not the caption text.
- Follow the practical pattern used by scientific Matplotlib style projects: small fixed figure size, editable vector output, consistent sans-serif labels, and minimal non-data ink.
- Use correct axis labels and units. Use evenly spaced and readable tick values.
- Put the legend in an empty region of the plot, usually upper right or upper left, so it does not cover data.
- Avoid grids unless they help interpretation. Do not let grids, legends, labels, or data overlap.
- Default style for generated charts should be clean and publication-like: white background, no grid, left and bottom axes only, outward major ticks, no top/right ticks, clear markers, fitted line when relevant, and sans-serif labels.
- For standard curves, show standards, fit line, unknown sample marker when useful, fitted equation, and $R^2$.
- Use figure body units as `Variable / unit` or `Variable (unit)`, consistently within one figure.

## Tables

- Use three-line tables with table title above the table.
- Table captions should read like `Table 1. Summary...` rather than `Table 1: ...`; configure LaTeX captions with `labelsep=period` when needed.
- Add table notes below the table when the table includes averages, SD, CV, blank correction, removed outliers, excluded standards, or any processing choice that a reader needs to interpret the values.
- Put units in table headers, not repeatedly inside cells.
- Left-align text columns and right-align numeric columns.
- Avoid listing the same item twice as both a material and equipment. Consumables such as plates belong in materials; instruments such as readers, incubators, and pipettors belong in equipment.
- For antibody rows, use a concrete dilution actually used in the experiment when available. Avoid unexplained ranges such as `1:40000 to 1:20000`; explain protocol ranges in a table note or Methods sentence if they must be retained.
- Keep tables on one page when possible. If a table must split, repeat the header on the next page.

## Units, Numbers, and Symbols

- In prose, put a space between numbers and units: `0.80 mg mL^{-1}`, `5 min`, `37 °C`.
- In prose, avoid slash or parentheses for units unless unavoidable; prefer `mg mL^{-1}` over `mg/mL`.
- In figures and tables, use slash or parentheses for units, but do not mix both styles in the same label.
- Use proper subscripts and superscripts: $A_{280}$, $A_{490}$, Na$_2$CO$_3$, mL$^{-1}$.
- Write dilution ratios as ratios, such as `1:400`, not as fractions such as `1/400`.

## Common Biochemistry Content

- GF reports often need an elution curve, a $K_{av}$ versus $\log_{10}(\mathrm{MW})$ standard curve, and an interpolated unknown MW calculation.
- UV absorbance reports often need a table of group results, comparison with other groups, and a mean of 2--3 groups when requested.
- BCA reports often need a standard curve figure, equation, $R^2$, and unknown sample concentration calculation.
- ELISA reports often need controls, replicate processing, model choice, standard curve explanation, and discussion of discrepancy between expected and measured concentrations.
- WB and pull-down reports often need a workflow diagram, a lane-design table, an annotated blot figure with brightness/contrast disclosure, and a Discussion that covers positive/negative result, additional experiments to prove the conclusion, factors affecting protein-protein interaction detection, and optimization. A separate `\section{Assignment}` after Discussion is common when the rubric asks for McAB-vs-PcAB, NC-vs-PVDF, or how-to-avoid-non-specific-bands.

## Tone and Claim Hedging

- Match claim strength to what the assay can support. Pull-down and WB show that two proteins **associate** under the conditions tested, not that they **interact directly**. Reserve "direct" for experiments that exclude bridging factors with fully purified components or use orthogonal techniques (SPR, ITC, crosslinking).
- Avoid superlatives in technical comparisons: "best", "cleanest", "perfect", "only", "the cleanest possible blots". Hedge with "often", "generally", "when well validated", "is typically chosen when".
- If a marker was not captured on a gel/blot image, do not claim observed molecular weight. State theoretical mass and explicitly note that absolute MW cannot be calibrated from this image.
- Do not fabricate biological identities for test proteins. If the user supplies "protein A, protein B, protein C" without saying what they are, write the report at that level of abstraction. Speculation about identity (e.g., assigning a protein to Atg8 because the mass matches) is worse than not naming.

## Western Blot and Pull-down Specifics

- Confirm lane-loading direction with the user before annotating. Lane 1 may be on the right rather than the left depending on the gel orientation; getting this wrong invalidates every band-by-band comparison in Results and Discussion.
- For an experimentally failed panel (e.g., AP/BCIP-NBT half with no signal across the cohort), do not draw an empty placeholder strip. Use "data not shown" in the figure caption and describe the negative result in the corresponding Results subsection.
- Pull-down reports need a bait-confirmation lane. Flag this if missing — any prey-side comparison can be confounded by uneven bait loading.
- When input lanes (e.g., 5 µL) and pull-down lanes (e.g., 25 µL) carry different volumes, acknowledge the fold ratio when comparing band intensities. A pull-down lane being darker than the input lane does not by itself prove enrichment.
- Common controls to mention in Discussion: empty Strep-Tactin or other empty-resin pull-down (no bait), known positive interactor, parallel Coomassie-stained gel for migration calibration, separate white-light marker exposure.
- Standard WB Discussion checklist: positive/negative result; how an additional experiment would prove the conclusion; factors affecting protein-protein interaction detection (buffer ionic strength, pH, detergents, bait/prey stoichiometry, incubation time/temperature, tag identity, antibody specificity, substrate freshness); optimization suggestions.
- Standard WB Assignment section (when the rubric asks): monoclonal vs polyclonal antibodies; nitrocellulose vs PVDF membrane; how to avoid non-specific bands. Place under `\section{Assignment}` after Discussion.
- For matplotlib-generated WB annotations, recommend Arial in subsequent PowerPoint touch-ups (DejaVu Sans is matplotlib's default but visually equivalent to Arial at small sizes, and Arial is universally available on Windows).

## Image Integrity (Gels, Blots, Micrographs)

- Any brightness/contrast adjustment must be (a) linear, (b) applied uniformly to the whole image, and (c) not obscure or eliminate any band. Selective region edits, gamma adjustments, or band splicing without explicit indication are prohibited.
- Disclose any image adjustment in the figure caption. Standard wording: "Brightness and contrast were linearly adjusted across the entire image for display purposes; no other manipulations were performed." Name the operation if specific (e.g., "2nd--99.5th percentile rescaling").
- Reference: Rossner & Yamada 2004, *J Cell Biol*; JCB and Nature image-integrity guidelines.
- When the user replaces an auto-generated figure with a hand-edited PowerPoint export, save it under a different filename (e.g., `wb_fig2.png` instead of `wb_annotated.png`) so a future rerun of the generation script cannot accidentally overwrite the hand-drawn version.

## Compile and Verification

- Always compile via `latexmk -pdfxe -interaction=nonstopmode -halt-on-error report.tex`. A single `xelatex` pass leaves cross-references showing as `??` because `\ref{...}` resolution requires a second pass that reads the `.aux` file.
- If the output `report.pdf` is locked by an open viewer, compile to an alternate filename and swap: `xelatex -jobname=report_new report.tex`, then `mv -f report_new.pdf report.pdf`. Tell the user which viewer to close. Run `latexmk` once more after the swap if cross-references are still unresolved.
- Verify rendered output with `pdftotext -enc UTF-8 report.pdf -`. Without `-enc UTF-8`, CJK characters can be stripped from the extracted text and falsely suggest a font-rendering bug.
- For an English `lang=en` document with limited Chinese content (e.g., the author line), do not switch to `lang=cn`. Add `\usepackage{xeCJK}` + `\setCJKmainfont{Microsoft YaHei}` to the preamble; English typesetting defaults are preserved.
- Inline arithmetic in body prose: write digits as upright text and put only the operator in math mode (`0.8~$\times$~48~$=$~38.4~mA`), not the whole expression in math mode (`$0.8 \times 48 = 38.4$~mA`), so digits visually match the surrounding sans-serif body.
