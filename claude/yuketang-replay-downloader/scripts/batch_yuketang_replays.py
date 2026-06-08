import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set
from urllib.parse import parse_qs, urlparse

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: playwright. Install it with `python -m pip install playwright`."
    ) from exc


COURSE_URL_FRAGMENT = "/v2/web/studentLog/"
REPORT_URL_FRAGMENT = "/v2/web/student-lesson-report/"
MEDIA_HOST_FRAGMENT = "ks-playback.xuetangx.com"
LESSON_BADGE = "\u8bfe\u5802"
PLAY_TEXT = "\u64ad\u653e"
MEDIA_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
MEDIA_HINT_RE = re.compile(r"(\.mp4\b|\.m3u8\b|ks-playback\.xuetangx\.com)", re.IGNORECASE)
SUBTITLE_HINT_RE = re.compile(r"(\.vtt\b|\.srt\b|subtitle|caption)", re.IGNORECASE)


def slugify(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"[\\/:*?\"<>|]", "_", value)
    return value[:180] or "lesson"


def unique_base_name(base_name: str, counts: Dict[str, int]) -> tuple[str, int]:
    occurrence = counts.get(base_name, 0) + 1
    counts[base_name] = occurrence
    if occurrence == 1:
        return base_name, occurrence

    suffix = f" - {occurrence}"
    return f"{base_name[:180 - len(suffix)]}{suffix}", occurrence


def media_part_base_name(base_name: str, media_index: int) -> str:
    if media_index <= 1:
        return base_name

    suffix = f" - part {media_index}"
    return f"{base_name[:180 - len(suffix)]}{suffix}"


def walk_strings(node: Any) -> Iterable[str]:
    if isinstance(node, str):
        yield node
        return
    if isinstance(node, dict):
        for value in node.values():
            yield from walk_strings(value)
        return
    if isinstance(node, list):
        for value in node:
            yield from walk_strings(value)


def extract_urls_from_json(payload: Any) -> List[str]:
    urls: List[str] = []
    seen: Set[str] = set()
    for text in walk_strings(payload):
        for match in MEDIA_URL_RE.findall(text):
            if match not in seen:
                seen.add(match)
                urls.append(match)
    return urls


def parse_course_metadata(course_url: str) -> Dict[str, str]:
    parsed = urlparse(course_url)
    query = parse_qs(parsed.query)
    classroom_match = re.search(r"/studentLog/(\d+)", parsed.path)
    classroom_id = classroom_match.group(1) if classroom_match else ""
    classroom_id = classroom_id or (query.get("classroom_id", [""])[0])

    if not classroom_id:
        raise RuntimeError("Could not determine classroom_id from --course-url")

    return {
        "classroom_id": classroom_id,
        "university_id": query.get("university_id", [""])[0],
        "platform_id": query.get("platform_id", [""])[0],
    }


def is_media_url(url: str) -> bool:
    return bool(MEDIA_HINT_RE.search(url))


def is_subtitle_url(url: str) -> bool:
    return bool(SUBTITLE_HINT_RE.search(url))


def fetch_json(api_context, url: str) -> Dict[str, Any]:
    response = api_context.get(url)
    if response.status != 200:
        raise RuntimeError(f"Request failed: {response.status} {url}")
    payload = response.json()
    if isinstance(payload, dict):
        if payload.get("errcode") not in (None, 0):
            raise RuntimeError(f"API errcode {payload.get('errcode')} for {url}")
        if payload.get("code") not in (None, 0):
            raise RuntimeError(f"API code {payload.get('code')} for {url}")
        if payload.get("success") is False:
            raise RuntimeError(f"API success=false for {url}")
    return payload


def collect_lessons_from_api(api_context, classroom_id: str) -> List[Dict[str, Any]]:
    page_index = 0
    offset = 20
    lessons: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    while True:
        url = (
            f"https://pro.yuketang.cn/v2/api/web/logs/learn/{classroom_id}"
            f"?actype=-1&page={page_index}&offset={offset}&sort=-1"
        )
        payload = fetch_json(api_context, url)
        data = payload.get("data", {})
        activities = data.get("activities", [])

        for activity in activities:
            if activity.get("type") != 14:
                continue
            activity_id = str(activity.get("id", ""))
            lesson_id = str(activity.get("courseware_id", ""))
            title = (activity.get("title") or "").strip()
            if not activity_id or not lesson_id or not title or activity_id in seen_ids:
                continue
            seen_ids.add(activity_id)
            lessons.append(
                {
                    "activity_id": activity_id,
                    "lesson_id": lesson_id,
                    "title": title,
                    "create_time": activity.get("create_time"),
                    "attend_status": activity.get("attend_status"),
                    "is_finished": activity.get("is_finished"),
                }
            )

        if not data.get("has_more"):
            break
        page_index += 1

    return lessons


