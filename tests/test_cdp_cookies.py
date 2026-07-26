"""chrome_cdp_cookies 純函式單元測試（不啟動瀏覽器、不連線）。"""

import chrome_cdp_cookies as cdp


def test_is_chromium_family():
    assert cdp.is_chromium_family("chrome")
    assert cdp.is_chromium_family("Chrome")
    assert cdp.is_chromium_family("edge")
    assert cdp.is_chromium_family("brave")
    assert cdp.is_chromium_family("chromium")
    assert not cdp.is_chromium_family("firefox")
    assert not cdp.is_chromium_family("safari")


def test_has_login_cookies_true_with_auth_cookie():
    cookies = [
        {"domain": ".youtube.com", "name": "YSC"},
        {"domain": ".google.com", "name": "SAPISID"},  # 登入態
    ]
    assert cdp.has_login_cookies(cookies)


def test_has_login_cookies_false_when_only_baseline():
    cookies = [
        {"domain": ".youtube.com", "name": "YSC"},
        {"domain": ".youtube.com", "name": "VISITOR_INFO1_LIVE"},
    ]
    assert not cdp.has_login_cookies(cookies)


def test_has_login_cookies_ignores_login_name_on_other_domain():
    # 登入 cookie 名稱但網域非 google/youtube，不算登入
    cookies = [{"domain": ".example.com", "name": "SID"}]
    assert not cdp.has_login_cookies(cookies)


def test_write_netscape_cookies_format_and_count(tmp_path):
    out = tmp_path / "cookies.txt"
    cookies = [
        {
            "domain": ".youtube.com",
            "name": "SID",
            "value": "abc",
            "path": "/",
            "secure": True,
            "expires": 1893456000,
        },
        {  # host-only（不以點開頭）→ includeSubdomains FALSE
            "domain": "www.youtube.com",
            "name": "PREF",
            "value": "x",
            "path": "/",
            "secure": False,
            "expires": -1,  # session → 0
        },
        {"domain": "", "name": "skip", "value": "1"},  # 無網域 → 跳過
        {"domain": ".x.com", "name": "", "value": "1"},  # 無名稱 → 跳過
        {  # 其他網站的有效 cookie 也不可寫出
            "domain": ".example.com",
            "name": "SESSION",
            "value": "secret",
            "path": "/",
        },
    ]
    n = cdp._write_netscape_cookies(cookies, out)
    assert n == 2

    body = out.read_text(encoding="utf-8")
    assert body.startswith("# Netscape HTTP Cookie File")
    lines = [ln for ln in body.splitlines() if ln and not ln.startswith("#")]
    assert len(lines) == 2

    sid = next(ln for ln in lines if "\tSID\t" in ln)
    fields = sid.split("\t")
    # domain, includeSub, path, secure, expires, name, value
    assert fields[0] == ".youtube.com"
    assert fields[1] == "TRUE"  # 以點開頭
    assert fields[3] == "TRUE"  # secure
    assert fields[4] == "1893456000"
    assert fields[5] == "SID"
    assert fields[6] == "abc"

    pref = next(ln for ln in lines if "\tPREF\t" in ln)
    pf = pref.split("\t")
    assert pf[1] == "FALSE"  # host-only
    assert pf[3] == "FALSE"  # not secure
    assert pf[4] == "0"  # session cookie 標為 0


def test_write_netscape_cookies_keeps_only_youtube_required_domains(tmp_path):
    out = tmp_path / "cookies.txt"
    cookies = [
        {"domain": ".youtube.com", "name": "SID", "value": "yt"},
        {"domain": "accounts.google.com", "name": "SID", "value": "google"},
        {"domain": ".googlevideo.com", "name": "AUTH", "value": "video"},
        {"domain": ".example.com", "name": "SESSION", "value": "secret"},
    ]

    assert cdp._write_netscape_cookies(cookies, out) == 3
    body = out.read_text(encoding="utf-8")
    records = [line.split("\t") for line in body.splitlines() if line and not line.startswith("#")]
    assert {record[0].removeprefix(".") for record in records} == {
        "youtube.com",
        "accounts.google.com",
        "googlevideo.com",
    }
    assert {record[6] for record in records} == {"yt", "google", "video"}


def test_remote_debugging_args_bind_loopback_without_wildcard_origin():
    args = cdp._remote_debugging_args(9222)

    assert "--remote-debugging-port=9222" in args
    assert "--remote-debugging-address=127.0.0.1" in args
    assert not any(arg.startswith("--remote-allow-origins") for arg in args)


def test_managed_paths_under_localappdata(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    data_dir = cdp.managed_data_dir()
    assert data_dir == tmp_path / "yt_fetch" / "browser"
    assert data_dir.exists()  # 會自動建立
    assert cdp.managed_cookies_path() == tmp_path / "yt_fetch" / "cookies.txt"


def test_parse_program_files_dirs_fallback(monkeypatch):
    for var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        monkeypatch.delenv(var, raising=False)
    assert cdp._program_files_dirs() == [r"C:\Program Files"]
