#!/usr/bin/env python3
"""Portable ChimeraX structure figure renderer.

This script intentionally delegates molecular display to ChimeraX and keeps a
reproducible .cxc command file beside every output image.
"""

from __future__ import annotations

import argparse
import csv
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_MODEL_COLORS = [
    "#B8BDC2",
    "#4F7DB8",
    "#F4A6C8",
    "#55B8B6",
    "#9A86B8",
    "#6F9273",
    "#D08A63",
]


def quote_cx(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    return '"' + text.replace('"', '\\"') + '"'


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def ensure_out_path(path: str | Path) -> Path:
    out = Path(path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def find_chimerax(explicit: str | None = None) -> Path:
    candidates: list[str | Path] = []
    if explicit:
        path = Path(explicit).expanduser()
        if path.exists():
            return path.resolve()
        candidates.append(explicit)
    for env_name in ("CHIMERAX_EXE", "CHIMERAX"):
        value = os.environ.get(env_name)
        if value:
            candidates.append(value)

    system = platform.system().lower()
    if system == "windows":
        candidates.extend(
            [
                r"C:\Program Files\ChimeraX\bin\ChimeraX.exe",
                r"C:\Program Files\ChimeraX 1.10\bin\ChimeraX.exe",
                r"C:\Program Files\ChimeraX 1.10.1\bin\ChimeraX.exe",
                r"D:\Program Files\ChimeraX 1.10.1\bin\ChimeraX.exe",
                r"E:\Program Files\ChimeraX\bin\ChimeraX.exe",
            ]
        )
    elif system == "darwin":
        candidates.extend(
            [
                "/Applications/ChimeraX.app/Contents/MacOS/ChimeraX",
                "/Applications/UCSF ChimeraX.app/Contents/MacOS/ChimeraX",
            ]
        )
    else:
        candidates.extend(["/usr/local/bin/ChimeraX", "/usr/bin/chimerax"])

    for name in ("ChimeraX", "ChimeraX.exe", "chimerax"):
        found = shutil.which(name)
        if found:
            candidates.append(found)

    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.exists():
            if not explicit and path.name.lower() == "chimerax-console.exe":
                continue
            return path.resolve()
    raise FileNotFoundError(
        "Could not find ChimeraX. Pass --chimerax or set CHIMERAX_EXE to the ChimeraX executable."
    )


def model_spec(index: int, chain: str | None = None) -> str:
    return f"#{index}/{chain}" if chain else f"#{index}"


def apply_colors(lines: list[str], args: argparse.Namespace, model_count: int) -> None:
    colors = split_csv(args.colors)
    chain_colors = split_csv(args.chain_colors)
    if args.color:
        for idx in range(1, model_count + 1):
            lines.append(f"color #{idx} {args.color}")
        return

    if chain_colors:
        for spec in chain_colors:
            if ":" not in spec:
                raise ValueError(f"Bad --chain-colors item {spec!r}; expected CHAIN:#RRGGBB")
            chain, color = spec.split(":", 1)
            for idx in range(1, model_count + 1):
                lines.append(f"color {model_spec(idx, chain)} {color}")
        return

    if colors:
        for idx in range(1, model_count + 1):
            color = colors[(idx - 1) % len(colors)]
            lines.append(f"color #{idx} {color}")
        return

    if args.color_mode == "chain":
        lines.append("color bychain")
    else:
        for idx in range(1, model_count + 1):
            lines.append(f"color #{idx} {DEFAULT_MODEL_COLORS[(idx - 1) % len(DEFAULT_MODEL_COLORS)]}")


def add_common_display(lines: list[str], args: argparse.Namespace) -> None:
    lines.extend(
        [
            "hide atoms",
            "hide cartoons",
            "hide surfaces",
        ]
    )
    if args.style == "cartoon":
        lines.append("show cartoons")
        lines.append(f"cartoon style width {args.cartoon_width:g} thickness {args.cartoon_thickness:g}")
    elif args.style == "sticks":
        lines.append("show atoms")
        lines.append("style stick")
    elif args.style == "surface":
        lines.append("show surfaces")
    else:
        raise ValueError(f"Unsupported style: {args.style}")

    lines.extend(
        [
            f"set bgColor {args.background}",
            f"lighting {args.lighting}",
            f"graphics silhouettes {'true' if args.silhouettes else 'false'}",
            f"graphics silhouettes width {args.silhouette_width:g}",
        ]
    )


def add_alignment(lines: list[str], args: argparse.Namespace, model_count: int) -> None:
    if args.no_matchmaker:
        return
    for idx in range(2, model_count + 1):
        lines.append(f"matchmaker #{idx} to #1")


def add_contact_display(lines: list[str], args: argparse.Namespace) -> None:
    if args.context:
        lines.append(f"show {args.context} cartoons")
    if args.contact_a:
        lines.append(f"show {args.contact_a} atoms")
        lines.append(f"style {args.contact_a} stick")
        lines.append(f"color {args.contact_a} {args.contact_a_color}")
    if args.contact_b:
        lines.append(f"show {args.contact_b} atoms")
        lines.append(f"style {args.contact_b} stick")
        lines.append(f"color {args.contact_b} {args.contact_b_color}")
    if args.hbonds:
        if not (args.contact_a and args.contact_b):
            raise ValueError("--hbonds requires --contact-a and --contact-b")
        lines.append("select clear")
        lines.append(f"select {args.contact_a} | {args.contact_b}")
        lines.append(
            f"hbonds restrict both reveal true color {args.hbond_color} radius {args.hbond_radius:g} "
            f"dashes {args.hbond_dashes:d} showDist {'true' if args.show_hbond_distances else 'false'}"
        )
        lines.append("select clear")


def add_view_and_save(lines: list[str], args: argparse.Namespace, out_png: Path, session_path: Path) -> None:
    for command in args.extra_cmd or []:
        lines.append(command)
    if args.focus:
        lines.append(f"view {args.focus}")
    elif args.view_command:
        lines.append(args.view_command)
    else:
        lines.append("view")
    if args.zoom:
        lines.append(f"zoom {args.zoom:g}")
    lines.append(f"save {quote_cx(session_path.name)}")
    lines.append(
        f"save {quote_cx(out_png)} width {args.width:d} height {args.height:d} "
        f"supersample {args.supersample:d} transparentBackground {'true' if args.transparent else 'false'}"
    )
    lines.append("exit")


def build_cxc(args: argparse.Namespace, out_png: Path, cxs_path: Path) -> list[str]:
    structures = [Path(p).expanduser().resolve() for p in args.structure]
    for structure in structures:
        if not structure.exists():
            raise FileNotFoundError(structure)

    lines: list[str] = []
    for idx, structure in enumerate(structures, start=1):
        lines.append(f"open {quote_cx(structure)} name model{idx}")

    add_common_display(lines, args)
    apply_colors(lines, args, len(structures))

    if args.mode in {"align", "align-contact"}:
        add_alignment(lines, args, len(structures))

    if args.mode in {"contact", "align-contact"}:
        add_contact_display(lines, args)

    add_view_and_save(lines, args, out_png, cxs_path)
    return lines


def run_chimerax(chimerax: Path, cxc_path: Path, out_dir: Path, dry_run: bool = False) -> None:
    if dry_run:
        return
    result = subprocess.run([str(chimerax), "--script", cxc_path.name], cwd=str(out_dir))
    if result.returncode != 0:
        raise RuntimeError(f"ChimeraX failed with exit code {result.returncode}: {cxc_path}")


def crop_png(path: Path, square: bool = False, pad: int = 40) -> None:
    try:
        from PIL import Image
        import numpy as np
    except Exception as exc:
        raise RuntimeError("Cropping requires Pillow and NumPy. Install them or omit --crop.") from exc

    image = Image.open(path).convert("RGBA")
    alpha = np.asarray(image.getchannel("A"))
    ys, xs = np.where(alpha > 8)
    if len(xs) == 0:
        raise RuntimeError(f"Rendered image is blank: {path}")
    box = (
        max(0, int(xs.min()) - pad),
        max(0, int(ys.min()) - pad),
        min(image.width, int(xs.max()) + 1 + pad),
        min(image.height, int(ys.max()) + 1 + pad),
    )
    cropped = image.crop(box)
    if square:
        side = max(cropped.width, cropped.height)
        canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
        canvas.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2))
        cropped = canvas
    cropped.save(path)


