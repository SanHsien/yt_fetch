import importlib


def test_import_module():
    """模組可被匯入（基本 smoke test）"""
    module = importlib.import_module("yt_fetch")
    assert hasattr(module, "main")


# --- normalize_channel_url ---


def test_normalize_channel_url_handle():
    """@handle 會被正規化為 /videos 頁面"""
    from yt_fetch import normalize_channel_url

    url = normalize_channel_url("@example_channel")
    assert url == "https://www.youtube.com/@example_channel/videos"


def test_normalize_channel_url_full_url_passthrough():
    """完整 URL 原樣保留"""
    from yt_fetch import normalize_channel_url

    full = "https://www.youtube.com/@example/videos"
    assert normalize_channel_url(full) == full


def test_normalize_channel_url_channel_id():
    """24 碼 UC 開頭頻道 ID 轉為 /channel/<id>/videos"""
    from yt_fetch import normalize_channel_url

    channel_id = "UC" + "x" * 22  # 共 24 碼
    url = normalize_channel_url(channel_id)
    assert url == f"https://www.youtube.com/channel/{channel_id}/videos"


def test_normalize_channel_url_bare_name_treated_as_handle():
    """裸名稱當作 handle 處理"""
    from yt_fetch import normalize_channel_url

    url = normalize_channel_url("example")
    assert url == "https://www.youtube.com/@example/videos"


def test_normalize_channel_url_strips_whitespace():
    """前後空白會被去除"""
    from yt_fetch import normalize_channel_url

    url = normalize_channel_url("  @example  ")
    assert url == "https://www.youtube.com/@example/videos"


# --- is_public_video ---


def test_is_public_video_accepts_public():
    from yt_fetch import is_public_video

    assert is_public_video({"id": "abc12345678", "title": "t", "availability": "public"})


def test_is_public_video_rejects_non_public():
    from yt_fetch import is_public_video

    assert not is_public_video(
        {"id": "abc12345678", "title": "t", "availability": "subscriber_only"}
    )


def test_is_public_video_rejects_empty_and_missing_title():
    from yt_fetch import is_public_video

    assert not is_public_video({})
    assert not is_public_video(None)
    assert not is_public_video({"id": "abc12345678"})  # 無標題


def test_is_public_video_accepts_when_availability_absent():
    """沒有 availability 但資訊完整時，視為公開"""
    from yt_fetch import is_public_video

    assert is_public_video({"id": "abc12345678", "title": "t"})


# --- filter_reason (Shorts / 公開判斷) ---


def test_filter_reason_accepts_normal_video():
    from yt_fetch import filter_reason

    info = {"id": "abc", "title": "normal", "duration": 600}
    assert filter_reason(info, include_shorts=False) is None


def test_filter_reason_rejects_shorts_by_url():
    from yt_fetch import filter_reason

    info = {"id": "abc", "webpage_url": "https://www.youtube.com/shorts/abc"}
    assert filter_reason(info, include_shorts=False) is not None


def test_filter_reason_short_video_not_marked_is_accepted():
    """時長 < 60 秒但未標記 shorts 的正常短片不應被誤殺"""
    from yt_fetch import filter_reason

    info = {"id": "abc", "title": "quick tip", "duration": 45}
    assert filter_reason(info, include_shorts=False) is None


def test_filter_reason_short_video_marked_shorts_is_rejected():
    from yt_fetch import filter_reason

    info = {"id": "abc", "title": "my #shorts clip", "duration": 30}
    assert filter_reason(info, include_shorts=False) is not None


def test_filter_reason_include_shorts_allows_shorts_url():
    from yt_fetch import filter_reason

    info = {"id": "abc", "webpage_url": "https://www.youtube.com/shorts/abc"}
    assert filter_reason(info, include_shorts=True) is None


def test_filter_reason_rejects_non_public():
    from yt_fetch import filter_reason

    info = {"id": "abc", "availability": "premium_only"}
    assert filter_reason(info, include_shorts=True) == "非公開影片"


# --- get_downloaded_ids ---


def test_get_downloaded_ids_from_archive_and_filenames(tmp_path, monkeypatch):
    import yt_fetch

    download_dir = tmp_path / "download"
    download_dir.mkdir()
    archive = download_dir / ".download_archive.txt"
    archive.write_text("youtube aaaaaaaaaaa\n# comment\nyoutube bbbbbbbbbbb\n", encoding="utf-8")

    # 一個檔名帶 11 碼 video id
    (download_dir / "Some Title [ccccccccccc].mp4").write_text("", encoding="utf-8")

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", download_dir)
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", archive)

    ids = yt_fetch.get_downloaded_ids()
    assert {"aaaaaaaaaaa", "bbbbbbbbbbb", "ccccccccccc"} <= ids