def fetch_replay_data(api_context, lesson_id: str) -> Dict[str, Any]:
    front_time = int(time.time() * 1000)
    url = (
        "https://pro.yuketang.cn/api/v3/classroom-report/replay"
        f"?lesson_id={lesson_id}&canFakeLive=1&front_time={front_time}"
    )
    payload = fetch_json(api_context, url)
    return payload.get("data", {})


def extract_media_entries(replay_data: Dict[str, Any]) -> Dict[str, List[str]]:
    media_urls: List[str] = []
    subtitle_urls: List[str] = []
    seen_media: Set[str] = set()
    seen_subtitles: Set[str] = set()

    for group_name in ("live", "record"):
        for entry in replay_data.get(group_name, []) or []:
            media_url = (entry.get("url") or "").strip()
            subtitle_url = (entry.get("subtitlePath") or "").strip()

            if media_url and media_url not in seen_media:
                seen_media.add(media_url)
                media_urls.append(media_url)

            if subtitle_url and subtitle_url not in seen_subtitles:
                seen_subtitles.add(subtitle_url)
                subtitle_urls.append(subtitle_url)

    return {
        "media_urls": media_urls,
        "subtitle_urls": subtitle_urls,
    }


def auto_scroll(page, pause_ms: int = 1000, max_rounds: int = 30) -> None:
    last_height = -1
    stable_rounds = 0
    for _ in range(max_rounds):
        height = page.evaluate("() => document.body.scrollHeight")
        if height == last_height:
            stable_rounds += 1
            if stable_rounds >= 2:
                break
        else:
            stable_rounds = 0
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(pause_ms)
        last_height = height
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(500)


def collect_lessons(page) -> List[Dict[str, str]]:
    auto_scroll(page)
    lesson_rows = page.evaluate(
        """
        () => {
          const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          const rows = [];
          const seen = new Set();
          const nodes = Array.from(document.querySelectorAll('a, div, li, article, section'));

          for (const node of nodes) {
            const text = normalize(node.innerText);
            if (!text || !text.includes('\\u8bfe\\u5802')) {
              continue;
            }

            const lines = (node.innerText || '')
              .split(/\\n+/)
              .map(normalize)
              .filter(Boolean);

            let title = lines.find((line) => /^\\d+\\.\\s*/.test(line)) || null;
            if (!title) {
              const match = text.match(/\\u8bfe\\u5802\\s*(\\d+\\.\\s*[^\\n]+)/);
              if (match) {
                title = normalize(match[1]);
              }
            }
            if (!title && lines.length >= 2 && lines[0] === '\\u8bfe\\u5802') {
              title = lines[1];
            }
            if (!title) {
              continue;
            }

            if (seen.has(title)) {
              continue;
            }
            seen.add(title);

            let href = null;
            if (node instanceof HTMLAnchorElement) {
              href = node.href;
            } else {
              const anchor = node.querySelector('a[href]');
              if (anchor instanceof HTMLAnchorElement) {
                href = anchor.href;
              }
            }

            rows.push({
              title,
              href: href || '',
              text
            });
          }

          return rows;
        }
        """
    )
    return lesson_rows


