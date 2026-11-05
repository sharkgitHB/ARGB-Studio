"""Privacy scan of the distributable zip: no usernames / home paths inside.

Run from argb-studio/:  .venv/Scripts/python tests/privacy_scan.py
"""

import sys
import zipfile
from pathlib import Path

ZIP = Path(__file__).resolve().parent.parent.parent / "dist" / "ARGB-Studio-Portable.zip"
TEXT_EXT = (".py", ".bat", ".ps1", ".md", ".json", ".txt", ".cfg", ".pth", ".htm")
MARKERS = ("Mohsen", "C:\\Users", "C:/Users")


def main():
    z = zipfile.ZipFile(ZIP)
    leaks = []
    for name in z.namelist():
        low = name.lower()
        # Third-party library sources (pip, platformdirs, ...) ship with every
        # Python install and legitimately contain generic example strings.
        if "runtime/python/lib/site-packages" in low:
            continue
        if "mohsen" in low:
            leaks.append("filename: " + name)
            continue
        if low.endswith(TEXT_EXT):
            try:
                data = z.read(name).decode("utf-8", "ignore")
            except Exception:
                continue
            for marker in MARKERS:
                if marker in data:
                    leaks.append(f"content [{marker}]: {name}")
                    break
    print("zip:", ZIP, f"({ZIP.stat().st_size // 1_000_000} MB, {len(z.namelist())} files)")
    print("privacy leaks:", leaks if leaks else "NONE - clean")
    return 1 if leaks else 0


if __name__ == "__main__":
    sys.exit(main())
