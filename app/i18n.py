"""Bilingual UI strings (fa/en) with a per-user language setting (settings.json)."""

import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
SETTINGS_PATH = APP_DIR / "settings.json"

_current = "fa"

FA = {
    "app_subtitle": "کنترل نور سیستم",
    "master_on": "روشن کردن همه",
    "master_off": "خاموش کردن همه",
    "reconnect": "اتصال مجدد",
    "status_preparing": "در حال آماده‌سازی…",
    "status_connecting": "در حال اتصال…",
    "status_detecting": "در حال شناسایی دستگاه‌ها…",
    "status_notfound": "OpenRGB یافت نشد — پوشه runtime/openrgb را بررسی کن",
    "status_launch_failed": "اجرای OpenRGB ناموفق بود",
    "connected_n": "وصل شد — {n} دستگاه",
    "lost": "ارتباط قطع شد: {err}",
    "connect_failed": "اتصال ناموفق: {err}",
    "leds_saved": "تعداد نور ثبت شد",
    "resizing": "در حال ثبت تعداد نورها…",
    "resize_failed": "تغییر تعداد نور ناموفق: {err}",
    "sel_none": "بخشی انتخاب نشده",
    "effect": "افکت",
    "color": "رنگ",
    "effect_speed": "سرعت افکت",
    "effect_speed_tip": "روی افکت‌های متحرک (رنگین‌کمان، نفس‌کشان، موج) اثر دارد",
    "brightness": "روشنایی",
    "led_layout": "ساختار نور (فقط بار اول برای هر هدر)",
    "choose_color": "انتخاب رنگ…",
    "color_dialog": "انتخاب رنگ",
    "set_count": "ثبت تعداد",
    "apply_all": "اعمال این تنظیم به همه بخش‌ها",
    "wizard_btn": "راه‌اندازی اولیه (پیدا کردن فن‌ها)",
    "wizard_tip": "هر هدر تنظیم‌نشده یکی‌یکی نارنجی چشمک می‌زند؛ تأیید کن کدام به فن‌هایت وصله",
    "autostart": "شروع خودکار با ویندوز (با دسترسی کامل)",
    "autostart_failed": "شروع خودکار فعال نشد: {msg}",
    "shortcut_btn": "ساخت میان‌بر روی دسکتاپ",
    "shortcut_ok": "میان‌بر «ARGB Studio» روی دسکتاپ ساخته شد ✅",
    "shortcut_failed": "ساخت میان‌بر ناموفق: {err}",
    "enabled": "فعال",
    "hint": "لایه سخت‌افزار باندل‌شده خودکار اجرا می‌شود. اگر نور مادربرد دیده نشد، "
            "برنامه را با run.bat اجرا کنید (دسترسی ادمین).",
    "not_configured": "تعداد نور ثبت نشده",
    "empty_title": "اتصال برقرار نیست",
    "empty_body": "چند لحظه صبر کن — برنامه خودش لایه سخت‌افزار را بالا می‌آورد.\n"
                  "اگر طول کشید، برنامه را با run.bat اجرا کن (دسترسی ادمین).",
    "wiz_all_done": "همه هدرها تعداد نور دارند و تنظیم شده‌اند ✅\n"
                    "اگر هنوز چیزی روشن نمی‌شود، کابل نورش را بررسی کن.",
    "wiz_done": "تمام شد! هر هدری که تأیید کردی ثبت و ذخیره شد ✅\n"
                "برای تنظیم دقیق تعداد نور، کارت هدر را انتخاب و «ثبت تعداد» را بزن.",
    "wiz_ask_title": "راه‌اندازی اولیه",
    "wiz_ask": "هدر «{name}» الان {n} نقطه نارنجی روشن است.\n\n"
               "نوری که الان نارنجی شده به همین هدر وصله؟",
    "wiz_yes": "بله، همین بود",
    "wiz_no": "نه، رد کن",
    "single_instance": "یک نسخه از برنامه در حال اجراست (احتمالاً کنار ساعت است).\n"
                       "اگر پنجره‌ای باز نشد: Task Manager → تب Details → pythonw.exe → End task",
    "tray_show": "نمایش برنامه",
    "tray_exit": "خروج کامل",
    "tray_hidden": "برنامه کنار ساعت ماند — برای خروج کامل از منوی آیکون استفاده کن",
    "percent": "٪",
}

