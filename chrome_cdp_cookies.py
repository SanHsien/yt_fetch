#!/usr/bin/env python3
"""透過 Chrome DevTools Protocol (CDP) 取得 Chrome 登入中的 cookies。

【為什麼需要這個模組】
Chrome 127+ 啟用 App-Bound Encryption (ABE)：cookie 解密金鑰綁定 Chrome 執行檔本身，
任何外部程式（含 yt-dlp）都無法直接解密 v20 cookies。唯一仍能取得「真實登入 cookies」
的可行途徑，是讓 Chrome 自己解密——也就是啟動一個帶 `--remote-debugging-port` 的 Chrome，
再用 CDP 的 `Storage.getCookies` 取回 Chrome 已解密的明文 cookies。

【做法】
1. 找到 chrome.exe 與使用者 User Data 目錄。
2. 把 `Local State`（含 ABE 金鑰）與指定 profile 的 `Network/Cookies` 複製到一個暫存
   user-data-dir（Chrome 136+ 禁止在「預設」資料夾開 remote debugging，故必用獨立資料夾；
   而同一台機器、同一個 chrome.exe 可解密複製過來的 ABE 金鑰，因此登入 cookies 仍可解出）。
3. 以 headless 啟動該 chrome.exe 指向暫存資料夾並開 remote debugging。
4. 連上 CDP，呼叫 `Storage.getCookies` 取回明文 cookies，寫成 Netscape cookies.txt。
5. 關閉暫存 Chrome 並清除暫存資料夾。

【邊界】
- 僅讀取使用者自己機器上、自己登入的 cookies；不繞過任何 YouTube 限制，只是把「Chrome
  能解密的東西」交給 yt-dlp 使用。
- 只支援 Windows 上的 Chrome / Chromium 系瀏覽器；其他情況回傳 None 由呼叫端決定後援。
"""

import json
import logging
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
from base64 import b64encode
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Chromium 系瀏覽器在 Windows 上的 User Data 相對路徑（相對於 %LOCALAPPDATA%）。
_CHROMIUM_USER_DATA = {
    "chrome": ["Google", "Chrome", "User Data"],
    "chromium": ["Chromium", "User Data"],
    "edge": ["Microsoft", "Edge", "User Data"],
    "brave": ["BraveSoftware", "Brave-Browser", "User Data"],
}

# 各瀏覽器 chrome.exe 候選路徑（{pf} 會以各 Program Files 變體展開）。
_BROWSER_EXES = {
    "chrome": [r"{pf}\Google\Chrome\Application\chrome.exe"],
    "chromium": [r"{pf}\Chromium\Application\chrome.exe"],
    "edge": [r"{pf}\Microsoft\Edge\Application\msedge.exe"],
    "brave": [r"{pf}\BraveSoftware\Brave-Browser\Application\brave.exe"],
}

_YOUTUBE_COOKIE_DOMAINS = ("youtube.com", "google.com", "googlevideo.com")


def is_chromium_family(browser: str) -> bool:
    """判斷瀏覽器是否為本模組支援的 Chromium 系。"""
    return browser.lower() in _CHROMIUM_USER_DATA


def _program_files_dirs() -> List[str]:
    seen = []
    for var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        val = os.environ.get(var)
        if val and val not in seen:
            seen.append(val)
    return seen or [r"C:\Program Files"]


def find_browser_executable(browser: str) -> Optional[Path]:
    """找出瀏覽器執行檔；找不到回傳 None。"""
    browser = browser.lower()
    for tmpl in _BROWSER_EXES.get(browser, []):
        for pf in _program_files_dirs():
            candidate = Path(tmpl.format(pf=pf))
            if candidate.exists():
                return candidate
    return None


def find_user_data_dir(browser: str) -> Optional[Path]:
    """找出瀏覽器的 User Data 目錄；找不到回傳 None。"""
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return None
    parts = _CHROMIUM_USER_DATA.get(browser.lower())
    if not parts:
        return None
    path = Path(local).joinpath(*parts)
    return path if path.exists() else None


