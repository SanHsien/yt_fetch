import importlib
import sys
import types

import pytest


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


def test_normalize_channel_url_videos_shorts_playlist_passthrough():
    """已是 /videos、/shorts、playlist 的完整 URL 原樣保留"""
    from yt_fetch import normalize_channel_url

    for url in (
        "https://www.youtube.com/@x/videos",
        "https://www.youtube.com/@x/shorts",
        "https://www.youtube.com/playlist?list=PL123",
    ):
        assert normalize_channel_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://youtube.com/@example/videos",
        "https://m.youtube.com/@example/videos",
        "https://music.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx",
        "https://youtu.be/abcdefghijk",
    ],
)
def test_normalize_channel_url_accepts_https_youtube_hosts(url):
    from yt_fetch import normalize_channel_url

    assert normalize_channel_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://www.youtube.com/@example/videos",
        "https://example.com/channel/demo",
        "https://youtube.com.example/@demo",
        "https://user:pass@youtube.com/@demo",
        "https://youtube.com:8443/@demo",
    ],
)
def test_normalize_channel_url_rejects_untrusted_urls(url):
    from yt_fetch import normalize_channel_url

    with pytest.raises(ValueError, match="YouTube"):
        normalize_channel_url(url)


def test_parse_cookies_from_browser_spec():
    from yt_fetch import parse_cookies_from_browser_spec

    assert parse_cookies_from_browser_spec("chrome") == ("chrome", None, None, None)
    assert parse_cookies_from_browser_spec("chrome:Default") == ("chrome", "Default", None, None)
    assert parse_cookies_from_browser_spec("chrome:Profile 1") == (
        "chrome",
        "Profile 1",
        None,
        None,
    )
    assert parse_cookies_from_browser_spec("firefox:default::Personal") == (
        "firefox",
        "default",
        None,
        "Personal",
    )
    assert parse_cookies_from_browser_spec("chrome+basictext:Default") == (
        "chrome",
        "Default",
        "BASICTEXT",
        None,
    )


def test_build_format_selector():
    from yt_fetch import build_format_selector

    assert build_format_selector("best").startswith("bestvideo[ext=mp4]+bestaudio")
    assert "height<=1080" in build_format_selector("1080p")
    assert "height<=720" in build_format_selector("720p")
    assert "height<=480" in build_format_selector("480p")


def test_build_format_selector_rejects_unknown_quality():
    import pytest

    from yt_fetch import build_format_selector

    with pytest.raises(ValueError):
        build_format_selector("144p")


# --- 版本與更新檢查 ---


def test_parse_version():
    from yt_fetch import parse_version

    assert parse_version("v1.2.0") == (1, 2, 0)
    assert parse_version("1.2") == (1, 2)
    assert parse_version("v2.0.1") == (2, 0, 1)
    assert parse_version("") == (0,)


def test_is_newer_version():
    from yt_fetch import is_newer_version

    assert is_newer_version("v1.3.0", "1.2.0")
    assert is_newer_version("1.2.1", "1.2.0")
    assert not is_newer_version("1.2.0", "1.2.0")
    assert not is_newer_version("v1.1.0", "1.2.0")


def test_build_ytdlp_update_message():
    from yt_fetch import build_ytdlp_update_message

    assert "已是 PyPI 最新" in build_ytdlp_update_message("2026.6.9", "2026.6.9")
    assert "建議更新" in build_ytdlp_update_message("2026.6.9", "2026.3.17")
    assert "無法檢查最新版本" in build_ytdlp_update_message(None, "2026.6.9")


def test_classify_error_message():
    from yt_fetch import classify_error_message

    assert classify_error_message("failed to load cookies") == "cookies"
    assert classify_error_message("HTTP Error 429: too many requests") == "rate"
    assert classify_error_message("Postprocessor failed: ffmpeg missing") == "ffmpeg"
    assert classify_error_message("Permission denied") == "disk"
    assert classify_error_message("unexpected problem") == "generic"


def test_build_error_diagnosis_message_uses_shared_table():
    from yt_fetch import build_error_diagnosis_message

    assert "cookies" in build_error_diagnosis_message("failed to load cookies", "en").lower()
    assert "磁碟" in build_error_diagnosis_message("Permission denied", "zh")
    assert "建議" in build_error_diagnosis_message("anything else", "unknown")


# --- 批次下載（--channels-file）---


def test_read_channels_file(tmp_path):
    from yt_fetch import read_channels_file

    f = tmp_path / "channels.txt"
    f.write_text(
        "# 註解行\n"
        "@chan1\n"
        "  \n"  # 空白行略過
        "https://www.youtube.com/@chan2/videos\n"
        "# 又一個註解\n"
        "UCxxxxxxxxxxxxxxxxxxxxxx\n",
        encoding="utf-8",
    )
    channels = read_channels_file(str(f))
    assert channels == [
        "@chan1",
        "https://www.youtube.com/@chan2/videos",
        "UCxxxxxxxxxxxxxxxxxxxxxx",
    ]


def test_read_channels_file_missing(tmp_path):
    import pytest

    from yt_fetch import read_channels_file

    with pytest.raises(FileNotFoundError):
        read_channels_file(str(tmp_path / "nope.txt"))


def test_run_batch_download_continues_on_failure(monkeypatch):
    """單一頻道失敗（含 sys.exit）不應中斷整批，且回傳每頻道結果"""
    import types

    import yt_fetch

    def fake_download(channel_url, *a, **k):
        if "boom" in channel_url:
            raise RuntimeError("壞掉了")
        if "exit" in channel_url:
            raise SystemExit(1)
        return [{"title": "t", "id": "x", "path": "p", "duration": 0}]

    monkeypatch.setattr(yt_fetch, "download_videos", fake_download)
    monkeypatch.setattr(yt_fetch, "normalize_channel_url", lambda c: c)

    args = types.SimpleNamespace(
        count=5,
        include_shorts=False,
        quality="best",
        retries=3,
        cookies_from_browser="",
        cookies="",
        ratelimit=0,
        sleep=0,
    )
    results = yt_fetch.run_batch_download(["ok-chan", "boom-chan", "exit-chan"], args)

    assert [r["status"] for r in results] == ["ok", "fail", "fail"]
    assert results[0]["downloaded"] == 1
    assert sum(r["downloaded"] for r in results) == 1


