#!/usr/bin/env python3
"""yt_fetch 的 Tkinter 桌面介面。

這是沿用 `yt_fetch` 既有下載邏輯的薄層介面，不重寫核心流程：
- 收集頻道、數量、是否含 Shorts、重試、速率限制、間隔等參數
  （cookies 不再以欄位輸入，改由「登入 YouTube 取得 cookies」按鈕提供）
- 於背景執行緒呼叫 `yt_fetch.download_videos`，主視窗不阻塞
- 即時顯示下載日誌與成功/失敗摘要、可選擇／開啟下載資料夾
- 選單提供「關於」、「檢查更新」（僅檢查、不自動下載）與中／英文語系切換

安全邊界與 CLI 一致：只處理使用者自己有權存取的內容，不保存 cookies 內容。
"""

import datetime
import logging
import os
import queue
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from types import SimpleNamespace
from typing import Dict

import yt_fetch

logger = yt_fetch.logger

# 介面文字（中／英）。
TRANSLATIONS = {
    "zh": {
        "window_title": "yt_fetch － YouTube 頻道影片下載",
        "label_channel": "頻道 URL / ID / @handle",
        "label_count": "下載數量",
        "label_quality": "下載畫質",
        "label_profile": "快速設定",
        "label_retries": "重試次數",
        "label_ratelimit": "速率限制 MB/s（0=無限制）",
        "label_sleep": "下載間隔秒數（0=不延遲）",
        "label_title_include": "標題必須包含",
        "label_title_exclude": "標題排除關鍵字",
        "label_date_after": "上傳日期起日 YYYYMMDD",
        "label_date_before": "上傳日期迄日 YYYYMMDD",
        "label_min_duration": "最短長度秒數（0=不限）",
        "label_max_duration": "最長長度秒數（0=不限）",
        "label_sub_langs": "字幕語言（逗號分隔）",
        "section_settings": "下載設定",
        "section_advanced": "進階篩選與字幕",
        "section_batch": "批次清單",
        "section_output": "輸出資料夾",
        "section_results": "下載結果",
        "section_log": "執行日誌",
        "check_shorts": "包含 Shorts（預設排除）",
        "check_write_subs": "下載字幕／自動字幕（若影片提供）",
        "btn_choose_dir": "選擇資料夾",
        "btn_open_dir": "開啟資料夾",
        "btn_choose_channels": "匯入頻道清單",
        "btn_clear_channels": "清除清單",
        "btn_start": "開始下載",
        "btn_open_file": "開啟檔案",
        "btn_open_parent": "開啟所在資料夾",
        "btn_export_report": "匯出紀錄",
        "btn_login": "登入 YouTube 取得 cookies",
        "profile_custom": "自訂",
        "profile_best": "最佳畫質",
        "profile_space_720p": "省空間 720p",
        "profile_low_480p": "低畫質 480p",
        "login_hint": (
            "登入為選填；公開影片不需登入。\n"
            "遇到會員／付費影片、年齡限制或驗證時，按「登入」。\n"
            "工具只使用你本來就有權觀看的內容。"
        ),
        "status_ready": "就緒",
        "status_downloading": "下載中…",
        "status_login": "請在彈出的視窗登入 YouTube…",
        "login_done": "已取得並保存 cookies，之後下載會自動使用。",
        "login_failed": "登入或取得 cookies 失敗，請重試。",
        "status_done": "完成：本次下載 {n} 支",
        "status_finished": "已結束",
        "status_error": "發生錯誤",
        "progress_idle": "進度：尚未開始",
        "progress_percent": "進度：{percent:.1f}%",
        "progress_done": "進度：完成",
        "log_done": "=== 完成，共下載 {n} 支 ===",
        "log_exit": "=== 流程結束（退出碼 {code}）；詳見上方日誌 ===",
        "err_download": "下載失敗：{err}",
        "err_open_dir": "無法開啟資料夾：{err}",
        "err_open_file": "無法開啟檔案：{err}",
        "err_export_report": "無法匯出紀錄：{err}",
        "err_channel_required": "請輸入頻道 URL、ID 或 @handle",
        "err_channels_file": "無法讀取頻道清單：{err}",
        "field_count": "下載數量",
        "field_retries": "重試次數",
        "field_ratelimit": "速率限制",
        "field_sleep": "下載間隔",
        "field_min_duration": "最短長度",
        "field_max_duration": "最長長度",
        "field_date_after": "上傳日期起日",
        "field_date_before": "上傳日期迄日",
        "err_int": "{name}必須是整數",
        "err_min": "{name}必須 ≥ {minimum}",
        "err_float": "{name}必須是數字",
        "err_nonnegative": "{name}不可為負數",
        "menu_help": "說明",
        "menu_about": "關於",
        "menu_check_updates": "檢查更新",
        "menu_ffmpeg_status": "ffmpeg 狀態",
        "menu_language": "語言",
        "lang_zh": "中文",
        "lang_en": "English",
        "about_title": "關於 yt_fetch",
        "about_body": (
            "yt_fetch － YouTube 頻道影片下載工具\n\n"
            "版本：{version}\n"
            "yt-dlp：{ytdlp_version}\n"
            "專案：https://github.com/{repo}\n"
            "授權：MIT\n\n"
            "網路上已有許多類似工具；yt_fetch 主打輕巧、可攜、具 GUI、簡潔易懂，"
            "提供免安裝單檔程式。\n\n"
            "亮點：內建「登入 YouTube」一鍵取得 cookies（克服 Chrome 127+ 無法讀取 cookies 的問題），"
            "可下載你本來就有權觀看的內容，包括你自己付費／訂閱的頻道會員影片、年齡限制影片等。\n\n"
            "本工具僅供個人學習與研究使用，請遵守 YouTube 服務條款與著作權法。\n"
            "cookies 僅在本機抽取並使用你自己的 cookies、絕不外傳；屬已授權存取，不繞過任何未付費的限制。"
        ),
        "update_title": "檢查更新",
        "update_checking": "檢查更新中…",
        "update_latest": "目前已是最新版本（{version}）。",
        "update_available": "有新版本 {latest}（目前 {current}）。\n\n{ytdlp_status}\n\n是否開啟下載頁面？",
        "update_core_outdated": (
            "目前程式版本已是最新，但下載核心可能過期：\n{ytdlp_status}\n\n"
            "EXE 會固定打包當時的 yt-dlp；若下載開始失敗，請改用最新版 Release，"
            "或從原始碼執行並更新 yt-dlp。\n\n是否開啟 Releases？"
        ),
        "update_status_suffix": "{message}\n\n{ytdlp_status}",
        "update_failed": "無法檢查更新（請稍後再試或檢查網路連線）。",
        "ffmpeg_title": "ffmpeg 狀態",
        "ffmpeg_available": "可用",
        "ffmpeg_missing": "未偵測到可用 ffmpeg",
        "report_title": "本次下載紀錄",
        "report_batch_title": "批次結果",
        "report_saved": "已匯出紀錄：{path}",
    },
    "en": {
        "window_title": "yt_fetch — YouTube channel downloader",
        "label_channel": "Channel URL / ID / @handle",
        "label_count": "Number of videos",
        "label_quality": "Download quality",
        "label_profile": "Preset",
        "label_retries": "Retries",
        "label_ratelimit": "Rate limit MB/s (0 = unlimited)",
        "label_sleep": "Delay between downloads, sec (0 = none)",
        "label_title_include": "Title must contain",
        "label_title_exclude": "Exclude title keyword",
        "label_date_after": "Upload date after YYYYMMDD",
        "label_date_before": "Upload date before YYYYMMDD",
        "label_min_duration": "Minimum duration, sec (0 = none)",
        "label_max_duration": "Maximum duration, sec (0 = none)",
        "label_sub_langs": "Subtitle languages (comma-separated)",
        "section_settings": "Download settings",
        "section_advanced": "Advanced filters and subtitles",
        "section_batch": "Batch list",
        "section_output": "Output folder",
        "section_results": "Download results",
        "section_log": "Run log",
        "check_shorts": "Include Shorts (excluded by default)",
        "check_write_subs": "Download subtitles / auto subtitles when available",
        "btn_choose_dir": "Choose folder",
        "btn_open_dir": "Open folder",
        "btn_choose_channels": "Import channel list",
        "btn_clear_channels": "Clear list",
        "btn_start": "Start download",
        "btn_open_file": "Open file",
        "btn_open_parent": "Open containing folder",
        "btn_export_report": "Export report",
        "btn_login": "Sign in to YouTube for cookies",
        "profile_custom": "Custom",
        "profile_best": "Best quality",
        "profile_space_720p": "Space-saving 720p",
        "profile_low_480p": "Low quality 480p",
        "login_hint": (
            "Sign-in is optional; public videos need no login.\n"
            'For memberships, paid videos, age checks, or verification, click "Sign in".\n'
            "The tool only uses content your account can already watch."
        ),
        "status_ready": "Ready",
        "status_downloading": "Downloading…",
        "status_login": "Please sign in to YouTube in the opened window…",
        "login_done": "Cookies saved; future downloads will use them automatically.",
        "login_failed": "Sign-in or cookie capture failed, please retry.",
        "status_done": "Done: downloaded {n}",
        "status_finished": "Finished",
        "status_error": "Error",
        "progress_idle": "Progress: not started",
        "progress_percent": "Progress: {percent:.1f}%",
        "progress_done": "Progress: done",
        "log_done": "=== Done: {n} downloaded ===",
        "log_exit": "=== Finished (exit code {code}); see log above ===",
        "err_download": "Download failed: {err}",
        "err_open_dir": "Cannot open folder: {err}",
        "err_open_file": "Cannot open file: {err}",
        "err_export_report": "Cannot export report: {err}",
        "err_channel_required": "Enter a channel URL, ID, or @handle",
        "err_channels_file": "Cannot read channel list: {err}",
        "field_count": "Number of videos",
        "field_retries": "Retries",
        "field_ratelimit": "Rate limit",
        "field_sleep": "Delay",
        "field_min_duration": "Minimum duration",
        "field_max_duration": "Maximum duration",
        "field_date_after": "Upload date after",
        "field_date_before": "Upload date before",
        "err_int": "{name} must be an integer",
        "err_min": "{name} must be >= {minimum}",
        "err_float": "{name} must be a number",
        "err_nonnegative": "{name} cannot be negative",
        "menu_help": "Help",
        "menu_about": "About",
        "menu_check_updates": "Check for updates",
        "menu_ffmpeg_status": "ffmpeg status",
        "menu_language": "Language",
        "lang_zh": "中文",
        "lang_en": "English",
        "about_title": "About yt_fetch",
        "about_body": (
            "yt_fetch — YouTube channel video downloader\n\n"
            "Version: {version}\n"
            "yt-dlp: {ytdlp_version}\n"
            "Project: https://github.com/{repo}\n"
            "License: MIT\n\n"
            "Many similar tools already exist; yt_fetch focuses on being lightweight, "
            "portable, GUI-friendly, and easy to understand, with a standalone no-install EXE.\n\n"
            "Highlight: a built-in one-click 'Sign in to YouTube' obtains cookies (overcoming "
            "Chrome 127+ which blocks reading cookies), so you can download content you are already "
            "entitled to view, including channel memberships you pay for/subscribe to and "
            "age-restricted videos.\n\n"
            "For personal learning and research only; please follow YouTube's "
            "Terms of Service and copyright law.\n"
            "Cookies are only extracted and used locally as your own; never transmitted. "
            "This is authenticated access and does not bypass anything you have not paid for."
        ),
        "update_title": "Check for updates",
        "update_checking": "Checking for updates…",
        "update_latest": "You are on the latest version ({version}).",
        "update_available": (
            "A new version {latest} is available (current {current}).\n\n"
            "{ytdlp_status}\n\nOpen the download page?"
        ),
        "update_core_outdated": (
            "The app version is current, but the download core may be stale:\n{ytdlp_status}\n\n"
            "The EXE bundles the yt-dlp version available at build time. If downloads start "
            "failing, use the latest Release, or run from source and update yt-dlp.\n\n"
            "Open Releases?"
        ),
        "update_status_suffix": "{message}\n\n{ytdlp_status}",
        "update_failed": "Could not check for updates (try again later or check your connection).",
        "ffmpeg_title": "ffmpeg status",
        "ffmpeg_available": "Available",
        "ffmpeg_missing": "No usable ffmpeg detected",
        "report_title": "Download report",
        "report_batch_title": "Batch results",
        "report_saved": "Report exported: {path}",
    },
}

