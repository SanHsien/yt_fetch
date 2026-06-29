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


def test_archive_contains(tmp_path, monkeypatch):
    import yt_fetch

    archive = tmp_path / ".download_archive.txt"
    archive.write_text("youtube aaaaaaaaaaa\nyoutube bbbbbbbbbbb\n", encoding="utf-8")
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", archive)

    assert yt_fetch.archive_contains("aaaaaaaaaaa")
    assert not yt_fetch.archive_contains("zzzzzzzzzzz")


def test_archive_contains_missing_file(tmp_path, monkeypatch):
    import yt_fetch

    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", tmp_path / "nope.txt")
    assert not yt_fetch.archive_contains("aaaaaaaaaaa")


# --- find_downloaded_file ---


def test_find_downloaded_file_prefers_tracked(tmp_path, monkeypatch):
    import yt_fetch

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", tmp_path)
    tracked = tmp_path / "Tracked [abcdefghijk].mp4"
    tracked.write_text("", encoding="utf-8")

    found = yt_fetch.find_downloaded_file("abcdefghijk", str(tracked))
    assert found == tracked


def test_find_downloaded_file_glob_fallback(tmp_path, monkeypatch):
    import yt_fetch

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", tmp_path)
    f = tmp_path / "My Video [abcdefghijk].mp4"
    f.write_text("", encoding="utf-8")

    # tracked 為 None 時退回用檔名 glob
    found = yt_fetch.find_downloaded_file("abcdefghijk", None)
    assert found == f


def test_find_downloaded_file_none_when_absent(tmp_path, monkeypatch):
    import yt_fetch

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", tmp_path)
    assert yt_fetch.find_downloaded_file("abcdefghijk", None) is None


# --- build_channel_urls ---


def test_build_channel_urls_videos_only_by_default():
    from yt_fetch import build_channel_urls

    urls = build_channel_urls("https://www.youtube.com/@x", include_shorts=False)
    assert urls == ["https://www.youtube.com/@x/videos"]


def test_build_channel_urls_includes_shorts():
    from yt_fetch import build_channel_urls

    urls = build_channel_urls("https://www.youtube.com/@x", include_shorts=True)
    assert urls == [
        "https://www.youtube.com/@x/videos",
        "https://www.youtube.com/@x/shorts",
    ]


def test_build_channel_urls_passthrough_specific_page():
    from yt_fetch import build_channel_urls

    url = "https://www.youtube.com/@x/videos"
    assert build_channel_urls(url, include_shorts=True) == [url]
    playlist = "https://www.youtube.com/playlist?list=PL123"
    assert build_channel_urls(playlist, include_shorts=False) == [playlist]


def test_build_channel_urls_no_legacy_params():
    """不應再附加已失效的 view=0&sort=dd 參數"""
    from yt_fetch import build_channel_urls

    for url in build_channel_urls("https://www.youtube.com/@x", include_shorts=True):
        assert "view=0" not in url and "sort=dd" not in url


# --- filter_downloadable_entries ---


def test_filter_downloadable_entries_excludes_live_nonpublic_downloaded():
    from yt_fetch import filter_downloadable_entries

    entries = [
        {"id": "aaaaaaaaaaa", "title": "ok", "availability": "public"},
        {"id": "bbbbbbbbbbb", "title": "live", "live_status": "is_live"},
        {"id": "ccccccccccc", "title": "priv", "availability": "private"},
        {"id": "ddddddddddd", "title": "dup", "availability": "public"},
        {"title": "no id"},
    ]
    result = filter_downloadable_entries(entries, downloaded_ids={"ddddddddddd"})

    ids = [e["id"] for e in result["entries"]]
    assert ids == ["aaaaaaaaaaa"]
    assert result["skipped_live"] == 1
    assert result["skipped_public"] == 1
