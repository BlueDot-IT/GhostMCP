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

    def test_release_verifies_tag_before_privileged_jobs(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        _, verification_and_release = workflow.split(
            "\n  verify-tag:\n", maxsplit=1
        )
        verification_job, release_and_publish = verification_and_release.split(
            "\n  release:\n", maxsplit=1
        )
        release_job, publish_job = release_and_publish.split(
            "\n  publish-pypi:\n", maxsplit=1
        )

        ancestry_check = (
            'git merge-base --is-ancestor "${GITHUB_SHA}" '
            "refs/remotes/origin/main"
        )
        version_read = 'PACKAGE_VERSION="$(python -c'

        self.assertIn("permissions:\n      contents: read", verification_job)
        self.assertNotIn("contents: write", verification_job)
        self.assertNotIn("id-token: write", verification_job)
        self.assertIn(
            "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            verification_job,
        )
        self.assertIn("fetch-depth: 0", verification_job)
        self.assertIn("persist-credentials: false", verification_job)
        self.assertIn(ancestry_check, verification_job)
        self.assertIn(
            'test "v${PACKAGE_VERSION}" = "${GITHUB_REF_NAME}"',
            verification_job,
        )
        self.assertLess(
            verification_job.index(ancestry_check),
            verification_job.index(version_read),
        )

        self.assertIn("needs: verify-tag", release_job)
        self.assertIn("persist-credentials: false", release_job)
        self.assertNotIn(ancestry_check, release_job)
        self.assertIn("needs: release", publish_job)

    def test_release_uses_explicitly_gated_trusted_publishing(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        _, publish_job = workflow.split("\n  publish-pypi:\n", maxsplit=1)

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
