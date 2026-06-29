#!/usr/bin/env python3
"""
YouTube 頻道影片下載工具

【需求】
從指定 YouTube 頻道取得最新的 N 支影片並下載為 mp4，儲存到 download/ 資料夾。

【安裝】
1. 確保已安裝 Python 3.7+
2. 執行：python yt_fetch.py --channel "<頻道URL或@handle>"
3. 腳本會自動建立 .venv 並安裝所需套件

【常見錯誤與處理】
- "ffmpeg not found": 腳本會嘗試以 imageio-ffmpeg 自動安裝；若仍失敗則中止，請手動安裝 ffmpeg
- "No videos found": 檢查頻道 URL 是否正確，或嘗試使用 @handle 格式
- "Network error": 檢查網路連線，或使用 --retries 增加重試次數
- "Permission denied": 確保有寫入 download/ 資料夾的權限

【授權提醒】
本工具僅供個人學習與研究使用。下載內容請遵守 YouTube 服務條款與著作權法。
"""

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# 常數
VENV_DIR = Path(__file__).parent / ".venv"
DOWNLOAD_DIR = Path(__file__).parent / "download"
ARCHIVE_FILE = DOWNLOAD_DIR / ".download_archive.txt"


def is_venv() -> bool:
    """檢查是否在虛擬環境中"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def ensure_venv_and_restart():
    """確保在 venv 中，若不在則建立並重新啟動"""
    if is_venv():
        return False  # 已在 venv 中，不需要重啟

    logger.info("未在虛擬環境中，建立 .venv...")

    # 建立 venv
    if sys.platform == "win32":
        venv_python = VENV_DIR / "Scripts" / "python.exe"
        venv_pip = VENV_DIR / "Scripts" / "pip.exe"
    else:
        venv_python = VENV_DIR / "bin" / "python"
        venv_pip = VENV_DIR / "bin" / "pip"

    if not VENV_DIR.exists():
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        logger.info(f"已建立虛擬環境: {VENV_DIR}")

    # 安裝 yt-dlp
    if not venv_pip.exists():
        logger.warning("venv 未完整建立，嘗試重新建立...")
        if VENV_DIR.exists():
            shutil.rmtree(VENV_DIR)
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)

    logger.info("安裝 yt-dlp...")
    subprocess.run([str(venv_pip), "install", "--upgrade", "yt-dlp"], check=True)

    # 安裝 imageio-ffmpeg（自動下載 ffmpeg）
    logger.info("安裝 imageio-ffmpeg（會自動下載 ffmpeg）...")
    try:
        subprocess.run([str(venv_pip), "install", "--upgrade", "imageio-ffmpeg"], check=True)
    except subprocess.CalledProcessError:
        logger.warning("安裝 imageio-ffmpeg 失敗，將在後續步驟中重試")

    # 重新啟動腳本（確保帶入所有原始參數）
    logger.info("以虛擬環境重新啟動腳本...")
    script_path = Path(__file__).resolve()
    # 確保帶入所有原始參數，包括 --channel 等
    cmd = [str(venv_python), str(script_path)] + sys.argv[1:]

    # 使用 subprocess 執行（跨平台兼容）
    try:
        if sys.platform == "win32":
            # Windows: 使用 CREATE_NEW_CONSOLE 確保新進程可見
            subprocess.run(cmd, check=True)
            sys.exit(0)
        else:
            # Unix-like: 使用 execv 替換當前進程
            os.execv(str(venv_python), cmd)
    except Exception as e:
        logger.error(f"重新啟動失敗: {e}")
        logger.error("請手動執行: " + " ".join(cmd))
        sys.exit(1)

    return True  # 理論上不會執行到這裡


def check_ffmpeg() -> bool:
    """檢查系統是否有 ffmpeg"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_ffmpeg() -> Optional[str]:
    """自動安裝 ffmpeg（使用 imageio-ffmpeg）

    Returns:
        ffmpeg 可執行檔的完整路徑，如果安裝失敗則返回 None
    """
    logger.info("嘗試自動安裝 ffmpeg...")

    try:
        # 檢查是否在 venv 中
        if sys.platform == "win32":
            venv_pip = VENV_DIR / "Scripts" / "pip.exe"
        else:
            venv_pip = VENV_DIR / "bin" / "pip"

        # 如果不在 venv，使用系統 pip
        pip_cmd = str(venv_pip) if venv_pip.exists() else [sys.executable, "-m", "pip"]
        if isinstance(pip_cmd, str):
            pip_cmd = [pip_cmd]

        # 安裝 imageio-ffmpeg，它會自動下載 ffmpeg
        logger.info("安裝 imageio-ffmpeg（會自動下載 ffmpeg）...")
        subprocess.run(
            pip_cmd + ["install", "--upgrade", "imageio-ffmpeg"], check=True, capture_output=True
        )

        # 嘗試導入並獲取 ffmpeg 路徑
        try:
            import imageio_ffmpeg

            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            logger.info(f"找到 ffmpeg: {ffmpeg_path}")

            # 驗證 ffmpeg 是否可用（使用完整路徑）
            try:
                subprocess.run(
                    [ffmpeg_path, "-version"], capture_output=True, check=True, timeout=5
                )
                logger.info("✓ ffmpeg 可用（使用完整路徑）")
                # 將 ffmpeg 所在目錄添加到 PATH（僅當前進程）
                ffmpeg_dir = Path(ffmpeg_path).parent
                current_path = os.environ.get("PATH", "")
                if str(ffmpeg_dir) not in current_path:
                    os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + current_path
                    logger.info(f"已將 {ffmpeg_dir} 添加到 PATH")
                # 返回 ffmpeg 完整路徑
                return str(ffmpeg_path)
            except Exception as e:
                logger.error(f"ffmpeg 路徑無效或無法執行: {e}")
                return None
        except ImportError:
            logger.error("無法導入 imageio_ffmpeg")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"安裝 ffmpeg 失敗: {e}")
        return None
    except Exception as e:
        logger.error(f"安裝 ffmpeg 時發生錯誤: {e}")
        return None


