"""依賴新鮮度檢查工具的純邏輯測試。"""

from pathlib import Path

from tools import check_dependency_freshness


def test_collect_status_marks_outdated(monkeypatch):
    monkeypatch.setattr(
        check_dependency_freshness,
        "declared_minimum_version",
        lambda name: "2026.3.17",
    )
    monkeypatch.setattr(check_dependency_freshness, "fetch_pypi_version", lambda name: "2026.6.9")

    rows = check_dependency_freshness.collect_status(["yt-dlp"])

    assert rows == [
        {
            "name": "yt-dlp",
            "current": "2026.3.17",
            "latest": "2026.6.9",
            "outdated": True,
            "check_failed": False,
        }
    ]


def test_declared_minimum_version_reads_project_dependency(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
dependencies = [
    "yt-dlp>=2026.7.4",
    "imageio-ffmpeg>=0.6.0",
]
""",
        encoding="utf-8",
    )

    assert check_dependency_freshness.declared_minimum_version("YT_DLP", pyproject) == "2026.7.4"


def test_collect_status_marks_lookup_failure_for_attention(monkeypatch):
    monkeypatch.setattr(
        check_dependency_freshness,
        "declared_minimum_version",
        lambda name: "2026.7.4",
    )
    monkeypatch.setattr(check_dependency_freshness, "fetch_pypi_version", lambda name: None)

    rows = check_dependency_freshness.collect_status(["yt-dlp"])

    assert rows[0]["outdated"] is False
    assert rows[0]["check_failed"] is True
    assert "檢查失敗" in check_dependency_freshness.render_markdown(rows)


def test_write_github_output_marks_failed_check_as_needing_attention(tmp_path, monkeypatch):
    output_path = tmp_path / "github-output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))

    check_dependency_freshness.write_github_output(
        outdated=False,
        check_failed=True,
        report_path=Path("dependency-freshness-report.md"),
    )

    output = output_path.read_text(encoding="utf-8")
    assert "outdated=false" in output
    assert "check_failed=true" in output
    assert "needs_attention=true" in output


def test_render_markdown_includes_rebuild_hint():
    rows = [
        {
            "name": "yt-dlp",
            "current": "2026.3.17",
            "latest": "2026.6.9",
            "outdated": True,
            "check_failed": False,
        }
    ]

    report = check_dependency_freshness.render_markdown(rows)

    assert "yt-dlp" in report
    assert "需要維護" in report
    assert "重新打包 EXE" in report
    assert "## 處理流程" in report
    assert "每次自動或人工合併後重新執行本檢查" in report
