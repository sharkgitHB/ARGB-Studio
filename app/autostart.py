"""Windows auto-start: a scheduled task (highest privileges) that runs the app
at logon. Elevated privileges are required for motherboard RGB access, and a
scheduled task with /RL HIGHEST starts without a UAC prompt every boot."""

import subprocess
from pathlib import Path

TASK_NAME = "ARGB Studio"
NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW


def _run(args):
    try:
        return subprocess.run(
            args, capture_output=True, text=True, creationflags=NO_WINDOW, timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _task_bat() -> str:
    return str(Path(__file__).resolve().parent.parent / "run_hidden.bat")


def is_enabled() -> bool:
    r = _run(["schtasks", "/Query", "/TN", TASK_NAME])
    return r is not None and r.returncode == 0


def enable():
    """Returns (ok, message)."""
    r = _run([
        "schtasks", "/Create", "/TN", TASK_NAME,
        "/TR", f'"{_task_bat()}"',
        "/SC", "ONLOGON", "/RL", "HIGHEST", "/F",
    ])
    if r is None:
        return False, "اجرا کردن schtasks ممکن نشد"
    if r.returncode == 0:
        return True, ""
    return False, (r.stderr or r.stdout or "خطای نامشخص").strip()


def disable():
    r = _run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])
    if r is None:
        return False, "اجرا کردن schtasks ممکن نشد"
    return r.returncode == 0, ""
