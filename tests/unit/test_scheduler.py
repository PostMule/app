"""Unit tests for postmule.core.scheduler."""

from unittest.mock import MagicMock, patch

import pytest

from postmule.core import scheduler


class TestBuildLaunchdPlist:
    def test_contains_label_command_and_time(self):
        plist = scheduler.build_launchd_plist(
            "com.postmule.dailyrun", ["/usr/bin/postmule"], "/work/dir", "02:30"
        )
        assert "<string>com.postmule.dailyrun</string>" in plist
        assert "<string>/usr/bin/postmule</string>" in plist
        assert "<string>/work/dir</string>" in plist
        assert "<key>Hour</key><integer>2</integer>" in plist
        assert "<key>Minute</key><integer>30</integer>" in plist

    def test_multiple_args_each_become_a_string_element(self):
        plist = scheduler.build_launchd_plist(
            "com.postmule.dailyrun", ["/usr/bin/python3", "-m", "postmule.cli"], "/work", "09:00"
        )
        assert "<string>/usr/bin/python3</string>" in plist
        assert "<string>-m</string>" in plist
        assert "<string>postmule.cli</string>" in plist

    def test_escapes_special_characters(self):
        plist = scheduler.build_launchd_plist("label", ["/path/<bin>&"], "/work", "00:00")
        assert "&lt;bin&gt;&amp;" in plist


class TestGetScheduler:
    def test_windows(self):
        assert isinstance(scheduler.get_scheduler("win32"), scheduler.WindowsScheduler)

    def test_macos(self):
        assert isinstance(scheduler.get_scheduler("darwin"), scheduler.MacScheduler)

    def test_unsupported_platform_raises(self):
        with pytest.raises(NotImplementedError):
            scheduler.get_scheduler("linux")

    def test_defaults_to_sys_platform(self):
        with patch.object(scheduler.sys, "platform", "win32"):
            assert isinstance(scheduler.get_scheduler(), scheduler.WindowsScheduler)


class TestWindowsScheduler:
    def test_register_success(self):
        adapter = scheduler.WindowsScheduler()
        with patch.object(scheduler.subprocess, "run") as run:
            run.return_value = MagicMock(returncode=0, stderr="")
            adapter.register("PostMule Daily Run", ["C:\\postmule.exe"], "02:00", "C:\\work")
        args = run.call_args[0][0]
        assert args[0] == "powershell.exe"
        ps = args[-1]
        assert "PostMule Daily Run" in ps
        assert "New-ScheduledTaskTrigger -Daily -At \"02:00\"" in ps
        assert "-Argument" not in ps

    def test_register_with_args_includes_argument_clause(self):
        adapter = scheduler.WindowsScheduler()
        with patch.object(scheduler.subprocess, "run") as run:
            run.return_value = MagicMock(returncode=0, stderr="")
            adapter.register("name", ["/usr/bin/python3", "-m", "postmule.cli"], "02:00", "/work")
        ps = run.call_args[0][0][-1]
        assert '-Argument "-m postmule.cli"' in ps

    def test_register_failure_raises(self):
        adapter = scheduler.WindowsScheduler()
        with patch.object(scheduler.subprocess, "run") as run:
            run.return_value = MagicMock(returncode=1, stderr="boom")
            with pytest.raises(RuntimeError, match="boom"):
                adapter.register("name", ["exe"], "02:00", "C:\\work")

    def test_unregister(self):
        adapter = scheduler.WindowsScheduler()
        with patch.object(scheduler.subprocess, "run") as run:
            run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            adapter.unregister("PostMule Daily Run")
        ps = run.call_args[0][0][-1]
        assert "Unregister-ScheduledTask" in ps

    def test_is_registered_true(self):
        adapter = scheduler.WindowsScheduler()
        with patch.object(scheduler.subprocess, "run") as run:
            run.return_value = MagicMock(returncode=0)
            assert adapter.is_registered("name") is True

    def test_is_registered_false(self):
        adapter = scheduler.WindowsScheduler()
        with patch.object(scheduler.subprocess, "run") as run:
            run.return_value = MagicMock(returncode=1)
            assert adapter.is_registered("name") is False


class TestMacScheduler:
    def test_register_writes_plist_and_bootstraps(self, tmp_path):
        adapter = scheduler.MacScheduler()
        with (
            patch.object(scheduler.Path, "home", return_value=tmp_path),
            patch.object(scheduler.os, "getuid", return_value=501, create=True),
            patch.object(scheduler.subprocess, "run") as run,
        ):
            run.return_value = MagicMock(returncode=0)
            adapter.register("com.postmule.dailyrun", ["/usr/bin/postmule"], "02:00", "/work")

        plist_path = tmp_path / "Library" / "LaunchAgents" / "com.postmule.dailyrun.plist"
        assert plist_path.exists()
        assert "com.postmule.dailyrun" in plist_path.read_text(encoding="utf-8")
        bootstrap_call = run.call_args_list[-1][0][0]
        assert bootstrap_call[:2] == ["launchctl", "bootstrap"]

    def test_unregister_removes_plist(self, tmp_path):
        adapter = scheduler.MacScheduler()
        plist_path = tmp_path / "Library" / "LaunchAgents" / "com.postmule.dailyrun.plist"
        plist_path.parent.mkdir(parents=True)
        plist_path.write_text("placeholder", encoding="utf-8")

        with (
            patch.object(scheduler.Path, "home", return_value=tmp_path),
            patch.object(scheduler.os, "getuid", return_value=501, create=True),
            patch.object(scheduler.subprocess, "run") as run,
        ):
            run.return_value = MagicMock(returncode=0)
            adapter.unregister("com.postmule.dailyrun")

        assert not plist_path.exists()

    def test_is_registered(self):
        adapter = scheduler.MacScheduler()
        with (
            patch.object(scheduler.os, "getuid", return_value=501, create=True),
            patch.object(scheduler.subprocess, "run") as run,
        ):
            run.return_value = MagicMock(returncode=0)
            assert adapter.is_registered("com.postmule.dailyrun") is True
        launchctl_call = run.call_args[0][0]
        assert launchctl_call == ["launchctl", "print", "gui/501/com.postmule.dailyrun"]
