# Status

## Current State

- Added `chimerax-structure-figures` for both Claude and Codex skill layouts.
- The skill is a generic UCSF ChimeraX structure-rendering workflow for
  standalone whole-structure panels, local contact closeups with optional
  hydrogen bonds, aligned whole-structure overlays, and aligned local-contact
  overlays.
- The bundled script generates reproducible `.cxc` command files, saves `.cxs`
  sessions, renders PNG output, supports transparent icon rendering, and avoids
  hardcoded project-local structure paths.
- Clarified the `yuketang-replay-downloader` naming guidance after a
  real-world audit case: for multi-segment lessons, the unsuffixed `Title.mp4`
  is part 1, and agents should check for older numbered files such as
  `11 Title - part 2.mp4` before recapturing signed URLs for a reported
  missing `Title - part 2.mp4`.
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
  `render_structure_figure.py`.
- The `chimerax-structure-figures` skill passed the Codex skill validator before
  import into this repository.
- A local MC4R single-structure transparent PNG render was tested before
  import; contact and align modes were checked with dry-run `.cxc` generation.
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
