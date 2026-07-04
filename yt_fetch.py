#!/usr/bin/env python3
"""
YouTube 頻道影片下載工具

【需求】
從指定 YouTube 頻道取得最新的 N 支影片並下載為 mp4，儲存到 download/ 資料夾。

【安裝】
1. 確保已安裝 Python 3.10+
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
import configparser
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

# 確保 stdout/stderr 為 UTF-8，避免 Windows 預設 cp1252 在輸出中文／✓ 時拋 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# 常數
# 打包成 exe（PyInstaller，sys.frozen）時，以執行檔所在目錄為基準，
# 讓 download/ 與 .venv 等輸出落在 exe 旁邊，而非暫存解壓目錄。
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

VENV_DIR = BASE_DIR / ".venv"
DOWNLOAD_DIR = BASE_DIR / "download"
ARCHIVE_FILE = DOWNLOAD_DIR / ".download_archive.txt"

# 版本與專案資訊（供 GUI「關於」與「檢查更新」使用）。
# 註：版本號以此為準，發布時與 pyproject.toml 同步（見 docs/RELEASING.md）。
__version__ = "1.9.1"
GITHUB_REPO = "SanHsien/yt_fetch"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
QUALITY_CHOICES = ("best", "1080p", "720p", "480p")
QUALITY_HEIGHTS = {
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
}
DATE_FILTER_RE = re.compile(r"^\d{8}$")
ERROR_DIAGNOSIS_PATTERNS = (
    ("cookies", ("cookie",)),
    ("entitlement", ("private", "members", "membership", "unavailable", "forbidden")),
    ("rate", ("rate", "429", "too many", "captcha", "sign in to confirm")),
    ("ffmpeg", ("ffmpeg", "postprocessor", "format")),
    ("disk", ("permission", "access denied", "disk", "no space")),
)
ERROR_DIAGNOSIS_MESSAGES = {
    "zh": {
        "cookies": "建議：cookies 載入失敗。公開影片可不登入；若需要登入，請重新登入或改用 cookies.txt。",
        "entitlement": "建議：YouTube 回報無法存取。請確認此內容是你自己的帳號已授權可觀看。",
        "rate": "建議：可能被限流。可調低速率限制、增加下載間隔，稍後再試。",
        "ffmpeg": "建議：ffmpeg 相關錯誤。請檢查 ffmpeg 狀態，或重新下載最新版 EXE。",
        "disk": "建議：可能是磁碟或權限問題。請確認下載資料夾可寫入且空間足夠。",
        "generic": "建議：請先確認網路、頻道網址、登入狀態與下載資料夾權限。",
    },
    "en": {
        "cookies": (
            "Suggestion: cookie loading failed. Public videos need no login; when login is "
            "needed, sign in again or use a cookies.txt file."
        ),
        "entitlement": (
            "Suggestion: YouTube denied access. Confirm that your own account is entitled "
            "to watch this content."
        ),
        "rate": (
            "Suggestion: this may be rate limiting. Lower the speed limit, increase delay, "
            "and retry later."
        ),
        "ffmpeg": (
            "Suggestion: ffmpeg-related error. Check ffmpeg status or download the latest EXE."
        ),
        "disk": (
            "Suggestion: this may be a disk or permission issue. Confirm the download folder "
            "is writable and has enough space."
        ),
        "generic": (
            "Suggestion: check network, channel URL, sign-in state, and download folder "
            "permissions first."
        ),
    },
}

# 設定檔（INI）。放在 exe／腳本旁，記住非敏感的預設值。
# 優先序：CLI 參數 > 環境變數(YOUTUBE_*) > 本檔 > 內建預設。
CONFIG_FILE = BASE_DIR / "yt_fetch.ini"
CONFIG_SECTION = "yt_fetch"
# 只持久化非敏感設定；cookies 相關欄位「永不」寫入。
CONFIG_PERSIST_KEYS = (
    "channel",
    "count",
    "retries",
    "include_shorts",
    "quality",
    "ratelimit",
    "sleep",
    "download_dir",
    "language",
    "title_include",
    "title_exclude",
    "date_after",
    "date_before",
    "min_duration",
    "max_duration",
    "write_subs",
    "sub_langs",
)
DEFAULT_CONFIG_TEXT = """\
# yt_fetch 設定檔（INI）
# 優先序：CLI 參數 > 環境變數(YOUTUBE_*) > 本檔 > 內建預設。
# GUI 會在每次下載後把當下的設定寫回此檔。
# 基於隱私，cookies（檔案路徑與瀏覽器來源）一律不會被保存。
# 數字／布林格式錯誤的項目會被忽略並回退內建預設。

