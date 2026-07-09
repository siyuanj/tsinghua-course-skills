# ChimeraX Command Patterns

Use this reference when the generated `.cxc` needs manual tuning.

## Structure Loading

```chimerax
open "path/to/model.cif" name model1
open "path/to/prediction.cif" name model2
```

Avoid spaces in model names used by generated scripts. Spaces in file paths are fine when paths are quoted.

## Basic Cartoon Rendering

```chimerax
hide atoms
hide cartoons
hide surfaces
show cartoons
cartoon style width 1.25 thickness 0.24
color bychain
set bgColor white
lighting soft
graphics silhouettes true
graphics silhouettes width 1.2
view
zoom 1.35
save "session.cxs"
save "panel.png" width 1400 height 1400 supersample 3 transparentBackground true
```

Use `transparentBackground true` for icons and `false` for paper panels on white.

## Selectors

Common atom specs:

```chimerax
#1                  model 1
#1/A                chain A in model 1
#1/A@CA             CA atoms in chain A
#1/A & protein      protein atoms in chain A
#1/B                ligand/peptide chain B in model 1
#1/A & within 4.5 of #1/B
```

For a local contact view, use a broader `--focus` than `--contact-a`, usually 7-10 A around the ligand/peptide.

## Coloring

Reference/prediction overlays:

```chimerax
color #1 #B8BDC2
color #2 #4F7DB8
color #3 #F4A6C8
```

Chain coloring:

```chimerax
color bychain
color #1/A #BFE9FF
color #1/B #F4A6C8
```

For Baker-style light blue/pink panels, start with:

```text
gray reference: #B8BDC2
AF/baseline blue: #4F7DB8
light GPCR icon blue: #BFE9FF
pink method/accent: #F4A6C8
teal method/accent: #55B8B6
```

## Alignment

Default protein overlay:

```chimerax
matchmaker #2 to #1
matchmaker #3 to #1
```

When automatic chain matching is wrong, use explicit chain matching:

```chimerax
match #2/A to #1/A
match #3/A to #1/A
```

Keep the same whole-structure orientation and only change zoom/focus for corresponding local panels.

## Local Contacts and Hydrogen Bonds

Show contact residues and ligand/peptide without surfaces:

```chimerax
show #1/A cartoons
show #1/A & within 4.5 of #1/B atoms
style #1/A & within 4.5 of #1/B stick
color #1/A & within 4.5 of #1/B #87B7E8
show #1/B atoms
style #1/B stick
color #1/B #F3A5C8
view #1/A & within 8 of #1/B | #1/B
zoom 1.8
```

Hydrogen-bond command pattern:

```chimerax
select clear
select #1/A & within 4.5 of #1/B | #1/B
hbonds restrict both reveal true color #D95F02 radius 0.08 dashes 6 showDist false
select clear
```

If a ChimeraX version rejects this command, render without `--hbonds`, then open the `.cxs` and run `hbonds` interactively from the ChimeraX command line. Keep the corrected command in the `.cxc` for reproducibility.

## Camera Tuning

Use these commands after loading/alignment and before save:

```chimerax
view
turn y 20
turn x -10
roll z 5
zoom 1.4
```

For icons, render large with transparency and crop after rendering. If tails or long loops dominate the crop, prepare a receptor-core structure first or hide selected termini in the `.cxc`.