def test_run_batch_download_passes_progress_callback(monkeypatch):
    """批次下載也應把 GUI/呼叫端提供的 progress callback 傳到 download_videos。"""
    import types

    import yt_fetch

    callbacks = []

    def fake_download(channel_url, *args):
        callbacks.append(args[8])
        return []

    monkeypatch.setattr(yt_fetch, "download_videos", fake_download)
    monkeypatch.setattr(yt_fetch, "normalize_channel_url", lambda c: c)

    args = types.SimpleNamespace(
        count=5,
        include_shorts=False,
        quality="best",
        retries=3,
        cookies_from_browser="",
        cookies="managed.txt",
        ratelimit=0,
        sleep=0,
    )
    callback = object()
    yt_fetch.run_batch_download(["@a", "@b"], args, progress_callback=callback)

    assert callbacks == [callback, callback]


# --- --help 乾淨輸出 ---


def test_help_is_clean_and_creates_no_config(capsys, monkeypatch, tmp_path):
    """--help 應乾淨退出（碼 0），不夾帶啟動 banner，也不建立設定檔"""
    import pytest

    import yt_fetch

    cfg = tmp_path / "yt_fetch.ini"
    monkeypatch.setattr(yt_fetch, "CONFIG_FILE", cfg)
    monkeypatch.setattr("sys.argv", ["yt_fetch.py", "--help"])

    with pytest.raises(SystemExit) as exc:
        yt_fetch.parse_args()
    assert exc.value.code == 0

    out = capsys.readouterr().out
    assert "YouTube 頻道影片下載工具" not in out  # 啟動 banner 不應出現在 --help
    assert not cfg.exists()  # --help 不建立設定檔


# --- is_public_video ---


def test_is_public_video_accepts_public():
    from yt_fetch import is_public_video

    assert is_public_video({"id": "abc12345678", "title": "t", "availability": "public"})


def test_is_public_video_rejects_non_public():
    from yt_fetch import is_public_video

    assert not is_public_video(
        {"id": "abc12345678", "title": "t", "availability": "subscriber_only"}
    )


@pytest.mark.parametrize("availability", ["subscriber_only", "premium_only", "needs_auth"])
def test_is_public_video_accepts_entitled_content_only_with_cookies(availability):
    from yt_fetch import is_public_video

    entry = {"id": "abc12345678", "title": "t", "availability": availability}

    assert not is_public_video(entry)
    assert is_public_video(entry, allow_entitled=True)


def test_is_public_video_rejects_private_even_with_cookies():
    from yt_fetch import is_public_video

    entry = {"id": "abc12345678", "title": "t", "availability": "private"}

    assert not is_public_video(entry, allow_entitled=True)


def test_is_public_video_rejects_empty_and_missing_title():
    from yt_fetch import is_public_video

    assert not is_public_video({})
    assert not is_public_video(None)
    assert not is_public_video({"id": "abc12345678"})  # 無標題


def test_is_public_video_accepts_when_availability_absent():
    """沒有 availability 但資訊完整時，視為公開"""
    from yt_fetch import is_public_video

    assert is_public_video({"id": "abc12345678", "title": "t"})


# --- env_int / env_float ---


def test_env_int_valid_missing_and_invalid(monkeypatch):
    from yt_fetch import env_int

    monkeypatch.setenv("YT_TEST_INT", "10")
    assert env_int("YT_TEST_INT", 5) == 10

    monkeypatch.delenv("YT_TEST_INT", raising=False)
    assert env_int("YT_TEST_INT", 5) == 5  # 缺漏 → 預設

    monkeypatch.setenv("YT_TEST_INT", "abc")
    assert env_int("YT_TEST_INT", 5) == 5  # 格式錯誤 → 預設，不拋例外

    monkeypatch.setenv("YT_TEST_INT", "  ")
    assert env_int("YT_TEST_INT", 7) == 7  # 空白 → 預設


def test_env_float_valid_and_invalid(monkeypatch):
    from yt_fetch import env_float

    monkeypatch.setenv("YT_TEST_FLOAT", "2.5")
    assert env_float("YT_TEST_FLOAT", 0.0) == 2.5

    monkeypatch.setenv("YT_TEST_FLOAT", "x")
    assert env_float("YT_TEST_FLOAT", 1.5) == 1.5


# --- 設定檔（INI）持久化 ---


def test_write_default_config_if_missing(tmp_path, monkeypatch):
    import yt_fetch

    cfg_path = tmp_path / "yt_fetch.ini"
    monkeypatch.setattr(yt_fetch, "CONFIG_FILE", cfg_path)

    assert not cfg_path.exists()
    yt_fetch.write_default_config_if_missing()
    assert cfg_path.exists()
    body = cfg_path.read_text(encoding="utf-8")
    assert "[yt_fetch]" in body
    # 不覆寫既有檔案
    cfg_path.write_text("[yt_fetch]\ncount = 9\n", encoding="utf-8")
    yt_fetch.write_default_config_if_missing()
    assert "count = 9" in cfg_path.read_text(encoding="utf-8")


