# YouTube Channel Video Downloader

[**English**](README.en.md) | [繁體中文](README.md)

[![Code Check](https://github.com/SanHsien/yt_fetch/actions/workflows/code-check.yml/badge.svg?branch=main)](https://github.com/SanHsien/yt_fetch/actions/workflows/code-check.yml)
[![CodeQL](https://github.com/SanHsien/yt_fetch/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/SanHsien/yt_fetch/actions/workflows/codeql.yml)
[![Dependency freshness](https://github.com/SanHsien/yt_fetch/actions/workflows/dependency-freshness.yml/badge.svg)](https://github.com/SanHsien/yt_fetch/actions/workflows/dependency-freshness.yml)
[![Release](https://img.shields.io/github/v/release/SanHsien/yt_fetch?sort=semver&display_name=tag)](https://github.com/SanHsien/yt_fetch/releases)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-SanHsien%2Fyt_fetch-lightgrey.svg)](https://github.com/SanHsien/yt_fetch)
[![GitHub stars](https://img.shields.io/github/stars/SanHsien/yt_fetch.svg?style=social&label=Star)](https://github.com/SanHsien/yt_fetch)
[![GitHub forks](https://img.shields.io/github/forks/SanHsien/yt_fetch.svg?style=social&label=Fork)](https://github.com/SanHsien/yt_fetch)
[![GitHub issues](https://img.shields.io/github/issues/SanHsien/yt_fetch.svg)](https://github.com/SanHsien/yt_fetch/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/SanHsien/yt_fetch.svg)](https://github.com/SanHsien/yt_fetch)

Fetch the latest N videos from a specified YouTube channel and download them as MP4 files into the `download/` folder.

Many similar tools already exist. This project focuses on being **lightweight, portable, GUI-friendly, and easy to understand**, so common personal backup tasks can be handled with a standalone no-install app instead of a large all-in-one downloader.

> ✨ **Highlight: download channel-membership videos you pay for yourself.** A built-in one-click "Sign in to YouTube" obtains cookies (overcoming Chrome 127+ App-Bound Encryption, which blocks reading cookies), so you can download content you are **already entitled** to view with your own login — including **channel memberships you subscribe to / pay for**, age-restricted videos, and more. This is **authenticated access, not paywall bypassing** (content you have not paid for is still denied by YouTube).

> **Important notice**: This tool is for personal learning and research only. Please follow YouTube's Terms of Service and copyright law.

## 🖼️ Screenshot

[![yt_fetch main window](docs/screenshots/main-window.png)](docs/screenshots/main-window.png)

> Graphical interface (`--gui`): fill in the channel and options to download. Downloads run in the background with a live progress bar, log, and result summary.

> The screenshot is generated deterministically (demo data only, no real cookies or personal paths): `python tools/generate_readme_screenshot.py`. See [docs/screenshot-workflow.md](docs/screenshot-workflow.md).

## ⬇️ Download (Windows standalone EXE)

If you'd rather not install Python, download the prebuilt Windows executable:

1. Download `yt_fetch-<version>-windows-x64.zip` from [Releases](https://github.com/SanHsien/yt_fetch/releases).
2. Unzip and double-click `yt_fetch.exe` to open the GUI.
3. Videos are saved to a `download/` folder next to the exe.
4. Verify integrity with the bundled `.sha256` file.

> The EXE is built and published automatically by GitHub Actions on `v*` tags (see `.github/workflows/release.yml`).
> To build it yourself on Windows: `pip install -e ".[build]"` then `python build_exe.py` (produces `dist/yt_fetch.exe`).

> **EXE update note**: the Windows EXE bundles the `yt-dlp` version available at build time. When YouTube changes,
> an old EXE may stop working. If videos cannot be fetched, check Releases for a newer build first. Source-code users
> can update the download core with `pip install -U yt-dlp`.

> **Windows SmartScreen**: the EXE is currently unsigned, so Windows may show "Windows protected your PC" on first run.
> If you have confirmed the file came from this project's Releases page, click "More info" -> "Run anyway".

## Features

- **Graphical interface (GUI)**: a Tkinter desktop UI that can also be packaged as a standalone Windows EXE.
- **Lightweight and portable**: keeps a single-file core and clear workflow, with a standalone no-install app for Windows users.
- **Automatic environment management**: automatically creates a virtual environment and installs required packages.
- **Cross-platform support**: works on Windows, macOS, and Linux.
- **Interactive and command-line modes**: run interactively to answer prompts, or pass command-line options for faster use.
- **Quality selection**: choose `best`, `1080p`, `720p`, or `480p`; resolution options download the best available quality at or below the selected cap.
- **GUI batch downloads**: import a channel list and process multiple channels sequentially; one failed channel does not stop the batch.
- **GUI presets**: quick profiles for best quality, space-saving 720p, and low quality 480p.
- **Smart format selection**: detects and installs ffmpeg, then merges the selected video quality with the best audio quality.
- **ffmpeg status check**: the GUI can show whether system ffmpeg or `imageio-ffmpeg` is used, plus version and path.
- **Idempotent downloads**: rerunning the tool does not download existing videos again.
- **Conservative access boundary**: filters private, unlisted, unauthorized, and other inaccessible content; cookies are only for videos your own account is already entitled to view.
- **Sign in for cookies (Windows/Chrome)**: a built-in managed-browser sign-in that solves Chrome 127+ App-Bound Encryption (which blocks reading Chrome cookies); download content you are already entitled to view using your own login (age-restricted videos, channel memberships you subscribe to, etc.) — never bypassing any access you have not paid for.
- **Shorts filtering**: excludes Shorts by default, with an option to include them. Supports YouTube channel Videos/Shorts tabs.
- **Detailed logs and GUI progress bar**: records the download process, shows progress, lists results, and exports a run report.
- **Error diagnosis**: gives next steps for common cookies, entitlement, rate limit, ffmpeg, and disk permission failures.

## Requirements

- Python 3.10 or later.
- **ffmpeg** (required): used to merge best-quality video and audio streams.

## Installation

### Method 1: Automatic Installation (Recommended)

The script automatically creates a virtual environment and installs required packages. No manual setup is needed:

```bash
python yt_fetch.py --channel "@channel_handle"
```

### Method 2: Manual Installation

If you prefer to manage dependencies manually:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Method 3: Install as a Package (Provides the `yt-fetch` Command)

Install the project in editable mode to use the `yt-fetch` command:

```bash
pip install -e .
yt-fetch --channel "@channel_handle"
```

`yt-fetch` accepts the same options as `python yt_fetch.py`.

## Usage

### Graphical Interface (GUI, recommended for beginners)

If you'd rather not use the command line, launch the desktop GUI and fill in the
channel, count, and other options in a window:

```bash
python yt_fetch.py --gui
```

After an editable install (`pip install -e .`), the `yt-fetch-gui` command also
launches it. The GUI reuses the exact same download logic as the CLI; downloads
run in a background thread so the window stays responsive. It can import a
channel list for sequential batch downloads, show a live log and result summary,
set title/date/duration advanced filters, download subtitles, open a downloaded
file or its containing folder, and export the current run report.

> The GUI uses Python's built-in Tkinter. Some slim Python builds (often on Linux)
> need `python3-tk` installed separately; official Windows/macOS installers usually
> include it.

### Method 1: Interactive Mode (Recommended for Beginners)

Run the script directly. It will ask for all required parameters:

```bash
python yt_fetch.py
```

The script will ask for:

- **Channel**: YouTube channel URL, ID, or @handle (required).
- **Target file count**: number of videos to download. Default: 5. Press Enter to use the default.
- **Include Shorts**: y/n. Default: n. Press Enter to use the default.
- **Download quality**: `best`, `1080p`, `720p`, or `480p`. Default: best.
- **Retry count**: number of retries when a download fails. Default: 3. Press Enter to use the default.

### Method 2: Command-Line Mode (Recommended for Advanced Users)

Pass command-line options directly, without interactive prompts:

```bash
python yt_fetch.py --channel "@channel_handle"
```

### Command-Line Options

| Option | Description | Default | Example |
|------|------|--------|------|
| `--channel` | Channel URL, ID, or @handle. If omitted, the script asks through prompts. | - | `--channel "@pewdiepie"` |
| `--count` | Number of videos to download. | 5 | `--count 10` |
| `--include-shorts` | Include Shorts. Shorts are excluded by default. | False | `--include-shorts` |
| `--quality` | Download quality: `best`, `1080p`, `720p`, or `480p`; resolution options choose the best available quality at or below the cap. | best | `--quality 720p` |
| `--retries` | Retry count. | 3 | `--retries 5` |
| `--cookies-from-browser` | Read cookies from a browser, useful for age or region restrictions. A profile may be specified. | - | `--cookies-from-browser chrome:Default` |
| `--cookies` | Path to a Netscape-format cookies file. | - | `--cookies cookies.txt` |
| `--ratelimit` | Download speed limit in MB/s. `0` means unlimited. | 0 | `--ratelimit 5` |
| `--sleep` | Seconds to wait between downloads, reducing rate-limit risk. | 0 | `--sleep 2` |
| `--title-include` | Only download videos whose title contains the text. | - | `--title-include Python` |
| `--title-exclude` | Exclude videos whose title contains the text. | - | `--title-exclude Shorts` |
| `--date-after` | Only download videos uploaded on/after this date, `YYYYMMDD`. | - | `--date-after 20260101` |
| `--date-before` | Only download videos uploaded on/before this date, `YYYYMMDD`. | - | `--date-before 20261231` |
| `--min-duration` | Only download videos at least this many seconds long; `0` means no limit. | 0 | `--min-duration 300` |
| `--max-duration` | Only download videos no longer than this many seconds; `0` means no limit. | 0 | `--max-duration 1800` |
| `--write-subs` | Download subtitles / auto subtitles when available. | False | `--write-subs` |
| `--sub-langs` | Subtitle languages, comma-separated. | `zh-Hant,zh-Hans,en` | `--sub-langs zh-Hant,en` |
| `--channels-file` | Batch mode: one channel per line (`#` for comments). | - | `--channels-file channels.txt` |
| `--gui` | Launch the graphical interface (other options set in the window). | False | `--gui` |
| `--login` | Open a managed browser to sign in to YouTube once and save cookies (Windows/Chrome; see below). | False | `--login` |

### How cookies are handled (GUI vs CLI)

Most public videos do not need cookies. You only need them when your own account can already legally view the content, but YouTube requires a signed-in session check.

- **GUI**: there are no manual cookie fields. When needed, just click the **"Sign in to YouTube for cookies"** button (see the Chrome 127+ section below); downloads then use it automatically.
- **CLI**: use one of these two options (advanced / non-Chrome cases such as Firefox or your own cookies.txt):
  - **`--cookies-from-browser`**: enter `chrome`, `firefox`, or `edge`, with an optional profile (`chrome:Default`, `chrome:Profile 1`). On Windows/Chrome it automatically routes through the managed-browser sign-in (see below).
  - **`--cookies`**: path to a Netscape-format `cookies.txt` file, e.g. one exported from a browser extension.

Do not fill both CLI options at the same time. The config file never persists cookie contents. These options are only for content you have the right to access; they must not be used to bypass paywalls, membership-only videos, private videos, or other access controls.

### Sign in for cookies on Chrome 127+ (managed browser, Windows)

> **This feature is optional.** Public videos need no sign-in or cookies at all; you only need this when a signed-in session is required.

Since **Chrome 127**, Google enabled **App-Bound Encryption (ABE)**: the cookie decryption key is bound to the Chrome executable itself, so on Windows `yt-dlp` (and any external tool) **can no longer read Chrome cookies directly** — the usual symptom is `failed to load cookies`.

To solve this, the tool offers a **managed-browser sign-in**: it launches a browser instance that is **dedicated to this tool and fully separate from your everyday Chrome**, lets you sign in to YouTube there, and then retrieves the cookies that **Chrome itself has already decrypted** via the Chrome DevTools Protocol. You do not need to close your normal Chrome, and your main profile is never touched.

The remote-debugging endpoint only listens on local `127.0.0.1`. Exported cookies are limited to
the `youtube.com`, `google.com`, and `googlevideo.com` domains needed for YouTube sign-in, so
cookies from unrelated sites are not written to this tool's `cookies.txt`.

How to use it (either one):

- **GUI**: click the **"Sign in to YouTube for cookies"** button on the main screen and sign in in the pop-up window.
- **Command line**: run `yt_fetch.exe --login` (or `python yt_fetch.py --login`) and sign in in the pop-up window.

After a successful sign-in, the cookies are saved to `%LOCALAPPDATA%\yt_fetch\cookies.txt`, and **future GUI downloads use them automatically and refresh them headlessly on each run**. You normally never need to sign in again until the cookies expire naturally; when they do, just click sign-in once more. CLI runs with `--cookies-from-browser chrome` also prefer these managed cookies.

#### Downloading membership videos you pay for yourself

When **you** are an actual **paying member / channel member (Membership)** of a channel, or have purchased some paid content, after signing in your account is **already entitled** to watch those videos, so the tool can download them using your own login (**for personal use only**, and please follow YouTube's Terms of Service and copyright rules).

The same applies to **age-restricted** videos, or when YouTube asks for a signed-in confirmation because it suspects bot activity.

> ⚠️ **Boundary (important)**: cookies only let you access content **as your own signed-in self** — they are **not** a paywall crack. For channels you have **not** joined or purchased, YouTube verifies your account entitlement server-side and denies access; cookies cannot help, and this tool **does not, cannot, and will not** implement anything that bypasses memberships, paywalls, private videos, or age/region restrictions.

### Environment Variables

All options can be configured with environment variables:

```bash
# Windows (PowerShell)
$env:YOUTUBE_CHANNEL="@channel_handle"
$env:YOUTUBE_COUNT="10"
$env:YOUTUBE_INCLUDE_SHORTS="1"
$env:YOUTUBE_QUALITY="720p"
$env:YOUTUBE_RETRIES="5"
$env:YOUTUBE_COOKIES_BROWSER="chrome"
$env:YOUTUBE_RATELIMIT="5"
$env:YOUTUBE_SLEEP="2"
$env:YOUTUBE_TITLE_INCLUDE="Python"
$env:YOUTUBE_TITLE_EXCLUDE="Shorts"
$env:YOUTUBE_DATE_AFTER="20260101"
$env:YOUTUBE_DATE_BEFORE="20261231"
$env:YOUTUBE_MIN_DURATION="300"
$env:YOUTUBE_MAX_DURATION="1800"
$env:YOUTUBE_WRITE_SUBS="1"
$env:YOUTUBE_SUB_LANGS="zh-Hant,en"
python yt_fetch.py

# macOS/Linux
export YOUTUBE_CHANNEL="@channel_handle"
export YOUTUBE_COUNT=10
export YOUTUBE_INCLUDE_SHORTS=1
export YOUTUBE_QUALITY=720p
export YOUTUBE_RETRIES=5
export YOUTUBE_COOKIES_BROWSER=chrome
export YOUTUBE_RATELIMIT=5
export YOUTUBE_SLEEP=2
export YOUTUBE_TITLE_INCLUDE=Python
export YOUTUBE_TITLE_EXCLUDE=Shorts
export YOUTUBE_DATE_AFTER=20260101
export YOUTUBE_DATE_BEFORE=20261231
export YOUTUBE_MIN_DURATION=300
export YOUTUBE_MAX_DURATION=1800
export YOUTUBE_WRITE_SUBS=1
export YOUTUBE_SUB_LANGS=zh-Hant,en
python yt_fetch.py
```

### Config file (yt_fetch.ini)

A `yt_fetch.ini` is auto-created next to the script (or exe) to remember your
common settings and pre-fill them on the next launch. The GUI writes the current
values back after each download, and the CLI reads it for defaults.

- Persisted: channel, count, retries, include-shorts, download quality, rate limit, sleep, advanced filters, subtitle settings, download folder.
- **Cookies are never persisted** (neither the file path nor the browser source).
- You can edit it by hand; invalid values are ignored and fall back to built-in defaults.

Precedence (high → low):

```
CLI arguments  >  environment variables (YOUTUBE_*)  >  yt_fetch.ini  >  built-in defaults
```

Example `yt_fetch.ini`:

```ini
[yt_fetch]
channel = @channel_handle
count = 10
retries = 3
include_shorts = false
quality = best
ratelimit = 0
sleep = 0
title_include =
title_exclude =
date_after =
date_before =
min_duration = 0
max_duration = 0
write_subs = false
sub_langs = zh-Hant,zh-Hans,en
download_dir =
```

### Batch download multiple channels

Put your channel list in a text file (one per line, `#` for comments):

```text
# my_channels.txt
@channel_one
https://www.youtube.com/@channel_two/videos
UCxxxxxxxxxxxxxxxxxxxxxx
```

Then:

```bash
python yt_fetch.py --channels-file my_channels.txt --count 5
```

- Each channel fetches its own latest N videos (`--count` is per channel).
- **A single channel's failure does not abort the batch**; a per-channel
  success/failure summary is printed at the end.
- Downloads stay sequential and conservative (no mass parallel downloads).

### Channel URL Formats

The tool supports several channel identifier formats:

- **@handle format**: `@channel_handle`
- **Full URL**: `https://www.youtube.com/@channel_handle`
- **Channel ID**: `UCxxxxxxxxxxxxxxxxxxxxxx`
- **Channel URL**: `https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx`

Full URLs must use HTTPS and an approved YouTube host (including `youtu.be`). HTTP URLs, other
sites, embedded credentials, and non-standard ports are rejected.

### Examples

#### Interactive Example

```bash
# Run directly. The script will ask for all parameters.
python yt_fetch.py

# Prompts:
# Channel: @channel_handle
# Count: 10          (press Enter to use the default 5)
# Include Shorts: n (press Enter to use the default n)
# Download quality: 720p (press Enter to use the default best)
# Retry count: 5    (press Enter to use the default 3)
```

#### Command-Line Examples

```bash
# Download the latest 5 videos. Specify the channel and use defaults for the rest.
python yt_fetch.py --channel "@channel_handle"

# Download the latest 10 videos
python yt_fetch.py --channel "@channel_handle" --count 10

# Include Shorts
python yt_fetch.py --channel "@channel_handle" --include-shorts

# Limit video quality to 720p or lower
python yt_fetch.py --channel "@channel_handle" --quality 720p

# Use a full URL
python yt_fetch.py --channel "https://www.youtube.com/@channel_handle/videos"

# Use browser cookies for age or region restrictions
python yt_fetch.py --channel "@channel_handle" --cookies-from-browser chrome

# Use a cookies file
python yt_fetch.py --channel "@channel_handle" --cookies cookies.txt

# Limit download speed and add delay to reduce rate-limit risk
python yt_fetch.py --channel "@channel_handle" --ratelimit 5 --sleep 2

# Only download videos with Python in the title, uploaded after 2026-01-01, and at least 5 minutes long
python yt_fetch.py --channel "@channel_handle" --title-include Python --date-after 20260101 --min-duration 300

# Download subtitles / auto subtitles when available
python yt_fetch.py --channel "@channel_handle" --write-subs --sub-langs zh-Hant,en

# Increase retry count for unstable networks
python yt_fetch.py --channel "@channel_handle" --retries 5

# Full example
python yt_fetch.py --channel "@channel_handle" --count 10 --include-shorts --quality 720p --retries 5 --ratelimit 5 --sleep 2
```

## Output

Downloaded videos are saved into a per-**channel** subfolder under `download/`, so multiple channels do not get mixed together:

```text
download/<Channel Name>/%(title)s [%(id)s].mp4
```

Example: `download/PAPAYA 電腦教室/My Video Title [dQw4w9WgXcQ].mp4`

(The download record `download/.download_archive.txt` is still shared; the already-downloaded check scans all subfolders recursively and remains compatible with older files placed directly in `download/`.)

## Idempotency

The script records downloaded videos automatically. Running it again will not download existing videos again:

- Uses yt-dlp's download archive: `download/.download_archive.txt`
- Checks video IDs in existing filenames.

`--count` is counted per channel: the script compares how many of that channel's videos are already downloaded and only fetches the remainder, so videos already downloaded from other channels do not reduce the count. If the channel's target is already met, it reports that the target has been reached and exits.

## ffmpeg Installation (Required)

ffmpeg is required to merge best-quality video and audio streams. If it is not installed, the script reports an error and exits.

### Windows

```bash
# Using Chocolatey
choco install ffmpeg

# Or download from the official website
# https://ffmpeg.org/download.html
```

### macOS

```bash
brew install ffmpeg
```

### Linux

```bash
# Debian/Ubuntu
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

**Note**: ffmpeg is required. If it is not installed, the script exits with an error. Please install ffmpeg first.

## FAQ

### Q: I see an "ffmpeg not found" error. What should I do?

**A:** ffmpeg is required. Install ffmpeg using the instructions above. The script detects ffmpeg automatically and shows installation guidance if it cannot find it.

### Q: No videos are found. What should I check?

**A:** Please check:

- Whether the channel URL is correct.
- Whether the channel is public.
- Try using the `@handle` format instead of a full URL.

### Q: Why are some videos not downloaded?

**A:** Without cookies, the tool only downloads publicly viewable VOD videos. With your own
authorized cookies, membership, Premium, and sign-in-required candidates are passed to YouTube,
which verifies the account's existing entitlement; unauthorized access is still denied. The tool
always skips:

- Private videos.
- Unlisted videos.
- Live streams, upcoming streams, finished live-stream entries, and other Live content.

Without cookies it also skips subscriber-only, Premium-only, and sign-in-required entries. This
only enables content you were already entitled to view; it does not bypass access controls.

### Q: Downloads fail or network errors occur. What should I do?

**A:** Try increasing the retry count:

```bash
python yt_fetch.py --channel "@channel" --retries 5
```

### Q: How should I choose download quality?

**A:** The default `best` downloads the best quality selected by yt-dlp. If you choose `1080p`, `720p`, or `480p`, the tool downloads the best available quality at or below that resolution cap; if the video does not provide that exact resolution, it falls back to a lower available quality.

### Q: I see a permission error. What should I do?

**A:** Make sure you have write permission for the `download/` folder.

### Q: How are Shorts excluded? Does the tool download livestreams?

**A:** Shorts are excluded by default, and livestreams are not downloaded. Since 2022, YouTube channels are split into Videos, Shorts, and Live tabs:

- `/videos` contains long-form videos. This tool downloads from this page by default.
- `/shorts` contains Shorts. This page is only fetched when `--include-shorts` is used.
- `/live` and related live content are automatically excluded through `live_status`, keeping only VOD entries.

Behavior:

- When **Shorts are not included** (default), the tool only fetches the `/videos` page and further uses `match_filter` to exclude videos whose URL contains `/shorts/`, or that are shorter than 60 seconds **and** marked as Shorts in the title/description (normal short videos without the marker are kept).
- When **Shorts are included** (`--include-shorts`), the tool fetches both `/videos` and `/shorts`, then merges and deduplicates entries.

Use `--include-shorts` if you want Shorts. Livestreams are never downloaded.

### Q: What if I encounter age-restricted or region-restricted videos?

**A:** Use `--cookies-from-browser chrome` (or another browser) or `--cookies cookies.txt` to provide login cookies. This can help with age or region restrictions. Note: this does not bypass paywalls.

### Q: How can I reduce YouTube rate limiting?

**A:** Use these options:

- `--ratelimit 5`: limit download speed to 5 MB/s.
- `--sleep 2`: wait 2 seconds between downloads.
- Using both together is usually better.

### Q: How do I clear the download history?

**A:** Delete the `download/.download_archive.txt` file.

## Exit Codes

- `0`: success, either videos were downloaded or the run was idempotent.
- `1`: argument error or network error.
- `2`: ffmpeg is required but not installed, and fallback is unavailable.

## Roadmap

- **Product direction**: stay lightweight, portable, GUI-friendly, and easy to understand for personal backup workflows. The CLI remains a stable entry point; the GUI is the everyday interface.
- **Completed foundation**: standalone Windows EXE, Tkinter GUI, shared CLI/GUI download core, managed-browser cookies, quality options, advanced filters, subtitle downloads, multi-channel batch downloads, per-channel output subfolders, result reports, ffmpeg status, dependency freshness checks, and the Release workflow.
- **Maintenance roadmap status**: the download flow now has helpers for `build_ytdlp_options()`, `_extract_entries()`, `dedupe_entries()`, `calculate_download_target()`, `prepare_entries_to_download()`, `download_entries_with_ytdlp()`, ffmpeg setup, progress hooks, match filters, candidate scan sizing, and yt-dlp fatal error handling. Error diagnosis is centralized in the core classifier and message table, shared by CLI and GUI. The GUI is grouped into download settings, batch list, output folder, download results, and run log sections; `docs/planning/` now records the current spec, completed state, not-planned items, and optional future items.
- **Download-core maintenance rule**: when adding or fixing download behavior, change the focused helper and test first instead of putting logic back inline inside `download_videos()`. When YouTube or yt-dlp behavior changes, add a reproducible test, then adjust the extraction, candidate, download-loop, success-detection, or error-handling helper.
- **Error-diagnosis maintenance rule**: when real yt-dlp, cookie, ffmpeg, disk-permission, rate-limit, or entitlement errors appear, add them to the core classifier and message table so CLI and GUI benefit together.
- **GUI maintenance rule**: the current feature set is enough; UI changes should only improve quick setup, clear status, or obvious next actions. Prefer layout density, wording, cookies/ffmpeg/batch status, and result presentation cleanup over more settings panels.
- **Batch principle**: keep batch downloads sequential and conservative to avoid unnecessary rate limiting or service pressure.
- **Release maintenance**: cut a new tag and rebuild the EXE only when dependency freshness, real download issues, or core fixes make a new user-facing build worthwhile. The monthly dependency freshness workflow compares the repository's declared `yt-dlp` / `imageio-ffmpeg` baselines with PyPI, while weekly Dependabot checks every direct Python dependency and GitHub Action. Each Release should list the bundled `yt-dlp` version, main changes, known limitations, and SHA256.
- **Optional but not urgent**: format conversion can be evaluated when there is a clear need. MP4 remains the default to avoid extra ffmpeg failure modes and GUI complexity.

### Not Planned

- Bypassing YouTube paywalls, membership-only videos, private videos, region restrictions, or other access controls (i.e. accessing content you are **not** entitled to view).
- Transmitting, uploading, sharing, exchanging, or leaking user cookies/tokens to any third party.
- Large parallel downloads or rate-limit circumvention.
- Automatic upload to cloud drives or third-party storage services.
- Web UI, scheduler daemon, new-video reminders, or system notifications; these would move the project away from its standalone GUI tool direction.

> About cookies: the cookie features (including the Chrome 127+ managed sign-in) only extract and use **your own** cookies on **your own** machine, stored locally in `cookies.txt` and never sent anywhere. They let you download content you are **already entitled** to view using your own login (e.g. channel memberships you pay for, age-restricted videos) — this is **authenticated access, not bypassing**; content you have not paid for or are not entitled to is still denied by YouTube server-side.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to participate.

## Security

If you find a security vulnerability, see [SECURITY.md](SECURITY.md) for how to report it.

## License

This project is licensed under the [MIT License](LICENSE).

## Disclaimer

This tool is for personal learning and research only. Downloaded content must comply with:

- YouTube Terms of Service.
- Copyright law.
- Applicable laws and regulations.

Users are solely responsible for all use of this tool.

## Technical Details

- **Dependencies**: yt-dlp>=2026.7.4, imageio-ffmpeg>=0.6.0.
- **Python version**: 3.10+.
- **Virtual environment**: automatically creates `.venv`.
- **CLI command**: `yt-fetch` is available after `pip install -e .`.
- **Download directory**: `download/`.
- **Archive file**: `download/.download_archive.txt`.

## Troubleshooting

If you encounter problems, check:

1. Python version is 3.10 or later.
2. Network connection is working.
3. The channel is public, or the content is legally accessible with your own signed-in account.
4. There is enough disk space.
5. Detailed error messages in the log output.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release history.

### Main Features

- Automatic environment management.
- Cross-platform support.
- Smart format selection (requires ffmpeg).
- Download quality options (best / 1080p / 720p / 480p).
- Advanced filters (title, date, duration) and subtitle downloads.
- Idempotent downloads.
- Shorts filtering, supporting YouTube channel tabs: Videos/Shorts/Live. By default, only the Videos page is fetched.
- Conservative access boundary, with automatic filtering of private, unlisted, unauthorized, and otherwise inaccessible content.
- Playlist extraction count limits to reduce YouTube rate-limit risk.
- Forced watch URL downloads to avoid m3u8 format issues.
- Progress hook tracking of actual downloaded filenames to identify files correctly.
- Interactive input prompt when `--channel` is not provided.
- Cookies support for age or region restrictions.
- Download speed limit and delay strategy to reduce rate-limit risk.
