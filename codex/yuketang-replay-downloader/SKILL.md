---
name: yuketang-replay-downloader
description: Download, resume, audit, and verify authorized Yuketang/Rain Classroom replay MP4s from a logged-in course session. Use when the user asks to find a course by name, capture replay URLs, download all replay segments, continue missing course videos, store course videos locally, or troubleshoot login redirects, expired signed URLs, duplicate-title collisions, incomplete multi-part downloads, already_downloaded, and no_media_found statuses.
---

# Yuketang Replay Downloader

## Scope And Safety

- Use only for replay videos available in the user's own authorized Yuketang/Rain Classroom browser session.
- Do not bypass login, DRM, payment, teacher visibility settings, or access controls.
- Do not publish signed media URLs, course manifests, cookies, local browser profiles, or user-specific course IDs.
- Signed replay URLs expire; recapture them through the normal logged-in course page instead of reusing old URLs.
- Do not transcribe videos unless the user asks for transcription.

## Included Scripts

- `scripts/batch_yuketang_replays.py`: reuses a local Chrome login session, reads the authorized course activity API, captures replay media URLs, and downloads every MP4 segment.
- `scripts/download_yuketang_replay.ps1`: downloads one signed MP4 URL with the required Yuketang headers and resume support.
- `scripts/audit_manifest.py`: audits `replays.json` for missing files, zero-byte files, incomplete multi-part lessons, and duplicate file-path collisions.

## Setup

Use Python 3.10+ with Playwright and a system Chrome installation:

```powershell
python -m pip install playwright
python -m playwright install chromium
python "$env:USERPROFILE\.codex\skills\yuketang-replay-downloader\scripts\batch_yuketang_replays.py" --help
```

Windows needs `curl.exe` in `PATH` for direct MP4 download. PowerShell examples should keep the course URL in a variable so query strings containing `&` are not split by the shell.

## Workflow

1. Create a task folder for logs, manifests, and notes.
2. Determine the course URL. If the user provides only a course name, use Course Discovery By Name below.
3. Run the audit script before declaring old downloads complete.
4. Run the batch downloader with a persistent Chrome profile. Sign in in the Chrome window if prompted.
5. Monitor stdout, stderr, and the download directory until the downloader exits.
6. Validate the manifest, file count, zero-byte files, multi-part coverage, and any `no_media_found` records.
7. Record what was downloaded and any remaining unavailable replays in task notes.

## Course Discovery By Name

Use this when the user names a course but does not provide the course URL.

- Reuse a persistent Chrome profile such as `.playwright-yuketang-profile`.
- Open the logged-in Yuketang/Rain Classroom course list or landing page.
- Capture normal page JSON responses and visible page text.
- Search by exact course name first, then teacher, semester, and display name.
- Extract `classroom_id`, `university_id`, and `platform_id` from the matching course object or link.
- Build the course URL:

```text
https://pro.yuketang.cn/v2/web/studentLog/CLASSROOM_ID?university_id=UNIVERSITY_ID&platform_id=PLATFORM_ID&classroom_id=CLASSROOM_ID&content_url=
```

If several courses match, ask the user to choose unless course name, teacher, semester, and IDs make the target unambiguous.

## Batch Download

```powershell
$skill = "$env:USERPROFILE\.codex\skills\yuketang-replay-downloader"
$courseUrl = "https://pro.yuketang.cn/v2/web/studentLog/CLASSROOM_ID?university_id=UNIVERSITY_ID&platform_id=PLATFORM_ID&classroom_id=CLASSROOM_ID&content_url="

python "$skill\scripts\batch_yuketang_replays.py" `
  --course-url $courseUrl `
  --output-dir downloads `
  --manifest-path downloads\replays.json `
  --profile-dir .playwright-yuketang-profile `
  --login-timeout-seconds 600
```

The batch script waits for the authenticated course API before collecting lessons. A redirected login page or API `401` means the user needs to sign in in the opened Chrome window and rerun the command.

## Naming Rules

- File names are derived from lesson titles with Windows-invalid characters replaced.
- Multi-segment lessons use `Title.mp4`, `Title - part 2.mp4`, `Title - part 3.mp4`, etc.
- If a user says `part 1` is missing for a multi-segment lesson, first check for the unsuffixed main file `Title.mp4`; in the current naming convention that file is part 1.
- If audit reports a missing `Title - part 2.mp4` but an older numbered file such as `11 Title - part 2.mp4` exists with the expected size and duration, reconcile the manifest path or copy/rename the file before recapturing signed URLs.
- Duplicate lesson titles in one run use `Title.mp4`, `Title - 2.mp4`, `Title - 3.mp4`, etc.
- Keep script-generated names unless the user asks for a rename; inspect the manifest before any manual rename.

## Audit And Validation

Run this after a download and before claiming completion:

```powershell
$skill = "$env:USERPROFILE\.codex\skills\yuketang-replay-downloader"
python "$skill\scripts\audit_manifest.py" `
  --manifest downloads\replays.json `
  --download-dir downloads
```

Interpretation:

- `ok: True`: manifest-covered media files exist and have nonzero size.
- `legacy_multipart_records`: old manifest has multiple `media_urls` but lacks complete `media_downloads`; rerun the fixed batch downloader.
- `multipart_gaps`: `media_downloads` count does not match `media_urls` count.
- `duplicate_file_collisions`: multiple lesson records point to the same MP4 path; recapture and redownload under unique names.
- `missing_files` or `zero_byte_files`: rerun after recapturing fresh signed URLs.

Also verify:

- Every record with media URLs has `len(media_downloads) == len(media_urls)`.
- `media_downloads[*].file_path` exists.
- No downloader process remains running.
- `no_media_found` records are documented; retry only if the normal course UI shows replay availability.
- For multi-part lessons, compare the sum of local part durations with the page's displayed total duration when possible.

## Single Signed URL

Use only when the user provides a fresh authorized replay URL:

```powershell
$skill = "$env:USERPROFILE\.codex\skills\yuketang-replay-downloader"
& "$skill\scripts\download_yuketang_replay.ps1" `
  -ReplayUrl "https://example.com/video.mp4?SIGNED_QUERY=..." `
  -OutputDir downloads `
  -OutputBaseName "lesson-title"
```

Do not commit or share the signed URL.
