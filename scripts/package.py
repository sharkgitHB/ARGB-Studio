"""Build the distributable zip for friends.

Excludes dev-only files and personal state. Run from argb-studio/:
    .venv/Scripts/python scripts/package.py
Result: ../dist/ARGB-Studio-Portable.zip
"""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT.parent / "dist" / "ARGB-Studio-Portable.zip"

EXCLUDE_DIRS = {".venv", "__pycache__", "python-dl", "tests", "dist", ".git", "gen"}
EXCLUDE_FILES = {
    "last_state.json", "settings.json", "restart_app.ps1", "ui_preview.png",
    "create_shortcut.ps1", "app.ico",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}

INCLUDE_TOP = {
    "main.py",
    "README.md",
    "requirements.txt",
    "run.bat",
    "run_hidden.bat",
    "THIRD-PARTY-NOTICE.md",
    "app",
    "runtime/openrgb",
    "runtime/python",
}


def included(rel: Path) -> bool:
    parts = rel.parts
    if not parts:
        return False
    top = parts[0]
    if top not in {p.split("/")[0] for p in INCLUDE_TOP}:
        return False
    if any(p in EXCLUDE_DIRS for p in parts):
        return False
    if rel.name in EXCLUDE_FILES or rel.suffix.lower() in EXCLUDE_SUFFIXES:
        return False
    # never ship the personal hardware config
    if parts[0] == "runtime" and "openrgb-config" in parts:
        return False
    return True


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(ROOT.rglob("*")):
            rel = path.relative_to(ROOT)
            if not included(rel):
                continue
            if path.is_file():
                zf.write(path, Path("ARGB-Studio") / rel)
                count += 1
    size_mb = OUT.stat().st_size / 1_000_000
    print(f"packaged {count} files -> {OUT} ({size_mb:.0f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
