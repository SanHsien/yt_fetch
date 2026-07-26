"""版本庫依賴更新排程的整合測試。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_dependabot_checks_python_and_github_actions_weekly():
    config = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

    assert 'package-ecosystem: "pip"' in config
    assert 'package-ecosystem: "github-actions"' in config
    assert config.count('interval: "weekly"') == 2
    assert config.count('timezone: "Asia/Taipei"') == 2
    assert 'versioning-strategy: "increase"' in config