def _win_shared_copy(src: Path, dst: Path) -> None:
    """以完整共享模式（READ|WRITE|DELETE）複製檔案。

    Chrome 執行中時會鎖住 Cookies DB，預設的 open/shutil.copy 會踩 WinError 32
    （sharing violation）。改用 CreateFileW 指定共享旗標即可讀取被鎖檔案——這也是
    yt-dlp 讀取開啟中瀏覽器 cookie DB 的相同做法。
    """
    import ctypes
    from ctypes import wintypes

    GENERIC_READ = 0x80000000
    FILE_SHARE_ALL = 0x1 | 0x2 | 0x4  # READ | WRITE | DELETE
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID_HANDLE = ctypes.c_void_p(-1).value

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel32.ReadFile.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    # 明確宣告 HANDLE 參數型別，避免 64 位元 handle 被 ctypes 預設的 c_int 截斷
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    handle = kernel32.CreateFileW(
        str(src), GENERIC_READ, FILE_SHARE_ALL, None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None
    )
    if not handle or handle == INVALID_HANDLE:
        raise OSError(ctypes.get_last_error(), f"CreateFileW 失敗：{src}")
    try:
        buf = ctypes.create_string_buffer(1024 * 1024)
        read = wintypes.DWORD(0)
        with open(dst, "wb") as out:
            while True:
                ok = kernel32.ReadFile(handle, buf, len(buf), ctypes.byref(read), None)
                if not ok:
                    raise OSError(ctypes.get_last_error(), f"ReadFile 失敗：{src}")
                if read.value == 0:
                    break
                out.write(buf.raw[: read.value])
    finally:
        kernel32.CloseHandle(handle)


def _stage_profile(user_data_dir: Path, profile: str, staging: Path) -> bool:
    """把解密所需的最少檔案複製到暫存 user-data-dir。

    需要：`Local State`（ABE 金鑰）+ `<profile>/Network/Cookies`（cookie DB，含 WAL）。
    另複製 `<profile>/Preferences`（若有）以降低 Chrome 啟動時的初始化雜訊。
    """
    local_state = user_data_dir / "Local State"
    if not local_state.exists():
        logger.error(f"找不到 Local State：{local_state}")
        return False

    src_profile = user_data_dir / profile
    cookies_db = src_profile / "Network" / "Cookies"
    if not cookies_db.exists():
        logger.error(f"找不到 cookie 資料庫：{cookies_db}（profile={profile!r} 是否正確？）")
        return False

    try:
        _win_shared_copy(local_state, staging / "Local State")
        dst_network = staging / profile / "Network"
        dst_network.mkdir(parents=True, exist_ok=True)
        # Cookies 本體與可能存在的 WAL/journal 一併複製，確保拿到最新寫入。
        for name in ("Cookies", "Cookies-journal", "Cookies-wal", "Cookies-shm"):
            src = src_profile / "Network" / name
            if src.exists():
                _win_shared_copy(src, dst_network / name)
        prefs = src_profile / "Preferences"
        if prefs.exists():
            _win_shared_copy(prefs, staging / profile / "Preferences")
        return True
    except OSError as e:
        # cookie DB 在 Chrome 開啟時通常仍可共享讀取；若失敗給出明確訊息。
        logger.error(f"複製 Chrome profile 檔案失敗：{e}")
        return False


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_devtools(port: int, timeout: float) -> Optional[str]:
    """等 Chrome 起來，回傳 browser 層級的 webSocketDebuggerUrl。"""
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/json/version"
    last_err: Optional[Exception] = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:  # nosec B310 - 固定 localhost
                data = json.loads(resp.read().decode("utf-8"))
            ws = data.get("webSocketDebuggerUrl")
            if ws:
                return ws
        except Exception as e:  # noqa: BLE001 - 啟動初期連不上屬正常，重試到逾時
            last_err = e
        time.sleep(0.3)
    if last_err:
        logger.debug(f"等待 DevTools 端點逾時：{last_err}")
    return None


def _remote_debugging_args(port: int) -> List[str]:
    """只在 loopback 開放 CDP，且不接受萬用 WebSocket origin。"""
    return [
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
    ]


# --- 極簡 WebSocket 客戶端：僅供一次性 CDP 請求/回應使用（不依賴第三方套件）---


