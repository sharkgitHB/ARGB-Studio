"""Effect math for LED frames. Pure Python: no Qt, no hardware, easy to unit-test.

All colors are (r, g, b) tuples with 0-255 values.
"""

import colorsys
import math

EFFECT_OFF = "off"
EFFECT_STATIC = "static"
EFFECT_RAINBOW = "rainbow"
EFFECT_BREATHING = "breathing"
EFFECT_WAVE = "wave"

EFFECTS = [EFFECT_OFF, EFFECT_STATIC, EFFECT_RAINBOW, EFFECT_BREATHING, EFFECT_WAVE]

# Persian labels shown in the UI, keyed by effect id.
EFFECT_LABELS_FA = {
    EFFECT_OFF: "خاموش",
    EFFECT_STATIC: "رنگ ثابت",
    EFFECT_RAINBOW: "رنگین‌کمان",
    EFFECT_BREATHING: "نفس‌کشان",
    EFFECT_WAVE: "موج",
}

# English labels for the bilingual UI.
EFFECT_LABELS_EN = {
    EFFECT_OFF: "Off",
    EFFECT_STATIC: "Static",
    EFFECT_RAINBOW: "Rainbow",
    EFFECT_BREATHING: "Breathing",
    EFFECT_WAVE: "Wave",
}


def hsv_to_rgb(h, s, v):
    """h, s, v in 0..1 -> (r, g, b) 0-255."""
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return (round(r * 255), round(g * 255), round(b * 255))


def scale(color, factor):
    return tuple(min(255, round(c * factor)) for c in color)


def zeros(n):
    return [(0, 0, 0)] * max(0, n)


def compute_frame(effect, color, speed, brightness, n, t, seed=0):
    """Return a list of n (r, g, b) tuples for one LED zone.

    effect   : one of EFFECTS
    color    : base (r, g, b)
    speed    : 1..10
    brightness: 0..1
    n        : LED count
    t        : seconds since engine start
    seed     : per-zone offset so zones do not pulse in perfect unison
    """
    n = max(0, n)
    if n == 0 or effect == EFFECT_OFF:
        return zeros(n)

    bright = max(0.0, min(1.0, brightness))
    speed = max(0.1, float(speed))

    if effect == EFFECT_STATIC:
        return [scale(color, bright)] * n

    if effect == EFFECT_RAINBOW:
        # Entire rainbow scrolls along the strip; 60 deg/s per speed step.
        base_deg = seed * 47 + t * speed * 60.0
        step = 720.0 / n  # two full cycles across the zone
        return [hsv_to_rgb(((base_deg + i * step) % 360.0) / 360.0, 1.0, bright) for i in range(n)]

    if effect == EFFECT_BREATHING:
        # One breath cycle = 3 s at speed 1.
        phase = 2.0 * math.pi * t * speed / 3.0 + seed * 0.37
        v = 0.5 * (1.0 + math.cos(phase))
        v = 0.06 + 0.94 * (v ** 1.4)  # deeper dip, never fully off
        return [scale(color, bright * v)] * n

    if effect == EFFECT_WAVE:
        # Brightness waves travelling along the strip in the chosen color.
        waves = 2.0
        out = []
        for i in range(n):
            phase = 2.0 * math.pi * (i / max(n, 1) * waves - t * speed / 3.0) + seed * 0.61
            w = 0.5 + 0.5 * math.sin(phase)
            v = 0.12 + 0.88 * (w ** 2)
            out.append(scale(color, bright * v))
        return out

    return zeros(n)