def normalize_channel_url(channel: str) -> str:
    """正規化頻道 URL/ID/handle"""
    channel = channel.strip()

    # 如果已經是完整 URL
    if channel.startswith("http"):
        return channel

    # 如果是 @handle 格式
    if channel.startswith("@"):
        return f"https://www.youtube.com/{channel}/videos"

    # 如果是頻道 ID (UC...)
    if channel.startswith("UC") and len(channel) == 24:
        return f"https://www.youtube.com/channel/{channel}/videos"

    # 嘗試作為 handle
    if not channel.startswith("/"):
        return f"https://www.youtube.com/@{channel}/videos"

    return channel


def read_archive_ids() -> set:
    """讀取下載 archive（yt-dlp 格式：`youtube <id>`）中的所有影片 ID。"""
    ids = set()
    if not ARCHIVE_FILE.exists():
        return ids
    try:
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 2:
                        ids.add(parts[1])
    except Exception as e:
        logger.warning(f"讀取 archive 檔案時發生錯誤: {e}")
    return ids


def get_downloaded_ids() -> set:
    """從 archive 檔案和現有檔案中取得已下載的影片 ID"""
    downloaded = read_archive_ids()

    # 從現有檔案名稱中提取 ID
    if DOWNLOAD_DIR.exists():
        pattern = re.compile(r"\[([a-zA-Z0-9_-]{11})\]\.mp4$")
        for file in DOWNLOAD_DIR.glob("*.mp4"):
            match = pattern.search(file.name)
            if match:
                downloaded.add(match.group(1))

    return downloaded


def archive_contains(video_id: str) -> bool:
    """檢查下載 archive 是否已記錄指定影片。"""
    return video_id in read_archive_ids()