def _ws_connect(ws_url: str, timeout: float) -> socket.socket:
    # ws_url 形如 ws://127.0.0.1:<port>/devtools/browser/<id>
    assert ws_url.startswith("ws://")
    rest = ws_url[len("ws://") :]
    hostport, _, path = rest.partition("/")
    host, _, port_s = hostport.partition(":")
    port = int(port_s or "80")
    path = "/" + path

    sock = socket.create_connection((host, port), timeout=timeout)
    key = b64encode(os.urandom(16)).decode("ascii")
    handshake = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    sock.sendall(handshake.encode("ascii"))

    # 讀取 HTTP 升級回應（到 \r\n\r\n 為止）
    buf = b""
    sock.settimeout(timeout)
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("WebSocket 握手失敗：連線關閉")
        buf += chunk
    status_line = buf.split(b"\r\n", 1)[0]
    if b" 101 " not in status_line:
        # 註：f-string 的 {} 內不可含反斜線（Python 3.12 前），故先取出 status_line
        raise ConnectionError(f"WebSocket 握手未回 101：{status_line!r}")
    return sock


def _ws_send_text(sock: socket.socket, text: str) -> None:
    payload = text.encode("utf-8")
    header = bytearray([0x81])  # FIN + text
    mask_bit = 0x80
    n = len(payload)
    if n < 126:
        header.append(mask_bit | n)
    elif n < 65536:
        header.append(mask_bit | 126)
        header += struct.pack(">H", n)
    else:
        header.append(mask_bit | 127)
        header += struct.pack(">Q", n)
    mask = os.urandom(4)
    header += mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    sock.sendall(bytes(header) + masked)