PROFILE_CHOICES = ("custom", "best", "space_720p", "low_480p")
PROFILE_VALUES = {
    "best": {"quality": "best", "ratelimit": "", "sleep": ""},
    "space_720p": {"quality": "720p", "ratelimit": "", "sleep": "1"},
    "low_480p": {"quality": "480p", "ratelimit": "3", "sleep": "1"},
}


def resource_path(rel: str) -> Path:
    """解析隨附資源路徑；打包成 exe（PyInstaller）時改用解壓目錄 sys._MEIPASS。"""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    return Path(__file__).resolve().parent / rel


def detect_language(config: Dict) -> str:
    """決定介面語言：設定檔 > 系統語系 > 預設中文。回傳 'zh' 或 'en'。"""
    lang = (config.get("language") or "").strip().lower()
    if lang in ("zh", "en"):
        return lang
    env = (os.environ.get("LANG") or os.environ.get("LC_ALL") or "").lower()
    return "en" if env.startswith("en") else "zh"


def form_text(lang: str, key: str, **kwargs) -> str:
    """取得表單驗證文字；給 parse_form_values 這類無 GUI 狀態的純函式使用。"""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["zh"]).get(key, key)
    return text.format(**kwargs) if kwargs else text


def parse_form_values(values: Dict[str, str], lang: str = "zh") -> Dict:  # noqa: C901
    """將 GUI 表單的原始字串值轉為 `download_videos` 需要的參數，並做基本驗證。

    Args:
        values: 介面欄位字串值（channel/count/retries/ratelimit/sleep/include_shorts）。
            cookies 不再由表單輸入，改由「登入 YouTube 取得 cookies」流程提供。

    Returns:
        可直接展開傳給 `yt_fetch.download_videos` 的參數 dict（不含 cookies）。

    Raises:
        ValueError: 欄位缺漏或格式錯誤，message 為可直接顯示的提示。
    """
    channel = (values.get("channel") or "").strip()
    channels_file = (values.get("channels_file") or "").strip()
    if not channel and not channels_file:
        raise ValueError(form_text(lang, "err_channel_required"))

    def _to_int(raw: str, default: int, name: str, minimum: int) -> int:
        raw = (raw or "").strip()
        if not raw:
            return default
        try:
            parsed = int(raw)
        except ValueError:
            raise ValueError(form_text(lang, "err_int", name=name))
        if parsed < minimum:
            raise ValueError(form_text(lang, "err_min", name=name, minimum=minimum))
        return parsed

    def _to_float(raw: str, default: float, name: str) -> float:
        raw = (raw or "").strip()
        if not raw:
            return default
        try:
            parsed = float(raw)
        except ValueError:
            raise ValueError(form_text(lang, "err_float", name=name))
        if parsed < 0:
            raise ValueError(form_text(lang, "err_nonnegative", name=name))
        return parsed

    quality = (values.get("quality") or "best").strip().lower()
    if quality not in yt_fetch.QUALITY_CHOICES:
        quality = "best"

    date_after = (values.get("date_after") or "").strip()
    date_before = (values.get("date_before") or "").strip()
    try:
        date_after = yt_fetch.normalize_date_filter(date_after, "--date-after")
        date_before = yt_fetch.normalize_date_filter(date_before, "--date-before")
    except ValueError as e:
        message = str(e)
        message = message.replace("--date-after", form_text(lang, "field_date_after"))
        message = message.replace("--date-before", form_text(lang, "field_date_before"))
        raise ValueError(message)

    min_duration = _to_int(
        values.get("min_duration"),
        0,
        form_text(lang, "field_min_duration"),
        0,
    )
    max_duration = _to_int(
        values.get("max_duration"),
        0,
        form_text(lang, "field_max_duration"),
        0,
    )
    if min_duration and max_duration and min_duration > max_duration:
        raise ValueError(
            f"{form_text(lang, 'field_min_duration')} must be <= {form_text(lang, 'field_max_duration')}"
            if lang == "en"
            else f"{form_text(lang, 'field_min_duration')}不可大於{form_text(lang, 'field_max_duration')}"
        )

    return {
        "channel": channel,
        "channels_file": channels_file,
        "count": _to_int(values.get("count"), 5, form_text(lang, "field_count"), 1),
        "include_shorts": bool(values.get("include_shorts")),
        "quality": quality,
        "retries": _to_int(values.get("retries"), 3, form_text(lang, "field_retries"), 1),
        "ratelimit": _to_float(values.get("ratelimit"), 0.0, form_text(lang, "field_ratelimit")),
        "sleep_seconds": _to_float(values.get("sleep"), 0.0, form_text(lang, "field_sleep")),
        "title_include": (values.get("title_include") or "").strip(),
        "title_exclude": (values.get("title_exclude") or "").strip(),
        "date_after": date_after,
        "date_before": date_before,
        "min_duration": min_duration,
        "max_duration": max_duration,
        "write_subs": bool(values.get("write_subs")),
        "sub_langs": (values.get("sub_langs") or "zh-Hant,zh-Hans,en").strip(),
    }