def wait_for_manual_login(page, course_url: str, timeout_seconds: int) -> None:
    page.goto(course_url, wait_until="domcontentloaded")
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        current_url = page.url
        if COURSE_URL_FRAGMENT in current_url and "/web/?next=" not in current_url:
            try:
                page.wait_for_load_state("load", timeout=5000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            return
        page.wait_for_timeout(1000)
    raise RuntimeError(
        "Timed out waiting for a logged-in course page. Re-run the script and sign in when Chrome opens."
    )


def wait_for_course_api_auth(page, api_context, course_url: str, classroom_id: str, timeout_seconds: int) -> None:
    page.goto(course_url, wait_until="domcontentloaded")
    deadline = time.time() + timeout_seconds
    last_status = "course page not ready"
    probe_url = (
        f"https://pro.yuketang.cn/v2/api/web/logs/learn/{classroom_id}"
        "?actype=-1&page=0&offset=1&sort=-1"
    )

    while time.time() < deadline:
        current_url = page.url
        if COURSE_URL_FRAGMENT in current_url and "/web/?next=" not in current_url:
            try:
                response = api_context.get(probe_url)
                last_status = f"API status {response.status}"
                if response.status == 200:
                    payload = response.json()
                    if isinstance(payload, dict):
                        if payload.get("errcode") not in (None, 0):
                            last_status = f"API errcode {payload.get('errcode')}"
                        elif payload.get("code") not in (None, 0):
                            last_status = f"API code {payload.get('code')}"
                        elif payload.get("success") is False:
                            last_status = "API success=false"
                        else:
                            try:
                                page.wait_for_load_state("load", timeout=5000)
                            except Exception:
                                pass
                            page.wait_for_timeout(1000)
                            return
            except Exception as exc:
                last_status = str(exc)
        else:
            last_status = f"current URL {current_url}"

        page.wait_for_timeout(2000)

    raise RuntimeError(
        "Timed out waiting for a logged-in course API session. "
        f"Sign in when Chrome opens and try again. Last check: {last_status}"
    )


def ensure_title_visible(page, title: str) -> None:
    for _ in range(12):
        if page.get_by_text(title, exact=True).count() > 0:
            return
        page.mouse.wheel(0, 1600)
        page.wait_for_timeout(400)
    raise RuntimeError(f"Could not find lesson title on course page: {title}")


def open_lesson_report(page, course_url: str, lesson: Dict[str, str]) -> str:
    page.goto(course_url, wait_until="domcontentloaded")
    ensure_title_visible(page, lesson["title"])
    target = page.get_by_text(lesson["title"], exact=True).first
    target.scroll_into_view_if_needed()
    target.click(timeout=10000)
    page.wait_for_url(f"**{REPORT_URL_FRAGMENT}**", timeout=15000)
    try:
        page.wait_for_load_state("load", timeout=5000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    return page.url


def kick_player(page) -> None:
    selectors = [
        "video",
        f"button:has-text('{PLAY_TEXT}')",
        f"button[aria-label*='{PLAY_TEXT}']",
        f"button[title*='{PLAY_TEXT}']",
        ".vjs-big-play-button",
        ".play-btn",
    ]
    for selector in selectors:
        locator = page.locator(selector)
        if locator.count() == 0:
            continue
        try:
            locator.first.click(timeout=1500)
            break
        except Exception:
            continue

    page.evaluate(
        """
        () => {
          for (const video of document.querySelectorAll('video')) {
            try {
              video.muted = true;
              const maybePromise = video.play();
              if (maybePromise && typeof maybePromise.catch === 'function') {
                maybePromise.catch(() => {});
              }
            } catch (error) {
            }
          }
        }
        """
    )


def scrape_page_urls(page) -> List[str]:
    performance_urls = page.evaluate(
        """
        () => performance.getEntriesByType('resource').map((entry) => entry.name)
        """
    )
    html = page.content()
    urls = list(performance_urls)
    urls.extend(MEDIA_URL_RE.findall(html))
    deduped: List[str] = []
    seen: Set[str] = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def capture_media(page, settle_seconds: int) -> Dict[str, List[str]]:
    media_urls: List[str] = []
    subtitle_urls: List[str] = []
    seen: Set[str] = set()

    def add_url(url: str) -> None:
        if url in seen:
            return
        seen.add(url)
        if is_media_url(url):
            media_urls.append(url)
        elif is_subtitle_url(url):
            subtitle_urls.append(url)

    def on_response(response) -> None:
        url = response.url
        content_type = (response.headers or {}).get("content-type", "")

        if is_media_url(url) or MEDIA_HOST_FRAGMENT in url or "video/" in content_type:
            add_url(url)
            return

        if is_subtitle_url(url):
            add_url(url)
            return

        if "json" in content_type or url.endswith("/view") or "/view?" in url:
            try:
                payload = response.json()
            except Exception:
                return
            for candidate in extract_urls_from_json(payload):
                add_url(candidate)

    page.on("response", on_response)
    kick_player(page)

    deadline = time.time() + settle_seconds
    while time.time() < deadline:
        page.wait_for_timeout(1000)
        if media_urls:
            break

    for candidate in scrape_page_urls(page):
        add_url(candidate)

    return {
        "media_urls": media_urls,
        "subtitle_urls": subtitle_urls,
    }


def download_replay(helper_script: Path, replay_url: str, output_dir: Path, base_name: str) -> None:
    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(helper_script),
        "-ReplayUrl",
        replay_url,
        "-OutputDir",
        str(output_dir),
        "-OutputBaseName",
        base_name,
    ]
    subprocess.run(command, check=True)


def save_manifest(manifest_path: Path, records: List[Dict[str, Any]]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch-export authorized Yuketang replay URLs by reusing a local logged-in Chrome session."
    )
    parser.add_argument("--course-url", required=True, help="The Yuketang course main page URL.")
    parser.add_argument(
        "--output-dir",
        default="downloads",
        help="Directory for downloaded replay files.",
    )
    parser.add_argument(
        "--manifest-path",
        default="downloads/replays.json",
        help="JSON manifest path for captured lesson metadata.",
    )
    parser.add_argument(
        "--profile-dir",
        default=".playwright-yuketang-profile",
        help="Persistent Chrome profile directory for manual login reuse.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Optional maximum number of lessons to process.")
    parser.add_argument(
        "--settle-seconds",
        type=int,
        default=12,
        help="Seconds to wait on each replay page for media requests to appear.",
    )
    parser.add_argument(
        "--login-timeout-seconds",
        type=int,
        default=300,
        help="How long to wait for manual login on first run.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Collect replay URLs without downloading media files.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome headlessly. Do not use this for the first login.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    manifest_path = Path(args.manifest_path).resolve()
    helper_script = (Path(__file__).resolve().parent / "download_yuketang_replay.ps1").resolve()
    course_meta = parse_course_metadata(args.course_url)
    if not helper_script.exists():
        raise RuntimeError(f"Missing helper downloader script: {helper_script}")

    records: List[Dict[str, Any]] = []

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(Path(args.profile_dir).resolve()),
            channel="chrome",
            headless=args.headless,
            no_viewport=True,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(10000)

        try:
            print("Opening course page. Sign in manually if Chrome prompts for login.")
            wait_for_course_api_auth(
                page,
                context.request,
                args.course_url,
                course_meta["classroom_id"],
                args.login_timeout_seconds,
            )
            page.wait_for_timeout(2000)
            lessons = collect_lessons_from_api(context.request, course_meta["classroom_id"])
            if args.limit > 0:
                lessons = lessons[: args.limit]

            print(f"Found {len(lessons)} lesson candidates.")
            save_manifest(manifest_path, records)

            base_name_counts: Dict[str, int] = {}

            for index, lesson in enumerate(lessons, start=1):
                title = lesson["title"]
                base_name, occurrence = unique_base_name(slugify(title), base_name_counts)
                video_path = output_dir / f"{base_name}.mp4"

                record: Dict[str, Any] = {
                    "title": title,
                    "status": "pending",
                    "lesson_id": lesson["lesson_id"],
                    "activity_id": lesson["activity_id"],
                    "report_url": (
                        f"https://pro.yuketang.cn/v2/web/student-lesson-report/"
                        f"{course_meta['classroom_id']}/{lesson['lesson_id']}/{lesson['activity_id']}"
                    ),
                    "media_urls": [],
                    "subtitle_urls": [],
                    "file_path": str(video_path),
                    "file_paths": [str(video_path)],
                    "media_downloads": [],
                }
                if occurrence > 1:
                    record["duplicate_occurrence"] = occurrence

                print(f"[{index}/{len(lessons)}] Processing {title}")
                try:
                    replay_data = fetch_replay_data(context.request, lesson["lesson_id"])
                    capture = extract_media_entries(replay_data)
                    record["media_urls"] = capture["media_urls"]
                    record["subtitle_urls"] = capture["subtitle_urls"]
                    record["replay_source"] = replay_data.get("replaySource")

                    if not capture["media_urls"]:
                        record["status"] = "no_media_found"
                    else:
                        file_paths: List[str] = []
                        media_downloads: List[Dict[str, Any]] = []

                        for media_index, media_url in enumerate(capture["media_urls"], start=1):
                            part_base_name = media_part_base_name(base_name, media_index)
                            part_video_path = output_dir / f"{part_base_name}.mp4"
                            part_record: Dict[str, Any] = {
                                "index": media_index,
                                "url": media_url,
                                "file_path": str(part_video_path),
                            }
                            file_paths.append(str(part_video_path))

                            if args.skip_download:
                                part_record["status"] = "captured_only"
                            elif part_video_path.exists():
                                part_record["status"] = "already_downloaded"
                            else:
                                download_replay(
                                    helper_script,
                                    media_url,
                                    output_dir,
                                    part_base_name,
                                )
                                part_record["status"] = "downloaded"

                            media_downloads.append(part_record)

                        record["file_path"] = file_paths[0]
                        record["file_paths"] = file_paths
                        record["media_downloads"] = media_downloads

                        part_statuses = {part["status"] for part in media_downloads}
                        if args.skip_download:
                            record["status"] = "captured_only"
                        elif part_statuses == {"already_downloaded"}:
                            record["status"] = "already_downloaded"
                        else:
                            record["status"] = "downloaded"

                except PlaywrightTimeoutError as exc:
                    record["status"] = "timeout"
                    record["error"] = str(exc)
                except Exception as exc:
                    record["status"] = "error"
                    record["error"] = str(exc)

                records.append(record)
                save_manifest(manifest_path, records)

        finally:
            context.close()

    print(f"Manifest written to {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
