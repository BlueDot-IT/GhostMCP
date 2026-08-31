from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

import ghostmcp
from ghostmcp.dashboard import app

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.2.1"


class ReleaseMetadataTests(unittest.TestCase):
    def test_release_identity_is_consistent(self) -> None:
        project = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

        self.assertEqual(project["name"], "ghostmcp-server")
        self.assertEqual(project["version"], EXPECTED_VERSION)
        self.assertEqual(ghostmcp.__version__, EXPECTED_VERSION)
        self.assertEqual(app.version, EXPECTED_VERSION)
        self.assertIn(f"## {EXPECTED_VERSION} — ", changelog)
        self.assertIn(f"package version is `{EXPECTED_VERSION}`", readme)
        self.assertIn(f"package version is `{EXPECTED_VERSION}`", security)

    def test_release_uses_explicitly_gated_trusted_publishing(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        release_job, publish_job = workflow.split(
            "\n  publish-pypi:\n", maxsplit=1
        )

        self.assertIn("fetch-depth: 0", release_job)
        self.assertIn(
            'test "v${PACKAGE_VERSION}" = "${GITHUB_REF_NAME}"',
            release_job,
        )
        self.assertIn(
            'git merge-base --is-ancestor "${GITHUB_SHA}" '
            "refs/remotes/origin/main",
            release_job,
        )
        self.assertIn("vars.PYPI_PUBLISH_ENABLED == 'true'", publish_job)
        self.assertIn("environment:\n      name: pypi", publish_job)
        self.assertIn("permissions:\n      id-token: write", publish_job)
        self.assertIn(
            "pypa/gh-action-pypi-publish@dc37677", publish_job
        )
        self.assertNotIn("PYPI_API_TOKEN", workflow)
        self.assertNotIn("TWINE_PASSWORD", workflow)


if __name__ == "__main__":
    unittest.main()
