"""驗證 Windows Release ZIP 的完整性與最小安全版面。"""

import argparse
import sys
import zipfile
from pathlib import Path, PurePosixPath


def _is_unsafe_entry(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        not name
        or name.startswith(("/", "\\"))
        or "\\" in name
        or (len(name) >= 2 and name[1] == ":")
        or ".." in path.parts
    )


def verify_release_zip(archive_path: Path) -> dict:
    """確認 ZIP CRC 正常，且只含根目錄下一個非空的 yt_fetch.exe。"""
    archive_path = Path(archive_path)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]

            if any(_is_unsafe_entry(name) for name in names):
                raise ValueError("ZIP 含不安全路徑")
            if len(names) != len(set(names)):
                raise ValueError("ZIP 含重複項目")

            failed_entry = archive.testzip()
            if failed_entry is not None:
                raise ValueError(f"ZIP CRC 驗證失敗：{failed_entry}")

            if len(entries) != 1:
                raise ValueError("ZIP 只能包含一個 yt_fetch.exe")
            entry = entries[0]
            if entry.filename != "yt_fetch.exe":
                raise ValueError("yt_fetch.exe 必須位於 ZIP 根目錄")
            if entry.is_dir() or entry.file_size <= 0:
                raise ValueError("yt_fetch.exe 不可為空")
    except zipfile.BadZipFile as exc:
        raise ValueError("不是有效的 ZIP 檔案") from exc

    return {"entry": entry.filename, "size": entry.file_size}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="待驗證的 Release ZIP")
    args = parser.parse_args()

    try:
        result = verify_release_zip(args.archive)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"PASS: {result['entry']} ({result['size']} bytes), ZIP CRC 與版面正確")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
