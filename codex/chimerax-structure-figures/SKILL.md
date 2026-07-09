---
name: chimerax-structure-figures
description: Create publication-ready molecular structure figures by driving UCSF ChimeraX from Codex. Use when rendering protein/RNA/DNA/complex PDB or mmCIF structures as clean PNG/PDF-style panels, including standalone whole-structure views, local contact closeups with hydrogen bonds, aligned structure overlays, aligned local contact closeups, GPCR/7TM receptor cartoons, transparent icon renders, saved ChimeraX sessions, and reproducible .cxc scripts.
---

# ChimeraX Structure Figures

## Overview

Use ChimeraX for final molecular rendering and keep the work reproducible: generate a `.cxc` command file, render a PNG, save a `.cxs` session, and keep a small source manifest in the output folder.

The bundled CLI handles four common figure types:

- `single`: one or more standalone whole-structure panels.
- `contact`: one complex, local contact closeup, optional hydrogen bonds, no surface by default.
- `align`: overlay multiple structures after `matchmaker` alignment.
- `align-contact`: align structures first, then render the same local contact region.

## Quick Start

Prefer the bundled script unless the user needs a hand-tuned ChimeraX session:

```bash
python /path/to/chimerax-structure-figures/scripts/render_structure_figure.py \
  --mode single \
  --structure receptor.cif \
  --out out/receptor.png \
  --transparent \
  --color-mode chain
```

Locate ChimeraX in this order:

1. `--chimerax /path/to/ChimeraX`
2. environment variable `CHIMERAX_EXE`
3. environment variable `CHIMERAX`
4. executable on `PATH`
5. common Windows/macOS/Linux install paths

For portable use on another computer, set `CHIMERAX_EXE` once and keep commands path-relative to the project.

## Rendering Policy

- Use cartoon mode for proteins unless the user asks for sticks/surface.
- Do not show surfaces for contact figures unless explicitly requested.
- Save both the final PNG and a `.cxs` session so the user can reopen and screenshot manually.
- Use white background for paper figures and transparent background for icons.
- When no color is specified for standalone structures, color by chain.
- For overlays, use neutral gray for reference/experimental structures, blue for baseline/prediction, and a distinct pastel/accent color for the alternative method.
- Keep the same camera for whole and local panels from the same structure set. For local views, align first and then zoom to the focus selection rather than reorienting from scratch.
- Use `--extra-cmd` for version-specific ChimeraX commands instead of hardcoding one-off edits into the skill.

## Workflows

### Whole Structure

Use for "整体单独结构展示", icons, receptor cartoons, and clean model renders.

```bash
python scripts/render_structure_figure.py \
  --mode single \
  --structure model.cif \
  --out figures/model_overall.png \
  --color-mode chain \
  --cartoon-width 1.25 \
  --transparent
```

If the user wants a single-color icon:

```bash
python scripts/render_structure_figure.py \
  --mode single \
  --structure mc4r.cif \
  --out icons/mc4r.png \
  --color "#BFE9FF" \
  --transparent --crop --square
```

### Local Contact

Use for "局部接触展示（单独）". Provide ChimeraX atom specs for the two sides of the interface. Keep the same camera as the whole panel by using `--view-command view` and `--focus` for zoom only.

```bash
python scripts/render_structure_figure.py \
  --mode contact \
  --structure complex.cif \
  --out figures/contact.png \
  --context "#1/A" \
  --contact-a "#1/A & within 4.5 of #1/B" \
  --contact-b "#1/B" \
  --focus "#1/A & within 8 of #1/B | #1/B" \
  --hbonds
```

Read `references/chimerax-command-patterns.md` before changing hydrogen-bond or selector syntax.

### Aligned Overall

Use for "整体 align 结构展示". Put the experimental/reference structure first.

```bash
python scripts/render_structure_figure.py \
  --mode align \
  --structure gt.cif \
  --structure af3.cif \
  --structure method.cif \
  --out figures/aligned_overall.png \
  --colors "#B8BDC2,#4F7DB8,#F4A6C8"
```

The script uses `matchmaker #N to #1` by default. If chain mapping is difficult, add explicit ChimeraX commands:

```bash
--no-matchmaker --extra-cmd "match #2/A to #1/A" --extra-cmd "match #3/A to #1/A"
```

### Aligned Local Contact

Use for "局部接触展示（align）". Align all structures first, then zoom to the reference interface.

```bash
python scripts/render_structure_figure.py \
  --mode align-contact \
  --structure gt.cif \
  --structure af3.cif \
  --structure method.cif \
  --out figures/aligned_contact.png \
  --colors "#B8BDC2,#4F7DB8,#F4A6C8" \
  --context "#1/A | #2/A | #3/A" \
  --contact-a "#1/A & within 4.5 of #1/B" \
  --contact-b "#1/B" \
  --focus "#1/A & within 8 of #1/B | #1/B" \
  --hbonds
```

## Quality Check

After rendering:

- Open the PNG and check it is nonblank, cropped correctly, and labels/background match the request.
- Confirm `.cxc` and `.cxs` exist in the output folder.
- If rendering an icon, verify the PNG is RGBA and has transparent pixels.
- If the angle is not acceptable, edit the generated `.cxc` with `turn`, `roll`, `view`, or `zoom`, rerun ChimeraX, and keep the edited `.cxc`.

## Resources

- `scripts/render_structure_figure.py`: portable CLI that writes `.cxc`, runs ChimeraX, and optionally crops transparent PNGs.
- `references/chimerax-command-patterns.md`: selector, coloring, alignment, and hydrogen-bond command patterns to read before manual tuning.
