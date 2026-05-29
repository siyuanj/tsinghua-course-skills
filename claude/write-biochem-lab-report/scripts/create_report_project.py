"""Create a biochemistry lab report project from bundled assets."""

from __future__ import annotations

import argparse
import shutil
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


def render_template(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--title", default="Biochemistry Laboratory Report")
    parser.add_argument("--name", default="Your Name")
    parser.add_argument("--student-id", default="Your Student ID")
    parser.add_argument("--class-name", default="Your Class")
    parser.add_argument("--date", default=date.today().strftime("%B %d, %Y"))
    parser.add_argument("--lang", choices=["en", "cn"], default="en")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing generated project files if they already exist.",
    )
    args = parser.parse_args()

    planned_files = [
        args.output_dir / "elegantpaper.cls",
        args.output_dir / "scripts" / "plot_biochem.py",
        args.output_dir / "scripts" / "check_report_tex.py",
        args.output_dir / "report.tex",
    ]
    existing = [path for path in planned_files if path.exists()]
    if existing and not args.overwrite:
        existing_list = "\n".join(f"  - {path}" for path in existing)
        raise SystemExit(
            "Refusing to overwrite existing report project files. "
            "Choose a new folder or pass --overwrite intentionally.\n"
            f"Existing files:\n{existing_list}"
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "data").mkdir(exist_ok=True)
    (args.output_dir / "figures").mkdir(exist_ok=True)
    (args.output_dir / "scripts").mkdir(exist_ok=True)

    shutil.copy2(ASSETS / "elegantpaper.cls", args.output_dir / "elegantpaper.cls")
    shutil.copy2(ROOT / "scripts" / "plot_biochem.py", args.output_dir / "scripts" / "plot_biochem.py")
    shutil.copy2(ROOT / "scripts" / "check_report_tex.py", args.output_dir / "scripts" / "check_report_tex.py")

    template = (ASSETS / "report_template.tex").read_text(encoding="utf-8")
    rendered = render_template(
        template,
        {
            "TITLE": args.title,
            "NAME": args.name,
            "STUDENT_ID": args.student_id,
            "CLASS_NAME": args.class_name,
            "DATE": args.date,
            "LANG": args.lang,
        },
    )
    (args.output_dir / "report.tex").write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
