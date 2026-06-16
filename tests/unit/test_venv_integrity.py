"""Verify the project runs in its .venv, not the global Python interpreter.

These tests guard against the class of bug where ops/scripts/safe-pip.ps1 installs
packages into the global Python instead of the project .venv (which has
include-system-site-packages = false, so global installs are invisible to the app).
See: ops proposals/safe-pip-targets-wrong-python.md, ops issue #11.
"""
import pathlib
import sys


class TestVenvIntegrity:
    def test_interpreter_is_in_project_venv(self):
        exe = pathlib.Path(sys.executable)
        assert ".venv" in exe.parts, (
            f"Tests must run inside the project .venv; got {exe}. "
            "Run pytest via .venv/Scripts/pytest.exe or .venv/bin/pytest"
        )

    def test_cryptography_installed_in_venv(self):
        import cryptography

        pkg_path = pathlib.Path(cryptography.__file__)
        assert ".venv" in pkg_path.parts, (
            f"cryptography is not installed in the project .venv.\n"
            f"  Path: {pkg_path}\n"
            "If safe-pip.ps1 was recently run, it may have installed into the "
            "global Python. See ops proposals/safe-pip-targets-wrong-python.md."
        )

    def test_requests_installed_in_venv(self):
        import requests

        pkg_path = pathlib.Path(requests.__file__)
        assert ".venv" in pkg_path.parts, (
            f"requests is not installed in the project .venv.\n"
            f"  Path: {pkg_path}"
        )
