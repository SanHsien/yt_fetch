"""Dependabot PR 自動核准政策的純邏輯測試。"""

from tools import classify_dependabot_update


def test_auto_merges_development_patch_with_expected_manifest():
    result = classify_dependabot_update.classify_update(
        ecosystem="pip",
        dependency_type="direct:development",
        update_type="version-update:semver-patch",
        changed_files=["pyproject.toml"],
    )

    assert result["decision"] == "auto_merge"


def test_auto_merges_development_minor_with_synced_manifests():
    result = classify_dependabot_update.classify_update(
        ecosystem="pip",
        dependency_type="direct:development",
        update_type="version-update:semver-minor",
        changed_files=["pyproject.toml", "requirements.txt"],
    )

    assert result["decision"] == "auto_merge"


def test_requires_manual_review_for_development_major():
    result = classify_dependabot_update.classify_update(
        ecosystem="pip",
        dependency_type="direct:development",
        update_type="version-update:semver-major",
        changed_files=["pyproject.toml"],
    )

    assert result["decision"] == "manual"
    assert "重大版本" in result["reason"]


def test_requires_manual_review_for_runtime_patch():
    result = classify_dependabot_update.classify_update(
        ecosystem="pip",
        dependency_type="direct:production",
        update_type="version-update:semver-patch",
        changed_files=["pyproject.toml"],
    )

    assert result["decision"] == "manual"
    assert "執行期" in result["reason"]


def test_auto_merges_github_actions_minor_in_workflow_scope():
    result = classify_dependabot_update.classify_update(
        ecosystem="github-actions",
        dependency_type="direct:production",
        update_type="version-update:semver-minor",
        changed_files=[".github/workflows/codeql.yml"],
    )

    assert result["decision"] == "auto_merge"


def test_requires_manual_review_when_action_update_touches_other_files():
    result = classify_dependabot_update.classify_update(
        ecosystem="github-actions",
        dependency_type="direct:production",
        update_type="version-update:semver-patch",
        changed_files=[".github/workflows/codeql.yml", "tools/release.py"],
    )

    assert result["decision"] == "manual"
    assert "檔案範圍" in result["reason"]


def test_requires_manual_review_for_unknown_metadata():
    result = classify_dependabot_update.classify_update(
        ecosystem="pip",
        dependency_type="indirect",
        update_type="version-update:semver-patch",
        changed_files=[],
    )

    assert result["decision"] == "manual"
