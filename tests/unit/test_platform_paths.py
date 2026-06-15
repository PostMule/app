"""Unit tests for postmule.core.platform_paths."""

from pathlib import Path

from postmule.core import platform_paths


class TestUserConfigDir:
    def test_windows(self, monkeypatch):
        monkeypatch.setattr(platform_paths.sys, "platform", "win32")
        monkeypatch.setenv("APPDATA", "C:\\Users\\test\\AppData\\Roaming")
        assert platform_paths.user_config_dir() == Path(
            "C:\\Users\\test\\AppData\\Roaming"
        ) / "PostMule"

    def test_windows_without_appdata_falls_back_to_home(self, monkeypatch):
        monkeypatch.setattr(platform_paths.sys, "platform", "win32")
        monkeypatch.delenv("APPDATA", raising=False)
        result = platform_paths.user_config_dir()
        assert result == Path.home() / "AppData" / "Roaming" / "PostMule"

    def test_macos(self, monkeypatch):
        monkeypatch.setattr(platform_paths.sys, "platform", "darwin")
        result = platform_paths.user_config_dir()
        assert result == Path.home() / "Library" / "Application Support" / "PostMule"

    def test_linux_with_xdg(self, monkeypatch):
        monkeypatch.setattr(platform_paths.sys, "platform", "linux")
        monkeypatch.setenv("XDG_CONFIG_HOME", "/home/test/.config")
        assert platform_paths.user_config_dir() == Path("/home/test/.config") / "PostMule"

    def test_linux_without_xdg_falls_back_to_home(self, monkeypatch):
        monkeypatch.setattr(platform_paths.sys, "platform", "linux")
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        result = platform_paths.user_config_dir()
        assert result == Path.home() / ".config" / "PostMule"


class TestDefaultInstallDir:
    def test_windows(self, monkeypatch):
        monkeypatch.setattr(platform_paths.sys, "platform", "win32")
        monkeypatch.setenv("PROGRAMDATA", "C:\\ProgramData")
        assert platform_paths.default_install_dir() == Path("C:\\ProgramData") / "PostMule"

    def test_windows_without_programdata_falls_back(self, monkeypatch):
        monkeypatch.setattr(platform_paths.sys, "platform", "win32")
        monkeypatch.delenv("PROGRAMDATA", raising=False)
        assert platform_paths.default_install_dir() == Path("C:\\ProgramData") / "PostMule"

    def test_macos(self, monkeypatch):
        monkeypatch.setattr(platform_paths.sys, "platform", "darwin")
        result = platform_paths.default_install_dir()
        assert result == Path.home() / "Library" / "Application Support" / "PostMule"

    def test_linux_with_xdg(self, monkeypatch):
        monkeypatch.setattr(platform_paths.sys, "platform", "linux")
        monkeypatch.setenv("XDG_DATA_HOME", "/home/test/.local/share")
        assert platform_paths.default_install_dir() == Path("/home/test/.local/share") / "PostMule"

    def test_linux_without_xdg_falls_back_to_home(self, monkeypatch):
        monkeypatch.setattr(platform_paths.sys, "platform", "linux")
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        result = platform_paths.default_install_dir()
        assert result == Path.home() / ".local" / "share" / "PostMule"
