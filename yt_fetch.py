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
- "ffmpeg not found": 安裝 ffmpeg 或腳本會嘗試回退到 progressive mp4
- "No videos found": 檢查頻道 URL 是否正確，或嘗試使用 @handle 格式
- "Network error": 檢查網路連線，或使用 --retries 增加重試次數
- "Permission denied": 確保有寫入 download/ 資料夾的權限

【授權提醒】
本工具僅供個人學習與研究使用。下載內容請遵守 YouTube 服務條款與著作權法。
"""

import os
import sys
import subprocess
import shutil
import argparse
import logging
import json
import re
import time
from pathlib import Path
from typing import Optional, List, Dict, Tuple

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 常數
VENV_DIR = Path(__file__).parent / '.venv'
DOWNLOAD_DIR = Path(__file__).parent / 'download'
ARCHIVE_FILE = DOWNLOAD_DIR / '.download_archive.txt'


def is_venv() -> bool:
    """檢查是否在虛擬環境中"""
    return (hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))


def ensure_venv_and_restart():
    """確保在 venv 中，若不在則建立並重新啟動"""
    if is_venv():
        return False  # 已在 venv 中，不需要重啟
    
    logger.info("未在虛擬環境中，建立 .venv...")
    
    # 建立 venv
    if sys.platform == 'win32':
        venv_python = VENV_DIR / 'Scripts' / 'python.exe'
        venv_pip = VENV_DIR / 'Scripts' / 'pip.exe'
    else:
        venv_python = VENV_DIR / 'bin' / 'python'
        venv_pip = VENV_DIR / 'bin' / 'pip'
    
    if not VENV_DIR.exists():
        subprocess.run([sys.executable, '-m', 'venv', str(VENV_DIR)], check=True)
        logger.info(f"已建立虛擬環境: {VENV_DIR}")
    
    # 安裝 yt-dlp
    if not venv_pip.exists():
        logger.warning("venv 未完整建立，嘗試重新建立...")
        if VENV_DIR.exists():
            shutil.rmtree(VENV_DIR)
        subprocess.run([sys.executable, '-m', 'venv', str(VENV_DIR)], check=True)
    
    logger.info("安裝 yt-dlp...")
    subprocess.run([str(venv_pip), 'install', '--upgrade', 'yt-dlp'], check=True)
    
    # 安裝 imageio-ffmpeg（自動下載 ffmpeg）
    logger.info("安裝 imageio-ffmpeg（會自動下載 ffmpeg）...")
    try:
        subprocess.run([str(venv_pip), 'install', '--upgrade', 'imageio-ffmpeg'], check=True)
    except subprocess.CalledProcessError:
        logger.warning("安裝 imageio-ffmpeg 失敗，將在後續步驟中重試")
    
    # 重新啟動腳本（確保帶入所有原始參數）
    logger.info("以虛擬環境重新啟動腳本...")
    script_path = Path(__file__).resolve()
    # 確保帶入所有原始參數，包括 --channel 等
    cmd = [str(venv_python), str(script_path)] + sys.argv[1:]
    
    # 使用 subprocess 執行（跨平台兼容）
    try:
        if sys.platform == 'win32':
            # Windows: 使用 CREATE_NEW_CONSOLE 確保新進程可見
            subprocess.run(cmd, check=True)
            sys.exit(0)
        else:
            # Unix-like: 使用 execv 替換當前進程
            os.execv(str(venv_python), cmd)
    except Exception as e:
        logger.error(f"重新啟動失敗: {e}")
        logger.error("請手動執行: " + ' '.join(cmd))
        sys.exit(1)
    
    return True  # 理論上不會執行到這裡


def check_ffmpeg() -> bool:
    """檢查系統是否有 ffmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, 
                      check=True,
                      timeout=5)
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
        if sys.platform == 'win32':
            venv_pip = VENV_DIR / 'Scripts' / 'pip.exe'
        else:
            venv_pip = VENV_DIR / 'bin' / 'pip'
        
        # 如果不在 venv，使用系統 pip
        pip_cmd = str(venv_pip) if venv_pip.exists() else [sys.executable, '-m', 'pip']
        if isinstance(pip_cmd, str):
            pip_cmd = [pip_cmd]
        
        # 安裝 imageio-ffmpeg，它會自動下載 ffmpeg
        logger.info("安裝 imageio-ffmpeg（會自動下載 ffmpeg）...")
        subprocess.run(pip_cmd + ['install', '--upgrade', 'imageio-ffmpeg'], 
                      check=True, 
                      capture_output=True)
        
        # 嘗試導入並獲取 ffmpeg 路徑
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            logger.info(f"找到 ffmpeg: {ffmpeg_path}")
            
            # 驗證 ffmpeg 是否可用（使用完整路徑）
            try:
                subprocess.run([ffmpeg_path, '-version'], 
                              capture_output=True, 
                              check=True,
                              timeout=5)
                logger.info("✓ ffmpeg 可用（使用完整路徑）")
                # 將 ffmpeg 所在目錄添加到 PATH（僅當前進程）
                ffmpeg_dir = Path(ffmpeg_path).parent
                current_path = os.environ.get('PATH', '')
                if str(ffmpeg_dir) not in current_path:
                    os.environ['PATH'] = str(ffmpeg_dir) + os.pathsep + current_path
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
    if channel.startswith('http'):
        return channel
    
    # 如果是 @handle 格式
    if channel.startswith('@'):
        return f'https://www.youtube.com/{channel}/videos'
    
    # 如果是頻道 ID (UC...)
    if channel.startswith('UC') and len(channel) == 24:
        return f'https://www.youtube.com/channel/{channel}/videos'
    
    # 嘗試作為 handle
    if not channel.startswith('/'):
        return f'https://www.youtube.com/@{channel}/videos'
    
    return channel