[yt_fetch]
# 頻道 URL、ID 或 @handle（留空表示不預設）
channel =
# 下載數量（最新 N 支）
count = 5
# 重試次數
retries = 3
# 是否包含 Shorts（true / false）
include_shorts = false
# 下載畫質（best / 1080p / 720p / 480p）
quality = best
# 下載速率限制 MB/s（0 = 無限制）
ratelimit = 0
# 每支下載之間的間隔秒數（0 = 不延遲）
sleep = 0
# 下載資料夾（留空 = 程式旁的 download/）
download_dir =
# 介面語言（zh / en；留空 = 依系統自動）
language =
# 標題必須包含的文字（留空 = 不限制）
title_include =
# 標題包含此文字時排除（留空 = 不限制）
title_exclude =
# 上傳日期起日 YYYYMMDD（留空 = 不限制）
date_after =
# 上傳日期迄日 YYYYMMDD（留空 = 不限制）
date_before =
# 最短影片長度秒數（0 = 不限制）
min_duration = 0
# 最長影片長度秒數（0 = 不限制）
max_duration = 0
# 是否下載字幕（true / false）
write_subs = false
# 字幕語言，逗號分隔
sub_langs = zh-Hant,zh-Hans,en
"""


def env_bool(name: str, default: bool) -> bool:
    """讀取布林環境變數；缺漏時回傳預設值。"""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def write_default_config_if_missing() -> None:
    """首次執行時，於程式旁建立帶註解的預設設定檔。"""
    if CONFIG_FILE.exists():
        return
    try:
        CONFIG_FILE.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
        logger.info(f"已建立預設設定檔：{CONFIG_FILE}")
    except Exception as e:
        logger.warning(f"無法建立設定檔 {CONFIG_FILE}: {e}")


def _coerce_setting(raw: str, caster, key: str, label: str):
    """把字串設定值轉型；空值回傳 None，格式錯誤則提示並回傳 None。"""
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return caster(raw)
    except ValueError:
        logger.warning(f"設定檔 {key}={raw!r} 不是{label}，已忽略")
        return None


def _str2bool(raw: str) -> bool:
    if raw.strip().lower() in ("1", "true", "yes", "on"):
        return True
    if raw.strip().lower() in ("0", "false", "no", "off"):
        return False
    raise ValueError(raw)


def load_config() -> Dict:
    """讀取設定檔，回傳已轉型的設定 dict（格式錯誤的項目會被略過）。

    不存在或解析失敗時回傳空 dict。cookies 相關欄位不在處理範圍內。
    """
    cfg: Dict = {}
    if not CONFIG_FILE.exists():
        return cfg

    parser = configparser.ConfigParser()
    try:
        parser.read(CONFIG_FILE, encoding="utf-8")
    except Exception as e:
        logger.warning(f"讀取設定檔 {CONFIG_FILE} 失敗：{e}")
        return cfg

    if not parser.has_section(CONFIG_SECTION):
        return cfg
    sec = parser[CONFIG_SECTION]

    casters = {
        "channel": (str, "字串"),
        "download_dir": (str, "字串"),
        "language": (str, "字串"),
        "quality": (str, "字串"),
        "title_include": (str, "字串"),
        "title_exclude": (str, "字串"),
        "date_after": (str, "字串"),
        "date_before": (str, "字串"),
        "sub_langs": (str, "字串"),
        "count": (int, "整數"),
        "retries": (int, "整數"),
        "ratelimit": (float, "數字"),
        "sleep": (float, "數字"),
        "min_duration": (int, "整數"),
        "max_duration": (int, "整數"),
        "include_shorts": (_str2bool, "布林"),
        "write_subs": (_str2bool, "布林"),
    }
    for key, (caster, label) in casters.items():
        value = _coerce_setting(sec.get(key, ""), caster, key, label)
        if value is not None:
            cfg[key] = value

    if "quality" in cfg:
        quality = cfg["quality"].strip().lower()
        if quality in QUALITY_CHOICES:
            cfg["quality"] = quality
        else:
            logger.warning(f"設定檔 quality={cfg['quality']!r} 不支援，已忽略")
            cfg.pop("quality", None)

    return cfg


def normalize_date_filter(value: str, option_name: str = "date") -> str:
    """驗證 YYYYMMDD 日期篩選字串；空值回傳空字串。"""
    value = (value or "").strip()
    if not value:
        return ""
    if not DATE_FILTER_RE.match(value):
        raise ValueError(f"{option_name} 必須是 YYYYMMDD 格式")
    try:
        time.strptime(value, "%Y%m%d")
    except ValueError as exc:
        raise ValueError(f"{option_name} 不是有效日期") from exc
    return value


def parse_subtitle_languages(value: str) -> List[str]:
    """解析字幕語言清單，空值回傳預設常用語言。"""
    raw = value or "zh-Hant,zh-Hans,en"
    langs = [part.strip() for part in raw.split(",") if part.strip()]
    return langs or ["zh-Hant", "zh-Hans", "en"]


def save_config(settings: Dict) -> None:
    """把非敏感設定寫回設定檔（cookies 相關欄位一律不寫入）。"""
    parser = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        try:
            parser.read(CONFIG_FILE, encoding="utf-8")
        except Exception:
            pass
    if not parser.has_section(CONFIG_SECTION):
        parser.add_section(CONFIG_SECTION)

    for key in CONFIG_PERSIST_KEYS:
        if key not in settings or settings[key] is None:
            continue
        value = settings[key]
        if isinstance(value, bool):
            value = "true" if value else "false"
        parser.set(CONFIG_SECTION, key, str(value))

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(
                "# yt_fetch 設定檔；優先序：CLI > 環境變數 > 本檔 > 內建預設。cookies 不會被保存。\n"
            )
            parser.write(f)
    except Exception as e:
        logger.warning(f"寫入設定檔 {CONFIG_FILE} 失敗：{e}")


def set_download_dir(path: Path) -> None:
    """切換下載資料夾（同步更新 archive 路徑）。CLI 與 GUI 共用。"""
    global DOWNLOAD_DIR, ARCHIVE_FILE
    DOWNLOAD_DIR = Path(path)
    ARCHIVE_FILE = DOWNLOAD_DIR / ".download_archive.txt"


def parse_version(text: str) -> tuple:
    """把版本字串（可帶前綴 v）轉成可比較的整數 tuple，例如 'v1.2.0' -> (1, 2, 0)。"""
    text = (text or "").strip().lstrip("vV")
    parts = []
    for piece in text.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def is_newer_version(latest: str, current: str) -> bool:
    """latest 是否比 current 新（語義化版本比較）。"""
    return parse_version(latest) > parse_version(current)


def get_installed_package_version(package_name: str) -> Optional[str]:
    """取得目前環境中已安裝套件版本；未安裝時回傳 None。"""
    from importlib import metadata

    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return None


def get_bundled_ytdlp_version() -> str:
    """取得目前執行環境內的 yt-dlp 版本；EXE 會回報打包當下內嵌的版本。"""
    return get_installed_package_version("yt-dlp") or "unknown"


def fetch_latest_pypi_version(package_name: str, timeout: float = 6.0) -> Optional[str]:
    """查 PyPI 最新版本；失敗回傳 None。"""
    import json
    import urllib.parse
    import urllib.request

    safe_name = urllib.parse.quote(package_name)
    url = f"https://pypi.org/pypi/{safe_name}/json"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "yt_fetch"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - 固定 https
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("info", {}).get("version")
    except Exception as e:  # noqa: BLE001 - 網路/解析失敗一律視為「查不到」
        logger.debug(f"檢查 PyPI 套件 {package_name} 版本失敗：{e}")
        return None


def build_ytdlp_update_message(latest: Optional[str], current: Optional[str] = None) -> str:
    """組出 yt-dlp 版本狀態文字，供 GUI/CLI 共用。"""
    current = current or get_bundled_ytdlp_version()
    if not latest:
        return f"yt-dlp: {current}（無法檢查最新版本）"
    if current == "unknown":
        return f"yt-dlp: unknown（PyPI 最新 {latest}）"
    if is_newer_version(latest, current):
        return f"yt-dlp: {current}（PyPI 最新 {latest}，建議更新或下載新版 EXE）"
    return f"yt-dlp: {current}（已是 PyPI 最新）"


def classify_error_message(message: str) -> str:
    """把常見 yt-dlp / 檔案系統錯誤分類成穩定 key。"""
    text = (message or "").lower()
    for key, tokens in ERROR_DIAGNOSIS_PATTERNS:
        if any(token in text for token in tokens):
            return key
    return "generic"


def build_error_diagnosis_message(message: str, lang: str = "zh") -> str:
    """把錯誤文字轉成可操作的診斷提示。"""
    language = lang if lang in ERROR_DIAGNOSIS_MESSAGES else "zh"
    diagnosis = classify_error_message(message)
    return ERROR_DIAGNOSIS_MESSAGES[language].get(
        diagnosis,
        ERROR_DIAGNOSIS_MESSAGES[language]["generic"],
    )


def fetch_latest_release_tag(timeout: float = 6.0) -> Optional[str]:
    """查 GitHub 最新 Release 的 tag 名稱；失敗回傳 None（僅檢查，不下載）。"""
    import json
    import urllib.request

    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "yt_fetch"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - 固定 https
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("tag_name")
    except Exception as e:  # noqa: BLE001 - 網路/解析失敗一律視為「查不到」
        logger.debug(f"檢查更新失敗：{e}")
        return None


def env_int(name: str, default: int) -> int:
    """讀取整數環境變數；缺漏或格式錯誤時回傳預設值並提示，避免啟動時拋例外。"""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError:
        logger.warning(f"環境變數 {name}={raw!r} 不是整數，改用預設值 {default}")
        return default


def env_float(name: str, default: float) -> float:
    """讀取浮點數環境變數；缺漏或格式錯誤時回傳預設值並提示。"""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw.strip())
    except ValueError:
        logger.warning(f"環境變數 {name}={raw!r} 不是數字，改用預設值 {default}")
        return default


def is_venv() -> bool:
    """檢查是否在虛擬環境中"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def ensure_venv_and_restart():
    """確保在 venv 中，若不在則建立並重新啟動"""
    # 打包成 exe 時，相依套件已內嵌，毋需（也不應）建立 venv 或重啟
    if getattr(sys, "frozen", False):
        return False
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
            # Windows: 以子行程執行並等待完成（沿用同一個主控台視窗）
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