def find_downloaded_file(video_id: str, tracked: Optional[str] = None) -> Optional[Path]:
    """找出已下載影片的檔案路徑。

    先採用 progress hook 記錄的檔名，找不到再用檔名中的 `[video_id]` glob。
    """
    if tracked:
        tracked_path = Path(tracked)
        if tracked_path.exists():
            return tracked_path
    # 注意：不可用 glob 的 f"* [{id}].mp4"，因為 [] 會被當成字元類別，
    # 無法比對檔名中字面的中括號；改以結尾字串比對。
    suffix = f"[{video_id}].mp4"
    matches = [p for p in DOWNLOAD_DIR.glob("*.mp4") if p.name.endswith(suffix)]
    return matches[0] if matches else None


def filter_downloadable_entries(entries: List[Dict], downloaded_ids: set) -> Dict:
    """從頻道影片清單篩出可下載的項目（排除直播/預告、非公開、已下載）。

    Shorts 不在此處理，留待 yt-dlp 的 match_filter 於實際下載時過濾。

    Returns:
        dict，含 keys: entries（可下載清單）、skipped_live、skipped_public。
    """
    filtered: List[Dict] = []
    skipped_live = 0
    skipped_public = 0
    for entry in entries:
        video_id = entry.get("id")
        if not video_id:
            continue

        # 排除直播與預告（只下載 VOD / 一般影片）
        live_status = str(entry.get("live_status") or "").lower()
        if live_status in ("is_live", "is_upcoming", "was_live"):
            skipped_live += 1
            logger.debug(f"跳過直播/預告影片 (live_status={live_status}): {video_id}")
            continue

        # 只下載公開影片
        if not is_public_video(entry):
            skipped_public += 1
            continue

        # 跳過已下載
        if video_id in downloaded_ids:
            logger.debug(f"跳過已下載: {video_id}")
            continue

        filtered.append(entry)

    return {
        "entries": filtered,
        "skipped_live": skipped_live,
        "skipped_public": skipped_public,
    }


def build_channel_urls(channel_url: str, include_shorts: bool) -> List[str]:
    """根據頻道 URL 與是否包含 Shorts，組出要提取的頁面 URL 清單。

    YouTube 自 2022 起把頻道分為 Videos / Shorts / Live 分頁；`/videos` 只含長片、
    `/shorts` 只含 Shorts。若輸入已是 playlist 或已指定特定分頁，則原樣使用。
    """
    if "/playlist" in channel_url or "/videos" in channel_url or "/shorts" in channel_url:
        return [channel_url]

    base_url = channel_url.rstrip("/")
    if include_shorts:
        return [f"{base_url}/videos", f"{base_url}/shorts"]
    return [f"{base_url}/videos"]


def filter_reason(info_dict: Dict, include_shorts: bool) -> Optional[str]:
    """判斷影片是否應被排除（供 yt-dlp 的 match_filter 使用）。

    Args:
        info_dict: yt-dlp 提供的影片資訊字典
        include_shorts: 是否包含 Shorts

    Returns:
        排除原因字串；若應接受該影片則回傳 None。
    """
    # 排除非公開影片
    availability = info_dict.get("availability")
    if availability and availability != "public":
        return "非公開影片"

    if not include_shorts:
        # 以 URL 是否包含 /shorts/ 為主要判斷依據
        url = info_dict.get("url", "") or info_dict.get("webpage_url", "")
        if "/shorts/" in str(url).lower():
            return "Shorts 影片（URL 包含 /shorts/）"

        # 時長 < 60 秒且標題/描述含 "shorts" 才視為 Shorts，
        # 避免誤殺合法的短篇一般影片。
        duration = info_dict.get("duration")
        if duration and duration < 60:
            title = str(info_dict.get("title", "")).lower()
            description = str(info_dict.get("description", "")).lower()
            if "shorts" in title or "shorts" in description:
                return f"Shorts 影片（時長 {duration} 秒且標題/描述包含 shorts）"

    return None