def test_load_config_typed_and_invalid(tmp_path, monkeypatch):
    import yt_fetch

    cfg_path = tmp_path / "yt_fetch.ini"
    cfg_path.write_text(
        "[yt_fetch]\n"
        "channel = @abc\n"
        "count = 8\n"
        "retries = bad\n"  # 無效整數 → 略過
        "include_shorts = true\n"
        "ratelimit = 2.5\n"
        "download_dir = /tmp/dl\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(yt_fetch, "CONFIG_FILE", cfg_path)

    cfg = yt_fetch.load_config()
    assert cfg["channel"] == "@abc"
    assert cfg["count"] == 8
    assert "retries" not in cfg  # 無效值被略過
    assert cfg["include_shorts"] is True
    assert cfg["ratelimit"] == 2.5
    assert cfg["download_dir"] == "/tmp/dl"


def test_load_config_missing_file(tmp_path, monkeypatch):
    import yt_fetch

    monkeypatch.setattr(yt_fetch, "CONFIG_FILE", tmp_path / "nope.ini")
    assert yt_fetch.load_config() == {}


def test_save_config_excludes_cookies(tmp_path, monkeypatch):
    import yt_fetch

    cfg_path = tmp_path / "yt_fetch.ini"
    monkeypatch.setattr(yt_fetch, "CONFIG_FILE", cfg_path)

    yt_fetch.save_config(
        {
            "channel": "@x",
            "count": 7,
            "include_shorts": True,
            "cookies_file": "/secret/cookies.txt",
            "cookies_from_browser": "chrome",
        }
    )
    body = cfg_path.read_text(encoding="utf-8")
    # cookies 欄位與其值一律不寫入（標題註解提及 cookies 字樣不算）
    assert "cookies_file" not in body
    assert "cookies_from_browser" not in body
    assert "secret" not in body

    reloaded = yt_fetch.load_config()
    assert reloaded["channel"] == "@x"
    assert reloaded["count"] == 7
    assert reloaded["include_shorts"] is True


def test_config_precedence_env_over_ini(tmp_path, monkeypatch):
    """parse_args 預設值優先序：環境變數 > ini > 內建"""
    import yt_fetch

    cfg_path = tmp_path / "yt_fetch.ini"
    cfg_path.write_text("[yt_fetch]\ncount = 8\nquality = 720p\n", encoding="utf-8")
    monkeypatch.setattr(yt_fetch, "CONFIG_FILE", cfg_path)

    # 只有 ini → 用 ini 值
    monkeypatch.delenv("YOUTUBE_COUNT", raising=False)
    monkeypatch.delenv("YOUTUBE_QUALITY", raising=False)
    monkeypatch.setattr("sys.argv", ["yt_fetch.py", "--channel", "@t"])
    args = yt_fetch.parse_args()
    assert args.count == 8
    assert args.quality == "720p"

    # ini + 環境變數 → 用環境變數
    monkeypatch.setenv("YOUTUBE_COUNT", "11")
    monkeypatch.setenv("YOUTUBE_QUALITY", "1080p")
    monkeypatch.setattr("sys.argv", ["yt_fetch.py", "--channel", "@t"])
    args = yt_fetch.parse_args()
    assert args.count == 11
    assert args.quality == "1080p"

    # CLI 參數最優先
    monkeypatch.setattr(
        "sys.argv", ["yt_fetch.py", "--channel", "@t", "--count", "3", "--quality", "480p"]
    )
    args = yt_fetch.parse_args()
    assert args.count == 3
    assert args.quality == "480p"


def test_invalid_quality_in_config_falls_back_to_default(tmp_path, monkeypatch):
    import yt_fetch

    cfg_path = tmp_path / "yt_fetch.ini"
    cfg_path.write_text("[yt_fetch]\nquality = 144p\n", encoding="utf-8")
    monkeypatch.setattr(yt_fetch, "CONFIG_FILE", cfg_path)
    monkeypatch.delenv("YOUTUBE_QUALITY", raising=False)
    monkeypatch.setattr("sys.argv", ["yt_fetch.py", "--channel", "@t"])

    assert yt_fetch.parse_args().quality == "best"


def test_parse_args_advanced_filters(monkeypatch):
    import yt_fetch

    monkeypatch.setattr(
        "sys.argv",
        [
            "yt_fetch.py",
            "--channel",
            "@x",
            "--title-include",
            "Python",
            "--title-exclude",
            "Shorts",
            "--date-after",
            "20260101",
            "--date-before",
            "20261231",
            "--min-duration",
            "300",
            "--max-duration",
            "1800",
            "--write-subs",
            "--sub-langs",
            "zh-Hant,en",
        ],
    )

    args = yt_fetch.parse_args()

    assert args.title_include == "Python"
    assert args.title_exclude == "Shorts"
    assert args.date_after == "20260101"
    assert args.date_before == "20261231"
    assert args.min_duration == 300
    assert args.max_duration == 1800
    assert args.write_subs is True
    assert args.sub_langs == "zh-Hant,en"


@pytest.mark.parametrize(
    "option,value",
    [
        ("--retries", "0"),
        ("--retries", "-1"),
        ("--ratelimit", "-1"),
        ("--sleep", "-1"),
    ],
)
def test_parse_args_rejects_invalid_runtime_controls(monkeypatch, option, value):
    import yt_fetch

    monkeypatch.setattr("sys.argv", ["yt_fetch.py", "--channel", "@example", option, value])

    with pytest.raises(SystemExit) as exc:
        yt_fetch.parse_args()

    assert exc.value.code == 2


def test_set_download_dir(tmp_path, monkeypatch):
    import yt_fetch

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", tmp_path / "old")
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", tmp_path / "old" / ".download_archive.txt")
    target = tmp_path / "new_dl"
    yt_fetch.set_download_dir(target)
    assert yt_fetch.DOWNLOAD_DIR == target
    assert yt_fetch.ARCHIVE_FILE == target / ".download_archive.txt"


def test_get_ffmpeg_status_system(monkeypatch):
    import subprocess

    import yt_fetch

    monkeypatch.setattr(yt_fetch.shutil, "which", lambda name: "C:/ffmpeg/bin/ffmpeg.exe")

    def fake_run(cmd, **kwargs):
        assert cmd == ["C:/ffmpeg/bin/ffmpeg.exe", "-version"]
        return subprocess.CompletedProcess(cmd, 0, stdout=b"ffmpeg version 7.1 Copyright")

    monkeypatch.setattr(yt_fetch.subprocess, "run", fake_run)
    status = yt_fetch.get_ffmpeg_status()

    assert status["available"] is True
    assert status["source"] == "system"
    assert status["version"].startswith("ffmpeg version 7.1")


def test_install_ffmpeg_frozen_skips_pip(monkeypatch, tmp_path):
    """打包 EXE（sys.frozen）時不得以 sys.executable 執行 pip（那會誤啟第二個 GUI 視窗），
    應直接使用內嵌的 imageio-ffmpeg。"""
    import subprocess

    import yt_fetch

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append([str(part) for part in cmd])
        return subprocess.CompletedProcess(cmd, 0)

    fake_exe = tmp_path / "ffmpeg.exe"
    fake_exe.write_text("", encoding="utf-8")

    monkeypatch.setattr(yt_fetch.sys, "frozen", True, raising=False)
    monkeypatch.setattr(yt_fetch.subprocess, "run", fake_run)
    monkeypatch.setenv("PATH", "dummy")  # 隔離 PATH 副作用
    monkeypatch.setitem(
        sys.modules,
        "imageio_ffmpeg",
        types.SimpleNamespace(get_ffmpeg_exe=lambda: str(fake_exe)),
    )

    path = yt_fetch.install_ffmpeg()

    assert path == str(fake_exe)
    # 只允許 ffmpeg -version 驗證呼叫，不得出現任何 pip 呼叫
    assert calls == [[str(fake_exe), "-version"]]


def test_get_ffmpeg_status_missing(monkeypatch):
    import yt_fetch

    monkeypatch.setattr(yt_fetch.shutil, "which", lambda name: None)
    monkeypatch.setattr(yt_fetch, "_get_imageio_ffmpeg_exe", lambda: None)
    status = yt_fetch.get_ffmpeg_status()

    assert status["available"] is False
    assert status["source"] == "missing"


def test_build_ytdlp_options_contains_core_fields(tmp_path):
    import yt_fetch

    def hook(_progress):
        return None

    opts = yt_fetch.build_ytdlp_options(
        download_dir=tmp_path,
        archive_file=tmp_path / ".download_archive.txt",
        quality="720p",
        retries=2,
        include_shorts=False,
        playlist_extract_count=10,
        progress_hook=hook,
        match_filter=lambda info: None,
        ffmpeg_path="C:/ffmpeg/bin/ffmpeg.exe",
        cookies_file="cookies.txt",
        ratelimit=1.5,
    )

    assert "height<=720" in opts["format"]
    assert opts["download_archive"].endswith(".download_archive.txt")
    assert opts["progress_hooks"] == [hook]
    assert opts["match_filter"] is not None
    assert opts["ffmpeg_location"] == "C:/ffmpeg/bin/ffmpeg.exe"
    assert opts["cookiefile"] == "cookies.txt"
    assert opts["ratelimit"] == int(1.5 * 1024 * 1024)


def test_build_ytdlp_options_enables_subtitles(tmp_path):
    import yt_fetch

    opts = yt_fetch.build_ytdlp_options(
        download_dir=tmp_path,
        archive_file=tmp_path / ".download_archive.txt",
        quality="best",
        retries=2,
        include_shorts=True,
        playlist_extract_count=10,
        progress_hook=lambda progress: None,
        match_filter=lambda info: None,
        write_subs=True,
        sub_langs="zh-Hant,en",
    )

    assert opts["writesubtitles"] is True
    assert opts["writeautomaticsub"] is True
    assert opts["subtitleslangs"] == ["zh-Hant", "en"]
    assert opts["match_filter"] is not None


def test_normalize_date_filter_and_subtitle_languages():
    import pytest

    import yt_fetch

    assert yt_fetch.normalize_date_filter("20260131", "--date-after") == "20260131"
    assert yt_fetch.parse_subtitle_languages(" zh-Hant, en ,, ") == ["zh-Hant", "en"]
    assert yt_fetch.parse_subtitle_languages("") == ["zh-Hant", "zh-Hans", "en"]
    with pytest.raises(ValueError):
        yt_fetch.normalize_date_filter("2026-01-31", "--date-after")
    with pytest.raises(ValueError):
        yt_fetch.normalize_date_filter("20260231", "--date-after")


# --- is_non_public ---


def test_is_non_public():
    from yt_fetch import is_non_public

    assert is_non_public({"availability": "subscriber_only"})
    assert is_non_public({"availability": "premium_only"})
    assert not is_non_public({"availability": "public"})
    assert not is_non_public({})  # 無 availability 欄位 → 不視為非公開


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


def test_filter_reason_allows_entitled_content_only_with_cookies():
    from yt_fetch import filter_reason

    member = {"id": "abc", "title": "member", "availability": "subscriber_only"}
    private = {"id": "def", "title": "private", "availability": "private"}

    assert filter_reason(member, include_shorts=True) == "非公開影片"
    assert filter_reason(member, include_shorts=True, allow_entitled=True) is None
    assert filter_reason(private, include_shorts=True, allow_entitled=True) == "非公開影片"


def test_advanced_filter_reason():
    from yt_fetch import advanced_filter_reason

    info = {
        "title": "Python Tutorial",
        "upload_date": "20260115",
        "duration": 600,
    }

    assert advanced_filter_reason(info, title_include="python") is None
    assert "未包含" in advanced_filter_reason(info, title_include="Rust")
    assert "排除" in advanced_filter_reason(info, title_exclude="tutorial")
    assert "早於" in advanced_filter_reason(info, date_after="20260201")
    assert "晚於" in advanced_filter_reason(info, date_before="20260101")
    assert "短於" in advanced_filter_reason(info, min_duration=900)
    assert "長於" in advanced_filter_reason(info, max_duration=300)


def test_build_match_filter_keeps_advanced_filters_when_including_shorts():
    from yt_fetch import build_match_filter

    match_filter = build_match_filter(include_shorts=True, title_include="Python")

    assert match_filter({"title": "Rust Talk", "duration": 600}) is not None
    assert match_filter({"title": "Python Talk", "duration": 600}) is None


def test_build_match_filter_defers_entitlement_to_youtube_when_cookies_exist():
    from yt_fetch import build_match_filter

    match_filter = build_match_filter(include_shorts=True, allow_entitled=True)

    assert match_filter({"id": "abc", "title": "member", "availability": "subscriber_only"}) is None
    assert (
        match_filter({"id": "def", "title": "private", "availability": "private"}) == "非公開影片"
    )


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


def test_prompt_user_input_exits_when_not_a_tty(monkeypatch):
    """非互動式終端機時，應明確退出而非卡住或拋例外"""
    import io

    import pytest

    import yt_fetch

    fake_stdin = io.StringIO("")
    monkeypatch.setattr(fake_stdin, "isatty", lambda: False, raising=False)
    monkeypatch.setattr("sys.stdin", fake_stdin)

    with pytest.raises(SystemExit) as exc:
        yt_fetch.prompt_user_input()
    assert exc.value.code == 1


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
    assert result["skipped_advanced"] == 0


def test_filter_downloadable_entries_keeps_entitled_candidates_only_with_cookies():
    from yt_fetch import filter_downloadable_entries

    entries = [
        {"id": "aaaaaaaaaaa", "title": "member", "availability": "subscriber_only"},
        {"id": "bbbbbbbbbbb", "title": "private", "availability": "private"},
    ]

    without_cookies = filter_downloadable_entries(entries, downloaded_ids=set())
    with_cookies = filter_downloadable_entries(
        entries,
        downloaded_ids=set(),
        allow_entitled=True,
    )

    assert without_cookies["entries"] == []
    assert [entry["id"] for entry in with_cookies["entries"]] == ["aaaaaaaaaaa"]


def test_filter_downloadable_entries_applies_title_filters_only_at_list_stage():
    from yt_fetch import filter_downloadable_entries

    entries = [
        {"id": "aaaaaaaaaaa", "title": "Python Guide"},
        {"id": "bbbbbbbbbbb", "title": "Rust Guide"},
    ]

    result = filter_downloadable_entries(
        entries,
        downloaded_ids=set(),
        title_include="Python",
        date_after="20260101",
        min_duration=300,
    )

    assert [e["id"] for e in result["entries"]] == ["aaaaaaaaaaa"]
    assert result["skipped_advanced"] == 1


def test_filter_reason_rejects_live_when_listing_is_flat():
    from yt_fetch import filter_reason

    info = {
        "id": "aaaaaaaaaaa",
        "title": "Live now",
        "live_status": "is_live",
    }

    assert "直播" in filter_reason(info, include_shorts=True)


def test_dedupe_entries_keeps_first_seen_id():
    from yt_fetch import dedupe_entries

    entries = [
        {"id": "aaaaaaaaaaa", "title": "first"},
        {"id": "bbbbbbbbbbb", "title": "second"},
        {"id": "aaaaaaaaaaa", "title": "duplicate"},
        {"title": "no id"},
    ]

    assert dedupe_entries(entries) == [
        {"id": "aaaaaaaaaaa", "title": "first"},
        {"id": "bbbbbbbbbbb", "title": "second"},
    ]


def test_calculate_download_target_counts_current_channel_only():
    from yt_fetch import calculate_download_target

    entries = [
        {"id": "aaaaaaaaaaa"},
        {"id": "bbbbbbbbbbb"},
        {"id": "ccccccccccc"},
    ]
    result = calculate_download_target(
        entries,
        downloaded_ids={"aaaaaaaaaaa", "external99999"},
        count=3,
    )

    assert result == {"existing_count": 1, "remaining_count": 2}


def test_prepare_entries_to_download_filters_and_counts():
    from yt_fetch import prepare_entries_to_download

    entries = [
        {"id": "aaaaaaaaaaa", "title": "ok"},
        {"id": "bbbbbbbbbbb", "title": "downloaded"},
        {"id": "ccccccccccc", "title": "live", "live_status": "is_live"},
        {"id": "aaaaaaaaaaa", "title": "dup"},
    ]

    result = prepare_entries_to_download(entries, {"bbbbbbbbbbb"}, count=3)

    assert [entry["id"] for entry in result["entries_to_download"]] == ["aaaaaaaaaaa"]
    assert result["existing_count"] == 1
    assert result["remaining_count"] == 2


def test_prepare_entries_to_download_keeps_authorized_member_candidate():
    from yt_fetch import prepare_entries_to_download

    entries = [
        {"id": "aaaaaaaaaaa", "title": "member", "availability": "subscriber_only"},
        {"id": "bbbbbbbbbbb", "title": "private", "availability": "private"},
    ]

    result = prepare_entries_to_download(
        entries,
        downloaded_ids=set(),
        count=1,
        allow_entitled=True,
    )

    assert [entry["id"] for entry in result["entries_to_download"]] == ["aaaaaaaaaaa"]


def test_calculate_playlist_extract_count_bounds():
    from yt_fetch import calculate_playlist_extract_count

    assert calculate_playlist_extract_count(1) == 50
    assert calculate_playlist_extract_count(20) == 100
    assert calculate_playlist_extract_count(100) == 200


def test_build_progress_hook_records_finished_and_ignores_callback_error():
    from yt_fetch import build_progress_hook

    downloaded_files = {}

    def bad_callback(event):
        raise RuntimeError("callback failed")

    hook = build_progress_hook(downloaded_files, bad_callback)
    hook(
        {
            "status": "finished",
            "info_dict": {"id": "abcdefghijk"},
            "filename": "C:/download/Fake [abcdefghijk].mp4",
        }
    )

    assert downloaded_files == {"abcdefghijk": "C:/download/Fake [abcdefghijk].mp4"}


def test_ensure_ffmpeg_ready_uses_existing_ffmpeg(monkeypatch):
    import yt_fetch

    monkeypatch.setattr(yt_fetch, "check_ffmpeg", lambda: True)
    monkeypatch.setattr(
        yt_fetch,
        "install_ffmpeg",
        lambda: (_ for _ in ()).throw(AssertionError("install_ffmpeg should not run")),
    )

    assert yt_fetch.ensure_ffmpeg_ready() is None


def test_handle_ytdlp_download_error_private_exits_zero():
    import pytest

    from yt_fetch import handle_ytdlp_download_error

    with pytest.raises(SystemExit) as exc:
        handle_ytdlp_download_error(RuntimeError("Private video"))

    assert exc.value.code == 0


def test_handle_ytdlp_download_error_format_exits_one():
    import pytest

    from yt_fetch import handle_ytdlp_download_error

    with pytest.raises(SystemExit) as exc:
        handle_ytdlp_download_error(RuntimeError("requested format is not available"))

    assert exc.value.code == 1


def test_download_entries_with_ytdlp_continues_after_single_failure(monkeypatch, tmp_path):
    import yt_fetch

    download_dir = tmp_path / "download"
    archive = download_dir / ".download_archive.txt"
    good_id = "bbbbbbbbbbb"
    bad_id = "aaaaaaaaaaa"

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", download_dir)
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", archive)

    class FakeYdl:
        def download(self, urls):
            if urls == [f"https://www.youtube.com/watch?v={bad_id}"]:
                raise RuntimeError("network fail")
            download_dir.mkdir(parents=True, exist_ok=True)
            (download_dir / f"Good [{good_id}].mp4").write_text("", encoding="utf-8")
            archive.write_text(f"youtube {good_id}\n", encoding="utf-8")

    downloaded = yt_fetch.download_entries_with_ytdlp(
        FakeYdl(),
        [
            {"id": bad_id, "title": "Bad", "duration": 10},
            {"id": good_id, "title": "Good", "duration": 20},
        ],
        remaining_count=1,
        total_target_count=1,
        existing_count=0,
        downloaded_files={},
        sleep_seconds=0,
    )

    assert downloaded == [
        {
            "title": "Good",
            "id": good_id,
            "path": str(download_dir / f"Good [{good_id}].mp4"),
            "duration": 20,
        }
    ]


# --- download_videos（mock yt-dlp，不連 YouTube）---


def test_download_videos_with_fake_ytdlp(monkeypatch, tmp_path):
    import yt_fetch

    download_dir = tmp_path / "download"
    archive = download_dir / ".download_archive.txt"
    video_id = "abcdefghijk"
    progress_events = []

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", download_dir)
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", archive)
    monkeypatch.setattr(yt_fetch, "check_ffmpeg", lambda: True)

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            assert download is False
            return {
                "entries": [
                    {
                        "id": video_id,
                        "title": "Fake Video",
                        "availability": "public",
                        "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
                        "duration": 120,
                    }
                ]
            }

        def download(self, urls):
            assert urls == [f"https://www.youtube.com/watch?v={video_id}"]
            download_dir.mkdir(parents=True, exist_ok=True)
            file_path = download_dir / f"Fake Video [{video_id}].mp4"
            file_path.write_text("", encoding="utf-8")
            archive.write_text(f"youtube {video_id}\n", encoding="utf-8")
            for hook in self.opts["progress_hooks"]:
                hook(
                    {
                        "status": "downloading",
                        "downloaded_bytes": 50,
                        "total_bytes": 100,
                    }
                )
                hook(
                    {
                        "status": "finished",
                        "info_dict": {"id": video_id},
                        "filename": str(file_path),
                    }
                )

    monkeypatch.setitem(sys.modules, "yt_dlp", types.SimpleNamespace(YoutubeDL=FakeYoutubeDL))

    downloaded = yt_fetch.download_videos(
        "https://www.youtube.com/@fake/videos",
        count=1,
        include_shorts=False,
        retries=1,
        progress_callback=progress_events.append,
    )

    assert downloaded == [
        {
            "title": "Fake Video",
            "id": video_id,
            "path": str(download_dir / f"Fake Video [{video_id}].mp4"),
            "duration": 120,
        }
    ]
    assert [event["status"] for event in progress_events] == ["downloading", "finished"]


def test_download_videos_passes_quality_to_ytdlp(monkeypatch, tmp_path):
    import yt_fetch

    download_dir = tmp_path / "download"
    archive = download_dir / ".download_archive.txt"
    video_id = "abcdefghijk"
    seen_opts = []

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", download_dir)
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", archive)
    monkeypatch.setattr(yt_fetch, "check_ffmpeg", lambda: True)
    download_dir.mkdir(parents=True, exist_ok=True)
    archive.write_text(f"youtube {video_id}\n", encoding="utf-8")

    class FakeYoutubeDL:
        def __init__(self, opts):
            seen_opts.append(dict(opts))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            return {
                "entries": [
                    {
                        "id": video_id,
                        "title": "Fake Video",
                        "availability": "public",
                        "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
                        "duration": 120,
                    }
                ]
            }

    monkeypatch.setitem(sys.modules, "yt_dlp", types.SimpleNamespace(YoutubeDL=FakeYoutubeDL))

    downloaded = yt_fetch.download_videos(
        "https://www.youtube.com/@fake/videos",
        count=1,
        include_shorts=False,
        retries=1,
        quality="720p",
    )

    assert downloaded == []
    assert "height<=720" in seen_opts[0]["format"]


def test_channel_listing_uses_flat_extraction(monkeypatch, tmp_path):
    """抽頻道清單應用 flat（extract_flat="in_playlist"），下載階段維持完整解析。

    回歸測試：非 flat 抽清單會逐支解析，遇會員限定影片或 YouTube 節流時整批回傳 0，
    導致「無法取得頻道資訊」。
    """
    import yt_fetch

    download_dir = tmp_path / "download"
    archive = download_dir / ".download_archive.txt"
    video_id = "abcdefghijk"
    seen_opts = []

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", download_dir)
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", archive)
    monkeypatch.setattr(yt_fetch, "check_ffmpeg", lambda: True)

    class FakeYoutubeDL:
        def __init__(self, opts):
            seen_opts.append(dict(opts))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            return {
                "entries": [
                    {
                        "id": video_id,
                        "title": "Fake Video",
                        "availability": "public",
                        "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
                        "duration": 120,
                    }
                ]
            }

        def download(self, urls):
            download_dir.mkdir(parents=True, exist_ok=True)
            (download_dir / f"Fake Video [{video_id}].mp4").write_text("", encoding="utf-8")
            archive.write_text(f"youtube {video_id}\n", encoding="utf-8")

    monkeypatch.setitem(sys.modules, "yt_dlp", types.SimpleNamespace(YoutubeDL=FakeYoutubeDL))

    yt_fetch.download_videos(
        "https://www.youtube.com/@fake/videos",
        count=1,
        include_shorts=False,
        retries=1,
    )

    # 第一個 YoutubeDL（抽清單）用 flat；下載階段（最後一個）維持非 flat
    assert seen_opts[0]["extract_flat"] == "in_playlist"
    assert seen_opts[-1]["extract_flat"] is False


def test_download_loop_backfills_past_failed_videos(monkeypatch, tmp_path):
    """下載遇到失敗（例如會員限定影片）應跳過並往後補，直到達成目標數量。"""
    import yt_fetch

    download_dir = tmp_path / "download"
    archive = download_dir / ".download_archive.txt"
    # v1、v3 模擬會員限定（下載失敗）；v0、v2、v4 可下載
    ids = ["v0aaaaaaaaa", "v1bbbbbbbbb", "v2ccccccccc", "v3ddddddddd", "v4eeeeeeeee"]
    member = {"v1bbbbbbbbb", "v3ddddddddd"}

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", download_dir)
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", archive)
    monkeypatch.setattr(yt_fetch, "check_ffmpeg", lambda: True)

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            return {
                "entries": [
                    {
                        "id": vid,
                        "title": f"Video {vid}",
                        "webpage_url": f"https://www.youtube.com/watch?v={vid}",
                        "duration": 120,
                    }
                    for vid in ids
                ]
            }

        def download(self, urls):
            vid = urls[0].split("watch?v=")[-1]
            if vid in member:
                raise RuntimeError("Join this channel to get access to members-only content")
            download_dir.mkdir(parents=True, exist_ok=True)
            (download_dir / f"Video {vid} [{vid}].mp4").write_text("", encoding="utf-8")
            with open(archive, "a", encoding="utf-8") as f:
                f.write(f"youtube {vid}\n")

    monkeypatch.setitem(sys.modules, "yt_dlp", types.SimpleNamespace(YoutubeDL=FakeYoutubeDL))

    downloaded = yt_fetch.download_videos(
        "https://www.youtube.com/@fake/videos",
        count=3,
        include_shorts=False,
        retries=1,
    )

    # 目標 3 支：跳過 v1、v3（會員失敗），補到 v0、v2、v4
    assert [item["id"] for item in downloaded] == ["v0aaaaaaaaa", "v2ccccccccc", "v4eeeeeeeee"]


def test_ytdlp_outtmpl_uses_channel_subdir(tmp_path):
    """輸出路徑應以頻道名稱作為子目錄，避免多頻道混在同一層。"""
    import yt_fetch

    opts = yt_fetch.build_ytdlp_options(
        download_dir=tmp_path,
        archive_file=tmp_path / ".download_archive.txt",
        quality="best",
        retries=1,
        include_shorts=False,
        playlist_extract_count=10,
        progress_hook=lambda d: None,
        match_filter=None,
    )
    outtmpl = opts["outtmpl"]
    assert "%(channel,uploader|Unknown Channel)s" in outtmpl
    # 頻道欄位在標題之前（作為上層子目錄）
    assert outtmpl.index("%(channel") < outtmpl.index("%(title)s")


def test_get_downloaded_ids_scans_channel_subdirs(tmp_path, monkeypatch):
    """已下載偵測應遞迴掃描頻道子目錄，同時相容舊的平放檔案。"""
    import yt_fetch

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", tmp_path)
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", tmp_path / ".download_archive.txt")

    sub = tmp_path / "Some Channel"
    sub.mkdir()
    (sub / "A Video [abcdefghijk].mp4").write_text("", encoding="utf-8")
    (tmp_path / "Old Flat [zyxwvutsrqp].mp4").write_text("", encoding="utf-8")

    ids = yt_fetch.get_downloaded_ids()
    assert "abcdefghijk" in ids  # 頻道子目錄內
    assert "zyxwvutsrqp" in ids  # 舊的平放檔案


def test_download_videos_reports_cookie_load_error(monkeypatch, tmp_path, caplog):
    import pytest

    import yt_fetch

    download_dir = tmp_path / "download"
    archive = download_dir / ".download_archive.txt"
    seen_opts = []

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", download_dir)
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", archive)
    monkeypatch.setattr(yt_fetch, "check_ffmpeg", lambda: True)

    class FakeDownloadError(Exception):
        pass

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts
            # 存快照（dict(opts)）而非參考：_extract_entries 會在 fallback 時就地移除 cookies，
            # 直接存參考會讓所有元素都指向同一個被改動後的 dict。
            seen_opts.append(dict(opts))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            raise FakeDownloadError("failed to load cookies")

    fake_yt_dlp = types.SimpleNamespace(
        YoutubeDL=FakeYoutubeDL,
        utils=types.SimpleNamespace(DownloadError=FakeDownloadError),
    )
    monkeypatch.setitem(sys.modules, "yt_dlp", fake_yt_dlp)

    with pytest.raises(SystemExit) as exc:
        yt_fetch.download_videos(
            "https://www.youtube.com/@fake/videos",
            count=1,
            include_shorts=False,
            retries=1,
            cookies_from_browser="chrome:Default",
        )

    assert exc.value.code == 1
    assert seen_opts[0]["cookiesfrombrowser"] == ("chrome", "Default", None, None)
    assert "載入 cookies 失敗" in caplog.text
    assert "chrome:Default" in caplog.text


def test_download_videos_falls_back_to_no_cookies_on_cookie_error(monkeypatch, tmp_path, caplog):
    """cookies 載入失敗時，公開頻道應自動改用『無 cookies』模式並成功下載。"""
    import logging

    import yt_fetch

    download_dir = tmp_path / "download"
    archive = download_dir / ".download_archive.txt"
    video_id = "abcdefghijk"
    seen_opts = []

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", download_dir)
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", archive)
    monkeypatch.setattr(yt_fetch, "check_ffmpeg", lambda: True)

    class FakeDownloadError(Exception):
        pass

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts
            # 存快照（見上一個測試說明）；has_cookies 反映「建構當下」的狀態。
            seen_opts.append(dict(opts))
            self.has_cookies = "cookiesfrombrowser" in opts or "cookiefile" in opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            # 帶 cookies 時模擬 Chrome App-Bound Encryption 擋住讀取；無 cookies 則成功。
            if self.has_cookies:
                raise FakeDownloadError("failed to load cookies")
            return {
                "entries": [
                    {
                        "id": video_id,
                        "title": "Fake Video",
                        "availability": "public",
                        "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
                        "duration": 120,
                    }
                ]
            }

        def download(self, urls):
            download_dir.mkdir(parents=True, exist_ok=True)
            (download_dir / f"Fake Video [{video_id}].mp4").write_text("", encoding="utf-8")
            archive.write_text(f"youtube {video_id}\n", encoding="utf-8")

    fake_yt_dlp = types.SimpleNamespace(
        YoutubeDL=FakeYoutubeDL,
        utils=types.SimpleNamespace(DownloadError=FakeDownloadError),
    )
    monkeypatch.setitem(sys.modules, "yt_dlp", fake_yt_dlp)

    with caplog.at_level(logging.WARNING):
        downloaded = yt_fetch.download_videos(
            "https://www.youtube.com/@fake/videos",
            count=1,
            include_shorts=False,
            retries=1,
            cookies_from_browser="chrome:Default",
        )

    # 公開影片在 fallback 後成功下載
    assert [item["id"] for item in downloaded] == [video_id]
    # 第一次嘗試帶 cookies，fallback 後（含下載階段）不帶 cookies
    assert "cookiesfrombrowser" in seen_opts[0]
    assert "cookiesfrombrowser" not in seen_opts[-1]
    assert (
        seen_opts[-1]["match_filter"](
            {"id": "member00001", "title": "member", "availability": "subscriber_only"}
        )
        == "非公開影片"
    )
    # 有提示改用無 cookies 模式
    assert "改用" in caplog.text


def test_download_videos_defers_member_entitlement_to_youtube_with_cookies(monkeypatch, tmp_path):
    """有合法 cookies 時保留會員候選，實際存取權由 yt-dlp／YouTube 驗證。"""
    import yt_fetch

    download_dir = tmp_path / "download"
    archive = download_dir / ".download_archive.txt"
    video_id = "member00001"
    seen_opts = []

    monkeypatch.setattr(yt_fetch, "DOWNLOAD_DIR", download_dir)
    monkeypatch.setattr(yt_fetch, "ARCHIVE_FILE", archive)
    monkeypatch.setattr(yt_fetch, "check_ffmpeg", lambda: True)

    class FakeDownloadError(Exception):
        pass

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = dict(opts)
            seen_opts.append(self.opts)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            return {
                "entries": [
                    {
                        "id": video_id,
                        "title": "Authorized Member Video",
                        "availability": "subscriber_only",
                        "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
                    }
                ]
            }

        def download(self, urls):
            candidate = {
                "id": video_id,
                "title": "Authorized Member Video",
                "availability": "subscriber_only",
            }
            assert self.opts["cookiefile"] == "cookies.txt"
            assert self.opts["match_filter"](candidate) is None
            download_dir.mkdir(parents=True, exist_ok=True)
            (download_dir / f"Authorized Member Video [{video_id}].mp4").write_text(
                "",
                encoding="utf-8",
            )
            archive.write_text(f"youtube {video_id}\n", encoding="utf-8")

    fake_yt_dlp = types.SimpleNamespace(
        YoutubeDL=FakeYoutubeDL,
        utils=types.SimpleNamespace(DownloadError=FakeDownloadError),
    )
    monkeypatch.setitem(sys.modules, "yt_dlp", fake_yt_dlp)

    downloaded = yt_fetch.download_videos(
        "https://www.youtube.com/@fake/videos",
        count=1,
        include_shorts=False,
        retries=1,
        cookies_file="cookies.txt",
    )

    assert [item["id"] for item in downloaded] == [video_id]
    assert all(opts["cookiefile"] == "cookies.txt" for opts in seen_opts)
