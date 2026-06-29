# YouTube Channel Video Downloader

[**English**](README.en.md) | [繁體中文](README.md)

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-SanHsien%2Fyt_fetch-lightgrey.svg)](https://github.com/SanHsien/yt_fetch)
[![GitHub stars](https://img.shields.io/github/stars/SanHsien/yt_fetch.svg?style=social&label=Star)](https://github.com/SanHsien/yt_fetch)
[![GitHub forks](https://img.shields.io/github/forks/SanHsien/yt_fetch.svg?style=social&label=Fork)](https://github.com/SanHsien/yt_fetch)
[![GitHub issues](https://img.shields.io/github/issues/SanHsien/yt_fetch.svg)](https://github.com/SanHsien/yt_fetch/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/SanHsien/yt_fetch.svg)](https://github.com/SanHsien/yt_fetch)

Fetch the latest N videos from a specified YouTube channel and download them as MP4 files into the `download/` folder.

> **Important notice**: This tool is for personal learning and research only. Please follow YouTube's Terms of Service and copyright law.

## Features

- **Automatic environment management**: automatically creates a virtual environment and installs required packages.
- **Cross-platform support**: works on Windows, macOS, and Linux.
- **Interactive and command-line modes**: run interactively to answer prompts, or pass command-line options for faster use.
- **Smart format selection**: detects and installs ffmpeg, then merges the best video and audio quality.
- **Idempotent downloads**: rerunning the tool does not download existing videos again.
- **Public videos only**: automatically filters private, unlisted, subscriber-only, and other non-public videos.
- **Shorts filtering**: excludes Shorts by default, with an option to include them. Supports YouTube channel Videos/Shorts tabs.
- **Detailed logs**: records the download process and result list.
- **Error handling**: provides friendly error messages and installation guidance.

## Requirements

- Python 3.7 or later.
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

### Method 1: Interactive Mode (Recommended for Beginners)

Run the script directly. It will ask for all required parameters:

```bash
python yt_fetch.py
```

The script will ask for:

- **Channel**: YouTube channel URL, ID, or @handle (required).
- **Target file count**: number of videos to download. Default: 5. Press Enter to use the default.
- **Include Shorts**: y/n. Default: n. Press Enter to use the default.
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
| `--retries` | Retry count. | 3 | `--retries 5` |
| `--cookies-from-browser` | Read cookies from a browser, useful for age or region restrictions. | - | `--cookies-from-browser chrome` |
| `--cookies` | Path to a Netscape-format cookies file. | - | `--cookies cookies.txt` |
| `--ratelimit` | Download speed limit in MB/s. `0` means unlimited. | 0 | `--ratelimit 5` |
| `--sleep` | Seconds to wait between downloads, reducing rate-limit risk. | 0 | `--sleep 2` |

### Environment Variables

All options can be configured with environment variables:

```bash
# Windows (PowerShell)
$env:YOUTUBE_CHANNEL="@channel_handle"
$env:YOUTUBE_COUNT="10"
$env:YOUTUBE_INCLUDE_SHORTS="1"
$env:YOUTUBE_RETRIES="5"
$env:YOUTUBE_COOKIES_BROWSER="chrome"
$env:YOUTUBE_RATELIMIT="5"
$env:YOUTUBE_SLEEP="2"
python yt_fetch.py

# macOS/Linux
export YOUTUBE_CHANNEL="@channel_handle"
export YOUTUBE_COUNT=10
export YOUTUBE_INCLUDE_SHORTS=1
export YOUTUBE_RETRIES=5
export YOUTUBE_COOKIES_BROWSER=chrome
export YOUTUBE_RATELIMIT=5
export YOUTUBE_SLEEP=2
python yt_fetch.py
```

### Channel URL Formats

The tool supports several channel identifier formats:

- **@handle format**: `@channel_handle`
- **Full URL**: `https://www.youtube.com/@channel_handle`
- **Channel ID**: `UCxxxxxxxxxxxxxxxxxxxxxx`
- **Channel URL**: `https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx`

### Examples

#### Interactive Example

```bash
# Run directly. The script will ask for all parameters.
python yt_fetch.py

# Prompts:
# Channel: @channel_handle
# Count: 10          (press Enter to use the default 5)
# Include Shorts: n (press Enter to use the default n)
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

# Use a full URL
python yt_fetch.py --channel "https://www.youtube.com/@channel_handle/videos"

# Use browser cookies for age or region restrictions
python yt_fetch.py --channel "@channel_handle" --cookies-from-browser chrome

# Use a cookies file
python yt_fetch.py --channel "@channel_handle" --cookies cookies.txt

# Limit download speed and add delay to reduce rate-limit risk
python yt_fetch.py --channel "@channel_handle" --ratelimit 5 --sleep 2

# Increase retry count for unstable networks
python yt_fetch.py --channel "@channel_handle" --retries 5

# Full example
python yt_fetch.py --channel "@channel_handle" --count 10 --include-shorts --retries 5 --ratelimit 5 --sleep 2
```

## Output

Downloaded videos are saved in the `download/` folder. Filename format:

```text
%(title)s [%(id)s].mp4
```

Example: `My Video Title [dQw4w9WgXcQ].mp4`

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

**A:** This tool only downloads publicly viewable VOD videos. It automatically skips:

- Private videos.
- Unlisted videos.
- Subscriber-only videos.
- Premium-only videos.
- Videos that require authentication.
- Live streams, upcoming streams, finished live-stream entries, and other Live content.

This ensures the tool only downloads legally accessible, non-live public content.

### Q: Downloads fail or network errors occur. What should I do?

**A:** Try increasing the retry count:

```bash
python yt_fetch.py --channel "@channel" --retries 5
```

### Q: I see a permission error. What should I do?

**A:** Make sure you have write permission for the `download/` folder.

### Q: How are Shorts excluded? Does the tool download livestreams?

**A:** Shorts are excluded by default, and livestreams are not downloaded. Since 2022, YouTube channels are split into Videos, Shorts, and Live tabs:

- `/videos` contains long-form videos. This tool downloads from this page by default.
- `/shorts` contains Shorts. This page is only fetched when `--include-shorts` is used.
- `/live` and related live content are automatically excluded through `live_status`, keeping only VOD entries.

Behavior:

- When **Shorts are not included** (default), the tool only fetches the `/videos` page and further excludes videos shorter than 60 seconds through `match_filter`.
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

`yt_fetch` will keep the CLI simple and reliable while prioritizing a GUI, so users who are not comfortable with command lines can choose a channel, set options, view progress, and review results more easily.

### Near-Term Goals

#### 1. GUI Desktop Interface (Highest Priority)

The goal is a thin desktop interface that reuses the existing download logic instead of rewriting the core workflow.

- Enter a channel URL, ID, or `@handle`.
- Set download count, Shorts inclusion, and retry count.
- Configure cookies source, download speed limit, and delay between downloads.
- Select or open the `download/` folder.
- Show current status, download progress, and success/failure summary.
- Keep the CLI as the stable fallback entry point.

Completion criteria:

- The GUI can launch on Windows.
- Downloads do not freeze the main window, and progress is visible.
- Download behavior matches the CLI.
- Cookies contents are not saved; only necessary settings or paths may be stored.

#### 2. Test Coverage

Prioritize pure logic tests that do not depend on live YouTube network responses.

- `normalize_channel_url()` formats: `@handle`, `handle`, `UC...` channel ID, `/videos`, `/shorts`, playlist URL.
- Downloaded ID parsing from `download/.download_archive.txt` and existing filenames containing `[video_id]`.
- Shorts and livestream filtering.
- cookies, ratelimit, and sleep option parsing.

Completion criteria:

- Main helper functions have tests.
- CI does not need to connect to YouTube.
- CLI or GUI behavior regressions can be caught quickly.

#### 3. Make the Download Flow Easier to Test

The main flow currently lives in `download_videos()`. Short term, extract low-risk helpers so CLI and GUI can share them.

- Channel URL list construction.
- `yt-dlp` options construction.
- Entry deduplication and filtering.
- Download success detection.

Completion criteria:

- `download_videos()` remains the orchestration layer.
- Helpers are covered by unit tests.
- Existing CLI interface and default behavior stay unchanged.

### Mid-Term Goals

#### 4. User Experience Fixes

- `--help` should not print the startup banner or extra logs.
- ffmpeg missing errors should stay clear.
- cookies documentation should include stronger safety reminders.
- Download failures should provide clearer next steps.

#### 5. Configuration File Support

Evaluate a simple config file without breaking the CLI, such as `yt_fetch.toml` or `yt_fetch.json`.

Possible settings:

- Default channel.
- Default download count.
- Whether to include Shorts.
- Rate limit and delay between downloads.
- cookies source path.

#### 6. Multi-Channel Batch Downloads

Possible form:

- `--channels-file channels.txt`
- One channel URL, ID, or `@handle` per line.

Completion criteria:

- One failed channel does not stop the whole batch.
- Each channel has a clear result summary.
- Defaults remain conservative; no large parallel downloading is added.

#### 7. Result Reports

Generate a simple human-readable report after downloads:

- Downloaded videos.
- Skipped videos.
- Failed videos and reasons.
- Archive path.

### Long-Term Direction

- Package release cleanup: versioning rules, GitHub Release checklist, PyPI feasibility.
- Fuller cross-platform verification: Windows runner, macOS runner, `yt-fetch --help` smoke test, editable install check.

### Not Planned

- Bypassing YouTube paywalls, membership-only videos, private videos, region restrictions, or other access controls.
- Managing, exchanging, extracting, or sharing user cookies/tokens.
- Large parallel downloads or rate-limit circumvention.
- Automatic upload to cloud drives or third-party storage services.

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

- **Dependencies**: yt-dlp, imageio-ffmpeg.
- **Python version**: 3.7+.
- **Virtual environment**: automatically creates `.venv`.
- **CLI command**: `yt-fetch` is available after `pip install -e .`.
- **Download directory**: `download/`.
- **Archive file**: `download/.download_archive.txt`.

## Troubleshooting

If you encounter problems, check:

1. Python version is 3.7 or later.
2. Network connection is working.
3. The channel is public and accessible.
4. There is enough disk space.
5. Detailed error messages in the log output.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release history.

### Main Features

- Automatic environment management.
- Cross-platform support.
- Smart format selection (requires ffmpeg).
- Idempotent downloads.
- Shorts filtering, supporting YouTube channel tabs: Videos/Shorts/Live. By default, only the Videos page is fetched.
- Public-video-only downloading, with automatic filtering of non-public content.
- Playlist extraction count limits to reduce YouTube rate-limit risk.
- Forced watch URL downloads to avoid m3u8 format issues.
- Progress hook tracking of actual downloaded filenames to identify files correctly.
- Interactive input prompt when `--channel` is not provided.
- Cookies support for age or region restrictions.
- Download speed limit and delay strategy to reduce rate-limit risk.