def is_public_video(entry: Dict) -> bool:
    """
    檢查影片是否為公開影片

    Args:
        entry: yt-dlp 提取的影片資訊字典

    Returns:
        True 如果影片是公開的，False 否則
    """
    if not entry:
        return False

    video_id = entry.get("id", "unknown")

    # 檢查 availability 欄位（最可靠的判斷方式）
    availability = entry.get("availability")
    if availability:
        # 只接受 'public' 狀態，排除所有其他狀態
        if availability != "public":
            logger.debug(f"跳過非公開影片 (availability={availability}): {video_id}")
            return False

    # 如果沒有明確的 availability 欄位，進行其他檢查
    # 檢查是否有 ID（沒有 ID 可能表示無法存取）
    if not video_id or video_id == "unknown":
        return False

    # 檢查是否有標題（沒有標題可能表示無法存取）
    if not entry.get("title"):
        logger.debug(f"跳過無標題影片（可能無法存取）: {video_id}")
        return False

    # 如果沒有明確標記為非公開，且基本資訊完整，認為是公開的
    return True


def prompt_user_input():
    """以輸入視窗詢問用戶參數"""
    print("\n" + "=" * 60)
    print("YouTube 頻道影片下載工具")
    print("=" * 60)
    print()

    # 詢問頻道
    print("請輸入要下載的 YouTube 頻道：")
    print("格式範例：@channel_handle")
    print("也可以輸入完整 URL 或頻道 ID")
    channel = input("頻道: ").strip()

    if not channel:
        logger.error("未輸入頻道，程式結束")
        sys.exit(1)

    # 詢問目標檔案數
    print("\n請輸入要下載的影片數量（預設：5）：")
    count_input = input("數量: ").strip()
    try:
        count = int(count_input) if count_input else 5
        if count < 1:
            logger.warning("數量必須大於 0，使用預設值 5")
            count = 5
    except ValueError:
        logger.warning("無效的數量，使用預設值 5")
        count = 5

    # 詢問是否包含 Shorts
    print("\n是否包含 Shorts？(y/n，預設：n)：")
    include_shorts_input = input("包含 Shorts: ").strip().lower()
    include_shorts = include_shorts_input in ("y", "yes", "1", "true")

    # 詢問重試次數
    print("\n請輸入重試次數（預設：3）：")
    retries_input = input("重試次數: ").strip()
    try:
        retries = int(retries_input) if retries_input else 3
        if retries < 1:
            retries = 3
    except ValueError:
        retries = 3

    return {
        "channel": channel,
        "count": count,
        "include_shorts": include_shorts,
        "retries": retries,
    }


