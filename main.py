"""ARGB Studio — control the RGB of your whole system through OpenRGB.

Usage:
    python main.py            launch the GUI
    python main.py --check    self-test without GUI (imports, effects, connection)
"""

import os
import socket
import sys

# Embedded Python (._pth mode) does not add the script dir to sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_check():
    """Non-GUI self-test: verify deps import, effect math works, and report
    whether the OpenRGB SDK server is reachable."""
    print("== ARGB Studio self-test ==")
    ok = True

    try:
        from app import effects
        frame = effects.compute_frame(effects.EFFECT_RAINBOW, (255, 0, 0), 4, 0.8, 12, 1.0, 0)
        assert len(frame) == 12 and all(len(c) == 3 for c in frame)
        frame = effects.compute_frame(effects.EFFECT_BREATHING, (0, 255, 0), 5, 1.0, 8, 0.7, 3)
        assert len(frame) == 8
        print("[OK] effect math (12-LED rainbow + 8-LED breathing)")
    except Exception as exc:
        ok = False
        print(f"[FAIL] effect math: {exc}")

    try:
        import PySide6  # noqa: F401
        print(f"[OK] PySide6 {PySide6.__version__}")
    except Exception as exc:
        ok = False
        print(f"[FAIL] PySide6 import: {exc}")

    try:
        import openrgb  # noqa: F401
        from openrgb.utils import RGBColor  # noqa: F401
        print("[OK] openrgb-python")
    except Exception as exc:
        ok = False
        print(f"[FAIL] openrgb-python import: {exc}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.5)
    try:
        sock.connect(("127.0.0.1", 6742))
        sock.close()
        print("[OK] OpenRGB SDK server reachable on 127.0.0.1:6742")
        try:
            from openrgb import OpenRGBClient
            client = OpenRGBClient(name="ARGBStudioCheck")
            print(f"[OK] devices reported by OpenRGB: {len(client.devices)}")
            for dev in client.devices:
                zones = ", ".join(f"{z.name} ({len(z.leds)} LED)" for z in dev.zones)
                print(f"     - {dev.name}: {zones}")
        except Exception as exc:
            print(f"[WARN] could not enumerate devices: {exc}")
    except OSError:
        print("[WARN] OpenRGB SDK server NOT reachable on 127.0.0.1:6742")
        print("       Start OpenRGB -> Settings (tab) -> SDK Server -> Start Server")

    print("== done ==")
    return 0 if ok else 1


def main():
    if "--check" in sys.argv:
        sys.exit(run_check())
    from app.main_window import launch
    launch()


if __name__ == "__main__":
    main()