def get_downloaded_ids() -> set:
    """從 archive 檔案和現有檔案中取得已下載的影片 ID"""
    downloaded = set()
    
    # 從 archive 檔案讀取
    if ARCHIVE_FILE.exists():
        try:
            with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # yt-dlp archive 格式：youtube <id>
                        parts = line.split()
                        if len(parts) >= 2:
                            downloaded.add(parts[1])
        except Exception as e:
            logger.warning(f"讀取 archive 檔案時發生錯誤: {e}")
    
    # 從現有檔案名稱中提取 ID
    if DOWNLOAD_DIR.exists():
        pattern = re.compile(r'\[([a-zA-Z0-9_-]{11})\]\.mp4$')
        for file in DOWNLOAD_DIR.glob('*.mp4'):
            match = pattern.search(file.name)
            if match:
                downloaded.add(match.group(1))
    
    return downloaded


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
    
    video_id = entry.get('id', 'unknown')
    
    # 檢查 availability 欄位（最可靠的判斷方式）
    availability = entry.get('availability')
    if availability:
        # 只接受 'public' 狀態，排除所有其他狀態
        if availability != 'public':
            logger.debug(f"跳過非公開影片 (availability={availability}): {video_id}")
            return False
    
    # 如果沒有明確的 availability 欄位，進行其他檢查
    # 檢查是否有 ID（沒有 ID 可能表示無法存取）
    if not video_id or video_id == 'unknown':
        return False
    
    # 檢查是否有標題（沒有標題可能表示無法存取）
    if not entry.get('title'):
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
    include_shorts = include_shorts_input in ('y', 'yes', '1', 'true')
    
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
        'channel': channel,
        'count': count,
        'include_shorts': include_shorts,
        'retries': retries
    }
def parse_args():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description='從 YouTube 頻道下載最新影片',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--channel',
        type=str,
        default=os.getenv('YOUTUBE_CHANNEL'),
        help='頻道 URL、ID 或 @handle（也可用環境變數 YOUTUBE_CHANNEL）。如果未提供，會以輸入視窗詢問'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=int(os.getenv('YOUTUBE_COUNT', '5')),
        help='下載數量（預設：5，也可用環境變數 YOUTUBE_COUNT）'
    )
    
    parser.add_argument(
        '--include-shorts',
        action='store_true',
        default=os.getenv('YOUTUBE_INCLUDE_SHORTS', '').lower() in ('1', 'true', 'yes'),
        help='包含 Shorts（預設排除，也可用環境變數 YOUTUBE_INCLUDE_SHORTS=1）'
    )
    
    parser.add_argument(
        '--retries',
        type=int,
        default=int(os.getenv('YOUTUBE_RETRIES', '3')),
        help='重試次數（預設：3，也可用環境變數 YOUTUBE_RETRIES）'
    )
    
    parser.add_argument(
        '--cookies-from-browser',
        type=str,
        default=os.getenv('YOUTUBE_COOKIES_BROWSER', ''),
        help='從瀏覽器讀取 cookies（例如：chrome, firefox, edge）。也可用環境變數 YOUTUBE_COOKIES_BROWSER'
    )
    
    parser.add_argument(
        '--cookies',
        type=str,
        default=os.getenv('YOUTUBE_COOKIES_FILE', ''),
        help='cookies 檔案路徑（Netscape 格式）。也可用環境變數 YOUTUBE_COOKIES_FILE'
    )
    
    parser.add_argument(
        '--ratelimit',
        type=float,
        default=float(os.getenv('YOUTUBE_RATELIMIT', '0')),
        help='下載速率限制（MB/s，0 表示無限制）。也可用環境變數 YOUTUBE_RATELIMIT'
    )
    
    parser.add_argument(
        '--sleep',
        type=float,
        default=float(os.getenv('YOUTUBE_SLEEP', '0')),
        help='每次下載之間的延遲秒數（減少被限流）。也可用環境變數 YOUTUBE_SLEEP'
    )
    
    args = parser.parse_args()
    
    # 如果沒有提供 channel，以輸入視窗詢問所有參數
    if not args.channel:
        user_input = prompt_user_input()
        args.channel = user_input['channel']
        args.count = user_input['count']
        args.include_shorts = user_input['include_shorts']
        args.retries = user_input['retries']
    
    if args.count < 1:
        parser.error('--count 必須大於 0')
    
    return args


