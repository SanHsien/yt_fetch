"""Windows Release ZIP 驗證工具測試。"""

import zipfile

import pytest

from tools.verify_release_zip import verify_release_zip


def write_zip(path, entries):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in entries:
            archive.writestr(name, content)


def test_verify_release_zip_accepts_single_nonempty_exe(tmp_path):
    archive_path = tmp_path / "yt_fetch.zip"
    write_zip(archive_path, [("yt_fetch.exe", b"MZ-test")])

    result = verify_release_zip(archive_path)

    assert result == {"entry": "yt_fetch.exe", "size": 7}


@pytest.mark.parametrize(
    "entries, message",
    [
        ([("nested/yt_fetch.exe", b"MZ")], "根目錄"),
        ([("yt_fetch.exe", b"")], "不可為空"),
        ([("../yt_fetch.exe", b"MZ")], "不安全路徑"),
        ([("yt_fetch.exe", b"MZ"), ("extra.txt", b"x")], "只能包含"),
    ],
)
def test_verify_release_zip_rejects_invalid_layout(tmp_path, entries, message):
    archive_path = tmp_path / "yt_fetch.zip"
    write_zip(archive_path, entries)

    with pytest.raises(ValueError, match=message):
        verify_release_zip(archive_path)


def test_verify_release_zip_rejects_crc_failure(tmp_path, monkeypatch):
    archive_path = tmp_path / "yt_fetch.zip"
    write_zip(archive_path, [("yt_fetch.exe", b"MZ-test")])
    monkeypatch.setattr(zipfile.ZipFile, "testzip", lambda self: "yt_fetch.exe")

    with pytest.raises(ValueError, match="CRC"):
        verify_release_zip(archive_path)
