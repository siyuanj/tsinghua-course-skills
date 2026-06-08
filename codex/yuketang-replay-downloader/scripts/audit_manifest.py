from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def resolve_path(path_value: str, base_dir: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def path_from_record(value: Any, base_dir: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return resolve_path(value, base_dir)


def load_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise SystemExit(f"Manifest must be a JSON list: {path}")
    return [record for record in payload if isinstance(record, dict)]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a Yuketang replay manifest for missing files, zero-byte files, duplicate path collisions, and incomplete multi-part lessons."
    )
    parser.add_argument("--manifest", required=True, help="Path to replays.json")
    parser.add_argument(
        "--download-dir",
        default=None,
        help="Directory containing MP4 files. Defaults to the manifest parent.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a text summary.",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    base_dir = Path(args.download_dir).resolve() if args.download_dir else manifest_path.parent
    records = load_records(manifest_path)

    status_counts = Counter(record.get("status") for record in records)
    media_count_by_record = Counter(len(record.get("media_urls") or []) for record in records)
    missing_files: list[dict[str, Any]] = []
    zero_byte_files: list[dict[str, Any]] = []
    multipart_gaps: list[dict[str, Any]] = []
    legacy_multipart_records: list[dict[str, Any]] = []
    file_to_records: defaultdict[str, list[str]] = defaultdict(list)

    total_media_urls = 0
    total_media_downloads = 0

    for index, record in enumerate(records, start=1):
        title = str(record.get("title") or f"record-{index}")
        media_urls = record.get("media_urls") or []
        media_downloads = record.get("media_downloads") or []
        total_media_urls += len(media_urls)
        total_media_downloads += len(media_downloads)

        if len(media_urls) > 1 and not media_downloads:
            legacy_multipart_records.append(
                {
                    "index": index,
                    "title": title,
                    "media_urls": len(media_urls),
                    "file_path": record.get("file_path"),
                }
            )

        if media_urls and media_downloads and len(media_urls) != len(media_downloads):
            multipart_gaps.append(
                {
                    "index": index,
                    "title": title,
                    "media_urls": len(media_urls),
                    "media_downloads": len(media_downloads),
                }
            )

        paths: list[tuple[int | None, Path]] = []
        if media_downloads:
            for part in media_downloads:
                if not isinstance(part, dict):
                    continue
                path = path_from_record(part.get("file_path"), base_dir)
                if path:
                    paths.append((part.get("index"), path))
        elif media_urls:
            path = path_from_record(record.get("file_path"), base_dir)
            if path:
                paths.append((None, path))

        for part_index, path in paths:
            file_to_records[str(path)].append(f"{index}:{title}")
            item = {
                "index": index,
                "part": part_index,
                "title": title,
                "file_path": str(path),
            }
            if not path.exists():
                missing_files.append(item)
            elif path.stat().st_size <= 0:
                zero_byte_files.append(item)

    duplicate_file_collisions = [
        {"file_path": path, "records": values}
        for path, values in sorted(file_to_records.items())
        if len(values) > 1
    ]

    report = {
        "manifest": str(manifest_path),
        "download_dir": str(base_dir),
        "records": len(records),
        "status_counts": dict(status_counts),
        "media_count_by_record": dict(media_count_by_record),
        "total_media_urls": total_media_urls,
        "total_media_downloads": total_media_downloads,
        "missing_files": missing_files,
        "zero_byte_files": zero_byte_files,
        "multipart_gaps": multipart_gaps,
        "legacy_multipart_records": legacy_multipart_records,
        "duplicate_file_collisions": duplicate_file_collisions,
        "ok": not (
            missing_files
            or zero_byte_files
            or multipart_gaps
            or legacy_multipart_records
            or duplicate_file_collisions
        ),
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 1

    print(f"manifest: {report['manifest']}")
    print(f"download_dir: {report['download_dir']}")
    print(f"records: {report['records']}")
    print(f"status_counts: {report['status_counts']}")
    print(f"media_count_by_record: {report['media_count_by_record']}")
    print(f"total_media_urls: {total_media_urls}")
    print(f"total_media_downloads: {total_media_downloads}")
    print(f"missing_files: {len(missing_files)}")
    print(f"zero_byte_files: {len(zero_byte_files)}")
    print(f"multipart_gaps: {len(multipart_gaps)}")
    print(f"legacy_multipart_records: {len(legacy_multipart_records)}")
    print(f"duplicate_file_collisions: {len(duplicate_file_collisions)}")

    for label in (
        "missing_files",
        "zero_byte_files",
        "multipart_gaps",
        "legacy_multipart_records",
        "duplicate_file_collisions",
    ):
        values = report[label]
        if values:
            print(f"\n{label}:")
            for value in values:
                print(json.dumps(value, ensure_ascii=False))

    print(f"\nok: {report['ok']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
