# Status

## Current State

- Added `yuketang-replay-downloader` for both Claude and Codex skill layouts.
- The skill is a generic authorized Yuketang/Rain Classroom replay downloader
  and auditor. It does not include user-specific course IDs, signed media URLs,
  browser profiles, cookies, manifests, local absolute paths, or downloaded
  videos.
- Added bundled scripts for batch replay capture/download, single signed URL
  download, and manifest auditing.
- Updated `.gitignore` to avoid committing downloaded course artifacts such as
  MP4 files, manifests, transcripts, and Playwright browser profiles.
- Updated `README.md` with the new skill, install examples, dependencies, and
  contribution privacy guidance.

## Validation

- Python syntax check passed for both Claude and Codex copies of
  `batch_yuketang_replays.py` and `audit_manifest.py`.
- PowerShell syntax check passed for both copies of
  `download_yuketang_replay.ps1`.
- Sensitive-content scan found no user-specific paths, course IDs, signed
  media URLs, or tokens in the new Yuketang skill files.

## Next Step

- After future changes to the Yuketang skill, rerun syntax checks and scan for
  local paths, signed URLs, cookies, browser profiles, manifests, and video
  files before pushing.