def apply_profile_to_values(profile: str, values: Dict[str, str]) -> Dict[str, str]:
    """套用 GUI 快速設定；custom 不改變原值。"""
    if profile not in PROFILE_VALUES:
        return dict(values)
    updated = dict(values)
    updated.update(PROFILE_VALUES[profile])
    return updated


def diagnose_error_message(message: str, lang: str = "zh") -> str:
    """把常見錯誤文字轉成更可操作的 GUI 提示。"""
    return yt_fetch.build_error_diagnosis_message(message, lang)


def format_run_report(downloaded, batch_results=None, lang: str = "zh") -> str:
    """產生可匯出的本次下載紀錄。"""
    lines = [
        form_text(lang, "report_title"),
        f"Generated: {datetime.datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    if downloaded:
        for idx, item in enumerate(downloaded, 1):
            lines.append(f"{idx}. {item.get('title', '')}")
            lines.append(f"   ID: {item.get('id', '')}")
            lines.append(f"   Path: {item.get('path', '')}")
            lines.append(f"   Duration: {item.get('duration', '')}")
    else:
        lines.append("No new videos downloaded." if lang == "en" else "本次沒有新下載影片。")

    if batch_results:
        lines.extend(["", form_text(lang, "report_batch_title")])
        for result in batch_results:
            detail = (
                f"{result.get('downloaded', 0)}"
                if result.get("status") == "ok"
                else str(result.get("error") or "")
            )
            lines.append(f"- {result.get('channel')}: {result.get('status')} ({detail})")
    return "\n".join(lines) + "\n"


def open_folder(path: Path) -> None:
    """以系統檔案總管開啟資料夾（跨平台）。"""
    path.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def open_file(path: Path) -> None:
    """以系統預設程式開啟檔案。"""
    if sys.platform == "win32":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


class _QueueLogHandler(logging.Handler):
    """把 log 記錄塞進 queue，供主執行緒安全地更新介面。"""

    def __init__(self, log_queue: "queue.Queue"):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put(self.format(record))


class YtFetchGUI:
    """主視窗。所有 Tk 物件都在這裡建立，import 模組不會啟動視窗。"""

    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = root
        self.root.minsize(720, 680)

        # 讀取設定檔作為表單初始值（首次執行會自動建立）
        yt_fetch.write_default_config_if_missing()
        self.config = yt_fetch.load_config()
        self.lang = detect_language(self.config)
        if self.config.get("download_dir"):
            self.download_dir = Path(self.config["download_dir"])
        else:
            self.download_dir = yt_fetch.DOWNLOAD_DIR

        self.log_queue: "queue.Queue" = queue.Queue()
        self.result_queue: "queue.Queue" = queue.Queue()
        self.update_queue: "queue.Queue" = queue.Queue()
        self.progress_queue: "queue.Queue" = queue.Queue()
        self.worker = None
        self.current_downloaded = []
        self.current_batch_results = None
        self.profile_key = "custom"

        # 表單變數只建立一次，切換語言重建 widget 時可保留使用者輸入
        cfg = self.config

        def num(key):
            value = cfg.get(key)
            return "" if not value else str(value)

        self.vars = {
            "channel": tk.StringVar(value=cfg.get("channel", "")),
            "channels_file": tk.StringVar(value=""),
            "count": tk.StringVar(value=str(cfg.get("count", 5))),
            "quality": tk.StringVar(value=cfg.get("quality", "best")),
            "retries": tk.StringVar(value=str(cfg.get("retries", 3))),
            "include_shorts": tk.BooleanVar(value=bool(cfg.get("include_shorts", False))),
            "ratelimit": tk.StringVar(value=num("ratelimit")),
            "sleep": tk.StringVar(value=num("sleep")),
            "title_include": tk.StringVar(value=cfg.get("title_include", "")),
            "title_exclude": tk.StringVar(value=cfg.get("title_exclude", "")),
            "date_after": tk.StringVar(value=cfg.get("date_after", "")),
            "date_before": tk.StringVar(value=cfg.get("date_before", "")),
            "min_duration": tk.StringVar(value=num("min_duration")),
            "max_duration": tk.StringVar(value=num("max_duration")),
            "write_subs": tk.BooleanVar(value=bool(cfg.get("write_subs", False))),
            "sub_langs": tk.StringVar(value=cfg.get("sub_langs", "zh-Hant,zh-Hans,en")),
        }
        self.dir_var = tk.StringVar(value=str(self.download_dir))
        self.status_var = tk.StringVar(value=self.t("status_ready"))
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text_var = tk.StringVar(value=self.t("progress_idle"))
        self.profile_var = tk.StringVar(value=self.t("profile_custom"))

        self.root.title(self.t("window_title"))
        self._set_window_icon()
        self._build_menu()
        self._build_widgets()
        self._attach_log_handler()
        self.root.after(150, self._poll)

    def _set_window_icon(self) -> None:
        """設定視窗圖示（找不到或失敗時靜默略過）。"""
        try:
            icon_png = resource_path("assets/yt_fetch.png")
            if icon_png.exists():
                self._icon_img = self.tk.PhotoImage(file=str(icon_png))
                self.root.iconphoto(True, self._icon_img)
        except Exception:  # noqa: BLE001 - 圖示非必要，失敗不影響功能
            pass

    # --- i18n ---

    def t(self, key: str, **kwargs) -> str:
        text = TRANSLATIONS.get(self.lang, TRANSLATIONS["zh"]).get(key, key)
        return text.format(**kwargs) if kwargs else text

    def _set_language(self, lang: str) -> None:
        if lang == self.lang:
            return
        self.lang = lang
        yt_fetch.save_config({"language": lang})
        # 保留日誌內容，重建選單與主體
        saved_log = self.log_text.get("1.0", "end-1c")
        self.body.destroy()
        self.status_var.set(self.t("status_ready"))
        self.progress_text_var.set(self.t("progress_idle"))
        self._build_menu()
        self._build_widgets()
        if saved_log:
            self._append_log(saved_log)
        self.root.title(self.t("window_title"))

    # --- 介面建立 ---

    def _build_menu(self) -> None:
        tk = self.tk
        menubar = tk.Menu(self.root)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=self.t("menu_about"), command=self._show_about)
        help_menu.add_command(label=self.t("menu_check_updates"), command=self._check_updates)
        help_menu.add_command(label=self.t("menu_ffmpeg_status"), command=self._show_ffmpeg_status)
        menubar.add_cascade(label=self.t("menu_help"), menu=help_menu)

        lang_menu = tk.Menu(menubar, tearoff=0)
        self._lang_choice = tk.StringVar(value=self.lang)
        lang_menu.add_radiobutton(
            label=self.t("lang_zh"),
            value="zh",
            variable=self._lang_choice,
            command=lambda: self._set_language("zh"),
        )
        lang_menu.add_radiobutton(
            label=self.t("lang_en"),
            value="en",
            variable=self._lang_choice,
            command=lambda: self._set_language("en"),
        )
        menubar.add_cascade(label=self.t("menu_language"), menu=lang_menu)

        self.root.config(menu=menubar)
        self.menubar = menubar

    def _build_widgets(self) -> None:
        tk, ttk = self.tk, self.ttk
        pad = {"padx": 6, "pady": 4}

        # 全部主體放在單一容器，切換語言時整體重建
        self.body = ttk.Frame(self.root)
        self.body.pack(fill="both", expand=True)

        pane = ttk.PanedWindow(self.body, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=6, pady=6)

        left = ttk.Frame(pane, width=520)
        right = ttk.Frame(pane)
        pane.add(left, weight=0)
        pane.add(right, weight=1)

        def set_initial_sash() -> None:
            try:
                pane.sashpos(0, 620)
            except Exception:  # noqa: BLE001 - 分隔線位置非必要功能
                pass

        self.root.after(0, set_initial_sash)

        form = ttk.LabelFrame(left, text=self.t("section_settings"))
        form.pack(fill="x", **pad)
        form.columnconfigure(1, weight=1)

        # cookies 不再以手動欄位輸入：需要時改按下方「登入 YouTube 取得 cookies」按鈕。
        rows = [
            ("label_channel", "channel"),
            ("label_count", "count"),
            ("label_quality", "quality"),
            ("label_profile", "profile"),
            ("label_retries", "retries"),
            ("label_ratelimit", "ratelimit"),
            ("label_sleep", "sleep"),
        ]
        row = 0
        for label_key, key in rows:
            ttk.Label(form, text=self.t(label_key)).grid(row=row, column=0, sticky="w", **pad)
            if key == "quality":
                ttk.Combobox(
                    form,
                    textvariable=self.vars[key],
                    values=yt_fetch.QUALITY_CHOICES,
                    state="readonly",
                ).grid(row=row, column=1, sticky="ew", **pad)
            elif key == "profile":
                self.profile_var.set(self.t(f"profile_{self.profile_key}"))
                self.profile_combo = ttk.Combobox(
                    form,
                    textvariable=self.profile_var,
                    values=[self.t(f"profile_{key}") for key in PROFILE_CHOICES],
                    state="readonly",
                )
                self.profile_combo.grid(row=row, column=1, sticky="ew", **pad)
                self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)
            else:
                ttk.Entry(form, textvariable=self.vars[key]).grid(
                    row=row, column=1, sticky="ew", **pad
                )
            row += 1

        ttk.Checkbutton(
            form, text=self.t("check_shorts"), variable=self.vars["include_shorts"]
        ).grid(row=row, column=1, sticky="w", **pad)

        advanced = ttk.LabelFrame(left, text=self.t("section_advanced"))
        advanced.pack(fill="x", **pad)
        advanced.columnconfigure(1, weight=1)
        advanced.columnconfigure(3, weight=1)
        advanced_rows = [
            ("label_title_include", "title_include", "label_title_exclude", "title_exclude"),
            ("label_date_after", "date_after", "label_date_before", "date_before"),
            ("label_min_duration", "min_duration", "label_max_duration", "max_duration"),
        ]
        for adv_row, (left_label, left_key, right_label, right_key) in enumerate(advanced_rows):
            ttk.Label(advanced, text=self.t(left_label)).grid(
                row=adv_row, column=0, sticky="w", **pad
            )
            ttk.Entry(advanced, textvariable=self.vars[left_key]).grid(
                row=adv_row, column=1, sticky="ew", **pad
            )
            ttk.Label(advanced, text=self.t(right_label)).grid(
                row=adv_row, column=2, sticky="w", **pad
            )
            ttk.Entry(advanced, textvariable=self.vars[right_key]).grid(
                row=adv_row, column=3, sticky="ew", **pad
            )
        ttk.Checkbutton(
            advanced,
            text=self.t("check_write_subs"),
            variable=self.vars["write_subs"],
        ).grid(row=3, column=0, columnspan=4, sticky="w", **pad)
        ttk.Label(advanced, text=self.t("label_sub_langs")).grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(advanced, textvariable=self.vars["sub_langs"]).grid(
            row=4, column=1, columnspan=3, sticky="ew", **pad
        )

        channels_frame = ttk.LabelFrame(left, text=self.t("section_batch"))
        channels_frame.pack(fill="x", **pad)
        channels_frame.columnconfigure(0, weight=1)
        ttk.Entry(channels_frame, textvariable=self.vars["channels_file"], state="readonly").grid(
            row=0, column=0, sticky="ew", **pad
        )
        ttk.Button(
            channels_frame,
            text=self.t("btn_choose_channels"),
            command=self._choose_channels_file,
        ).grid(row=0, column=1, **pad)
        ttk.Button(
            channels_frame,
            text=self.t("btn_clear_channels"),
            command=lambda: self.vars["channels_file"].set(""),
        ).grid(row=0, column=2, **pad)

        # 下載資料夾列
        dir_frame = ttk.LabelFrame(left, text=self.t("section_output"))
        dir_frame.pack(fill="x", **pad)
        dir_frame.columnconfigure(0, weight=1)
        ttk.Entry(dir_frame, textvariable=self.dir_var, state="readonly").grid(
            row=0, column=0, sticky="ew", **pad
        )
        ttk.Button(dir_frame, text=self.t("btn_choose_dir"), command=self._choose_dir).grid(
            row=0, column=1, **pad
        )
        ttk.Button(dir_frame, text=self.t("btn_open_dir"), command=self._open_dir).grid(
            row=0, column=2, **pad
        )

        # 動作列
        action = ttk.Frame(left)
        action.pack(fill="x", **pad)
        self.start_btn = ttk.Button(action, text=self.t("btn_start"), command=self._on_start)
        self.start_btn.pack(side="left", **pad)
        # 受控登入按鈕（僅 Windows + Chrome 系；解決 Chrome 127+ 無法讀取 cookies）
        if sys.platform == "win32":
            self.login_btn = ttk.Button(action, text=self.t("btn_login"), command=self._on_login)
            self.login_btn.pack(side="left", **pad)
        ttk.Label(action, textvariable=self.status_var).pack(side="left", **pad)

        # 登入功能說明（選填）
        if sys.platform == "win32":
            ttk.Label(
                left,
                text=self.t("login_hint"),
                foreground="#555555",
                wraplength=560,
                justify="left",
            ).pack(fill="x", padx=6, anchor="w")

        progress_frame = ttk.Frame(right)
        progress_frame.pack(fill="x", **pad)
        ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100.0,
            mode="determinate",
        ).pack(side="left", fill="x", expand=True, **pad)
        ttk.Label(progress_frame, textvariable=self.progress_text_var, width=18).pack(
            side="left", **pad
        )

        result_frame = ttk.LabelFrame(right, text=self.t("section_results"))
        result_frame.pack(fill="both", **pad)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        self.result_list = tk.Listbox(result_frame, height=8)
        self.result_list.grid(row=0, column=0, rowspan=3, sticky="nsew", **pad)
        ttk.Button(
            result_frame, text=self.t("btn_open_file"), command=self._open_selected_file
        ).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(
            result_frame, text=self.t("btn_open_parent"), command=self._open_selected_parent
        ).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(
            result_frame, text=self.t("btn_export_report"), command=self._export_report
        ).grid(row=2, column=1, sticky="ew", **pad)

        # 日誌區
        log_frame = ttk.LabelFrame(right, text=self.t("section_log"))
        log_frame.pack(fill="both", expand=True, **pad)
        self.log_text = tk.Text(log_frame, height=24, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _attach_log_handler(self) -> None:
        handler = _QueueLogHandler(self.log_queue)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S")
        )
        logger.addHandler(handler)
        self._log_handler = handler

    def maximize_initial_window(self) -> None:
        """啟動 GUI 時預設最大化；失敗時退回較寬的桌面尺寸。"""
        try:
            if sys.platform == "win32":
                self.root.state("zoomed")
                return
            if sys.platform.startswith("linux"):
                self.root.attributes("-zoomed", True)
                return
        except Exception:  # noqa: BLE001 - 最大化不是必要功能
            pass

        try:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            width = min(max(1180, int(screen_w * 0.86)), screen_w)
            height = min(max(820, int(screen_h * 0.86)), screen_h)
            x = max((screen_w - width) // 2, 0)
            y = max((screen_h - height) // 2, 0)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:  # noqa: BLE001
            self.root.geometry("1180x820")

    # --- 說明選單 ---

    def _show_about(self) -> None:
        from tkinter import messagebox

        messagebox.showinfo(
            self.t("about_title"),
            self.t(
                "about_body",
                version=yt_fetch.__version__,
                ytdlp_version=yt_fetch.get_bundled_ytdlp_version(),
                repo=yt_fetch.GITHUB_REPO,
            ),
        )

    def _show_ffmpeg_status(self) -> None:
        from tkinter import messagebox

        status = yt_fetch.get_ffmpeg_status()
        if status["available"]:
            body = (
                f"{self.t('ffmpeg_available')}\n"
                f"Source: {status['source']}\n"
                f"Path: {status['path']}\n"
                f"Version: {status['version']}"
            )
        else:
            body = self.t("ffmpeg_missing")
        messagebox.showinfo(self.t("ffmpeg_title"), body)

    def _check_updates(self) -> None:
        """僅檢查 GitHub 最新版本並提示，不自動下載。"""
        self.status_var.set(self.t("update_checking"))
        threading.Thread(target=self._fetch_update, daemon=True).start()

    def _fetch_update(self) -> None:
        tag = yt_fetch.fetch_latest_release_tag()
        ytdlp_latest = yt_fetch.fetch_latest_pypi_version("yt-dlp")
        self.update_queue.put({"release_tag": tag, "ytdlp_latest": ytdlp_latest})

    def _on_update_result(self, result) -> None:
        from tkinter import messagebox

        self.status_var.set(self.t("status_ready"))
        if isinstance(result, dict):
            tag = result.get("release_tag")
            ytdlp_latest = result.get("ytdlp_latest")
        else:
            tag = result
            ytdlp_latest = None
        current = yt_fetch.__version__
        ytdlp_status = yt_fetch.build_ytdlp_update_message(ytdlp_latest)
        ytdlp_current = yt_fetch.get_bundled_ytdlp_version()
        ytdlp_outdated = bool(
            ytdlp_latest
            and ytdlp_current != "unknown"
            and yt_fetch.is_newer_version(ytdlp_latest, ytdlp_current)
        )
        if not tag:
            messagebox.showwarning(
                self.t("update_title"),
                self.t(
                    "update_status_suffix",
                    message=self.t("update_failed"),
                    ytdlp_status=ytdlp_status,
                ),
            )
        elif yt_fetch.is_newer_version(tag, current):
            if messagebox.askyesno(
                self.t("update_title"),
                self.t(
                    "update_available",
                    latest=tag,
                    current=current,
                    ytdlp_status=ytdlp_status,
                ),
            ):
                webbrowser.open(yt_fetch.RELEASES_URL)
        elif ytdlp_outdated:
            if messagebox.askyesno(
                self.t("update_title"),
                self.t("update_core_outdated", ytdlp_status=ytdlp_status),
            ):
                webbrowser.open(yt_fetch.RELEASES_URL)
        else:
            messagebox.showinfo(
                self.t("update_title"),
                self.t(
                    "update_status_suffix",
                    message=self.t("update_latest", version=current),
                    ytdlp_status=ytdlp_status,
                ),
            )

    # --- 下載事件 ---

    def _choose_dir(self) -> None:
        from tkinter import filedialog

        chosen = filedialog.askdirectory(initialdir=str(self.download_dir))
        if chosen:
            self.download_dir = Path(chosen)
            self.dir_var.set(str(self.download_dir))

    def _choose_channels_file(self) -> None:
        from tkinter import filedialog

        chosen = filedialog.askopenfilename(
            title=self.t("btn_choose_channels"),
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
        )
        if chosen:
            self.vars["channels_file"].set(chosen)

    def _on_profile_selected(self, _event=None) -> None:
        selected = self.profile_var.get()
        label_to_key = {self.t(f"profile_{key}"): key for key in PROFILE_CHOICES}
        self.profile_key = label_to_key.get(selected, "custom")
        raw = {k: v.get() for k, v in self.vars.items()}
        updated = apply_profile_to_values(self.profile_key, raw)
        for key in ("quality", "ratelimit", "sleep"):
            self.vars[key].set(updated[key])

    def _open_dir(self) -> None:
        try:
            open_folder(self.download_dir)
        except Exception as e:  # noqa: BLE001 - 開檔案總管失敗只需提示
            self._show_error(self.t("err_open_dir", err=e))

    def _on_start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        raw = {k: v.get() for k, v in self.vars.items()}
        try:
            params = parse_form_values(raw, self.lang)
        except ValueError as e:
            self._show_error(str(e))
            return

        # 套用使用者選擇的下載資料夾（download_videos 使用模組層常數）
        yt_fetch.set_download_dir(self.download_dir)

        # 把當次的非敏感設定寫回設定檔（cookies 不寫入；語言一併保留）
        yt_fetch.save_config(
            {
                "channel": params["channel"],
                "count": params["count"],
                "quality": params["quality"],
                "retries": params["retries"],
                "include_shorts": params["include_shorts"],
                "ratelimit": params["ratelimit"],
                "sleep": params["sleep_seconds"],
                "title_include": params["title_include"],
                "title_exclude": params["title_exclude"],
                "date_after": params["date_after"],
                "date_before": params["date_before"],
                "min_duration": params["min_duration"],
                "max_duration": params["max_duration"],
                "write_subs": params["write_subs"],
                "sub_langs": params["sub_langs"],
                "download_dir": str(self.download_dir),
                "language": self.lang,
            }
        )

        self.start_btn.configure(state="disabled")
        self.status_var.set(self.t("status_downloading"))
        self.progress_var.set(0.0)
        self.progress_text_var.set(self.t("progress_idle"))
        self.current_downloaded = []
        self.current_batch_results = None
        self._clear_log()
        self._clear_results()
        self.worker = threading.Thread(target=self._run_download, args=(params,), daemon=True)
        self.worker.start()

    def _on_login(self) -> None:
        """開啟受控瀏覽器登入 YouTube 取得 cookies（背景執行緒，不阻塞 UI）。"""
        if getattr(self, "_login_worker", None) and self._login_worker.is_alive():
            return
        if self.worker and self.worker.is_alive():
            return
        self.start_btn.configure(state="disabled")
        if hasattr(self, "login_btn"):
            self.login_btn.configure(state="disabled")
        self.status_var.set(self.t("status_login"))
        self._clear_log()
        self._login_worker = threading.Thread(target=self._run_login, daemon=True)
        self._login_worker.start()

    def _run_login(self) -> None:
        ok = False
        try:
            import chrome_cdp_cookies as cdp

            ok = bool(cdp.interactive_login("chrome"))
        except Exception as e:  # noqa: BLE001 - 任何錯誤都回報到介面
            logger.error(f"登入失敗：{e}")
        # 回主執行緒更新 UI
        self.root.after(0, self._on_login_done, ok)

    def _on_login_done(self, ok: bool) -> None:
        self.start_btn.configure(state="normal")
        if hasattr(self, "login_btn"):
            self.login_btn.configure(state="normal")
        if ok:
            self.status_var.set(self.t("login_done"))
            logger.info(self.t("login_done"))
        else:
            self.status_var.set(self.t("login_failed"))
            logger.warning(self.t("login_failed"))

    def _run_download(self, params: Dict) -> None:
        """背景執行緒：呼叫核心下載邏輯，結果丟回 queue。"""
        try:
            # 自動沿用「登入 YouTube」取得的受控 cookies（未登入則為空、改以無 cookies 下載）
            cookies_file = yt_fetch.managed_cookies_file()
            if cookies_file:
                logger.info(f"使用受控瀏覽器 cookies：{cookies_file}")
            if params["channels_file"]:
                channels = yt_fetch.read_channels_file(params["channels_file"])
                batch_args = SimpleNamespace(
                    count=params["count"],
                    include_shorts=params["include_shorts"],
                    retries=params["retries"],
                    cookies_from_browser="",
                    cookies=cookies_file,
                    ratelimit=params["ratelimit"],
                    sleep=params["sleep_seconds"],
                    quality=params["quality"],
                    title_include=params["title_include"],
                    title_exclude=params["title_exclude"],
                    date_after=params["date_after"],
                    date_before=params["date_before"],
                    min_duration=params["min_duration"],
                    max_duration=params["max_duration"],
                    write_subs=params["write_subs"],
                    sub_langs=params["sub_langs"],
                )
                batch_results = yt_fetch.run_batch_download(
                    channels, batch_args, progress_callback=self._on_download_progress
                )
                downloaded = [
                    item for result in batch_results for item in result.get("downloaded_items", [])
                ]
                self.result_queue.put(
                    ("batch_done", {"downloaded": downloaded, "batch": batch_results})
                )
                return

            channel_url = yt_fetch.normalize_channel_url(params["channel"])
            downloaded = yt_fetch.download_videos(
                channel_url,
                params["count"],
                params["include_shorts"],
                params["retries"],
                "",
                cookies_file,
                params["ratelimit"],
                params["sleep_seconds"],
                params["quality"],
                self._on_download_progress,
                params["title_include"],
                params["title_exclude"],
                params["date_after"],
                params["date_before"],
                params["min_duration"],
                params["max_duration"],
                params["write_subs"],
                params["sub_langs"],
            )
            self.result_queue.put(("done", downloaded))
        except SystemExit as e:
            # download_videos 在致命錯誤時會 sys.exit；於執行緒中轉為訊息
            self.result_queue.put(("exit", e.code))
        except FileNotFoundError as e:
            self.result_queue.put(("error", self.t("err_channels_file", err=e)))
        except Exception as e:  # noqa: BLE001 - 任意錯誤都回報到介面
            self.result_queue.put(("error", str(e)))

    def _on_download_progress(self, progress: Dict) -> None:
        """背景執行緒收到 yt-dlp progress hook 後，轉送主執行緒更新 UI。"""
        self.progress_queue.put(progress)

    # --- 主執行緒輪詢 ---

    def _poll(self) -> None:
        while True:
            try:
                msg = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self._append_log(msg)

        try:
            kind, payload = self.result_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            self._on_finished(kind, payload)

        while True:
            try:
                progress = self.progress_queue.get_nowait()
            except queue.Empty:
                break
            self._on_progress(progress)

        try:
            tag = self.update_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            self._on_update_result(tag)

        self.root.after(150, self._poll)

    def _on_progress(self, progress: Dict) -> None:
        status = progress.get("status")
        if status == "finished":
            self.progress_var.set(100.0)
            self.progress_text_var.set(self.t("progress_done"))
            return

        total = progress.get("total_bytes") or progress.get("total_bytes_estimate")
        downloaded = progress.get("downloaded_bytes")
        if total and downloaded is not None:
            percent = max(0.0, min(100.0, downloaded / total * 100))
            self.progress_var.set(percent)
            self.progress_text_var.set(self.t("progress_percent", percent=percent))

    def _on_finished(self, kind: str, payload) -> None:
        self.start_btn.configure(state="normal")
        if kind in ("done", "batch_done"):
            downloaded = payload if kind == "done" else payload["downloaded"]
            batch_results = None if kind == "done" else payload["batch"]
            self.current_downloaded = downloaded
            self.current_batch_results = batch_results
            count = len(downloaded)
            self.status_var.set(self.t("status_done", n=count))
            self.progress_var.set(100.0)
            self.progress_text_var.set(self.t("progress_done"))
            self._append_log(self.t("log_done", n=count))
            for i, item in enumerate(downloaded, 1):
                self._append_log(f"{i}. {item['title']} -> {item['path']}")
                self._append_result(item)
            if batch_results:
                for result in batch_results:
                    self._append_log(
                        f"{result['channel']}：{result['status']} ({result['downloaded']})"
                    )
        elif kind == "exit":
            self.status_var.set(self.t("status_finished"))
            self._append_log(self.t("log_exit", code=payload))
            self._append_log(diagnose_error_message(str(payload), self.lang))
        else:
            self.status_var.set(self.t("status_error"))
            diagnosis = diagnose_error_message(str(payload), self.lang)
            self._append_log(diagnosis)
            self._show_error(f"{self.t('err_download', err=payload)}\n\n{diagnosis}")

    # --- 介面小工具 ---

    def _append_log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _append_result(self, item: Dict) -> None:
        label = f"{item.get('title', '')} [{item.get('id', '')}]"
        self.result_list.insert("end", label)

    def _clear_results(self) -> None:
        self.result_list.delete(0, "end")

    def _selected_result_path(self) -> Path:
        selection = self.result_list.curselection()
        if not selection:
            raise ValueError("no selection")
        index = selection[0]
        return Path(self.current_downloaded[index].get("path") or "")

    def _open_selected_file(self) -> None:
        try:
            path = self._selected_result_path()
            if not path.exists():
                raise FileNotFoundError(path)
            open_file(path)
        except Exception as e:  # noqa: BLE001
            self._show_error(self.t("err_open_file", err=e))

    def _open_selected_parent(self) -> None:
        try:
            path = self._selected_result_path()
            open_folder(path.parent)
        except Exception as e:  # noqa: BLE001
            self._show_error(self.t("err_open_dir", err=e))

    def _export_report(self) -> None:
        try:
            report = format_run_report(
                self.current_downloaded,
                self.current_batch_results,
                self.lang,
            )
            self.download_dir.mkdir(parents=True, exist_ok=True)
            path = self.download_dir / (
                "yt_fetch_report_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
            )
            path.write_text(report, encoding="utf-8")
            logger.info(self.t("report_saved", path=path))
        except Exception as e:  # noqa: BLE001
            self._show_error(self.t("err_export_report", err=e))

    def _show_error(self, message: str) -> None:
        from tkinter import messagebox

        messagebox.showerror("yt_fetch", message)


def launch() -> int:
    """建立並啟動 GUI。回傳行程退出碼。"""
    try:
        import tkinter as tk
    except ImportError:
        logger.error("此 Python 未安裝 tkinter，無法啟動 GUI")
        logger.error("請改用 CLI（--channel ...），或安裝對應的 tk 套件（如 Linux 的 python3-tk）")
        return 1

    root = tk.Tk()
    app = YtFetchGUI(root)
    root.after(0, app.maximize_initial_window)
    root.mainloop()
    return 0


def main() -> None:
    sys.exit(launch())


if __name__ == "__main__":
    main()