def download_videos(
    channel_url: str, 
    count: int, 
    include_shorts: bool, 
    retries: int,
    cookies_from_browser: str = '',
    cookies_file: str = '',
    ratelimit: float = 0,
    sleep_seconds: float = 0
) -> List[Dict]:
    """下載影片主函數"""
    try:
        import yt_dlp
    except ImportError:
        logger.error("無法匯入 yt-dlp，請確認已正確安裝")
        sys.exit(1)
    
    # 確保下載目錄存在
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # 取得已下載的 ID
    downloaded_ids = get_downloaded_ids()
    existing_count = len(downloaded_ids)
    logger.info(f"資料夾內已有 {existing_count} 支影片（從 archive 和檔案名稱判斷）")
    
    # 計算需要下載的數量（目標數量 - 已存在的數量）
    # 如果已存在的數量 >= 目標數量，則不需要下載
    remaining_count = max(0, count - existing_count)
    
    if remaining_count == 0:
        logger.info(f"已達到目標數量 {count} 支（已有 {existing_count} 支），無需下載新影片")
        return []
    
    logger.info(f"目標下載 {count} 支，已有 {existing_count} 支，還需下載 {remaining_count} 支")
    
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
    format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best'
    merge_format = 'mp4'
    
    # 準備 progress hook 來追蹤下載的檔案
    downloaded_files = {}  # video_id -> filepath
    
    def progress_hook(d):
        """追蹤下載進度並記錄實際檔名"""
        if d.get('status') == 'finished':
            # 從 info_dict 獲取 video_id
            info_dict = d.get('info_dict', {})
            video_id = info_dict.get('id')
            # 從 d 直接獲取 filename（yt-dlp 會在 finished 時提供）
            filename = d.get('filename')
            if video_id and filename:
                downloaded_files[video_id] = filename
                logger.debug(f"記錄下載檔案: {video_id} -> {filename}")
    
    # 建立 match_filter 來過濾 Shorts（預設排除）
    def match_filter(info_dict):
        """過濾影片的 match_filter 函數
        返回 None 表示接受，返回字符串表示拒絕
        """
        # 檢查是否為公開影片
        availability = info_dict.get('availability')
        if availability and availability != 'public':
            return '非公開影片'
        
        # 如果不需要包含 Shorts，過濾掉 Shorts
        if not include_shorts:
            # 檢查 URL 是否包含 /shorts/
            url = info_dict.get('url', '') or info_dict.get('webpage_url', '')
            if '/shorts/' in str(url).lower():
                return 'Shorts 影片（URL 包含 /shorts/）'
            
            # 檢查時長（Shorts 通常 < 60 秒）
            duration = info_dict.get('duration')
            if duration and duration is not None and duration < 60:
                # 額外檢查標題或描述是否包含 "shorts"
                title = str(info_dict.get('title', '')).lower()
                description = str(info_dict.get('description', '')).lower()
                if 'shorts' in title or 'shorts' in description:
                    return f'Shorts 影片（時長 {duration} 秒且標題/描述包含 shorts）'
                # 如果時長 < 60 秒但沒有明確標記為 shorts，也過濾掉（保守策略，避免誤下載 Shorts）
                return f'Shorts 影片（時長 {duration} 秒，預設排除）'
        
        return None  # 返回 None 表示接受此影片
    
    # 計算需要提取的影片數量（比目標數量更多，以備過濾）
    # 考慮到可能有大量不符合條件的影片（會員影片、非公開、Shorts等）
    # 使用「需新下載數量 * 5」與 50 取最小值，避免提取過多又確保有足夠候選
    playlist_extract_count = min(remaining_count * 5, 50) if remaining_count > 0 else 0
    
    ydl_opts = {
        'format': format_str,
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s [%(id)s].%(ext)s'),
        'merge_output_format': merge_format,
        'noplaylist': False,
        'extract_flat': False,
        'ignoreerrors': True,
        'no_warnings': False,
        'quiet': False,
        'retries': retries,
        'fragment_retries': retries,
        'file_access_retries': retries,
        'download_archive': str(ARCHIVE_FILE),
        'writesubtitles': False,
        'writeautomaticsub': False,
        'progress_hooks': [progress_hook],
        # 限制播放清單提取數量，避免掃到太多筆被限流
        # 提取比目標數量更多的影片，以備過濾（非公開、Shorts、已下載等）
        'playlistend': playlist_extract_count,
        # 使用 match_filter 過濾 Shorts
        'match_filter': match_filter if not include_shorts else None,
    }
    
    # 如果指定了 ffmpeg 路徑，傳遞給 yt-dlp
    if ffmpeg_path:
        ydl_opts['ffmpeg_location'] = ffmpeg_path
        logger.info(f"yt-dlp 將使用指定的 ffmpeg: {ffmpeg_path}")
    
    # 添加 cookies 支援
    if cookies_from_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_from_browser,)
        logger.info(f"使用瀏覽器 cookies: {cookies_from_browser}")
    elif cookies_file:
        ydl_opts['cookiefile'] = cookies_file
        logger.info(f"使用 cookies 檔案: {cookies_file}")
    
    # 添加速率限制
    if ratelimit > 0:
        # yt-dlp 的 ratelimit 單位是 bytes/s，需要轉換
        ydl_opts['ratelimit'] = int(ratelimit * 1024 * 1024)  # MB/s 轉 bytes/s
        logger.info(f"下載速率限制: {ratelimit} MB/s")
    
    # 過濾 Shorts（在提取階段處理，不在 match_filter 中）
    # match_filter 會在實際下載時才執行，我們在提取清單後手動過濾更可靠
    
    # 構建頻道 URL（根據是否包含 Shorts 決定從哪些頁面獲取）
    # YouTube 從 2022 年起將頻道分為 Videos、Shorts、Live 三個分頁
    # /videos 只包含長片，/shorts 只包含 Shorts
    original_url = channel_url
    
    # 如果已經是播放清單 URL，直接使用
    if '/playlist' in channel_url:
        channel_urls = [channel_url]  # 保持原樣
    elif '/videos' in channel_url or '/shorts' in channel_url:
        # 如果已經指定了特定頁面，直接使用
        channel_urls = [channel_url]
    else:
        # 根據 include_shorts 決定從哪些頁面獲取
        base_url = channel_url.rstrip('/')
        if base_url.endswith('/'):
            base_url = base_url.rstrip('/')
        
        if include_shorts:
            # 包含 Shorts：需要從 /videos 和 /shorts 兩個頁面獲取
            videos_url = f"{base_url}/videos"
            shorts_url = f"{base_url}/shorts"
            channel_urls = [videos_url, shorts_url]
            logger.info(f"將從 Videos 和 Shorts 兩個頁面獲取影片")
        else:
            # 不包含 Shorts：只從 /videos 頁面獲取
            videos_url = f"{base_url}/videos"
            channel_urls = [videos_url]
            logger.info(f"將從 Videos 頁面獲取影片（不包含 Shorts）")
    
    # 為每個 URL 添加排序參數（最新優先）
    channel_urls_with_params = []
    for url in channel_urls:
        if '?' in url:
            if 'view=0' not in url and 'sort=dd' not in url:
                url += '&view=0&sort=dd'
        else:
            url += '?view=0&sort=dd'
        channel_urls_with_params.append(url)
    
    logger.info(f"開始處理頻道: {', '.join(channel_urls_with_params)}")
    logger.info(f"目標數量: {count}, 包含 Shorts: {include_shorts}, 重試次數: {retries}")
    
    downloaded_list = []
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 先提取播放清單資訊（不實際下載）
            # 如果包含 Shorts，需要從多個頁面獲取並合併
            all_entries = []
            
            for url in channel_urls_with_params:
                logger.info(f"提取頻道影片清單: {url}（限制前 {playlist_extract_count} 支以避免限流）...")
                try:
                    info = ydl.extract_info(url, download=False)
                    
                    if info and 'entries' in info:
                        url_entries = [e for e in info.get('entries', []) if e is not None]
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
                video_id = entry.get('id')
                if video_id and video_id not in seen_ids:
                    seen_ids.add(video_id)
                    entries.append(entry)
            
            logger.info(f"合併後共找到 {len(entries)} 支不重複影片")
            
            if not entries:
                logger.warning("頻道中沒有找到影片")
                return []
            
            logger.info(f"找到 {len(entries)} 支影片，開始篩選...")
            
            # 過濾已下載、非公開影片與直播
            # 注意：Shorts 過濾現在由 match_filter 處理，在實際下載時會自動過濾
            filtered_entries = []
            skipped_public = 0
            skipped_live = 0
            for entry in entries:
                video_id = entry.get('id')
                if not video_id:
                    continue
                
                # 排除直播與預告（只下載 VOD / 一般影片）
                live_status = str(entry.get('live_status') or '').lower()
                # 常見值：'not_live', 'is_live', 'is_upcoming', 'was_live'
                if live_status in ('is_live', 'is_upcoming', 'was_live'):
                    skipped_live += 1
                    logger.debug(f"跳過直播/預告影片 (live_status={live_status}): {video_id}")
                    continue
                
                # 檢查是否為公開影片（優先檢查）
                if not is_public_video(entry):
                    skipped_public += 1
                    continue
                
                # 跳過已下載
                if video_id in downloaded_ids:
                    logger.debug(f"跳過已下載: {video_id}")
                    continue
                
                # Shorts 過濾現在由 match_filter 在實際下載時處理
                # 這裡只做基本過濾，避免在提取階段就過濾掉太多
                
                filtered_entries.append(entry)
            
            if skipped_public > 0:
                logger.info(f"已跳過 {skipped_public} 支非公開影片（僅下載公開影片）")
            if skipped_live > 0:
                logger.info(f"已跳過 {skipped_live} 支直播/預告影片（只下載 VOD）")
            
            # 不限制數量，讓下載邏輯繼續下載直到達到目標數量
            # 這樣即使有些影片被過濾或下載失敗，也能確保下載足夠的數量
            entries_to_download = filtered_entries
            
            if not entries_to_download:
                logger.info("沒有需要下載的新影片")
                return []
            
            logger.info(f"找到 {len(entries_to_download)} 支可下載影片，目標下載 {remaining_count} 支新影片（總目標 {count} 支，已有 {existing_count} 支）...")
            
            # 逐一下載，直到達到目標數量或沒有更多影片
            # downloaded_count 從 0 開始，表示本次下載的新影片數量
            downloaded_count = 0
            for i, entry in enumerate(entries_to_download, 1):
                # 如果已達到目標數量（已下載的新影片數量 >= 還需下載的數量），停止下載
                if downloaded_count >= remaining_count:
                    total_count = existing_count + downloaded_count
                    logger.info(f"已達到目標下載數量 {count} 支（原有 {existing_count} 支 + 新下載 {downloaded_count} 支），停止下載")
                    break
                
                video_id = entry.get('id')
                if not video_id:
                    logger.warning(f"跳過無 ID 的影片: {entry.get('title', 'Unknown')}")
                    continue
                
                # 永遠使用 watch URL，不要使用 entry.get('url')（可能是 m3u8）
                video_url = entry.get('webpage_url') or f'https://www.youtube.com/watch?v={video_id}'
                title = entry.get('title', 'Unknown')
                
                total_current = existing_count + downloaded_count
                logger.info(f"[{i}/{len(entries_to_download)}] 下載 ({downloaded_count}/{remaining_count} 新影片, 總計 {total_current}/{count}): {title[:60]}...")
                
                try:
                    # 記錄下載前的 archive 狀態
                    archive_before = set()
                    if ARCHIVE_FILE.exists():
                        try:
                            with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#'):
                                        parts = line.split()
                                        if len(parts) >= 2:
                                            archive_before.add(parts[1])
                        except:
                            pass
                    
                    # 清除該影片的追蹤記錄（如果有的話）
                    if video_id in downloaded_files:
                        del downloaded_files[video_id]
                    
                    # 實際下載（使用 watch URL）
                    ydl.download([video_url])
                    
                    # 檢查下載是否成功：檢查 archive 是否更新或檔案是否存在
                    download_success = False
                    
                    # 方法1：檢查 archive 是否包含此影片
                    if ARCHIVE_FILE.exists():
                        try:
                            with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#'):
                                        parts = line.split()
                                        if len(parts) >= 2 and parts[1] == video_id:
                                            download_success = True
                                            break
                        except:
                            pass
                    
                    # 方法2：檢查 progress hook 是否記錄了檔案
                    if not download_success:
                        file_path = downloaded_files.get(video_id)
                        if file_path and Path(file_path).exists():
                            download_success = True
                    
                    # 方法3：檢查檔案系統是否有此影片
                    if not download_success:
                        pattern = f'* [{video_id}].mp4'
                        files = list(DOWNLOAD_DIR.glob(pattern))
                        if files:
                            file_path = str(files[0])
                            download_success = True
                    
                    if download_success:
                        # 確定檔案路徑
                        file_path_obj = None
                        if video_id in downloaded_files:
                            file_path_obj = Path(downloaded_files[video_id])
                        else:
                            pattern = f'* [{video_id}].mp4'
                            files = list(DOWNLOAD_DIR.glob(pattern))
                            if files:
                                file_path_obj = files[0]
                        
                        if file_path_obj and file_path_obj.exists():
                            duration = entry.get('duration', 0)
                            downloaded_list.append({
                                'title': title,
                                'id': video_id,
                                'path': str(file_path_obj),
                                'duration': duration
                            })
                            downloaded_count += 1
                            total_current = existing_count + downloaded_count
                            logger.info(f"✓ 完成 ({downloaded_count}/{remaining_count} 新影片, 總計 {total_current}/{count}): {file_path_obj.name}")
                            
                            # 檢查是否已達到目標數量，立即停止
                            if downloaded_count >= remaining_count:
                                logger.info(f"已達到目標下載數量 {count} 支（原有 {existing_count} 支 + 新下載 {downloaded_count} 支），停止下載")
                                break
                        else:
                            # 下載成功但找不到檔案（不應該發生）
                            logger.warning(f"下載成功但找不到檔案: {video_id}")
                            # 仍然計入成功（因為 archive 已記錄）
                            downloaded_count += 1
                            if downloaded_count >= remaining_count:
                                total_current = existing_count + downloaded_count
                                logger.info(f"已達到目標下載數量 {count} 支（原有 {existing_count} 支 + 新下載 {downloaded_count} 支），停止下載")
                                break
                    else:
                        # 下載失敗或被過濾（例如 Shorts）
                        logger.warning(f"下載失敗或被過濾: {video_id} ({title[:60]})")
                        # 不計入成功，繼續下載下一個
                
                    # 如果設定了 sleep，在下載之間延遲
                    if sleep_seconds > 0 and downloaded_count < count and i < len(entries_to_download):
                        logger.debug(f"等待 {sleep_seconds} 秒以避免限流...")
                        time.sleep(sleep_seconds)
                
                except Exception as e:
                    logger.error(f"下載失敗 {video_id}: {e}")
                    # 不計入成功，繼續下載下一個
                    continue
    
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'Private video' in error_msg or 'This video is unavailable' in error_msg or 'Video unavailable' in error_msg:
            logger.warning("偵測到可能無法合法下載的內容，安全退出")
            logger.warning("請確認頻道是否為公開，以及您是否有權限存取這些影片")
            sys.exit(0)
        elif 'ffmpeg' in error_msg.lower() or 'postprocessor' in error_msg.lower():
            logger.error(f"ffmpeg 處理錯誤: {e}")
            logger.error("請確認 ffmpeg 已正確安裝並在 PATH 中")
            sys.exit(1)
        elif 'format' in error_msg.lower() and 'not available' in error_msg.lower():
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
        args.sleep
    )
    
    # 輸出結果
    logger.info("=" * 60)
    logger.info("下載完成")
    logger.info("=" * 60)
    
    if downloaded_list:
        logger.info(f"\n實際下載清單（共 {len(downloaded_list)} 支）:")
        for i, item in enumerate(downloaded_list, 1):
            duration_str = f"{int(item['duration'])} 秒" if item['duration'] else "未知"
            logger.info(f"\n{i}. 標題: {item['title']}")
            logger.info(f"   ID: {item['id']}")
            logger.info(f"   路徑: {item['path']}")
            logger.info(f"   時長: {duration_str}")
    else:
        logger.info("沒有新影片下載（可能已全部下載過）")
    
    logger.info("=" * 60)
    sys.exit(0)


if __name__ == '__main__':
    main()


