import importlib


def test_import_module():
    """模組可被匯入（基本 smoke test）"""
    module = importlib.import_module("yt_fetch")
    assert hasattr(module, "main")


def test_normalize_channel_url_handle():
    """@handle 會被正規化為 /videos 頁面"""
    from yt_fetch import normalize_channel_url

    url = normalize_channel_url("@example_channel")
    assert url == "https://www.youtube.com/@example_channel/videos"