def write_manifest(path: Path, args: argparse.Namespace, cxc_path: Path, cxs_path: Path, chimerax: Path | None) -> None:
    fields = [
        "mode",
        "output_png",
        "cxc",
        "cxs",
        "chimerax",
        "structures",
        "transparent",
        "style",
        "colors",
        "chain_colors",
        "contact_a",
        "contact_b",
        "focus",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "mode": args.mode,
                "output_png": str(Path(args.out).resolve()),
                "cxc": str(cxc_path),
                "cxs": str(cxs_path),
                "chimerax": str(chimerax) if chimerax else "",
                "structures": ";".join(str(Path(p).resolve()) for p in args.structure),
                "transparent": str(bool(args.transparent)),
                "style": args.style,
                "colors": args.colors or "",
                "chain_colors": args.chain_colors or "",
                "contact_a": args.contact_a or "",
                "contact_b": args.contact_b or "",
                "focus": args.focus or "",
            }
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render structure figures through ChimeraX.")
    parser.add_argument("--mode", choices=["single", "contact", "align", "align-contact"], required=True)
    parser.add_argument("--structure", action="append", required=True, help="Input PDB/mmCIF. Repeat for overlays.")
    parser.add_argument("--out", required=True, help="Output PNG path.")
    parser.add_argument("--chimerax", help="Path to ChimeraX executable.")
    parser.add_argument("--dry-run", action="store_true", help="Only write the .cxc and manifest; do not run ChimeraX.")

    parser.add_argument("--style", choices=["cartoon", "sticks", "surface"], default="cartoon")
    parser.add_argument("--color-mode", choices=["chain", "model"], default="chain")
    parser.add_argument("--color", help="Single color for all visible atoms/cartoons, e.g. #BFE9FF.")
    parser.add_argument("--colors", help="Comma-separated model colors.")
    parser.add_argument("--chain-colors", help="Comma-separated CHAIN:#RRGGBB pairs applied to all models.")
    parser.add_argument("--cartoon-width", type=float, default=1.25)
    parser.add_argument("--cartoon-thickness", type=float, default=0.24)

    parser.add_argument("--context", help="ChimeraX atom spec for cartoon context in contact modes.")
    parser.add_argument("--contact-a", help="First side of local contact, ChimeraX atom spec.")
    parser.add_argument("--contact-b", help="Second side of local contact, ChimeraX atom spec.")
    parser.add_argument("--contact-a-color", default="#87B7E8")
    parser.add_argument("--contact-b-color", default="#F3A5C8")
    parser.add_argument("--focus", help="ChimeraX atom spec to view/zoom around.")
    parser.add_argument("--hbonds", action="store_true", help="Draw hydrogen bonds between selected contact atoms.")
    parser.add_argument("--hbond-color", default="#D95F02")
    parser.add_argument("--hbond-radius", type=float, default=0.08)
    parser.add_argument("--hbond-dashes", type=int, default=6)
    parser.add_argument("--show-hbond-distances", action="store_true")

    parser.add_argument("--no-matchmaker", action="store_true", help="Do not run matchmaker in align modes.")
    parser.add_argument("--extra-cmd", action="append", help="Extra raw ChimeraX command appended before view/save.")
    parser.add_argument("--view-command", default="view", help="Raw ChimeraX view command, e.g. 'view orient'.")
    parser.add_argument("--zoom", type=float, default=1.35)

    parser.add_argument("--background", default="white")
    parser.add_argument("--transparent", action="store_true")
    parser.add_argument("--width", type=int, default=1400)
    parser.add_argument("--height", type=int, default=1400)
    parser.add_argument("--supersample", type=int, default=3)
    parser.add_argument("--lighting", default="soft")
    parser.add_argument("--silhouettes", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--silhouette-width", type=float, default=1.2)
    parser.add_argument("--crop", action="store_true", help="Crop transparent PNG to nonblank alpha bounds.")
    parser.add_argument("--square", action="store_true", help="Pad cropped transparent PNG to a square.")
    parser.add_argument("--crop-pad", type=int, default=40)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.mode in {"align", "align-contact"} and len(args.structure) < 2:
        raise SystemExit("--mode align and align-contact require at least two --structure inputs")
    if args.mode in {"contact", "align-contact"} and not (args.contact_a and args.contact_b):
        raise SystemExit("--mode contact and align-contact require --contact-a and --contact-b")

    out_png = ensure_out_path(args.out)
    out_dir = out_png.parent
    stem = out_png.with_suffix("")
    cxc_path = stem.with_suffix(".cxc")
    cxs_path = stem.with_suffix(".cxs")
    manifest_path = stem.with_name(stem.name + "_manifest.csv")

    chimerax = None if args.dry_run else find_chimerax(args.chimerax)
    cxc_lines = build_cxc(args, out_png, cxs_path)
    cxc_path.write_text("\n".join(cxc_lines) + "\n", encoding="utf-8")
    write_manifest(manifest_path, args, cxc_path, cxs_path, chimerax)
    if chimerax:
        run_chimerax(chimerax, cxc_path, out_dir, dry_run=args.dry_run)
    if args.crop:
        crop_png(out_png, square=args.square, pad=args.crop_pad)

    print(f"Wrote CXC: {cxc_path}")
    if not args.dry_run:
        print(f"Wrote PNG: {out_png}")
        print(f"Wrote CXS: {cxs_path}")
    print(f"Wrote manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
