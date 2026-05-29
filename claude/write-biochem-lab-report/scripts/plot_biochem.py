"""Generate clean biochemistry report figures from CSV data.

Examples:
  python scripts/plot_biochem.py elution data/gf_elution.csv figures/elution_curve.pdf
  python scripts/plot_biochem.py standard data/gf_standard.csv figures/gf_standard_curve.pdf --x kav --y log_mw --unknown-x 0.55
  python scripts/plot_biochem.py bca data/bca_standard.csv figures/bca_standard_curve.pdf --unknown-y 0.612
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


def setup_report_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 9.5,
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8.5,
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.edgecolor": "black",
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.top": False,
            "ytick.right": False,
            "xtick.major.size": 3.5,
            "ytick.major.size": 3.5,
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "legend.handlelength": 1.8,
            "legend.handletextpad": 0.5,
            "legend.borderaxespad": 0.3,
        }
    )


def finish_axes(ax) -> None:
    ax.minorticks_off()
    ax.tick_params(which="both", direction="out", top=False, right=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color("black")
        ax.spines[side].set_linewidth(0.8)


def save_figure(fig, output: Path, *, overwrite: bool = False) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    paired_png = output.with_suffix(".png") if output.suffix.lower() == ".pdf" else None
    existing = [path for path in [output, paired_png] if path is not None and path.exists()]
    try:
        if existing and not overwrite:
            existing_list = "\n".join(f"  - {path}" for path in existing)
            raise SystemExit(
                "Refusing to overwrite existing figure files. "
                "Choose a new output name or pass --overwrite intentionally.\n"
                f"Existing files:\n{existing_list}"
            )
        fig.tight_layout(pad=0.55)
        fig.savefig(output)
        if paired_png is not None:
            fig.savefig(paired_png)
    finally:
        plt.close(fig)


def write_results(path: Path, lines: list[str], *, overwrite: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise SystemExit(
            "Refusing to overwrite existing results file. "
            "Choose a new --results path or pass --overwrite intentionally.\n"
            f"Existing file:\n  - {path}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_elution(args: argparse.Namespace) -> None:
    df = pd.read_csv(args.csv)
    fig, ax = plt.subplots(figsize=(args.width, args.height))
    ax.plot(
        df[args.x],
        df[args.y],
        color=args.line_color,
        marker="o",
        markerfacecolor="white",
        markeredgecolor=args.line_color,
        markeredgewidth=0.9,
        linewidth=1.25,
        markersize=3.6,
        label=args.legend,
    )
    if args.title:
        ax.set_title(args.title)
    ax.set_xlabel(args.xlabel)
    ax.set_ylabel(args.ylabel)
    if args.legend:
        ax.legend(loc=args.legend_loc, frameon=False, handlelength=2.2)
    finish_axes(ax)
    save_figure(fig, args.output, overwrite=args.overwrite)


def plot_standard(args: argparse.Namespace) -> None:
    df = pd.read_csv(args.csv)
    x = df[args.x].to_numpy(dtype=float)
    y = df[args.y].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    fitted = slope * x + intercept
    r2 = 1 - np.sum((y - fitted) ** 2) / np.sum((y - y.mean()) ** 2)

    xfit = np.linspace(x.min() - 0.05 * (x.max() - x.min()), x.max() + 0.05 * (x.max() - x.min()), 100)
    yfit = slope * xfit + intercept
    fig, ax = plt.subplots(figsize=(args.width, args.height))
    ax.scatter(
        x,
        y,
        facecolors="white",
        edgecolors="black",
        linewidths=0.9,
        s=30,
        label=args.standard_label,
        zorder=3,
    )
    ax.plot(xfit, yfit, color=args.fit_color, linewidth=1.2, label="Linear fit")

    result_lines = [f"slope={slope:.6g}", f"intercept={intercept:.6g}", f"r2={r2:.6g}"]
    if args.unknown_x is not None:
        unknown_y = slope * args.unknown_x + intercept
        ax.scatter(
            [args.unknown_x],
            [unknown_y],
            marker="s",
            facecolors=args.unknown_color,
            edgecolors="black",
            linewidths=0.8,
            s=34,
            label=args.unknown_label,
            zorder=4,
        )
        result_lines.append(f"unknown_y={unknown_y:.6g}")

    if args.title:
        ax.set_title(args.title)
    ax.set_xlabel(args.xlabel)
    ax.set_ylabel(args.ylabel)
    ax.legend(loc=args.legend_loc, frameon=False, handlelength=2.2)
    ax.text(args.eq_x, args.eq_y, f"$y={slope:.3g}x+{intercept:.3g}$\n$R^2={r2:.3f}$", transform=ax.transAxes, fontsize=8.5)
    finish_axes(ax)
    save_figure(fig, args.output, overwrite=args.overwrite)
    if args.results:
        write_results(args.results, result_lines, overwrite=args.overwrite)


def plot_bca(args: argparse.Namespace) -> None:
    df = pd.read_csv(args.csv)
    x = df[args.x].to_numpy(dtype=float)
    y = df[args.y].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    fitted = slope * x + intercept
    r2 = 1 - np.sum((y - fitted) ** 2) / np.sum((y - y.mean()) ** 2)
    unknown_x = None if args.unknown_y is None else (args.unknown_y - intercept) / slope

    xfit = np.linspace(0, x.max() * 1.05, 100)
    yfit = slope * xfit + intercept
    fig, ax = plt.subplots(figsize=(args.width, args.height))
    ax.scatter(x, y, facecolors="white", edgecolors="black", linewidths=0.9, s=30, label=args.standard_label, zorder=3)
    ax.plot(xfit, yfit, color=args.fit_color, linewidth=1.2, label="Linear fit")
    result_lines = [f"slope={slope:.6g}", f"intercept={intercept:.6g}", f"r2={r2:.6g}"]
    if unknown_x is not None:
        ax.scatter([unknown_x], [args.unknown_y], marker="s", facecolors=args.unknown_color, edgecolors="black", linewidths=0.8, s=34, label=args.unknown_label, zorder=4)
        result_lines.append(f"unknown_concentration={unknown_x:.6g}")
    if args.title:
        ax.set_title(args.title)
    ax.set_xlabel(args.xlabel)
    ax.set_ylabel(args.ylabel)
    ax.legend(loc=args.legend_loc, frameon=False, handlelength=2.2)
    ax.text(args.eq_x, args.eq_y, f"$y={slope:.3g}x+{intercept:.3g}$\n$R^2={r2:.3f}$", transform=ax.transAxes, fontsize=8.5)
    finish_axes(ax)
    save_figure(fig, args.output, overwrite=args.overwrite)
    if args.results:
        write_results(args.results, result_lines, overwrite=args.overwrite)


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("csv", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--width", type=float, default=4.9)
    parser.add_argument("--height", type=float, default=2.95)
    parser.add_argument("--title", default="")
    parser.add_argument("--xlabel", default="")
    parser.add_argument("--ylabel", default="")
    parser.add_argument("--legend-loc", default="upper right")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing output figure files.")


def main() -> None:
    setup_report_style()
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="kind", required=True)

    elution = subparsers.add_parser("elution")
    add_common(elution)
    elution.add_argument("--x", default="volume_ml")
    elution.add_argument("--y", default="a280")
    elution.add_argument("--legend", default="Protein absorbance")
    elution.add_argument("--line-color", default="#1f77b4")
    elution.set_defaults(func=plot_elution)

    standard = subparsers.add_parser("standard")
    add_common(standard)
    standard.add_argument("--x", required=True)
    standard.add_argument("--y", required=True)
    standard.add_argument("--unknown-x", type=float)
    standard.add_argument("--standard-label", default="Standard proteins")
    standard.add_argument("--unknown-label", default="Unknown sample")
    standard.add_argument("--unknown-color", default="#2ca02c")
    standard.add_argument("--fit-color", default="#d62728")
    standard.add_argument("--eq-x", type=float, default=0.05)
    standard.add_argument("--eq-y", type=float, default=0.08)
    standard.add_argument("--results", type=Path)
    standard.set_defaults(func=plot_standard)

    bca = subparsers.add_parser("bca")
    add_common(bca)
    bca.add_argument("--x", default="concentration_mg_ml")
    bca.add_argument("--y", default="a562")
    bca.add_argument("--unknown-y", type=float)
    bca.add_argument("--standard-label", default="BSA standards")
    bca.add_argument("--unknown-label", default="Unknown sample")
    bca.add_argument("--unknown-color", default="#2ca02c")
    bca.add_argument("--fit-color", default="#d62728")
    bca.add_argument("--eq-x", type=float, default=0.56)
    bca.add_argument("--eq-y", type=float, default=0.10)
    bca.add_argument("--results", type=Path)
    bca.set_defaults(func=plot_bca)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
