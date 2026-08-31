from __future__ import annotations

import tomllib
from pathlib import Path

import ghostmcp
from ghostmcp.dashboard import app

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.2.1"


def test_release_identity_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

    assert project["name"] == "ghostmcp-server"
    assert project["version"] == EXPECTED_VERSION
    assert ghostmcp.__version__ == EXPECTED_VERSION
    assert app.version == EXPECTED_VERSION
    assert f"## {EXPECTED_VERSION} — " in changelog
    assert f"package version is `{EXPECTED_VERSION}`" in readme
    assert f"package version is `{EXPECTED_VERSION}`" in security


def test_release_uses_explicitly_gated_trusted_publishing() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "vars.PYPI_PUBLISH_ENABLED == 'true'" in workflow
    assert "environment:\n      name: pypi" in workflow
    assert "permissions:\n      id-token: write" in workflow
    assert "pypa/gh-action-pypi-publish@dc37677" in workflow
    assert "PYPI_API_TOKEN" not in workflow
    assert "TWINE_PASSWORD" not in workflow
