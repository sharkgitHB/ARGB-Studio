"""Probe: light up every unconfigured header with a distinct color so the user
can see where the CPU fan is connected.

  Header 2            -> GREEN
  Header 3            -> BLUE
  Header 1 (LED 13+)  -> RED   (in case the CPU fan is chained after the hub)

Run from argb-studio/:  .venv/Scripts/python tests/probe_cpu.py
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
        exe = find_openrgb_exe()
        proc = launch_headless(exe)
        deadline = time.time() + 60
        while time.time() < deadline and not port_open(OPENRGB_PORT):
            time.sleep(0.3)

    from openrgb import OpenRGBClient
    from openrgb.utils import RGBColor

    client = OpenRGBClient(name="CPUFanProbe")
    dev = client.devices[0]
    print("board:", dev.name)
    for zi, z in enumerate(dev.zones):
        print(f"  zone {zi}: {z.name} ({len(z.leds)} LEDs)")

    zones = {z.name: (zi, z) for zi, z in enumerate(dev.zones)}
    h1 = zones.get("Addressable RGB Header 1")
    h2 = zones.get("Addressable RGB Header 2")
    h3 = zones.get("Addressable RGB Header 3")

    # Header 2 -> green
    if h2 and len(h2[1].leds) == 0:
        resize(client, dev, h2[0], 8)
        time.sleep(0.5)
        dev.update()
        z = dev.zones[h2[0]]
        if len(z.leds):
            z.set_colors([RGBColor(0, 255, 0)] * len(z.leds), fast=True)
            print("sent: Header 2 = GREEN (8 LEDs)")

    # Header 3 -> blue
    if h3 and len(h3[1].leds) == 0:
        resize(client, dev, h3[0], 8)
        time.sleep(0.5)
        dev.update()
        z = dev.zones[h3[0]]
        if len(z.leds):
            z.set_colors([RGBColor(0, 80, 255)] * len(z.leds), fast=True)
            print("sent: Header 3 = BLUE (8 LEDs)")

    # Header 1 extension (LED 13..32) -> red, in case the fan is chained
    if h1 and 0 < len(h1[1].leds) <= 12:
        resize(client, dev, h1[0], 32)
        time.sleep(0.5)
        dev.update()
        z = dev.zones[h1[0]]
        n = len(z.leds)
        if n >= 32:
            base = [RGBColor(0, 0, 0)] * 12
            z.set_colors(base + [RGBColor(255, 0, 0)] * (n - 12), fast=True)
            print("sent: Header 1 LEDs 13-32 = RED")

    time.sleep(2)
    print("PROBE DONE - colors stay on until changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