def parse_args():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="從 YouTube 頻道下載最新影片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--channel",
        type=str,
        default=os.getenv("YOUTUBE_CHANNEL"),
        help="頻道 URL、ID 或 @handle（也可用環境變數 YOUTUBE_CHANNEL）。如果未提供，會以輸入視窗詢問",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=int(os.getenv("YOUTUBE_COUNT", "5")),
        help="下載數量（預設：5，也可用環境變數 YOUTUBE_COUNT）",
    )

    parser.add_argument(
        "--include-shorts",
        action="store_true",
        default=os.getenv("YOUTUBE_INCLUDE_SHORTS", "").lower() in ("1", "true", "yes"),
        help="包含 Shorts（預設排除，也可用環境變數 YOUTUBE_INCLUDE_SHORTS=1）",
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=int(os.getenv("YOUTUBE_RETRIES", "3")),
        help="重試次數（預設：3，也可用環境變數 YOUTUBE_RETRIES）",
    )

    parser.add_argument(
        "--cookies-from-browser",
        type=str,
        default=os.getenv("YOUTUBE_COOKIES_BROWSER", ""),
        help="從瀏覽器讀取 cookies（例如：chrome, firefox, edge）。也可用環境變數 YOUTUBE_COOKIES_BROWSER",
    )

    parser.add_argument(
        "--cookies",
        type=str,
        default=os.getenv("YOUTUBE_COOKIES_FILE", ""),
        help="cookies 檔案路徑（Netscape 格式）。也可用環境變數 YOUTUBE_COOKIES_FILE",
    )

    parser.add_argument(
        "--ratelimit",
        type=float,
        default=float(os.getenv("YOUTUBE_RATELIMIT", "0")),
        help="下載速率限制（MB/s，0 表示無限制）。也可用環境變數 YOUTUBE_RATELIMIT",
    )

    parser.add_argument(
        "--sleep",
        type=float,
        default=float(os.getenv("YOUTUBE_SLEEP", "0")),
        help="每次下載之間的延遲秒數（減少被限流）。也可用環境變數 YOUTUBE_SLEEP",
    )

    args = parser.parse_args()

    # 如果沒有提供 channel，以輸入視窗詢問所有參數
    if not args.channel:
        user_input = prompt_user_input()
        args.channel = user_input["channel"]
        args.count = user_input["count"]
        args.include_shorts = user_input["include_shorts"]
        args.retries = user_input["retries"]

    if args.count < 1:
        parser.error("--count 必須大於 0")

    return args


