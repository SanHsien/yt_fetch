#!/usr/bin/env python3
"""依依賴類型、版本幅度與變更範圍判斷 Dependabot PR 是否可自動合併。"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, Iterable

AUTO_MERGE_LABEL = "dependencies-auto-merge"
MANUAL_REVIEW_LABEL = "dependencies-manual-review"
SEMVER_UPDATE_TYPES = {
    "version-update:semver-patch",
    "version-update:semver-minor",
    "version-update:semver-major",
}
SAFE_GITHUB_ACTION_UPDATE_TYPES = SEMVER_UPDATE_TYPES - {"version-update:semver-major"}
PIP_MANIFESTS = {"pyproject.toml", "requirements.txt"}
CI_EXERCISED_DEV_PACKAGES = {
    "black",
    "flake8",
    "isort",
    "pre-commit",
    "pytest",
    "vermin",
}
CI_EXERCISED_BUILD_PACKAGES = {"setuptools", "wheel"}


def _manual(reason: str) -> Dict[str, str]:
    return {
        "decision": "manual",
        "label": MANUAL_REVIEW_LABEL,
        "reason": reason,
    }


def classify_update(
    ecosystem: str,
    dependency_type: str,
    update_type: str,
    changed_files: Iterable[str],
    dependency_names: Iterable[str],
) -> Dict[str, str]:
    """回傳 ``auto_merge`` 或 ``manual``，預設一律人工審查。"""
    files = {Path(path).as_posix() for path in changed_files if path}
    if not files:
        return _manual("沒有可驗證的變更檔案，保留人工審查。")

    if update_type not in SEMVER_UPDATE_TYPES:
        return _manual("無法確認版本更新幅度，保留人工審查。")

    if ecosystem == "pip":
        if not files.issubset(PIP_MANIFESTS):
            return _manual("Python 依賴 PR 超出允許的 manifest 檔案範圍。")
        names = {re.sub(r"[-_.]+", "-", name).lower() for name in dependency_names if name}
        if not names:
            return _manual("沒有可驗證的依賴名稱，保留人工審查。")

        if dependency_type == "direct:production":
            if names.issubset(CI_EXERCISED_BUILD_PACKAGES):
                return {
                    "decision": "auto_merge",
                    "label": AUTO_MERGE_LABEL,
                    "reason": (
                        "建置依賴由必要 CI 的乾淨安裝與 wheel build 直接驗證，"
                        "且變更只限依賴 manifest。"
                    ),
                }
            return _manual("執行期依賴會影響下載或已發布 EXE，保留人工與實機審查。")
        if dependency_type != "direct:development":
            return _manual("不是可自動處理的直接開發依賴。")
        if not names.issubset(CI_EXERCISED_DEV_PACKAGES):
            return _manual("包含未被必要 CI 直接驗證的開發／發布工具。")
        return {
            "decision": "auto_merge",
            "label": AUTO_MERGE_LABEL,
            "reason": (
                "開發工具由必要 CI 直接執行，即使是 major 更新也須先通過完整測試，"
                "且變更只限依賴 manifest。"
            ),
        }

    if ecosystem == "github-actions":
        if update_type not in SAFE_GITHUB_ACTION_UPDATE_TYPES:
            return _manual("GitHub Actions major 更新可能改變未在 PR 中執行的發布行為。")
        workflow_only = all(
            path.startswith(".github/workflows/") and Path(path).suffix.lower() in {".yml", ".yaml"}
            for path in files
        )
        if not workflow_only:
            return _manual("GitHub Actions PR 超出 workflow 檔案範圍。")
        return {
            "decision": "auto_merge",
            "label": AUTO_MERGE_LABEL,
            "reason": "GitHub Actions 的 patch 或 minor 更新，且只修改 workflow。",
        }

    return _manual("未列入自動核准政策的套件生態系。")


def write_github_output(result: Dict[str, str]) -> None:
    """把判斷結果寫入 GitHub Actions output。"""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as output:
        for key in ("decision", "label", "reason"):
            output.write(f"{key}={result[key]}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="判斷 Dependabot PR 是否可自動核准與合併")
    parser.add_argument("--ecosystem", required=True)
    parser.add_argument("--dependency-type", required=True)
    parser.add_argument("--update-type", required=True)
    parser.add_argument("--dependency-names", required=True)
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--github-output", action="store_true")
    args = parser.parse_args()

    result = classify_update(
        ecosystem=args.ecosystem,
        dependency_type=args.dependency_type,
        update_type=args.update_type,
        changed_files=args.changed_file,
        dependency_names=[name.strip() for name in args.dependency_names.split(",")],
    )
    print(json.dumps(result, ensure_ascii=False))
    if args.github_output:
        write_github_output(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
