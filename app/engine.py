"""Engine: owns the OpenRGB connection, computes effect frames and ships them out.

Design notes:
- All blocking socket work happens on a plain `threading.Thread` (Sender) so the
  Qt UI never stalls, even if OpenRGB hiccups.
- `tick()` is called ~30x/s from the UI timer: it computes frames (cheap math,
  also used by the preview widget) and enqueues the sends.
- The thin `openrgb` import lives inside functions so the app can still run in
  --check mode (and show setup hints) without the library installed.
"""

import json
import queue
import struct
import threading
import time
from dataclasses import dataclass, asdict, fields

from PySide6.QtCore import QObject, Signal

from . import effects, i18n


@dataclass
class ZoneConfig:
    enabled: bool = True
    effect: str = effects.EFFECT_RAINBOW
    color: tuple = (138, 43, 226)  # violet-ish default
    speed: int = 4
    brightness: float = 0.8

    def to_json(self):
        d = asdict(self)
        d["color"] = list(self.color)
        return d

    @classmethod
    def from_json(cls, d):
        cfg = cls()
        for f in fields(cls):
            if f.name in d:
                val = d[f.name]
                if f.name == "color":
                    val = tuple(int(c) for c in val)
                elif f.name == "speed":
                    val = int(val)
                elif f.name == "brightness":
                    val = float(val)
                elif f.name == "enabled":
                    val = bool(val)
                setattr(cfg, f.name, val)
        return cfg


class ConnectionBridge(QObject):
    """Thread-safe signal bridge: worker threads emit, the UI thread listens."""

    status = Signal(bool, str)     # (connected, message)
    devices_loaded = Signal()


class Sender(threading.Thread):
    """Executes submitted callables serially on a background thread."""

    def __init__(self, on_error=None):
        super().__init__(daemon=True, name="OpenRGBSender")
        self._q = queue.Queue()
        self._on_error = on_error
        self._closed = False

    def submit(self, fn):
        if not self._closed:
            self._q.put(fn)

    def close(self):
        self._closed = True
        self._q.put(None)

    def run(self):
        while True:
            item = self._q.get()
            if item is None:
                break
            try:
                item()
            except Exception as exc:  # noqa: BLE001 - report, keep the thread alive
                if self._on_error:
                    try:
                        self._on_error(exc)
                    except Exception:
                        pass


class Engine:
    def __init__(self):
        self.bridge = ConnectionBridge()
        self.sender = Sender(on_error=self._on_worker_error)
        self.sender.start()
        self.client = None
        self.devices_meta = []   # [{"name": str, "type": str, "zones": [{"name": str, "leds": int}]}]
        self.config = {}         # (device_idx, zone_idx) -> ZoneConfig
        self.frames = {}         # (device_idx, zone_idx) -> [(r, g, b), ...] for the preview
        self.connected = False
        self._resizing = False
        self._loaded_state = {}
        self._t0 = time.monotonic()

    # ---------------------------------------------------------------- connection

    def connect_async(self, host="127.0.0.1", port=6742):
        self.bridge.status.emit(False, i18n.tr("status_connecting"))

        def job():
            from openrgb import OpenRGBClient
            client = OpenRGBClient(address=host, port=port, name="ARGB Studio")
            self._set_client(client)

        self.sender.submit(job)

    def _set_client(self, client):
        self.client = client
        self.connected = True
        # Put every device into its Direct mode, otherwise native effects on
        # the hardware keep fighting our color packets. Runs here (sender
        # thread) because set_mode blocks on confirmations.
        for dev in client.devices:
            try:
                dev.set_mode("Direct")
            except Exception:
                pass  # no Direct mode (or stubborn device) -> try anyway
        self.config = {}
        self.frames = {}
        self._build_meta()
        # Restore last session's settings now that zones exist.
        for key, raw in self._loaded_state.items():
            try:
                d, z = (int(part) for part in key.split(","))
            except ValueError:
                continue
            if (d, z) in self.config:
                self.config[(d, z)] = ZoneConfig.from_json(raw)
        self.bridge.status.emit(True, i18n.tr("connected_n", n=len(self.devices_meta)))
        self.bridge.devices_loaded.emit()

    def _build_meta(self):
        """Rebuild devices_meta from the live client, keeping existing configs."""
        self.devices_meta = []
        for di, dev in enumerate(self.client.devices):
            dev_type = getattr(dev.type, "name", str(dev.type)).replace("DeviceType.", "")
            zones = [{"name": z.name, "leds": len(z.leds)} for z in dev.zones]
            self.devices_meta.append({"name": dev.name, "type": dev_type, "zones": zones})
            for zi in range(len(zones)):
                self.config.setdefault((di, zi), ZoneConfig())

    def _on_worker_error(self, exc):
        if self.connected:
            # Connection dropped mid-session.
            self.connected = False
            self.client = None
            self.bridge.status.emit(False, i18n.tr("lost", err=exc))
        else:
            self.bridge.status.emit(False, i18n.tr("connect_failed", err=exc))

    # ---------------------------------------------------------------- state i/o

    def save_state(self, path):
        data = {f"{d},{z}": cfg.to_json() for (d, z), cfg in self.config.items()}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    def load_state(self, path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                self._loaded_state = json.load(fh)
        except (OSError, ValueError):
            self._loaded_state = {}

    # ---------------------------------------------------------------- zone resize

    def resize_zone(self, di, zi, size):
        """Set the LED count of a zone (needed once per ARGB header; the server
        persists it). Safe against the tick loop via the _resizing flag and the
        FIFO sender queue."""
        if not self.connected or self.client is None:
            return
        self._resizing = True

        def job():
            try:
                dev = self.client.devices[di]
                payload = struct.pack("ii", zi, int(size))
                # 1000 == PacketType.RGBCONTROLLER_RESIZEZONE; server reads
                # exactly 8 raw bytes: zone_idx (i32), new_size (i32).
                self.client.comms.send_header(dev.device_id, 1000, len(payload))
                self.client.comms.send_data(payload)
                time.sleep(0.5)
                dev.update()
                self._build_meta()
                self.bridge.status.emit(True, i18n.tr("leds_saved"))
                self.bridge.devices_loaded.emit()
            except Exception as exc:  # noqa: BLE001
                self.bridge.status.emit(False, i18n.tr("resize_failed", err=exc))
            finally:
                self._resizing = False

        self.sender.submit(job)

    # ---------------------------------------------------------------- frame loop

    def tick(self):
        """Called from the UI timer (~30 fps): compute + enqueue sends."""
        if not self.connected or self.client is None or self._resizing:
            return
        t = time.monotonic() - self._t0
        devices = self.client.devices
        for (di, zi), cfg in self.config.items():
            try:
                n = len(devices[di].zones[zi].leds)
            except (IndexError, AttributeError):
                continue
            if n <= 0:
                continue
            seed = di * 131 + zi * 17
            if cfg.enabled:
                frame = effects.compute_frame(
                    cfg.effect, cfg.color, cfg.speed, cfg.brightness, n, t, seed
                )
            else:
                frame = effects.zeros(n)
            self.frames[(di, zi)] = frame
            zone = devices[di].zones[zi]
            self.sender.submit(lambda z=zone, f=frame: self._send(z, f))

    @staticmethod
    def _send(zone, frame):
        from openrgb.utils import RGBColor
        zone.set_colors([RGBColor(*c) for c in frame], fast=True)
