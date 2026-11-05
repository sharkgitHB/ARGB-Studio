"""End-to-end test: launch bundled OpenRGB headless, wait for SDK port,
enumerate devices, then shut it down. Run from argb-studio/ with the venv:

    .venv/Scripts/python tests/e2e.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backend import (  # noqa: E402
    OPENRGB_PORT,
    find_openrgb_exe,
    launch_headless,
    port_open,
)


def main():
    exe = find_openrgb_exe()
    if not exe:
        print("[FAIL] OpenRGB.exe not found in runtime/openrgb")
        return 1
    print(f"[OK] bundled OpenRGB: {exe}")

    proc = launch_headless(exe)
    print(f"[..] launched pid={proc.pid}, waiting for SDK port {OPENRGB_PORT}...")
    deadline = time.time() + 60
    while time.time() < deadline:
        if port_open(OPENRGB_PORT):
            break
        if proc.poll() is not None:
            print(f"[FAIL] OpenRGB exited early, code={proc.returncode}")
            return 1
        time.sleep(0.3)
    else:
        print("[FAIL] SDK port never opened")
        proc.kill()
        return 1
    print("[OK] SDK server is listening (headless)")

    from openrgb import OpenRGBClient
    client = None
    for attempt in range(10):
        try:
            client = OpenRGBClient(name="E2ETest")
            if client.devices:
                break
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] connect attempt {attempt + 1}: {exc}")
        time.sleep(3)

    if client is None:
        print("[FAIL] could not connect")
        proc.terminate()
        return 1

    print(f"[OK] devices detected: {len(client.devices)}")
    for dev in client.devices:
        zones = ", ".join(f"{z.name} ({len(z.leds)} LED)" for z in dev.zones)
        print(f"     - {dev.name}: {zones}")
    if not client.devices:
        print("[NOTE] 0 devices -> probably needs administrator rights "
              "(run.bat self-elevates for this)")

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:  # noqa: BLE001
        proc.kill()
    print("[OK] headless OpenRGB stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
