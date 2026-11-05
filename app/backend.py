"""Manages the bundled headless OpenRGB process — our hardware layer.

The app ships a portable OpenRGB in ``runtime/openrgb``. On startup the
manager checks whether an SDK server is already listening; if not, it launches
the bundled OpenRGB completely headless (``--server``, no GUI window, private
config dir) and waits for the port to open. The UI never blocks: all waiting
happens on a background thread and results arrive via Qt signals.
"""

import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, Signal

OPENRGB_PORT = 6742
LOCK_PORT = 6767   # single-instance fallback for non-Windows platforms
_MUTEX_NAME = "Local\\ARGBStudio.SingleInstance"


def app_dir() -> Path:
    """argb-studio/ — the parent of the app package."""
    return Path(__file__).resolve().parent.parent


def port_open(port, host="127.0.0.1", timeout=0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def acquire_lock():
    """Single-instance guard.

    Windows: a named mutex — the canonical mechanism. It is visible in tools,
    cannot collide with unrelated software (unlike a fixed TCP port) and is
    released automatically by the kernel if the owning process dies.
    Returns a keep-alive handle, or None if another instance already runs.
    """
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        ERROR_ALREADY_EXISTS = 183
        handle = kernel32.CreateMutexW(None, True, _MUTEX_NAME)
        if not handle:
            return None  # could not create; fail safe to "blocked"
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return None
        return handle
    # Non-Windows fallback: TCP loopback bind.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", LOCK_PORT))
        return s
    except OSError:
        s.close()
        return None


def surface_existing_window() -> bool:
    """Try to bring an already-running instance's window to the front."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "ARGB Studio")
        if not hwnd:
            return False
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def find_openrgb_exe() -> Path | None:
    candidates = [
        app_dir() / "runtime" / "openrgb" / "OpenRGB.exe",
        app_dir() / "runtime" / "openrgb" / "openrgb.exe",
        Path(r"C:\Program Files\OpenRGB\OpenRGB.exe"),
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def launch_headless(exe: Path) -> subprocess.Popen:
    """Start bundled OpenRGB as a windowless SDK server with a private config dir."""
    cfg_dir = app_dir() / "runtime" / "openrgb-config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(exe),
        "--server",
        "--config", str(cfg_dir),
        "--loglevel", "2",  # errors only
    ]
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    return subprocess.Popen(
        cmd,
        cwd=str(exe.parent),
        creationflags=subprocess.CREATE_NO_WINDOW,
        startupinfo=si,
    )


class OpenRGBManager(QObject):
    stateChanged = Signal(str)
    # states: "already-running" | "launched" | "notfound" | "failed"

    def __init__(self):
        super().__init__()
        self.process: subprocess.Popen | None = None
        self.we_launched = False

    # ---------------------------------------------------------------- public

    def ensure_running_async(self, wait_for_port=30.0):
        threading.Thread(
            target=self.ensure_running, args=(wait_for_port,), daemon=True
        ).start()

    def ensure_running(self, wait_for_port=30.0) -> bool:
        if port_open(OPENRGB_PORT):
            self.stateChanged.emit("already-running")
            return True

        exe = find_openrgb_exe()
        if exe is None:
            self.stateChanged.emit("notfound")
            return False

        try:
            self.process = launch_headless(exe)
        except OSError:
            self.stateChanged.emit("failed")
            return False
        self.we_launched = True

        deadline = time.time() + wait_for_port
        while time.time() < deadline:
            if port_open(OPENRGB_PORT):
                self.stateChanged.emit("launched")
                return True
            if self.process.poll() is not None:
                self.stateChanged.emit("failed")
                return False
            time.sleep(0.25)
        self.stateChanged.emit("failed")
        return False

    def shutdown(self):
        """Close the server only if we started it ourselves."""
        if self.we_launched and self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
