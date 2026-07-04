import pytest


@pytest.fixture(autouse=True)
def _isolate_config(tmp_path, monkeypatch):
    """讓每個測試使用獨立的設定檔路徑，避免讀寫到 repo 根目錄的 yt_fetch.ini。"""
    import yt_fetch

    monkeypatch.setattr(yt_fetch, "CONFIG_FILE", tmp_path / "yt_fetch.ini")
