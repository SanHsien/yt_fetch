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
    assert "development-minor-and-patch:" in config
    assert "development-major:" in config
    assert 'update-types: ["minor", "patch"]' in config
    assert 'update-types: ["major"]' in config


def test_dependabot_review_and_merge_workflows_keep_strict_guards():
    review = (ROOT / ".github" / "workflows" / "dependabot-review.yml").read_text(encoding="utf-8")
    merge = (ROOT / ".github" / "workflows" / "dependabot-merge.yml").read_text(encoding="utf-8")

    assert "pull_request_target:" in review
    assert "checks: write" in review
    assert "dependabot[bot]" in review
    assert "25dd0e34f4fe68f24cc83900b1fe3fe149efef98" in review
    assert "tools/classify_dependabot_update.py" in review
    assert "Dependabot policy" in review
    assert "workflow_run:" in merge
    assert "actions: write" in merge
    assert "group: dependabot-merge-" in merge
    assert "cancel-in-progress: false" in merge
    assert "GH_REPO: ${{ github.repository }}" in merge
    assert 'author" != "app/dependabot"' in merge
    assert "dependencies-auto-merge" in merge
    assert 'app.slug == "github-actions"' in merge
    assert merge.count("dependencies-auto-merge") >= 2
    assert "dependencies-manual-review" in merge
    assert "--match-head-commit" in merge
    assert "check (windows-latest, 3.12)" in merge
    assert "Python security scan" in merge
    assert "gh workflow run dependency-freshness.yml" in merge


def test_freshness_workflow_owns_and_resolves_one_maintenance_issue():
    workflow = (ROOT / ".github" / "workflows" / "dependency-freshness.yml").read_text(
        encoding="utf-8"
    )

    assert "gh label create dependencies" in workflow
    assert "group: dependency-freshness" in workflow
    assert "cancel-in-progress: true" in workflow
    assert "pyproject.toml" in workflow
    assert "--author app/dependabot" in workflow
    assert "--state all" in workflow
    assert 'gh issue reopen "$issue"' in workflow
    assert 'checked_sha="$(git rev-parse HEAD)"' in workflow
    assert '--add-assignee "$GITHUB_REPOSITORY_OWNER"' in workflow
    assert "--add-label dependencies" in workflow
    assert 'gh issue edit "$issue" --body-file' in workflow
    assert 'gh issue close "$issue"' in workflow
