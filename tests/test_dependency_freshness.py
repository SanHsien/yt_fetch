"""依賴新鮮度檢查工具的純邏輯測試。"""

from tools import check_dependency_freshness


def test_collect_status_marks_outdated(monkeypatch):
    monkeypatch.setattr(check_dependency_freshness, "installed_version", lambda name: "2026.3.17")
    monkeypatch.setattr(check_dependency_freshness, "fetch_pypi_version", lambda name: "2026.6.9")

    rows = check_dependency_freshness.collect_status(["yt-dlp"])

    assert rows == [
        {
            "name": "yt-dlp",
            "current": "2026.3.17",
            "latest": "2026.6.9",
            "outdated": True,
        }
    ]


def test_render_markdown_includes_rebuild_hint():
    rows = [
        {
            "name": "yt-dlp",
            "current": "2026.3.17",
            "latest": "2026.6.9",
            "outdated": True,
        }
    ]

    report = check_dependency_freshness.render_markdown(rows)

    assert "yt-dlp" in report
    assert "需要維護" in report
    assert "重新打包 EXE" in report
