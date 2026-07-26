"""版本庫輸出隔離規則的整合測試。"""

import shutil
import subprocess

import pytest


@pytest.mark.parametrize(
    "path",
    [
        "download/Test Channel/video.mp4",
        "download/Test Channel/subtitles.zh-Hant.vtt",
        "download/Test Channel/report.json",
    ],
)
def test_download_outputs_are_ignored_at_any_depth(path):
    if not shutil.which("git"):
        pytest.skip("需要 git 才能驗證 .gitignore")

    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", "--", path],
        check=False,
    )

    assert result.returncode == 0, f"下載產物未被 .gitignore 排除：{path}"
