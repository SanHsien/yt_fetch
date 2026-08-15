# ChannelDepot

[繁體中文](README.md)

[![Release](https://img.shields.io/github/v/release/SanHsien/yt_fetch?sort=semver&display_name=tag)](https://github.com/SanHsien/yt_fetch/releases/latest)
[![CI](https://github.com/SanHsien/yt_fetch/actions/workflows/code-check.yml/badge.svg?branch=main)](https://github.com/SanHsien/yt_fetch/actions/workflows/code-check.yml)
[![CodeQL](https://github.com/SanHsien/yt_fetch/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/SanHsien/yt_fetch/actions/workflows/codeql.yml)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Source-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#platform-support)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**ChannelDepot** is a lightweight, portable YouTube channel archiving tool. Give it a channel and a target count; it uses `yt-dlp` to find the newest accessible videos, applies Shorts / quality / date / title / duration filters, and downloads the results locally.

Windows users can use the standalone GUI build. Advanced users can use the CLI, batch channel imports, and their own sign-in cookies.

> The project was formerly named `yt_fetch`. To avoid breaking existing users, `yt_fetch.py`, `yt-fetch`, `yt-fetch-gui`, and the current Windows Release filenames keep their legacy names for now.

> Use it only for content you are authorized to download or back up. Sign-in support does not bypass paywalls, memberships, private videos, or other YouTube access controls.

## Screenshot

[![ChannelDepot main window](docs/screenshots/main-window.png)](docs/screenshots/main-window.png)

The GUI downloads in the background and shows progress, logs, and results. It can import multiple channels, apply common quality profiles and advanced filters, and export the current download record.

## Download the portable Windows build

1. Open the [Latest Release](https://github.com/SanHsien/yt_fetch/releases/latest).
2. Download `yt_fetch-vX.Y.Z-windows-x64.zip`.
3. Extract it and run `yt_fetch.exe`.
4. Downloads go to the adjacent `download/` folder by default; each Release also includes a `.sha256` checksum.

The Windows executable is currently unsigned, so SmartScreen may warn on first launch. Only obtain the executable from this repository's Releases and verify its source.

> The Windows build bundles the `yt-dlp` version current at release time. If YouTube changes and an older build stops working, check for a newer Release first.

## Why ChannelDepot

- **One download core for GUI and CLI**: click through the GUI or automate from the command line.
- **Channel-focused workflow**: designed around “back up the newest N videos from this channel,” not every possible downloader feature.
- **Batch jobs**: import channel lists in the GUI; one failed channel does not stop the whole batch.
- **Useful filters**: Shorts, maximum quality, title, date, duration, and subtitle language.
- **Idempotent downloads**: a download archive plus YouTube video IDs in filenames prevent repeat downloads.
- **ffmpeg fallback**: uses system ffmpeg when available, with `imageio-ffmpeg` as a fallback source.
- **Authorized sign-in support**: your own cookies can be used for content your account is already entitled to watch.
- **Actionable diagnostics**: common cookie, entitlement, rate-limit, ffmpeg, and disk errors include next steps.

## Quick start

### GUI

From source:

```bash
python yt_fetch.py --gui
```

After an editable install:

```bash
yt-fetch-gui
```

### CLI

Download the newest five regular videos from a channel:

```bash
python yt_fetch.py --channel "@channel_handle"
```

Set a count and quality ceiling:

```bash
python yt_fetch.py --channel "@channel_handle" --count 10 --quality 720p
```

Include Shorts:

```bash
python yt_fetch.py --channel "@channel_handle" --include-shorts
```

Limit download speed and add a delay:

```bash
python yt_fetch.py --channel "@channel_handle" --ratelimit 5 --sleep 2
```

For the complete CLI reference:

```bash
python yt_fetch.py --help
```

## Using your own sign-in state

Public videos normally need no login. When YouTube requires authentication and your account is **already entitled to watch the content**, you can use:

```bash
python yt_fetch.py --channel "@channel_handle" --cookies cookies.txt
python yt_fetch.py --channel "@channel_handle" --cookies-from-browser chrome:Default
```

The Windows GUI also provides a controlled Chrome sign-in flow that can obtain the current user's own YouTube cookies locally. This is for authorized cases such as your own membership entitlement or age verification; it does not grant access to memberships you did not purchase or to private / unauthorized videos.

Security boundaries:

- Never commit cookies, tokens, or account credentials to the repository.
- Controlled sign-in should export only your own cookies and use them locally.
- The tool does not provide DRM removal, paywall bypass, or unauthorized-content access.
- Users remain responsible for YouTube terms, copyright, and content licensing requirements.

See [SECURITY.md](SECURITY.md) for more detail.

## Install from source

Python 3.10+ is required:

```bash
git clone https://github.com/SanHsien/yt_fetch.git
cd yt_fetch
python -m venv .venv
```

Activate the virtual environment, then:

```bash
pip install -e .
```

You can then run:

```bash
yt-fetch --channel "@channel_handle"
yt-fetch-gui
```

`yt_fetch.py` also keeps its convenience path that can create `.venv` and install required packages when run directly.

## Platform support

| Mode | Windows | macOS | Linux |
|---|---:|---:|---:|
| Portable Windows EXE | Yes | No | No |
| Python CLI | Yes | Yes | Yes |
| Tkinter GUI | Yes | Yes | Yes* |
| Controlled Chrome sign-in | Primary target | Browser-dependent | Browser-dependent |

\* Some minimal Linux distributions require the separate `python3-tk` package.

## Development and validation

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m black --check yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
python -m isort --check-only yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
python -m flake8 yt_fetch.py yt_fetch_gui.py chrome_cdp_cookies.py build_exe.py tools/ tests/
```

Official releases are built by GitHub Actions as Windows ZIP archives and validated for ZIP integrity, SHA-256, and required files. See [docs/RELEASING.md](docs/RELEASING.md).

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md): contribution workflow
- [SECURITY.md](SECURITY.md): security and cookie-handling boundaries
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): development and tests
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): structure and data flow
- [docs/COMPUTER_USE_VALIDATION.md](docs/COMPUTER_USE_VALIDATION.md): Windows GUI / Release validation
- [docs/RELEASING.md](docs/RELEASING.md): release process
- [CHANGELOG.md](CHANGELOG.md): version history

## License

Licensed under the [MIT License](LICENSE). Third-party components and supplemental notices are documented in [NOTICE.md](NOTICE.md).