def _ws_recv_exact(sock: socket.socket, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("WebSocket 連線提前關閉")
        data += chunk
    return data


def _ws_recv_message(sock: socket.socket) -> Tuple[int, bytes]:
    """讀取一則完整訊息（自動重組分片），回傳 (opcode, payload)。"""
    message = b""
    first_opcode = None
    while True:
        b0, b1 = _ws_recv_exact(sock, 2)
        fin = b0 & 0x80
        opcode = b0 & 0x0F
        length = b1 & 0x7F
        if length == 126:
            length = struct.unpack(">H", _ws_recv_exact(sock, 2))[0]
        elif length == 127:
            length = struct.unpack(">Q", _ws_recv_exact(sock, 8))[0]
        payload = _ws_recv_exact(sock, length) if length else b""
        if opcode == 0x9:  # ping -> 回 pong（伺服器→客戶端不遮罩，這裡簡化忽略）
            continue
        if opcode in (0x1, 0x2, 0x0):
            if first_opcode is None:
                first_opcode = opcode
            message += payload
            if fin:
                return first_opcode, message
        elif opcode == 0x8:  # close
            return opcode, payload
        # 其他控制幀忽略


def _ws_request(
    sock: socket.socket, msg_id: int, method: str, params: Optional[Dict], timeout: float
) -> Optional[Dict]:
    """送一個 CDP 命令並等對應 id 的回應，回傳 result（失敗回 None）。"""
    payload = {"id": msg_id, "method": method}
    if params:
        payload["params"] = params
    _ws_send_text(sock, json.dumps(payload))
    deadline = time.time() + timeout
    while time.time() < deadline:
        opcode, data = _ws_recv_message(sock)
        if opcode == 0x8:
            return None
        try:
            resp = json.loads(data.decode("utf-8"))
        except ValueError:
            continue
        if resp.get("id") == msg_id:
            if "error" in resp:
                logger.debug(f"CDP {method} 回錯：{resp['error']}")
                return None
            return resp.get("result", {})
    return None


def _cdp_get_all_cookies(ws_url: str, timeout: float) -> Optional[List[Dict]]:
    sock = None
    try:
        sock = _ws_connect(ws_url, timeout)
        # 先試瀏覽器層級 Storage.getCookies
        result = _ws_request(sock, 1, "Storage.getCookies", None, timeout)
        cookies = (result or {}).get("cookies", []) if result is not None else []
        logger.info(f"Storage.getCookies 取得 {len(cookies)} 筆")
        if cookies:
            return cookies

        # 備援：開一個分頁、啟用 Network、用 Network.getAllCookies（有時較完整）
        logger.info("改試分頁層級 Network.getAllCookies...")
        created = _ws_request(sock, 2, "Target.createTarget", {"url": "about:blank"}, timeout)
        target_id = (created or {}).get("targetId")
        if not target_id:
            logger.debug("Target.createTarget 失敗")
            return cookies or None
        attached = _ws_request(
            sock, 3, "Target.attachToTarget", {"targetId": target_id, "flatten": True}, timeout
        )
        session_id = (attached or {}).get("sessionId")
        if not session_id:
            logger.debug("attachToTarget 失敗")
            return cookies or None

        # 在 session 內送 Network.enable + getAllCookies（夾帶 sessionId）
        def _session_send(mid, method, params=None):
            p = {"id": mid, "method": method, "sessionId": session_id}
            if params:
                p["params"] = params
            _ws_send_text(sock, json.dumps(p))
            dl = time.time() + timeout
            while time.time() < dl:
                op, dat = _ws_recv_message(sock)
                if op == 0x8:
                    return None
                try:
                    r = json.loads(dat.decode("utf-8"))
                except ValueError:
                    continue
                if r.get("id") == mid:
                    return r.get("result", {}) if "error" not in r else None
            return None

        _session_send(4, "Network.enable")
        r2 = _session_send(5, "Network.getAllCookies")
        c2 = (r2 or {}).get("cookies", [])
        logger.info(f"Network.getAllCookies 取得 {len(c2)} 筆")
        return c2 or cookies or None
    except Exception as e:  # noqa: BLE001 - 任何連線/協定錯誤皆視為取得失敗
        logger.error(f"CDP 取得 cookies 失敗：{e}")
        return None
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass


def _graceful_close(
    ws_url: Optional[str], proc: Optional[subprocess.Popen], timeout: float = 8.0
) -> None:
    """以 CDP Browser.close 優雅關閉 Chrome（會 flush 登入態到磁碟），再等程序結束。

    優雅關閉很重要：硬殺（terminate/kill）不會把記憶體中的 cookie 寫回 profile，
    會導致受控 profile 在磁碟上仍是登出狀態、日後無法 headless 刷新。
    """
    if ws_url:
        try:
            sock = _ws_connect(ws_url, timeout=5.0)
            try:
                _ws_send_text(sock, json.dumps({"id": 999, "method": "Browser.close"}))
                time.sleep(0.5)
            finally:
                sock.close()
        except Exception:  # noqa: BLE001 - 關閉失敗時退回硬殺
            pass
    if proc is None:
        return
    try:
        proc.wait(timeout=timeout)
        return
    except Exception:  # noqa: BLE001
        pass
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:  # noqa: BLE001
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass


def _write_netscape_cookies(cookies: List[Dict], out_path: Path) -> int:
    """只把 YouTube 存取所需網域寫成 Netscape cookies.txt。"""
    lines = [
        "# Netscape HTTP Cookie File",
        "# 由 yt_fetch 透過 Chrome DevTools Protocol 產生；請勿手動編輯。",
        "",
    ]
    count = 0
    for c in cookies:
        domain = c.get("domain", "")
        if not domain:
            continue
        normalized_domain = domain.lstrip(".").lower()
        if not any(
            normalized_domain == allowed or normalized_domain.endswith(f".{allowed}")
            for allowed in _YOUTUBE_COOKIE_DOMAINS
        ):
            continue
        include_sub = "TRUE" if domain.startswith(".") else "FALSE"
        path = c.get("path", "/") or "/"
        secure = "TRUE" if c.get("secure") else "FALSE"
        expires = c.get("expires", 0)
        # session cookie（expires 為 -1 或 0）以 0 表示
        expires = int(expires) if expires and expires > 0 else 0
        name = c.get("name", "")
        value = c.get("value", "")
        if not name:
            continue
        lines.append("\t".join([domain, include_sub, path, secure, str(expires), name, value]))
        count += 1
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return count


def export_cookies_via_cdp(
    browser: str,
    profile: Optional[str],
    out_path: Path,
    startup_timeout: float = 25.0,
) -> Optional[Path]:
    """以 CDP 從 Chrome/Chromium 取得登入 cookies，寫成 Netscape cookies.txt。

    成功回傳 out_path；任何環節失敗回傳 None（由呼叫端決定後援）。
    """
    if sys.platform != "win32":
        logger.debug("CDP cookie 擷取目前僅支援 Windows")
        return None

    browser = (browser or "").lower()
    if not is_chromium_family(browser):
        logger.debug(f"{browser!r} 非 Chromium 系，略過 CDP 擷取")
        return None

    profile = profile or "Default"

    exe = find_browser_executable(browser)
    if not exe:
        logger.error(f"找不到 {browser} 執行檔，無法以 CDP 擷取 cookies")
        return None

    user_data_dir = find_user_data_dir(browser)
    if not user_data_dir:
        logger.error(f"找不到 {browser} 的 User Data 目錄")
        return None

    staging = Path(tempfile.mkdtemp(prefix="yt_fetch_cdp_"))
    proc = None
    try:
        logger.info(f"以 CDP 從 {browser}（profile={profile}）擷取 cookies...")
        if not _stage_profile(user_data_dir, profile, staging):
            return None

        port = _free_port()
        # 預設 headless；設環境變數 YT_FETCH_CDP_HEADLESS=0 可改用可見視窗（除錯用）。
        use_headless = os.environ.get("YT_FETCH_CDP_HEADLESS", "1") != "0"
        cmd = [
            str(exe),
            f"--user-data-dir={staging}",
            f"--profile-directory={profile}",
            *_remote_debugging_args(port),
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-sync",
            "--window-size=1,1",
            "about:blank",
        ]
        if use_headless:
            cmd.insert(5, "--headless=new")
        creationflags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )

        ws_url = _wait_devtools(port, startup_timeout)
        if not ws_url:
            logger.error("Chrome remote debugging 端點未就緒（可能被 Chrome 136+ 限制或啟動失敗）")
            return None

        # 讓網路服務有時間載入並解密 cookie DB 後再查詢。
        time.sleep(2.0)
        cookies = _cdp_get_all_cookies(ws_url, timeout=15.0)
        if not cookies:
            logger.error("CDP 未取得任何 cookies")
            return None

        n = _write_netscape_cookies(cookies, out_path)
        if n == 0:
            logger.error("CDP 取得 cookies 但寫入 0 筆")
            return None
        logger.info(f"✓ 已透過 CDP 取得 {n} 筆 cookies → {out_path}")
        return out_path
    finally:
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:  # noqa: BLE001 - 清理階段不阻斷
                try:
                    proc.kill()
                except Exception:  # noqa: BLE001
                    pass
        shutil.rmtree(staging, ignore_errors=True)


