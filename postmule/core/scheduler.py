"""Per-OS scheduler adapter for PostMule's daily run.

Windows registers a Task Scheduler entry via the Register-ScheduledTask
PowerShell cmdlet (unchanged from the prior cli.py implementation). macOS
registers a LaunchAgents plist via launchctl. Both interpret run_time as a
local HH:MM daily trigger.

macOS status: implemented but UNTESTED on real hardware — verify at
bring-up before relying on it.
"""

from __future__ import annotations

import abc
import os
import subprocess
import sys
import xml.sax.saxutils as sax
from pathlib import Path


class SchedulerAdapter(abc.ABC):
    @abc.abstractmethod
    def register(self, name: str, command: list[str], run_time: str, work_dir: str) -> None: ...

    @abc.abstractmethod
    def unregister(self, name: str) -> None: ...

    @abc.abstractmethod
    def is_registered(self, name: str) -> bool: ...


def build_launchd_plist(label: str, command: list[str], work_dir: str, run_time: str) -> str:
    """macOS launchd plist with a StartCalendarInterval daily trigger at run_time (local HH:MM)."""
    hour, minute = run_time.split(":")
    args = "".join(f"    <string>{sax.escape(a)}</string>\n" for a in command)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{sax.escape(label)}</string>
  <key>ProgramArguments</key>
  <array>
{args}  </array>
  <key>WorkingDirectory</key><string>{sax.escape(work_dir)}</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>{int(hour)}</integer>
    <key>Minute</key><integer>{int(minute)}</integer>
  </dict>
  <key>RunAtLoad</key><false/>
</dict>
</plist>"""


class WindowsScheduler(SchedulerAdapter):
    """Windows Task Scheduler, via Register-ScheduledTask."""

    def register(self, name: str, command: list[str], run_time: str, work_dir: str) -> None:
        exe = command[0]
        arg_clause = f' -Argument "{" ".join(command[1:])}"' if len(command) > 1 else ""
        action = (
            f'New-ScheduledTaskAction -Execute "{exe}"{arg_clause} -WorkingDirectory "{work_dir}"'
        )
        ps = (
            f'$action   = {action}; '
            f'$trigger  = New-ScheduledTaskTrigger -Daily -At "{run_time}"; '
            f'$settings = New-ScheduledTaskSettingsSet '
            f'  -ExecutionTimeLimit (New-TimeSpan -Hours 2) '
            f'  -RestartCount 1 -RestartInterval (New-TimeSpan -Minutes 30) '
            f'  -StartWhenAvailable; '
            f'if (Get-ScheduledTask -TaskName "{name}" -ErrorAction SilentlyContinue) {{ '
            f'  Unregister-ScheduledTask -TaskName "{name}" -Confirm:$false }}; '
            f'Register-ScheduledTask -TaskName "{name}" -Action $action -Trigger $trigger '
            f'  -Settings $settings -RunLevel Highest '
            f'  -Description "PostMule daily mail processing run" | Out-Null'
        )
        result = subprocess.run(
            ["powershell.exe", "-NonInteractive", "-Command", ps],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Task Scheduler registration failed: {result.stderr.strip()}")

    def unregister(self, name: str) -> None:
        ps = (
            f'if (Get-ScheduledTask -TaskName "{name}" -ErrorAction SilentlyContinue) {{ '
            f'  Unregister-ScheduledTask -TaskName "{name}" -Confirm:$false; '
            f'  Write-Host "Task removed." '
            f'}} else {{ Write-Host "Task not found — nothing to remove." }}'
        )
        subprocess.run(
            ["powershell.exe", "-NonInteractive", "-Command", ps],
            capture_output=True, text=True,
        )

    def is_registered(self, name: str) -> bool:
        ps = (
            f'if (Get-ScheduledTask -TaskName "{name}" -ErrorAction SilentlyContinue) '
            f'{{ exit 0 }} else {{ exit 1 }}'
        )
        result = subprocess.run(
            ["powershell.exe", "-NonInteractive", "-Command", ps],
            capture_output=True,
        )
        return result.returncode == 0


class MacScheduler(SchedulerAdapter):
    """macOS launchd, via a per-user LaunchAgents plist. Implemented but UNTESTED on hardware."""

    def _plist_path(self, name: str) -> Path:
        return Path.home() / "Library" / "LaunchAgents" / f"{name}.plist"

    def register(self, name: str, command: list[str], run_time: str, work_dir: str) -> None:
        plist = build_launchd_plist(name, command, work_dir, run_time)
        path = self._plist_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plist, encoding="utf-8")
        uid = os.getuid()  # type: ignore[attr-defined]  # POSIX-only; this class runs on macOS
        subprocess.run(["launchctl", "bootout", f"gui/{uid}", str(path)], check=False)
        subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(path)], check=True)

    def unregister(self, name: str) -> None:
        path = self._plist_path(name)
        uid = os.getuid()  # type: ignore[attr-defined]
        subprocess.run(["launchctl", "bootout", f"gui/{uid}", str(path)], check=False)
        if path.exists():
            path.unlink()

    def is_registered(self, name: str) -> bool:
        uid = os.getuid()  # type: ignore[attr-defined]
        result = subprocess.run(
            ["launchctl", "print", f"gui/{uid}/{name}"],
            capture_output=True,
        )
        return result.returncode == 0


def get_scheduler(target_platform: str | None = None) -> SchedulerAdapter:
    """Return the scheduler adapter for target_platform (default: sys.platform)."""
    target_platform = target_platform or sys.platform
    if target_platform == "win32":
        return WindowsScheduler()
    if target_platform == "darwin":
        return MacScheduler()
    raise NotImplementedError(f"no scheduler adapter for platform {target_platform!r}")
