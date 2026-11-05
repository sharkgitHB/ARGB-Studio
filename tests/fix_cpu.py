"""Finalize CPU fan setup after the green-probe hit:
- Header 1: back to 12 (probe stretched it to 32 for testing)
- Header 2: 16 LEDs (CPU fan lives here; overshoot is harmless)
- Header 3: try to release back to 0
- Header 2: white fill as instant confirmation until the app takes over

Run from argb-studio/:  .venv/Scripts/python tests/fix_cpu.py
"""

import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backend import OPENRGB_PORT, find_openrgb_exe, launch_headless, port_open  # noqa: E402


def resize(client, dev, zone_idx, size):
    payload = struct.pack("ii", zone_idx, size)
    client.comms.send_header(dev.device_id, 1000, len(payload))
    client.comms.send_data(payload)


def main():
    proc = None
    if not port_open(OPENRGB_PORT):
        proc = launch_headless(find_openrgb_exe())
        deadline = time.time() + 60
        while time.time() < deadline and not port_open(OPENRGB_PORT):
            time.sleep(0.3)

    from openrgb import OpenRGBClient
    from openrgb.utils import RGBColor

    client = OpenRGBClient(name="CPUFanFix")
    dev = client.devices[0]
    zones = {z.name: (zi, z) for zi, z in enumerate(dev.zones)}

    h1 = zones.get("Addressable RGB Header 1")
    h2 = zones.get("Addressable RGB Header 2")
    h3 = zones.get("Addressable RGB Header 3")

    if h1 and len(h1[1].leds) != 12:
        resize(client, dev, h1[0], 12)
        time.sleep(0.4)
        dev.update()
        print("Header 1 ->", len(dev.zones[h1[0]].leds), "LEDs")

    if h2:
        resize(client, dev, h2[0], 16)
        time.sleep(0.4)
        dev.update()
        z = dev.zones[h2[0]]
        n = len(z.leds)
        z.set_colors([RGBColor(255, 255, 255)] * n, fast=True)
        print(f"Header 2 -> {n} LEDs, filled WHITE (confirmation)")

    if h3 and len(h3[1].leds) != 0:
        try:
            resize(client, dev, h3[0], 0)
            time.sleep(0.4)
            dev.update()
            print("Header 3 ->", len(dev.zones[h3[0]].leds), "LEDs")
        except Exception as exc:  # noqa: BLE001
            print("Header 3 release skipped:", exc)

    print("DONE - now press 'اتصال مجدد' inside the app")
    return 0


if __name__ == "__main__":
    sys.exit(main())