# ---------------------------------------------------------------------------
# 受控瀏覽器（managed browser）流程
#
# 比「複製主 profile 再解密」穩健得多：開一個本工具專屬的 Chrome 實例（獨立
# user-data-dir，故不受 Chrome 136+ 對預設資料夾 remote debugging 的限制），讓使用者
# 在裡面登入 YouTube。之後 CDP 直接取得「該實例自己的」明文 cookies——Chrome 自行解密，
# 不碰 ABE、不碰檔案鎖、也不需要關閉使用者的主 Chrome。登入狀態持久保存在專屬資料夾，
# 後續可 headless 自動刷新 cookies。
# ---------------------------------------------------------------------------

# 出現任一登入 cookie 即視為已登入 YouTube。
_LOGIN_COOKIE_NAMES = {
    "SID",
    "SSID",
    "SAPISID",
    "APISID",
    "LOGIN_INFO",
    "__Secure-1PSID",
    "__Secure-3PSID",
    "__Secure-1PAPISID",
    "__Secure-3PAPISID",
}


def managed_data_dir() -> Path:
    """本工具專屬 Chrome 實例的 user-data-dir（持久保存登入）。"""
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "yt_fetch" / "browser"
    base.mkdir(parents=True, exist_ok=True)
    return base


def managed_cookies_path() -> Path:
    """受控流程產生的 cookies.txt 標準位置。"""
    return managed_data_dir().parent / "cookies.txt"


def has_login_cookies(cookies: List[Dict]) -> bool:
    """cookies 中是否含 YouTube/Google 登入態 cookie。"""
    for c in cookies:
        domain = c.get("domain", "")
        if ("youtube" in domain or "google" in domain) and c.get("name") in _LOGIN_COOKIE_NAMES:
            return True
    return False


