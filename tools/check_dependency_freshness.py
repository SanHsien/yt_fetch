#!/usr/bin/env python3
"""檢查容易影響 EXE 可用性的依賴是否落後。

此工具供 GitHub Actions 排程與本地維護使用；它只檢查版本並輸出報告，
不會自行升級套件或建立 Release。
"""

import argparse
import json
import os
import sys
import urllib.request
from importlib import metadata
from pathlib import Path
from typing import Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yt_fetch  # noqa: E402

TRACKED_PACKAGES = ("yt-dlp", "imageio-ffmpeg")


def fetch_pypi_version(package_name: str, timeout: float = 10.0) -> Optional[str]:
    """回傳 PyPI 最新版本；查不到時回傳 None。"""
    req = urllib.request.Request(
        f"https://pypi.org/pypi/{package_name}/json",
        headers={"Accept": "application/json", "User-Agent": "yt_fetch-dependency-check"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - 固定 https
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("info", {}).get("version")
    except Exception:
        return None


def installed_version(package_name: str) -> Optional[str]:
    """回傳目前環境安裝版本；未安裝時回傳 None。"""
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return None


def collect_status(packages: Iterable[str]) -> List[Dict[str, object]]:
    """收集每個套件的目前版本、最新版本與是否落後。"""
    rows = []
    for package_name in packages:
        current = installed_version(package_name)
        latest = fetch_pypi_version(package_name)
        outdated = bool(current and latest and yt_fetch.is_newer_version(latest, current))
        rows.append(
            {
                "name": package_name,
                "current": current or "not installed",
                "latest": latest or "unknown",
                "outdated": outdated,
            }
        )
    return rows


def render_markdown(rows: List[Dict[str, object]]) -> str:
    """輸出 GitHub issue / log 可讀的 Markdown。"""
    lines = [
        "# yt_fetch 依賴新鮮度檢查",
        "",
        "| 套件 | 目前版本 | PyPI 最新 | 狀態 |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        status = "需要維護" if row["outdated"] else "OK"
        lines.append(f"| `{row['name']}` | `{row['current']}` | `{row['latest']}` | {status} |")
    lines.extend(
        [
            "",
            "若 `yt-dlp` 落後，Windows EXE 可能因 YouTube 改版而下載失敗。",
            "建議確認測試後切新版 tag，讓 release workflow 重新打包 EXE。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_github_output(outdated: bool, report_path: Path) -> None:
    """寫入 GitHub Actions output。"""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(f"outdated={'true' if outdated else 'false'}\n")
        f.write(f"report_path={report_path.as_posix()}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="檢查 yt_fetch 依賴是否落後")
    parser.add_argument(
        "--output",
        default="dependency-freshness-report.md",
        help="Markdown 報告輸出路徑",
    )
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="同時寫入 GitHub Actions output",
    )
    args = parser.parse_args()

    rows = collect_status(TRACKED_PACKAGES)
    report = render_markdown(rows)
    output_path = Path(args.output)
    output_path.write_text(report, encoding="utf-8")
    print(report)

    outdated = any(bool(row["outdated"]) for row in rows)
    if args.github_output:
        write_github_output(outdated, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
