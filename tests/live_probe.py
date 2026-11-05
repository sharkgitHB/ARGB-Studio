"""Live probe: verify on real hardware that
1) zone.set_colors actually applies colors, and
2) a handcrafted RESIZEZONE packet resizes a 0-LED header zone.

Run from argb-studio/:  .venv/Scripts/python tests/live_probe.py
"""

import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backend import OPENRGB_PORT, find_openrgb_exe, launch_headless, port_open  # noqa: E402


def resize_zone(client, dev_id, zone_idx, new_size):
    """RESIZEZONE: server expects exactly 8 bytes: zone_idx (i32), new_size (i32)."""
    payload = struct.pack("ii", zone_idx, new_size)
    client.comms.send_header(dev_id, 1000, len(payload))  # 1000 = RGBCONTROLLER_RESIZEZONE
    client.comms.send_data(payload)


def main():
    exe = find_openrgb_exe()
    proc = launch_headless(exe)
    deadline = time.time() + 60
    while time.time() < deadline and not port_open(OPENRGB_PORT):
        if proc.poll() is not None:
            print("[FAIL] OpenRGB died early")
            return 1
        time.sleep(0.3)
    print("[OK] SDK server up")

    from openrgb import OpenRGBClient
    from openrgb.utils import RGBColor

    client = OpenRGBClient(name="LiveProbe")
    print(f"[OK] connected, devices: {len(client.devices)}")
    dev = client.devices[0]
    print(f"     board: {dev.name}")
    for zi, z in enumerate(dev.zones):
        print(f"     zone {zi}: {z.name!r} leds={len(z.leds)}")

    # ---- test 1: set_colors on the 1-LED onboard zone
    zone0 = dev.zones[0]
    print("[..] set_colors red on zone 0 ...")
    zone0.set_colors([RGBColor(255, 0, 0)], fast=True)
    dev.update()
    val = zone0.colors[0]
    print(f"[OK] readback zone0 led0 = {val}")
    time.sleep(2.0)

    # ---- test 2: resize a 0-LED header zone to 12
    target = next((zi for zi, z in enumerate(dev.zones) if len(z.leds) == 0), None)
    if target is None:
        print("[WARN] no 0-LED zone to test resize on")
    else:
        print(f"[..] resizing zone {target} ({dev.zones[target].name!r}) to 12 ...")
        try:
            resize_zone(client, dev.device_id, target, 12)
            time.sleep(0.5)
            dev.update()
            n = len(dev.zones[target].leds)
            print(f"[{'OK' if n == 12 else 'FAIL'}] zone {target} leds after resize = {n}")
            if n == 12:
                dev.zones[target].set_colors(
                    [RGBColor(0, 255, 0)] * 12, fast=True
                )
                print("[OK] set_colors on resized zone sent")
                time.sleep(2.0)
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] resize failed: {exc}")

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:  # noqa: BLE001
        proc.kill()
    print("[OK] done, server stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