def _launch_managed(
    browser: str, port: int, headless: bool, url: str
) -> Optional[subprocess.Popen]:
    exe = find_browser_executable(browser)
    if not exe:
        logger.error(f"找不到 {browser} 執行檔")
        return None
    data_dir = managed_data_dir()
    cmd = [
        str(exe),
        f"--user-data-dir={data_dir}",
        *_remote_debugging_args(port),
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",
        # 關閉視窗即完全退出，避免背景程序卡住同一 user-data-dir 的後續 headless 刷新。
        "--disable-background-mode",
    ]
    if headless:
        cmd += ["--headless=new", "--window-size=1,1"]
    cmd.append(url)
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if headless else 0
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def interactive_login(
    browser: str = "chrome",
    out_path: Optional[Path] = None,
    login_timeout: float = 300.0,
) -> Optional[Path]:
    """開啟受控（可見）瀏覽器讓使用者登入 YouTube，登入後輸出 cookies.txt。

    會輪詢 CDP 直到偵測到登入 cookie 或逾時。成功回傳 cookies.txt 路徑，否則 None。
    """
    if sys.platform != "win32" or not is_chromium_family(browser):
        logger.error("受控登入目前僅支援 Windows 的 Chrome/Chromium 系瀏覽器")
        return None

    out_path = out_path or managed_cookies_path()
    port = _free_port()
    proc = _launch_managed(browser, port, headless=False, url="https://www.youtube.com/")
    if proc is None:
        return None
    ws_url = None
    try:
        ws_url = _wait_devtools(port, timeout=30.0)
        if not ws_url:
            logger.error("受控瀏覽器 remote debugging 端點未就緒")
            return None

        logger.info(
            "已開啟受控瀏覽器，請在該視窗登入 YouTube（等待中，最長 %d 秒）...", int(login_timeout)
        )
        deadline = time.time() + login_timeout
        cookies: List[Dict] = []
        while time.time() < deadline:
            cookies = _cdp_get_all_cookies(ws_url, timeout=15.0) or []
            if has_login_cookies(cookies):
                logger.info("✓ 偵測到登入態 cookies")
                break
            time.sleep(3)
        else:
            logger.warning("等待登入逾時；若你已登入，仍會輸出目前 cookies")

        if not cookies:
            cookies = _cdp_get_all_cookies(ws_url, timeout=15.0) or []
        if not cookies:
            logger.error("未取得任何 cookies")
            return None
        n = _write_netscape_cookies(cookies, out_path)
        logger.info(f"✓ 已輸出 {n} 筆 cookies → {out_path}")
        return out_path if n else None
    finally:
        # 優雅關閉，讓 Chrome 把登入態寫回受控 profile，日後可 headless 刷新
        _graceful_close(ws_url, proc)


def refresh_from_managed(
    browser: str = "chrome",
    out_path: Optional[Path] = None,
    require_login: bool = True,
) -> Optional[Path]:
    """以既有的受控（已登入）profile，headless 取得最新 cookies 並更新 cookies.txt。

    若 require_login 為真但 profile 尚未登入（無登入 cookie），回傳 None 由呼叫端提示先登入。
    需確保受控瀏覽器未在前景開啟（同一 user-data-dir 不可同時兩個實例）。
    """
    if sys.platform != "win32" or not is_chromium_family(browser):
        return None
    if not (managed_data_dir() / "Default").exists():
        logger.debug("受控 profile 尚未建立（需先執行一次互動登入）")
        return None

    out_path = out_path or managed_cookies_path()
    port = _free_port()
    proc = _launch_managed(browser, port, headless=True, url="https://www.youtube.com/")
    if proc is None:
        return None
    ws_url = None
    try:
        ws_url = _wait_devtools(port, timeout=25.0)
        if not ws_url:
            logger.debug("受控瀏覽器（headless）端點未就緒")
            return None
        time.sleep(2.0)
        cookies = _cdp_get_all_cookies(ws_url, timeout=15.0) or []
        if not cookies:
            return None
        if require_login and not has_login_cookies(cookies):
            logger.info("受控 profile 尚未登入 YouTube；請先執行一次互動登入")
            return None
        n = _write_netscape_cookies(cookies, out_path)
        logger.info(f"✓ 已更新 {n} 筆 cookies → {out_path}")
        return out_path if n else None
    finally:
        _graceful_close(ws_url, proc)


if __name__ == "__main__":
    # 手動測試：
    #   python chrome_cdp_cookies.py login            # 受控視窗登入並輸出 cookies.txt
    #   python chrome_cdp_cookies.py refresh           # headless 由已登入 profile 刷新
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    mode = sys.argv[1] if len(sys.argv) > 1 else "login"
    if mode == "refresh":
        result = refresh_from_managed("chrome")
    else:
        result = interactive_login("chrome")
    print("OK:" if result else "FAILED", result or "")
    sys.exit(0 if result else 1)