def _read_ffmpeg_version(executable: str) -> str:
    """讀取 ffmpeg 第一行版本文字；失敗回傳 unknown。"""
    try:
        proc = subprocess.run(
            [executable, "-version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        output = proc.stdout.decode("utf-8", errors="replace").splitlines()
        return output[0] if output else "unknown"
    except Exception:
        return "unknown"


def _get_imageio_ffmpeg_exe() -> Optional[str]:
    """取得 imageio-ffmpeg 提供的 ffmpeg 路徑；未安裝或失敗時回傳 None。"""
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def get_ffmpeg_status() -> Dict:
    """取得目前可用 ffmpeg 狀態，不安裝任何東西。"""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return {
            "available": True,
            "source": "system",
            "path": system_ffmpeg,
            "version": _read_ffmpeg_version(system_ffmpeg),
        }

    bundled = _get_imageio_ffmpeg_exe()
    if bundled and Path(bundled).exists():
        return {
            "available": True,
            "source": "imageio-ffmpeg",
            "path": bundled,
            "version": _read_ffmpeg_version(bundled),
        }

    return {
        "available": False,
        "source": "missing",
        "path": "",
        "version": "unknown",
    }


def install_ffmpeg() -> Optional[str]:
    """自動安裝 ffmpeg（使用 imageio-ffmpeg）

    Returns:
        ffmpeg 可執行檔的完整路徑，如果安裝失敗則返回 None
    """
    logger.info("嘗試自動安裝 ffmpeg...")

    try:
        # 打包成 exe（sys.frozen）時 imageio-ffmpeg 已內嵌，且 sys.executable 是本程式
        # 自身（用它跑 `-m pip` 會誤啟第二個 GUI 視窗），故跳過 pip 安裝直接取用。
        if getattr(sys, "frozen", False):
            logger.info("偵測到打包執行檔，使用內嵌的 imageio-ffmpeg...")
        else:
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
                pip_cmd + ["install", "--upgrade", "imageio-ffmpeg"],
                check=True,
                capture_output=True,
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

    # 從現有檔案名稱中提取 ID（遞迴掃描，涵蓋各頻道子目錄與相容舊的平放檔案）
    if DOWNLOAD_DIR.exists():
        pattern = re.compile(r"\[([a-zA-Z0-9_-]{11})\]\.mp4$")
        for file in DOWNLOAD_DIR.rglob("*.mp4"):
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
    matches = [p for p in DOWNLOAD_DIR.rglob("*.mp4") if p.name.endswith(suffix)]
    return matches[0] if matches else None


def is_live_or_upcoming(info: Dict) -> bool:
    """判斷影片是否為直播、預告或直播回放。"""
    live_status = str(info.get("live_status") or "").lower()
    return live_status in ("is_live", "is_upcoming", "was_live")


def filter_downloadable_entries(
    entries: List[Dict],
    downloaded_ids: set,
    title_include: str = "",
    title_exclude: str = "",
    date_after: str = "",
    date_before: str = "",
    min_duration: int = 0,
    max_duration: int = 0,
) -> Dict:
    """從頻道影片清單篩出可下載的項目（排除直播/預告、非公開、已下載）。

    Shorts 不在此處理，留待 yt-dlp 的 match_filter 於實際下載時過濾。

    Returns:
        dict，含 keys: entries（可下載清單）、skipped_live、skipped_public。
    """
    filtered: List[Dict] = []
    skipped_live = 0
    skipped_public = 0
    skipped_advanced = 0
    date_after = normalize_date_filter(date_after, "--date-after")
    date_before = normalize_date_filter(date_before, "--date-before")
    for entry in entries:
        video_id = entry.get("id")
        if not video_id:
            continue

        # 排除直播與預告（只下載 VOD / 一般影片）
        if is_live_or_upcoming(entry):
            skipped_live += 1
            live_status = str(entry.get("live_status") or "").lower()
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

        advanced_reason = advanced_filter_reason(
            entry,
            title_include,
            title_exclude,
            "",
            "",
            0,
            0,
        )
        if advanced_reason:
            skipped_advanced += 1
            logger.debug(f"跳過影片 ({advanced_reason}): {video_id}")
            continue

        filtered.append(entry)

    return {
        "entries": filtered,
        "skipped_live": skipped_live,
        "skipped_public": skipped_public,
        "skipped_advanced": skipped_advanced,
    }


def dedupe_entries(entries: List[Dict]) -> List[Dict]:
    """依 YouTube video id 合併多個來源頁面的影片清單。"""
    seen_ids = set()
    unique_entries = []
    for entry in entries:
        video_id = entry.get("id")
        if video_id and video_id not in seen_ids:
            seen_ids.add(video_id)
            unique_entries.append(entry)
    return unique_entries


def calculate_download_target(
    entries: List[Dict], downloaded_ids: set, count: int
) -> Dict[str, int]:
    """計算本頻道已下載數與本次還需下載數。"""
    existing_count = sum(1 for entry in entries if entry.get("id") in downloaded_ids)
    return {
        "existing_count": existing_count,
        "remaining_count": max(0, count - existing_count),
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


def build_format_selector(quality: str) -> str:
    """依使用者選擇的畫質產生 yt-dlp format selector。"""
    quality = (quality or "best").strip().lower()
    if quality == "best":
        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best"

    height = QUALITY_HEIGHTS.get(quality)
    if not height:
        raise ValueError(f"不支援的下載畫質：{quality}")

    return (
        f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={height}]+bestaudio/"
        f"best[height<={height}][ext=mp4]/"
        f"best[height<={height}]"
    )


def build_ytdlp_options(
    download_dir: Path,
    archive_file: Path,
    quality: str,
    retries: int,
    include_shorts: bool,
    playlist_extract_count: int,
    progress_hook: Callable[[Dict], None],
    match_filter: Optional[Callable[[Dict], Optional[str]]],
    ffmpeg_path: Optional[str] = None,
    cookies_from_browser: str = "",
    cookies_file: str = "",
    ratelimit: float = 0,
    write_subs: bool = False,
    sub_langs: str = "zh-Hant,zh-Hans,en",
) -> Dict:
    """集中組裝 yt-dlp options，供 CLI/GUI 與測試共用。"""
    ydl_opts = {
        "format": build_format_selector(quality),
        # 依頻道名稱建立子目錄，避免多個頻道的影片混在同一層。
        # %(channel,uploader|Unknown Channel)s：優先用頻道名、退而用上傳者，皆無則 Unknown Channel；
        # yt-dlp 會對此欄位值做檔名安全處理（移除路徑分隔字元等）。
        "outtmpl": str(
            download_dir / "%(channel,uploader|Unknown Channel)s" / "%(title)s [%(id)s].%(ext)s"
        ),
        "merge_output_format": "mp4",
        "noplaylist": False,
        "extract_flat": False,
        "ignoreerrors": True,
        "no_warnings": False,
        "quiet": False,
        "retries": retries,
        "fragment_retries": retries,
        "file_access_retries": retries,
        "download_archive": str(archive_file),
        "writesubtitles": bool(write_subs),
        "writeautomaticsub": bool(write_subs),
        "subtitleslangs": parse_subtitle_languages(sub_langs),
        "subtitlesformat": "best",
        "progress_hooks": [progress_hook],
        "playlistend": playlist_extract_count,
        "match_filter": match_filter,
    }

    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = parse_cookies_from_browser_spec(cookies_from_browser)
    elif cookies_file:
        ydl_opts["cookiefile"] = cookies_file

    if ratelimit > 0:
        ydl_opts["ratelimit"] = int(ratelimit * 1024 * 1024)

    return ydl_opts


def parse_cookies_from_browser_spec(spec: str) -> tuple:
    """解析 yt-dlp 的 BROWSER[+KEYRING][:PROFILE][::CONTAINER] 格式。"""
    raw = (spec or "").strip()
    if not raw:
        return ()

    container = None
    if "::" in raw:
        raw, container = raw.split("::", 1)
        container = container or None

    profile = None
    if ":" in raw:
        raw, profile = raw.split(":", 1)
        profile = profile or None

    keyring = None
    if "+" in raw:
        browser, keyring = raw.split("+", 1)
        keyring = keyring.upper() if keyring else None
    else:
        browser = raw

    if not browser:
        raise ValueError("瀏覽器 cookies 來源不可為空")

    return (browser.lower(), profile, keyring, container)


def is_cookie_load_error(error: Exception) -> bool:
    """判斷 yt-dlp 錯誤是否為 cookies 載入失敗。"""
    text = str(error).lower()
    return (
        "failed to load cookies" in text
        or ("could not find" in text and "cookies" in text)
        or ("cookie" in text and "decrypt" in text)
    )


def log_cookie_load_error(source: str, error: Exception) -> None:
    """輸出 cookies 載入失敗時的可操作提示。"""
    logger.error(f"載入 cookies 失敗: {error}")
    logger.error(f"目前使用的 cookies 來源: {source}")
    logger.error("請確認瀏覽器已登入 YouTube，並先完全關閉瀏覽器後再重試。")
    logger.error("若仍失敗，請改用 Netscape 格式 cookies.txt，填入 cookies 檔案路徑。")
    logger.error("瀏覽器 cookies 可指定 profile，例如 chrome:Default 或 chrome:Profile 1。")


class _CookiesLoadError(Exception):
    """內部訊號：cookies 載入失敗，用來觸發『無 cookies 模式』fallback。

    不對外暴露；只在 download_videos 內部由提取階段拋出、由 fallback 邏輯攔截。
    """


def _extract_entries(
    yt_dlp,
    ydl_opts: Dict,
    channel_urls: List[str],
    playlist_extract_count: int,
    cookies_from_browser: str,
    cookies_file: str,
) -> List[Dict]:
    """提取頻道影片清單；cookies 載入失敗時自動改用『無 cookies』模式重試一次。

    公開頻道不需 cookies 即可取得清單，因此當瀏覽器 cookies 無法載入（常見於
    Chrome App-Bound Encryption 擋住讀取）時，與其直接中止，不如改用無 cookies 模式
    重試，讓公開內容仍可下載。

    若觸發 fallback，會「就地」把 cookies 設定從 ydl_opts 移除，使後續下載階段
    一致地不使用 cookies。回傳合併去重前的影片清單（all_entries）。
    """
    cookies_source = cookies_from_browser or cookies_file

    def _extract(opts: Dict, allow_fallback: bool) -> List[Dict]:
        # 抽清單一律用 flat（extract_flat="in_playlist"）：只取影片 ID 清單，不逐支完整解析。
        # 非 flat 抽清單時，遇到頻道內的會員限定影片會逐支解析失敗，且大量逐支解析容易
        # 被 YouTube 節流，導致整批回傳 0 支（"無法取得頻道資訊"）。是否公開／會員／直播的
        # 判斷與實際下載一起留到下載階段處理（有登入 cookie 才能取得你有權觀看的會員影片）。
        list_opts = dict(opts)
        list_opts["extract_flat"] = "in_playlist"
        collected: List[Dict] = []
        with yt_dlp.YoutubeDL(list_opts) as ydl:
            for url in channel_urls:
                logger.info(
                    f"提取頻道影片清單: {url}（掃描前 {playlist_extract_count} 支作為下載候選）..."
                )
                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as e:  # noqa: BLE001 - 區分 cookie 失敗與一般提取錯誤
                    if allow_fallback and cookies_source and is_cookie_load_error(e):
                        raise _CookiesLoadError(e) from e
                    logger.warning(f"從 {url} 提取影片時發生錯誤: {e}")
                    continue

                if info and "entries" in info:
                    url_entries = [e for e in info.get("entries", []) if e is not None]
                    collected.extend(url_entries)
                    logger.info(f"從 {url} 獲取到 {len(url_entries)} 支影片")
                else:
                    logger.warning(f"無法從 {url} 取得影片資訊")
        return collected

    try:
        return _extract(ydl_opts, allow_fallback=bool(cookies_source))
    except _CookiesLoadError as fallback:
        original = fallback.__cause__ or fallback
        log_cookie_load_error(cookies_source, original)
        logger.warning("改用『無 cookies』模式重試（公開頻道不需 cookies）...")
        for key in ("cookiesfrombrowser", "cookiefile"):
            ydl_opts.pop(key, None)
        # 重試時不再觸發 fallback：若無 cookies 仍失敗，交由呼叫端以「無法取得頻道資訊」處理
        return _extract(ydl_opts, allow_fallback=False)


def is_non_public(info: Dict) -> bool:
    """依 `availability` 欄位判斷影片是否明確標記為非公開。

    沒有 availability 欄位時回傳 False（交由其他啟發式判斷）。
    """
    availability = info.get("availability")
    return bool(availability) and availability != "public"


def filter_reason(info_dict: Dict, include_shorts: bool) -> Optional[str]:
    """判斷影片是否應被排除（供 yt-dlp 的 match_filter 使用）。

    Args:
        info_dict: yt-dlp 提供的影片資訊字典
        include_shorts: 是否包含 Shorts

    Returns:
        排除原因字串；若應接受該影片則回傳 None。
    """
    if is_live_or_upcoming(info_dict):
        return "直播/預告影片（只下載一般 VOD）"

    # 排除非公開影片
    if is_non_public(info_dict):
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


def advanced_filter_reason(
    info_dict: Dict,
    title_include: str = "",
    title_exclude: str = "",
    date_after: str = "",
    date_before: str = "",
    min_duration: int = 0,
    max_duration: int = 0,
) -> Optional[str]:
    """判斷進階過濾條件是否排除影片。"""
    title = str(info_dict.get("title") or "")
    title_lower = title.lower()
    include_text = (title_include or "").strip().lower()
    exclude_text = (title_exclude or "").strip().lower()

    if include_text and include_text not in title_lower:
        return f"標題未包含關鍵字：{title_include}"
    if exclude_text and exclude_text in title_lower:
        return f"標題包含排除關鍵字：{title_exclude}"

    upload_date = str(info_dict.get("upload_date") or "").strip()
    if date_after or date_before:
        if not DATE_FILTER_RE.match(upload_date):
            return "缺少可判斷的上傳日期"
        if date_after and upload_date < date_after:
            return f"上傳日期早於 {date_after}"
        if date_before and upload_date > date_before:
            return f"上傳日期晚於 {date_before}"

    if min_duration or max_duration:
        try:
            duration = float(info_dict.get("duration"))
        except (TypeError, ValueError):
            return "缺少可判斷的影片長度"
        if min_duration and duration < min_duration:
            return f"影片長度短於 {min_duration} 秒"
        if max_duration and duration > max_duration:
            return f"影片長度長於 {max_duration} 秒"

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

    # 檢查 availability 欄位（最可靠的判斷方式）：只接受 'public'
    if is_non_public(entry):
        logger.debug(f"跳過非公開影片 (availability={entry.get('availability')}): {video_id}")
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
    """以互動輸入詢問用戶參數"""
    # 無互動終端機（例如被 pipe、在 CI 或無 tty 環境）時，input() 會直接 EOF，
    # 給出明確指引而非拋出例外或卡住。
    if not sys.stdin or not sys.stdin.isatty():
        logger.error("未提供 --channel，且目前不是互動式終端機，無法詢問參數")
        logger.error("請改用 --channel 參數或設定 YOUTUBE_CHANNEL 環境變數")
        sys.exit(1)

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

    # 詢問下載畫質
    print("\n請選擇下載畫質（best/1080p/720p/480p，預設：best）：")
    quality_input = input("下載畫質: ").strip().lower()
    quality = quality_input if quality_input in QUALITY_CHOICES else "best"

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
        "quality": quality,
        "retries": retries,
    }


def parse_args():
    """解析命令列參數"""
    # 讀取設定檔作為各參數的預設來源（唯讀，不在此建立檔案，確保 --help 乾淨）。
    # 優先序：CLI 參數 > 環境變數 > 設定檔(ini) > 內建預設。
    cfg = load_config()

    parser = argparse.ArgumentParser(
        description="從 YouTube 頻道下載最新影片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--channel",
        type=str,
        default=os.getenv("YOUTUBE_CHANNEL") or cfg.get("channel"),
        help="頻道 URL、ID 或 @handle（也可用環境變數 YOUTUBE_CHANNEL）。如果未提供，會以輸入視窗詢問",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=env_int("YOUTUBE_COUNT", cfg.get("count", 5)),
        help="下載數量（預設：5，也可用環境變數 YOUTUBE_COUNT）",
    )

    parser.add_argument(
        "--include-shorts",
        action="store_true",
        default=env_bool("YOUTUBE_INCLUDE_SHORTS", cfg.get("include_shorts", False)),
        help="包含 Shorts（預設排除，也可用環境變數 YOUTUBE_INCLUDE_SHORTS=1）",
    )

    parser.add_argument(
        "--quality",
        choices=QUALITY_CHOICES,
        default=(os.getenv("YOUTUBE_QUALITY") or cfg.get("quality") or "best"),
        help=(
            "下載畫質（best/1080p/720p/480p，預設 best）。"
            "會選擇不高於指定上限的最佳可用畫質；也可用環境變數 YOUTUBE_QUALITY"
        ),
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=env_int("YOUTUBE_RETRIES", cfg.get("retries", 3)),
        help="重試次數（預設：3，也可用環境變數 YOUTUBE_RETRIES）",
    )

    parser.add_argument(
        "--cookies-from-browser",
        type=str,
        default=os.getenv("YOUTUBE_COOKIES_BROWSER", ""),
        help=(
            "從瀏覽器讀取 cookies（例如：chrome, firefox, edge）。"
            "僅用於你自己有權存取的內容；cookies 不會被本工具保存。"
            "也可用環境變數 YOUTUBE_COOKIES_BROWSER"
        ),
    )

    parser.add_argument(
        "--cookies",
        type=str,
        default=os.getenv("YOUTUBE_COOKIES_FILE", ""),
        help=(
            "cookies 檔案路徑（Netscape 格式）。"
            "僅用於你自己有權存取的內容；cookies 不會被本工具保存。"
            "也可用環境變數 YOUTUBE_COOKIES_FILE"
        ),
    )

    parser.add_argument(
        "--ratelimit",
        type=float,
        default=env_float("YOUTUBE_RATELIMIT", cfg.get("ratelimit", 0.0)),
        help="下載速率限制（MB/s，0 表示無限制）。也可用環境變數 YOUTUBE_RATELIMIT",
    )

    parser.add_argument(
        "--sleep",
        type=float,
        default=env_float("YOUTUBE_SLEEP", cfg.get("sleep", 0.0)),
        help="每次下載之間的延遲秒數（減少被限流）。也可用環境變數 YOUTUBE_SLEEP",
    )

    parser.add_argument(
        "--title-include",
        type=str,
        default=os.getenv("YOUTUBE_TITLE_INCLUDE") or cfg.get("title_include", ""),
        help="只下載標題包含指定文字的影片。也可用環境變數 YOUTUBE_TITLE_INCLUDE",
    )

    parser.add_argument(
        "--title-exclude",
        type=str,
        default=os.getenv("YOUTUBE_TITLE_EXCLUDE") or cfg.get("title_exclude", ""),
        help="排除標題包含指定文字的影片。也可用環境變數 YOUTUBE_TITLE_EXCLUDE",
    )

    parser.add_argument(
        "--date-after",
        type=str,
        default=os.getenv("YOUTUBE_DATE_AFTER") or cfg.get("date_after", ""),
        help="只下載此日期之後（含）的影片，格式 YYYYMMDD。也可用環境變數 YOUTUBE_DATE_AFTER",
    )

    parser.add_argument(
        "--date-before",
        type=str,
        default=os.getenv("YOUTUBE_DATE_BEFORE") or cfg.get("date_before", ""),
        help="只下載此日期之前（含）的影片，格式 YYYYMMDD。也可用環境變數 YOUTUBE_DATE_BEFORE",
    )

    parser.add_argument(
        "--min-duration",
        type=int,
        default=env_int("YOUTUBE_MIN_DURATION", cfg.get("min_duration", 0)),
        help="只下載長度不少於指定秒數的影片，0 表示不限制。也可用環境變數 YOUTUBE_MIN_DURATION",
    )

    parser.add_argument(
        "--max-duration",
        type=int,
        default=env_int("YOUTUBE_MAX_DURATION", cfg.get("max_duration", 0)),
        help="只下載長度不超過指定秒數的影片，0 表示不限制。也可用環境變數 YOUTUBE_MAX_DURATION",
    )

    parser.add_argument(
        "--write-subs",
        action="store_true",
        default=env_bool("YOUTUBE_WRITE_SUBS", cfg.get("write_subs", False)),
        help="同時下載字幕／自動字幕（若影片提供）。也可用環境變數 YOUTUBE_WRITE_SUBS=1",
    )

    parser.add_argument(
        "--sub-langs",
        type=str,
        default=os.getenv("YOUTUBE_SUB_LANGS") or cfg.get("sub_langs", "zh-Hant,zh-Hans,en"),
        help="字幕語言，逗號分隔（預設：zh-Hant,zh-Hans,en）。也可用環境變數 YOUTUBE_SUB_LANGS",
    )

    parser.add_argument(
        "--channels-file",
        type=str,
        default=os.getenv("YOUTUBE_CHANNELS_FILE", ""),
        help=(
            "批次下載：指定一個檔案，每行一個頻道 URL/ID/@handle（# 開頭為註解）。"
            "單一頻道失敗不會中斷整批。也可用環境變數 YOUTUBE_CHANNELS_FILE"
        ),
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="啟動圖形介面（Tkinter）；其餘參數於介面中設定",
    )

    parser.add_argument(
        "--login",
        action="store_true",
        help=(
            "開啟受控瀏覽器讓你登入 YouTube 一次並保存 cookies（Windows/Chrome）。"
            "解決 Chrome 127+ App-Bound Encryption 導致無法直接讀取 cookies 的問題；"
            "登入後之後的下載會自動使用並 headless 刷新這份 cookies。"
        ),
    )

    args = parser.parse_args()

    # GUI 與批次模式不在此詢問 channel；否則若沒有提供 channel，以互動輸入詢問所有參數
    if not args.gui and not args.channel and not args.channels_file:
        user_input = prompt_user_input()
        args.channel = user_input["channel"]
        args.count = user_input["count"]
        args.include_shorts = user_input["include_shorts"]
        args.quality = user_input["quality"]
        args.retries = user_input["retries"]

    if args.count < 1:
        parser.error("--count 必須大於 0")
    if args.quality not in QUALITY_CHOICES:
        parser.error(f"--quality 必須是：{', '.join(QUALITY_CHOICES)}")
    try:
        args.date_after = normalize_date_filter(args.date_after, "--date-after")
        args.date_before = normalize_date_filter(args.date_before, "--date-before")
    except ValueError as e:
        parser.error(str(e))
    if args.min_duration < 0:
        parser.error("--min-duration 不可為負數")
    if args.max_duration < 0:
        parser.error("--max-duration 不可為負數")
    if args.min_duration and args.max_duration and args.min_duration > args.max_duration:
        parser.error("--min-duration 不可大於 --max-duration")

    return args


def read_channels_file(path: str) -> List[str]:
    """讀取批次頻道清單檔，回傳頻道字串清單。

    每行一個頻道（URL / ID / @handle）；空行與 `#` 開頭的註解行會被略過。
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"找不到頻道清單檔：{path}")
    channels = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            channels.append(line)
    return channels


def download_entries_with_ytdlp(
    ydl,
    entries_to_download: List[Dict],
    remaining_count: int,
    total_target_count: int,
    existing_count: int,
    downloaded_files: Dict[str, str],
    sleep_seconds: float,
) -> List[Dict]:
    """逐一下載已篩選的影片，回傳本次成功下載清單。"""
    downloaded_list = []
    downloaded_count = 0

    for index, entry in enumerate(entries_to_download, 1):
        if downloaded_count >= remaining_count:
            logger.info(
                f"已達到目標下載數量 {total_target_count} 支（原有 {existing_count} 支 + 新下載 {downloaded_count} 支），停止下載"
            )
            break

        video_id = entry.get("id")
        if not video_id:
            logger.warning(f"跳過無 ID 的影片: {entry.get('title', 'Unknown')}")
            continue

        video_url = entry.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"
        title = entry.get("title", "Unknown")
        total_current = existing_count + downloaded_count
        logger.info(
            f"[{index}/{len(entries_to_download)}] 下載 ({downloaded_count}/{remaining_count} 新影片, 總計 {total_current}/{total_target_count}): {title[:60]}..."
        )

        downloaded_files.pop(video_id, None)
        try:
            ydl.download([video_url])
        except Exception as e:  # noqa: BLE001 - 單支失敗不應中止整個頻道
            logger.error(f"下載失敗 {video_id}: {e}")
            continue

        file_path_obj = find_downloaded_file(video_id, downloaded_files.get(video_id))
        if not (archive_contains(video_id) or file_path_obj):
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
            f"✓ 完成 ({downloaded_count}/{remaining_count} 新影片, 總計 {total_current}/{total_target_count}): {done_name}"
        )

        if downloaded_count >= remaining_count:
            logger.info(
                f"已達到目標下載數量 {total_target_count} 支（原有 {existing_count} 支 + 新下載 {downloaded_count} 支），停止下載"
            )
            break

        if sleep_seconds > 0 and index < len(entries_to_download):
            logger.debug(f"等待 {sleep_seconds} 秒以避免限流...")
            time.sleep(sleep_seconds)

    return downloaded_list


def ensure_ffmpeg_ready() -> Optional[str]:
    """確認 ffmpeg 可用；必要時嘗試使用 imageio-ffmpeg，失敗則結束程式。"""
    ffmpeg_path = None
    has_ffmpeg = check_ffmpeg()

    if not has_ffmpeg:
        logger.warning("未偵測到 ffmpeg，嘗試自動安裝...")
        ffmpeg_path = install_ffmpeg()
        if ffmpeg_path:
            has_ffmpeg = True
            logger.info(f"將使用 ffmpeg: {ffmpeg_path}")
        else:
            has_ffmpeg = check_ffmpeg()

    if has_ffmpeg:
        return ffmpeg_path

    logger.error("未偵測到 ffmpeg，且自動安裝失敗")
    logger.error("安裝指引:")
    logger.error("  Windows: choco install ffmpeg 或從 https://ffmpeg.org/download.html 下載")
    logger.error("  macOS: brew install ffmpeg")
    logger.error("  Linux: sudo apt-get install ffmpeg 或 sudo yum install ffmpeg")
    logger.error("或腳本會嘗試使用 imageio-ffmpeg 自動下載")
    sys.exit(2)


def build_progress_hook(
    downloaded_files: Dict[str, str],
    progress_callback: Optional[Callable[[Dict], None]] = None,
) -> Callable[[Dict], None]:
    """建立 yt-dlp progress hook，轉發 GUI 進度並記錄完成檔名。"""

    def progress_hook(event: Dict) -> None:
        if progress_callback:
            try:
                progress_callback(event)
            except Exception as e:  # noqa: BLE001 - 進度回呼不得中斷下載
                logger.debug(f"進度回呼失敗：{e}")
        if event.get("status") == "finished":
            info_dict = event.get("info_dict", {})
            video_id = info_dict.get("id")
            filename = event.get("filename")
            if video_id and filename:
                downloaded_files[video_id] = filename
                logger.debug(f"記錄下載檔案: {video_id} -> {filename}")

    return progress_hook


def build_match_filter(
    include_shorts: bool,
    title_include: str = "",
    title_exclude: str = "",
    date_after: str = "",
    date_before: str = "",
    min_duration: int = 0,
    max_duration: int = 0,
) -> Callable[[Dict], Optional[str]]:
    """建立 yt-dlp match_filter。"""
    date_after = normalize_date_filter(date_after, "--date-after")
    date_before = normalize_date_filter(date_before, "--date-before")
    if min_duration < 0 or max_duration < 0:
        raise ValueError("影片長度篩選不可為負數")
    if min_duration and max_duration and min_duration > max_duration:
        raise ValueError("--min-duration 不可大於 --max-duration")

    def match_filter(info_dict: Dict) -> Optional[str]:
        return filter_reason(info_dict, include_shorts) or advanced_filter_reason(
            info_dict,
            title_include,
            title_exclude,
            date_after,
            date_before,
            min_duration,
            max_duration,
        )

    return match_filter


def calculate_playlist_extract_count(count: int) -> int:
    """計算候選影片掃描數量。"""
    return min(max(count * 5, 50), 200)


def log_download_options(
    ffmpeg_path: Optional[str],
    cookies_from_browser: str,
    cookies_file: str,
    ratelimit: float,
    title_include: str = "",
    title_exclude: str = "",
    date_after: str = "",
    date_before: str = "",
    min_duration: int = 0,
    max_duration: int = 0,
    write_subs: bool = False,
    sub_langs: str = "",
) -> None:
    """輸出使用者可理解的下載選項摘要。"""
    if ffmpeg_path:
        logger.info(f"yt-dlp 將使用指定的 ffmpeg: {ffmpeg_path}")
    if cookies_from_browser:
        logger.info(f"使用瀏覽器 cookies: {cookies_from_browser}")
    elif cookies_file:
        logger.info(f"使用 cookies 檔案: {cookies_file}")
    if ratelimit > 0:
        logger.info(f"下載速率限制: {ratelimit} MB/s")
    if title_include:
        logger.info(f"標題必須包含: {title_include}")
    if title_exclude:
        logger.info(f"標題排除關鍵字: {title_exclude}")
    if date_after or date_before:
        logger.info(f"上傳日期篩選: {date_after or '不限'} ~ {date_before or '不限'}")
    if min_duration or max_duration:
        logger.info(f"影片長度篩選: {min_duration or '不限'} ~ {max_duration or '不限'} 秒")
    if write_subs:
        logger.info(f"下載字幕: {', '.join(parse_subtitle_languages(sub_langs))}")


def handle_ytdlp_download_error(error: Exception, cookies_source: str = "") -> None:
    """處理 yt-dlp 下載階段的致命錯誤並結束程式。"""
    error_msg = str(error)
    if cookies_source and is_cookie_load_error(error):
        log_cookie_load_error(cookies_source, error)
        logger.error(build_error_diagnosis_message(error_msg))
        sys.exit(1)
    if (
        "Private video" in error_msg
        or "This video is unavailable" in error_msg
        or "Video unavailable" in error_msg
    ):
        logger.warning("偵測到可能無法合法下載的內容，安全退出")
        logger.warning("請確認頻道是否為公開，以及您是否有權限存取這些影片")
        logger.warning(build_error_diagnosis_message(error_msg))
        sys.exit(0)
    if "ffmpeg" in error_msg.lower() or "postprocessor" in error_msg.lower():
        logger.error(f"ffmpeg 處理錯誤: {error}")
        logger.error("請確認 ffmpeg 已正確安裝並在 PATH 中")
        logger.error(build_error_diagnosis_message(error_msg))
        sys.exit(1)
    if "format" in error_msg.lower() and "not available" in error_msg.lower():
        logger.error(f"格式錯誤: {error}")
        logger.error("請確認 ffmpeg 已正確安裝")
        logger.error(build_error_diagnosis_message(error_msg))
        sys.exit(1)

    logger.error(f"下載錯誤: {error}")
    logger.error(build_error_diagnosis_message(error_msg))
    sys.exit(1)


def prepare_entries_to_download(
    all_entries: List[Dict],
    downloaded_ids: set,
    count: int,
    title_include: str = "",
    title_exclude: str = "",
    date_after: str = "",
    date_before: str = "",
    min_duration: int = 0,
    max_duration: int = 0,
) -> Dict[str, object]:
    """整理提取結果，回傳可下載候選與目標數資訊。"""
    if not all_entries:
        logger.error("無法取得頻道資訊，請確認頻道 URL 是否正確")
        sys.exit(1)

    entries = dedupe_entries(all_entries)
    logger.info(f"合併後共找到 {len(entries)} 支不重複影片")

    if not entries:
        logger.warning("頻道中沒有找到影片")
        return {
            "entries": [],
            "entries_to_download": [],
            "existing_count": 0,
            "remaining_count": 0,
        }

    has_deferred_filters = bool(date_after or date_before or min_duration or max_duration)
    if has_deferred_filters:
        # Flat channel listings often do not include upload_date/duration. These filters are enforced
        # by yt-dlp after full video metadata is loaded, so do not let unrelated existing downloads
        # satisfy the target count too early.
        existing_count = 0
        remaining_count = count
    else:
        entries_for_target = [
            entry
            for entry in entries
            if not advanced_filter_reason(entry, title_include, title_exclude)
        ]
        target = calculate_download_target(entries_for_target, downloaded_ids, count)
        existing_count = target["existing_count"]
        remaining_count = target["remaining_count"]
    logger.info(f"本頻道已下載 {existing_count} 支，目標 {count} 支，還需下載 {remaining_count} 支")

    if remaining_count == 0:
        logger.info(f"已達到本頻道目標數量 {count} 支，無需下載新影片")
        return {
            "entries": entries,
            "entries_to_download": [],
            "existing_count": existing_count,
            "remaining_count": remaining_count,
        }

    logger.info(f"找到 {len(entries)} 支影片，開始篩選...")
    result = filter_downloadable_entries(
        entries,
        downloaded_ids,
        title_include,
        title_exclude,
        date_after,
        date_before,
        min_duration,
        max_duration,
    )
    entries_to_download = result["entries"]

    if result["skipped_public"] > 0:
        logger.info(f"已跳過 {result['skipped_public']} 支非公開或無權存取影片")
    if result["skipped_live"] > 0:
        logger.info(f"已跳過 {result['skipped_live']} 支直播/預告影片（只下載 VOD）")
    if result["skipped_advanced"] > 0:
        logger.info(f"已依進階篩選條件跳過 {result['skipped_advanced']} 支影片")

    if not entries_to_download:
        logger.info("沒有需要下載的新影片")
    else:
        logger.info(
            f"找到 {len(entries_to_download)} 支可下載影片，目標下載 {remaining_count} 支新影片（總目標 {count} 支，已有 {existing_count} 支）..."
        )

    return {
        "entries": entries,
        "entries_to_download": entries_to_download,
        "existing_count": existing_count,
        "remaining_count": remaining_count,
    }


def download_videos(  # noqa: C901
    channel_url: str,
    count: int,
    include_shorts: bool,
    retries: int,
    cookies_from_browser: str = "",
    cookies_file: str = "",
    ratelimit: float = 0,
    sleep_seconds: float = 0,
    quality: str = "best",
    progress_callback: Optional[Callable[[Dict], None]] = None,
    title_include: str = "",
    title_exclude: str = "",
    date_after: str = "",
    date_before: str = "",
    min_duration: int = 0,
    max_duration: int = 0,
    write_subs: bool = False,
    sub_langs: str = "zh-Hant,zh-Hans,en",
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

    ffmpeg_path = ensure_ffmpeg_ready()

    # 準備 progress hook 來追蹤下載的檔案
    downloaded_files = {}  # video_id -> filepath
    progress_hook = build_progress_hook(downloaded_files, progress_callback)
    try:
        date_after = normalize_date_filter(date_after, "--date-after")
        date_before = normalize_date_filter(date_before, "--date-before")
        match_filter = build_match_filter(
            include_shorts,
            title_include,
            title_exclude,
            date_after,
            date_before,
            min_duration,
            max_duration,
        )
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # 計算要掃描的候選影片數量（比目標數量更多，以備跳過後回填）。
    # 頻道可能夾雜大量不能下載/需跳過的影片（會員限定、非公開、直播、Shorts、已下載等），
    # 下載時遇到就跳過並往後補，因此候選池要夠大才填得滿使用者設定的數量。
    # 抽清單已改用 flat（便宜），故放寬上限：至少 50，約 count*5，最多 200。
    playlist_extract_count = calculate_playlist_extract_count(count)

    try:
        ydl_opts = build_ytdlp_options(
            DOWNLOAD_DIR,
            ARCHIVE_FILE,
            quality,
            retries,
            include_shorts,
            playlist_extract_count,
            progress_hook,
            match_filter,
            ffmpeg_path,
            cookies_from_browser,
            cookies_file,
            ratelimit,
            write_subs,
            sub_langs,
        )
    except ValueError as e:
        if "cookies" in str(e):
            logger.error(f"瀏覽器 cookies 來源格式錯誤: {e}")
        else:
            logger.error(str(e))
        sys.exit(1)

    log_download_options(
        ffmpeg_path,
        cookies_from_browser,
        cookies_file,
        ratelimit,
        title_include,
        title_exclude,
        date_after,
        date_before,
        min_duration,
        max_duration,
        write_subs,
        sub_langs,
    )

    # 構建頻道 URL（根據是否包含 Shorts 決定從哪些頁面獲取）
    # 註：/videos、/shorts 分頁本身即依最新排序，毋需附加 view/sort 等已失效的 query 參數
    channel_urls = build_channel_urls(channel_url, include_shorts)
    if include_shorts and len(channel_urls) > 1:
        logger.info("將從 Videos 和 Shorts 兩個頁面獲取影片")

    logger.info(f"開始處理頻道: {', '.join(channel_urls)}")
    logger.info(
        f"目標數量: {count}, 包含 Shorts: {include_shorts}, 畫質: {quality}, 重試次數: {retries}"
    )

    downloaded_list = []

    # 階段一：提取頻道影片清單。cookies 載入失敗時（例如 Chrome App-Bound Encryption
    # 擋住讀取），_extract_entries 會自動改用『無 cookies』模式重試——公開頻道不需 cookies。
    all_entries = _extract_entries(
        yt_dlp,
        ydl_opts,
        channel_urls,
        playlist_extract_count,
        cookies_from_browser,
        cookies_file,
    )

    candidate_plan = prepare_entries_to_download(
        all_entries,
        downloaded_ids,
        count,
        title_include,
        title_exclude,
        date_after,
        date_before,
        min_duration,
        max_duration,
    )
    entries_to_download = candidate_plan["entries_to_download"]
    existing_count = candidate_plan["existing_count"]
    remaining_count = candidate_plan["remaining_count"]

    if not entries_to_download:
        return []

    # 階段二：下載（若階段一已 fallback 為無 cookies，ydl_opts 內的 cookies 已被移除）
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            downloaded_list = download_entries_with_ytdlp(
                ydl,
                entries_to_download,
                remaining_count,
                count,
                existing_count,
                downloaded_files,
                sleep_seconds,
            )

    except yt_dlp.utils.DownloadError as e:
        handle_ytdlp_download_error(e, cookies_from_browser or cookies_file)
    except Exception as e:
        logger.error(f"未預期的錯誤: {e}", exc_info=True)
        sys.exit(1)

    return downloaded_list


def print_download_summary(downloaded_list: List[Dict]) -> None:
    """印出單一頻道的下載清單摘要。"""
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


def run_batch_download(
    channels: List[str],
    args,
    progress_callback: Optional[Callable[[Dict], None]] = None,
) -> List[Dict]:
    """批次下載多個頻道；單一頻道失敗（含致命 sys.exit）不中斷整批。

    Returns:
        每個頻道的結果 dict 清單：channel / status / downloaded / error。
    """
    logger.info(f"批次模式：共 {len(channels)} 個頻道")
    results: List[Dict] = []

    for idx, channel in enumerate(channels, 1):
        logger.info("-" * 60)
        logger.info(f"[{idx}/{len(channels)}] 頻道：{channel}")
        try:
            channel_url = normalize_channel_url(channel)
            downloaded = download_videos(
                channel_url,
                args.count,
                args.include_shorts,
                args.retries,
                args.cookies_from_browser,
                args.cookies,
                args.ratelimit,
                args.sleep,
                args.quality,
                progress_callback,
                getattr(args, "title_include", ""),
                getattr(args, "title_exclude", ""),
                getattr(args, "date_after", ""),
                getattr(args, "date_before", ""),
                getattr(args, "min_duration", 0),
                getattr(args, "max_duration", 0),
                getattr(args, "write_subs", False),
                getattr(args, "sub_langs", "zh-Hant,zh-Hans,en"),
            )
            results.append(
                {
                    "channel": channel,
                    "status": "ok",
                    "downloaded": len(downloaded),
                    "downloaded_items": downloaded,
                    "error": None,
                }
            )
        except SystemExit as e:
            # download_videos 在致命錯誤時會 sys.exit；批次中視為該頻道失敗，繼續下一個
            logger.warning(f"頻道提前結束（code={e.code}），繼續下一個：{channel}")
            results.append(
                {
                    "channel": channel,
                    "status": "fail",
                    "downloaded": 0,
                    "downloaded_items": [],
                    "error": f"code={e.code}",
                }
            )
        except Exception as e:  # noqa: BLE001 - 單一頻道任何錯誤都不應中斷整批
            logger.error(f"頻道失敗，繼續下一個：{channel}：{e}")
            results.append(
                {
                    "channel": channel,
                    "status": "fail",
                    "downloaded": 0,
                    "downloaded_items": [],
                    "error": str(e),
                }
            )

    # 批次總結報表
    total_downloaded = sum(r["downloaded"] for r in results)
    ok = [r for r in results if r["status"] == "ok"]
    failed = [r for r in results if r["status"] == "fail"]

    logger.info("=" * 60)
    logger.info("批次下載完成")
    logger.info("=" * 60)
    logger.info(f"頻道：{len(results)} 個（成功 {len(ok)}、失敗 {len(failed)}）")
    logger.info(f"本次共下載 {total_downloaded} 支影片")
    for r in results:
        mark = "✓" if r["status"] == "ok" else "✗"
        detail = f"{r['downloaded']} 支" if r["status"] == "ok" else f"失敗（{r['error']}）"
        logger.info(f"  {mark} {r['channel']}：{detail}")
    if failed:
        logger.info(f"失敗頻道：{', '.join(r['channel'] for r in failed)}")
    logger.info(f"下載紀錄（archive）：{ARCHIVE_FILE}")
    logger.info("=" * 60)
    return results


def run_login() -> int:
    """開啟受控瀏覽器讓使用者登入 YouTube 並保存 cookies。回傳 exit code。"""
    try:
        import chrome_cdp_cookies as cdp
    except ImportError:
        logger.error("缺少 chrome_cdp_cookies 模組，無法執行受控登入")
        return 1
    path = cdp.interactive_login("chrome")
    if path:
        logger.info(f"✓ cookies 已保存：{path}")
        logger.info("之後的下載會自動使用這份 cookies，並於每次執行時 headless 刷新。")
        return 0
    logger.error("登入或取得 cookies 失敗")
    return 1


def managed_cookies_file() -> str:
    """回傳受控登入的 cookies.txt 路徑（headless 刷新優先，否則用既有快取）；無則空字串。

    僅在 Windows 上有效；尚未登入、找不到 Chrome 或非 Windows 一律回傳空字串。
    GUI 與 CLI 共用：登入後下載即自動沿用這份 cookies。
    """
    if sys.platform != "win32":
        return ""
    try:
        import chrome_cdp_cookies as cdp
    except ImportError:
        return ""
    path = cdp.refresh_from_managed("chrome")
    if not path and cdp.managed_cookies_path().exists():
        path = cdp.managed_cookies_path()  # headless 刷新失敗時退用既有快取
    return str(path) if path else ""


def resolve_managed_cookies(cookies_from_browser: str, cookies_file: str):
    """把 Chrome 系的瀏覽器 cookies 來源導向受控瀏覽器 cookies，回傳實際要用的
    (cookies_from_browser, cookies_file)。

    Chrome 127+ 的 App-Bound Encryption 讓 yt-dlp 無法直接讀取 Chrome cookies，因此改用
    本工具的受控瀏覽器（見 chrome_cdp_cookies）：若已登入則 headless 刷新並改用 cookies.txt；
    若尚未設定則提示使用者先登入，本次以無 cookies 繼續（公開頻道仍可下載）。

    非 Windows、未指定瀏覽器來源、已指定 cookies 檔、或非 Chromium 系來源（如 firefox）
    一律原樣回傳，交由 yt-dlp 原生處理。
    """
    if cookies_file or not cookies_from_browser or sys.platform != "win32":
        return cookies_from_browser, cookies_file
    try:
        import chrome_cdp_cookies as cdp
    except ImportError:
        return cookies_from_browser, cookies_file
    spec = cookies_from_browser.split("::")[0].split(":")[0].split("+")[0].strip().lower()
    if not cdp.is_chromium_family(spec):
        return cookies_from_browser, cookies_file

    path = managed_cookies_file()
    if path:
        logger.info(f"使用受控瀏覽器 cookies：{path}")
        return "", path

    logger.warning("Chrome 127+ 無法被外部工具直接讀取 cookies（App-Bound Encryption）。")
    logger.warning(
        "請先在受控視窗登入 YouTube（CLI：yt_fetch --login；GUI：登入按鈕）即可長期自動使用。"
    )
    logger.warning("本次先以『無 cookies』繼續（公開頻道通常不需 cookies）。")
    return "", ""


def maybe_use_managed_cookies(args) -> None:
    """CLI 入口：就地把 args 的 cookies 來源換成受控瀏覽器 cookies。"""
    args.cookies_from_browser, args.cookies = resolve_managed_cookies(
        args.cookies_from_browser, args.cookies
    )


def main():  # noqa: C901
    """主函數"""
    # --help / -h：略過 venv 準備，讓 argparse 直接輸出說明，不夾帶建立 venv 的 log
    wants_help = any(a in ("-h", "--help") for a in sys.argv[1:])

    # 確保在 venv 中（若需重啟，避免在重啟前先印橫幅造成重複輸出）
    if not wants_help and ensure_venv_and_restart():
        return  # 已重新啟動，此執行結束

    # 先解析參數（--help / 參數錯誤會在此乾淨退出，不夾帶 banner 或 log）
    args = parse_args()

    # 確認要實際執行後，才建立設定檔（避免 --help 也產生檔案）
    write_default_config_if_missing()

    # 受控登入模式：開瀏覽器登入 YouTube 取得 cookies 後結束
    if args.login:
        sys.exit(run_login())

    # GUI 模式：交給 Tkinter 介面（沿用相同的下載邏輯）
    if args.gui:
        import yt_fetch_gui

        sys.exit(yt_fetch_gui.launch())

    logger.info("=" * 60)
    logger.info("YouTube 頻道影片下載工具")
    logger.info("=" * 60)

    # 套用設定檔指定的下載資料夾（無對應 CLI 旗標，故僅由 ini 提供）
    cfg = load_config()
    if cfg.get("download_dir"):
        set_download_dir(Path(cfg["download_dir"]))

    # Chrome 系 cookies 導向受控瀏覽器（解決 Chrome 127+ ABE 無法直接讀取的問題）
    maybe_use_managed_cookies(args)

    logger.info(f"數量: {args.count}")
    logger.info(f"包含 Shorts: {args.include_shorts}")
    logger.info(f"下載畫質: {args.quality}")
    logger.info(f"重試次數: {args.retries}")
    if args.cookies_from_browser:
        logger.info(f"使用瀏覽器 cookies: {args.cookies_from_browser}")
    elif args.cookies:
        logger.info(f"使用 cookies 檔案: {args.cookies}")
    if args.ratelimit > 0:
        logger.info(f"下載速率限制: {args.ratelimit} MB/s")
    if args.sleep > 0:
        logger.info(f"下載間隔: {args.sleep} 秒")
    if args.title_include:
        logger.info(f"標題必須包含: {args.title_include}")
    if args.title_exclude:
        logger.info(f"標題排除關鍵字: {args.title_exclude}")
    if args.date_after or args.date_before:
        logger.info(f"上傳日期篩選: {args.date_after or '不限'} ~ {args.date_before or '不限'}")
    if args.min_duration or args.max_duration:
        logger.info(
            f"影片長度篩選: {args.min_duration or '不限'} ~ {args.max_duration or '不限'} 秒"
        )
    if args.write_subs:
        logger.info(f"下載字幕: {', '.join(parse_subtitle_languages(args.sub_langs))}")

    # 批次模式：逐一處理頻道清單，單一失敗不中斷整批
    if args.channels_file:
        channels = read_channels_file(args.channels_file)
        if not channels:
            logger.error(f"頻道清單檔沒有有效頻道：{args.channels_file}")
            sys.exit(1)
        run_batch_download(channels, args)
        sys.exit(0)

    # 單一頻道
    channel_url = normalize_channel_url(args.channel)
    logger.info(f"頻道: {channel_url}")
    downloaded_list = download_videos(
        channel_url,
        args.count,
        args.include_shorts,
        args.retries,
        args.cookies_from_browser,
        args.cookies,
        args.ratelimit,
        args.sleep,
        args.quality,
        None,
        args.title_include,
        args.title_exclude,
        args.date_after,
        args.date_before,
        args.min_duration,
        args.max_duration,
        args.write_subs,
        args.sub_langs,
    )

    logger.info("=" * 60)
    logger.info("下載完成")
    logger.info("=" * 60)
    print_download_summary(downloaded_list)
    logger.info(f"下載紀錄（archive）：{ARCHIVE_FILE}")
    logger.info("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n已取消（使用者中斷）")
        sys.exit(130)