def download_videos(  # noqa: C901
    channel_url: str,
    count: int,
    include_shorts: bool,
    retries: int,
    cookies_from_browser: str = "",
    cookies_file: str = "",
    ratelimit: float = 0,
    sleep_seconds: float = 0,
) -> List[Dict]:
    """下載影片主函數"""
    try:
        import yt_dlp
    except ImportError:
        logger.error("無法匯入 yt-dlp，請確認已正確安裝")
        sys.exit(1)

    # 確保下載目錄存在
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 取得已下載的 ID（全域；用於下載時跳過已存在的影片）
    # 注意：existing_count / remaining_count 會在取得「本頻道」影片清單後再計算，
    # 以本頻道實際重疊的影片數量為準，避免被其他頻道的下載紀錄干擾。
    downloaded_ids = get_downloaded_ids()
    logger.info(f"資料夾內已有 {len(downloaded_ids)} 支影片（從 archive 和檔案名稱判斷）")

    # 檢查 ffmpeg（必須），如果沒有則嘗試自動安裝
    ffmpeg_path = None
    has_ffmpeg = check_ffmpeg()

    if not has_ffmpeg:
        logger.warning("未偵測到 ffmpeg，嘗試自動安裝...")
        ffmpeg_path = install_ffmpeg()
        if ffmpeg_path:
            # 安裝成功，使用返回的路徑
            has_ffmpeg = True
            logger.info(f"將使用 ffmpeg: {ffmpeg_path}")
        else:
            # 安裝失敗，再次檢查 PATH（可能用戶手動安裝了）
            has_ffmpeg = check_ffmpeg()

    if not has_ffmpeg:
        logger.error("未偵測到 ffmpeg，且自動安裝失敗")
        logger.error("安裝指引:")
        logger.error("  Windows: choco install ffmpeg 或從 https://ffmpeg.org/download.html 下載")
        logger.error("  macOS: brew install ffmpeg")
        logger.error("  Linux: sudo apt-get install ffmpeg 或 sudo yum install ffmpeg")
        logger.error("或腳本會嘗試使用 imageio-ffmpeg 自動下載")
        sys.exit(2)

    # 準備 yt-dlp 選項（有 ffmpeg：優先最佳畫質+音質，合併為 mp4）
    format_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best"
    merge_format = "mp4"

    # 準備 progress hook 來追蹤下載的檔案
    downloaded_files = {}  # video_id -> filepath

    def progress_hook(d):
        """追蹤下載進度並記錄實際檔名"""
        if d.get("status") == "finished":
            # 從 info_dict 獲取 video_id
            info_dict = d.get("info_dict", {})
            video_id = info_dict.get("id")
            # 從 d 直接獲取 filename（yt-dlp 會在 finished 時提供）
            filename = d.get("filename")
            if video_id and filename:
                downloaded_files[video_id] = filename
                logger.debug(f"記錄下載檔案: {video_id} -> {filename}")

    # 建立 match_filter 來過濾 Shorts（預設排除），實際判斷委派給 filter_reason
    def match_filter(info_dict):
        return filter_reason(info_dict, include_shorts)

    # 計算需要提取的影片數量（比目標數量更多，以備過濾）
    # 考慮到可能有大量不符合條件的影片（會員影片、非公開、Shorts等）
    # 使用「目標數量 * 5」與 50 取最小值，避免提取過多又確保有足夠候選
    playlist_extract_count = min(count * 5, 50)

    ydl_opts = {
        "format": format_str,
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s"),
        "merge_output_format": merge_format,
        "noplaylist": False,
        "extract_flat": False,
        "ignoreerrors": True,
        "no_warnings": False,
        "quiet": False,
        "retries": retries,
        "fragment_retries": retries,
        "file_access_retries": retries,
        "download_archive": str(ARCHIVE_FILE),
        "writesubtitles": False,
        "writeautomaticsub": False,
        "progress_hooks": [progress_hook],
        # 限制播放清單提取數量，避免掃到太多筆被限流
        # 提取比目標數量更多的影片，以備過濾（非公開、Shorts、已下載等）
        "playlistend": playlist_extract_count,
        # 使用 match_filter 過濾 Shorts
        "match_filter": match_filter if not include_shorts else None,
    }

    # 如果指定了 ffmpeg 路徑，傳遞給 yt-dlp
    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = ffmpeg_path
        logger.info(f"yt-dlp 將使用指定的 ffmpeg: {ffmpeg_path}")

    # 添加 cookies 支援
    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)
        logger.info(f"使用瀏覽器 cookies: {cookies_from_browser}")
    elif cookies_file:
        ydl_opts["cookiefile"] = cookies_file
        logger.info(f"使用 cookies 檔案: {cookies_file}")

    # 添加速率限制
    if ratelimit > 0:
        # yt-dlp 的 ratelimit 單位是 bytes/s，需要轉換
        ydl_opts["ratelimit"] = int(ratelimit * 1024 * 1024)  # MB/s 轉 bytes/s
        logger.info(f"下載速率限制: {ratelimit} MB/s")

    # 構建頻道 URL（根據是否包含 Shorts 決定從哪些頁面獲取）
    # 註：/videos、/shorts 分頁本身即依最新排序，毋需附加 view/sort 等已失效的 query 參數
    channel_urls = build_channel_urls(channel_url, include_shorts)
    if include_shorts and len(channel_urls) > 1:
        logger.info("將從 Videos 和 Shorts 兩個頁面獲取影片")

    logger.info(f"開始處理頻道: {', '.join(channel_urls)}")
    logger.info(f"目標數量: {count}, 包含 Shorts: {include_shorts}, 重試次數: {retries}")

    downloaded_list = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 先提取播放清單資訊（不實際下載）
            # 如果包含 Shorts，需要從多個頁面獲取並合併
            all_entries = []

            for url in channel_urls:
                logger.info(
                    f"提取頻道影片清單: {url}（限制前 {playlist_extract_count} 支以避免限流）..."
                )
                try:
                    info = ydl.extract_info(url, download=False)

                    if info and "entries" in info:
                        url_entries = [e for e in info.get("entries", []) if e is not None]
                        all_entries.extend(url_entries)
                        logger.info(f"從 {url} 獲取到 {len(url_entries)} 支影片")
                    else:
                        logger.warning(f"無法從 {url} 取得影片資訊")
                except Exception as e:
                    logger.warning(f"從 {url} 提取影片時發生錯誤: {e}")
                    continue

            if not all_entries:
                logger.error("無法取得頻道資訊，請確認頻道 URL 是否正確")
                sys.exit(1)

            # 合併所有頁面的影片，並去重（根據 video_id）
            seen_ids = set()
            entries = []
            for entry in all_entries:
                video_id = entry.get("id")
                if video_id and video_id not in seen_ids:
                    seen_ids.add(video_id)
                    entries.append(entry)

            logger.info(f"合併後共找到 {len(entries)} 支不重複影片")

            if not entries:
                logger.warning("頻道中沒有找到影片")
                return []

            # 以「本頻道」實際重疊的影片數量計算下載目標，
            # 避免被其他頻道的下載紀錄影響（--count 是本頻道的最新 N 支）。
            existing_count = sum(1 for e in entries if e.get("id") in downloaded_ids)
            remaining_count = max(0, count - existing_count)
            logger.info(
                f"本頻道已下載 {existing_count} 支，目標 {count} 支，還需下載 {remaining_count} 支"
            )

            if remaining_count == 0:
                logger.info(f"已達到本頻道目標數量 {count} 支，無需下載新影片")
                return []

            logger.info(f"找到 {len(entries)} 支影片，開始篩選...")

            # 過濾已下載、非公開影片與直播（Shorts 由 match_filter 於下載時處理）
            result = filter_downloadable_entries(entries, downloaded_ids)
            entries_to_download = result["entries"]

            if result["skipped_public"] > 0:
                logger.info(f"已跳過 {result['skipped_public']} 支非公開影片（僅下載公開影片）")
            if result["skipped_live"] > 0:
                logger.info(f"已跳過 {result['skipped_live']} 支直播/預告影片（只下載 VOD）")

            if not entries_to_download:
                logger.info("沒有需要下載的新影片")
                return []

            logger.info(
                f"找到 {len(entries_to_download)} 支可下載影片，目標下載 {remaining_count} 支新影片（總目標 {count} 支，已有 {existing_count} 支）..."
            )

            # 逐一下載，直到達到目標數量或沒有更多影片
            # downloaded_count 從 0 開始，表示本次下載的新影片數量
            downloaded_count = 0
            for i, entry in enumerate(entries_to_download, 1):
                # 如果已達到目標數量（已下載的新影片數量 >= 還需下載的數量），停止下載
                if downloaded_count >= remaining_count:
                    logger.info(
                        f"已達到目標下載數量 {count} 支（原有 {existing_count} 支 + 新下載 {downloaded_count} 支），停止下載"
                    )
                    break

                video_id = entry.get("id")
                if not video_id:
                    logger.warning(f"跳過無 ID 的影片: {entry.get('title', 'Unknown')}")
                    continue

                # 永遠使用 watch URL，不要使用 entry.get('url')（可能是 m3u8）
                video_url = (
                    entry.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"
                )
                title = entry.get("title", "Unknown")

                total_current = existing_count + downloaded_count
                logger.info(
                    f"[{i}/{len(entries_to_download)}] 下載 ({downloaded_count}/{remaining_count} 新影片, 總計 {total_current}/{count}): {title[:60]}..."
                )

                # 清除舊的追蹤記錄後實際下載（使用 watch URL）
                downloaded_files.pop(video_id, None)
                try:
                    ydl.download([video_url])
                except Exception as e:
                    logger.error(f"下載失敗 {video_id}: {e}")
                    continue

                # 判斷是否成功：archive 已記錄、或檔案已存在皆視為成功
                file_path_obj = find_downloaded_file(video_id, downloaded_files.get(video_id))
                if not (archive_contains(video_id) or file_path_obj):
                    # 下載失敗或被 match_filter 過濾（例如 Shorts）
                    logger.warning(f"下載失敗或被過濾: {video_id} ({title[:60]})")
                    continue

                downloaded_count += 1
                downloaded_list.append(
                    {
                        "title": title,
                        "id": video_id,
                        "path": str(file_path_obj) if file_path_obj else "",
                        "duration": entry.get("duration", 0),
                    }
                )
                total_current = existing_count + downloaded_count
                done_name = file_path_obj.name if file_path_obj else video_id
                logger.info(
                    f"✓ 完成 ({downloaded_count}/{remaining_count} 新影片, 總計 {total_current}/{count}): {done_name}"
                )

                # 已達到目標數量，立即停止
                if downloaded_count >= remaining_count:
                    logger.info(
                        f"已達到目標下載數量 {count} 支（原有 {existing_count} 支 + 新下載 {downloaded_count} 支），停止下載"
                    )
                    break

                # 如果設定了 sleep，在下載之間延遲
                if sleep_seconds > 0 and i < len(entries_to_download):
                    logger.debug(f"等待 {sleep_seconds} 秒以避免限流...")
                    time.sleep(sleep_seconds)

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if (
            "Private video" in error_msg
            or "This video is unavailable" in error_msg
            or "Video unavailable" in error_msg
        ):
            logger.warning("偵測到可能無法合法下載的內容，安全退出")
            logger.warning("請確認頻道是否為公開，以及您是否有權限存取這些影片")
            sys.exit(0)
        elif "ffmpeg" in error_msg.lower() or "postprocessor" in error_msg.lower():
            logger.error(f"ffmpeg 處理錯誤: {e}")
            logger.error("請確認 ffmpeg 已正確安裝並在 PATH 中")
            sys.exit(1)
        elif "format" in error_msg.lower() and "not available" in error_msg.lower():
            logger.error(f"格式錯誤: {e}")
            logger.error("請確認 ffmpeg 已正確安裝")
            sys.exit(1)
        else:
            logger.error(f"下載錯誤: {e}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"未預期的錯誤: {e}", exc_info=True)
        sys.exit(1)

    return downloaded_list


def main():
    """主函數"""
    logger.info("=" * 60)
    logger.info("YouTube 頻道影片下載工具")
    logger.info("=" * 60)

    # 確保在 venv 中
    if ensure_venv_and_restart():
        return  # 已重新啟動，此執行結束

    # 解析參數
    args = parse_args()

    # 正規化頻道 URL
    channel_url = normalize_channel_url(args.channel)

    logger.info(f"頻道: {channel_url}")
    logger.info(f"數量: {args.count}")
    logger.info(f"包含 Shorts: {args.include_shorts}")
    logger.info(f"重試次數: {args.retries}")
    if args.cookies_from_browser:
        logger.info(f"使用瀏覽器 cookies: {args.cookies_from_browser}")
    elif args.cookies:
        logger.info(f"使用 cookies 檔案: {args.cookies}")
    if args.ratelimit > 0:
        logger.info(f"下載速率限制: {args.ratelimit} MB/s")
    if args.sleep > 0:
        logger.info(f"下載間隔: {args.sleep} 秒")

    # 下載影片
    downloaded_list = download_videos(
        channel_url,
        args.count,
        args.include_shorts,
        args.retries,
        args.cookies_from_browser,
        args.cookies,
        args.ratelimit,
        args.sleep,
    )

    # 輸出結果
    logger.info("=" * 60)
    logger.info("下載完成")
    logger.info("=" * 60)

    if downloaded_list:
        logger.info(f"\n實際下載清單（共 {len(downloaded_list)} 支）:")
        for i, item in enumerate(downloaded_list, 1):
            duration_str = f"{int(item['duration'])} 秒" if item["duration"] else "未知"
            logger.info(f"\n{i}. 標題: {item['title']}")
            logger.info(f"   ID: {item['id']}")
            logger.info(f"   路徑: {item['path']}")
            logger.info(f"   時長: {duration_str}")
    else:
        logger.info("沒有新影片下載（可能已全部下載過）")

    logger.info("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
