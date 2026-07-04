"""yt_fetch_gui 的純邏輯測試（不建立 Tk 視窗，可在無顯示器環境執行）。"""

import importlib

import pytest


def test_import_does_not_open_window():
    """匯入模組不應建立 Tk 視窗（headless/CI 也能 import）"""
    module = importlib.import_module("yt_fetch_gui")
    assert hasattr(module, "launch")
    assert hasattr(module, "parse_form_values")


def test_detect_language(monkeypatch):
    from yt_fetch_gui import detect_language

    # 設定檔優先
    assert detect_language({"language": "en"}) == "en"
    assert detect_language({"language": "zh"}) == "zh"
    # 無設定 → 看系統語系
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    monkeypatch.delenv("LC_ALL", raising=False)
    assert detect_language({}) == "en"
    monkeypatch.setenv("LANG", "zh_TW.UTF-8")
    assert detect_language({}) == "zh"


def test_translations_have_same_keys():
    """中英文字典 key 必須一致，避免漏譯造成 KeyError 回退"""
    from yt_fetch_gui import TRANSLATIONS

    assert set(TRANSLATIONS["zh"]) == set(TRANSLATIONS["en"])


def test_parse_form_values_defaults():
    from yt_fetch_gui import parse_form_values

    params = parse_form_values({"channel": "@abc"})
    assert params["channel"] == "@abc"
    assert params["count"] == 5
    assert params["retries"] == 3
    assert params["include_shorts"] is False
    assert params["quality"] == "best"
    assert params["ratelimit"] == 0.0
    assert params["sleep_seconds"] == 0.0
    assert params["channels_file"] == ""
    assert params["title_include"] == ""
    assert params["date_after"] == ""
    assert params["min_duration"] == 0
    assert params["write_subs"] is False
    assert params["sub_langs"] == "zh-Hant,zh-Hans,en"


def test_parse_form_values_full():
    from yt_fetch_gui import parse_form_values

    params = parse_form_values(
        {
            "channel": "  https://youtube.com/@x  ",
            "count": "10",
            "retries": "5",
            "include_shorts": True,
            "quality": "720p",
            "ratelimit": "2.5",
            "sleep": "1",
            "title_include": "Python",
            "title_exclude": "Shorts",
            "date_after": "20260101",
            "date_before": "20261231",
            "min_duration": "300",
            "max_duration": "1800",
            "write_subs": True,
            "sub_langs": "zh-Hant,en",
        }
    )
    assert params["channel"] == "https://youtube.com/@x"
    assert params["count"] == 10
    assert params["retries"] == 5
    assert params["include_shorts"] is True
    assert params["quality"] == "720p"
    # cookies 不再由表單提供
    assert "cookies_from_browser" not in params
    assert "cookies_file" not in params
    assert params["ratelimit"] == 2.5
    assert params["sleep_seconds"] == 1.0
    assert params["title_include"] == "Python"
    assert params["title_exclude"] == "Shorts"
    assert params["date_after"] == "20260101"
    assert params["date_before"] == "20261231"
    assert params["min_duration"] == 300
    assert params["max_duration"] == 1800
    assert params["write_subs"] is True
    assert params["sub_langs"] == "zh-Hant,en"


def test_parse_form_values_requires_channel():
    from yt_fetch_gui import parse_form_values

    with pytest.raises(ValueError):
        parse_form_values({"channel": "   "})


def test_parse_form_values_allows_channels_file_without_channel():
    from yt_fetch_gui import parse_form_values

    params = parse_form_values({"channel": "   ", "channels_file": "channels.txt"})
    assert params["channel"] == ""
    assert params["channels_file"] == "channels.txt"


def test_apply_profile_to_values():
    from yt_fetch_gui import apply_profile_to_values

    values = {"quality": "best", "ratelimit": "", "sleep": ""}
    assert apply_profile_to_values("space_720p", values)["quality"] == "720p"
    low = apply_profile_to_values("low_480p", values)
    assert low["quality"] == "480p"
    assert low["ratelimit"] == "3"
    assert apply_profile_to_values("custom", values) == values


def test_format_run_report_single_and_batch():
    from yt_fetch_gui import format_run_report

    report = format_run_report(
        [{"title": "T", "id": "abc", "path": "C:/x.mp4", "duration": 60}],
        None,
        lang="zh",
    )
    assert "本次下載紀錄" in report
    assert "C:/x.mp4" in report

    batch_report = format_run_report(
        [],
        [{"channel": "@a", "status": "ok", "downloaded": 1, "error": None}],
        lang="en",
    )
    assert "Batch results" in batch_report
    assert "@a" in batch_report


def test_diagnose_error_message():
    from yt_fetch_gui import diagnose_error_message

    assert "cookies" in diagnose_error_message("failed to load cookies", "en").lower()
    assert "ffmpeg" in diagnose_error_message("postprocessor failed: ffmpeg missing", "en").lower()
    assert "磁碟" in diagnose_error_message("Permission denied", "zh")


def test_parse_form_values_rejects_bad_numbers():
    from yt_fetch_gui import parse_form_values

    with pytest.raises(ValueError):
        parse_form_values({"channel": "@x", "count": "abc"})
    with pytest.raises(ValueError):
        parse_form_values({"channel": "@x", "count": "0"})
    with pytest.raises(ValueError):
        parse_form_values({"channel": "@x", "ratelimit": "-1"})
    with pytest.raises(ValueError):
        parse_form_values({"channel": "@x", "date_after": "2026-01-01"})
    with pytest.raises(ValueError):
        parse_form_values({"channel": "@x", "min_duration": "900", "max_duration": "300"})


def test_parse_form_values_uses_english_errors():
    from yt_fetch_gui import parse_form_values

    with pytest.raises(ValueError) as exc:
        parse_form_values({"channel": "   "}, lang="en")
    assert "Enter a channel" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        parse_form_values({"channel": "@x", "count": "abc"}, lang="en")
    assert "Number of videos must be an integer" in str(exc.value)


def test_gui_flag_parsed(monkeypatch):
    """--gui 旗標可被解析，且不會觸發互動輸入"""
    import yt_fetch

    monkeypatch.setattr("sys.argv", ["yt_fetch.py", "--gui"])
    args = yt_fetch.parse_args()
    assert args.gui is True
    assert not args.channel