EN = {
    "app_subtitle": "System lighting control",
    "master_on": "Turn ALL on",
    "master_off": "Turn ALL off",
    "reconnect": "Reconnect",
    "status_preparing": "Preparing…",
    "status_connecting": "Connecting…",
    "status_detecting": "Detecting devices…",
    "status_notfound": "OpenRGB not found — check the runtime/openrgb folder",
    "status_launch_failed": "Failed to start OpenRGB",
    "connected_n": "Connected — {n} device(s)",
    "lost": "Connection lost: {err}",
    "connect_failed": "Connection failed: {err}",
    "leds_saved": "LED count saved",
    "resizing": "Saving LED count…",
    "resize_failed": "LED count change failed: {err}",
    "sel_none": "No zone selected",
    "effect": "Effect",
    "color": "Color",
    "effect_speed": "Effect speed",
    "effect_speed_tip": "Affects animated effects (rainbow, breathing, wave)",
    "brightness": "Brightness",
    "led_layout": "LED layout (first time per header)",
    "choose_color": "Choose color…",
    "color_dialog": "Pick a color",
    "set_count": "Set count",
    "apply_all": "Apply this to ALL zones",
    "wizard_btn": "First-run setup (find my fans)",
    "wizard_tip": "Each unconfigured header blinks amber in turn; confirm which one feeds your fans",
    "autostart": "Start with Windows (full privileges)",
    "autostart_failed": "Autostart failed: {msg}",
    "shortcut_btn": "Create desktop shortcut",
    "shortcut_ok": "“ARGB Studio” shortcut created on the desktop ✅",
    "shortcut_failed": "Shortcut creation failed: {err}",
    "enabled": "Enabled",
    "hint": "The bundled hardware layer starts automatically. If motherboard lights "
            "don't appear, launch via run.bat (admin).",
    "not_configured": "Not configured",
    "empty_title": "Not connected",
    "empty_body": "Give it a moment — the app starts its hardware layer automatically.\n"
                  "If it takes long, launch via run.bat (admin).",
    "wiz_all_done": "Every header already has an LED count ✅\n"
                    "If something is still dark, check its cable.",
    "wiz_done": "Done! Confirmed headers were saved ✅\n"
                "Fine-tune a count by selecting a card and pressing “Set count”.",
    "wiz_ask_title": "First-run setup",
    "wiz_ask": "Header “{name}” is now glowing amber ({n} dots).\n\n"
               "Is the lighting that is glowing now connected to this header?",
    "wiz_yes": "Yes, that's it",
    "wiz_no": "No, skip",
    "single_instance": "An instance is already running (likely next to the clock).\n"
                       "If no window appeared: Task Manager → Details tab → pythonw.exe → End task",
    "tray_show": "Show window",
    "tray_exit": "Exit",
    "tray_hidden": "Minimized to tray — use the icon menu to exit",
    "percent": "%",
}

STRINGS = {"fa": FA, "en": EN}


def current() -> str:
    return _current


def is_rtl() -> bool:
    return _current == "fa"


def load_lang() -> str:
    global _current
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        _current = data.get("lang") if data.get("lang") in STRINGS else "fa"
    except (OSError, ValueError):
        _current = "fa"
    return _current


def set_lang(lang: str):
    global _current
    _current = lang if lang in STRINGS else "fa"
    try:
        SETTINGS_PATH.write_text(
            json.dumps({"lang": _current}, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass


def tr(key: str, **fmt) -> str:
    val = STRINGS[_current].get(key) or STRINGS["fa"].get(key) or key
    return val.format(**fmt) if fmt else val
