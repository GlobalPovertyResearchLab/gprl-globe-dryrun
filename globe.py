#!/usr/bin/env python3
"""Build people.js from people/*/profile.json, then open the globe.

    python3 globe.py            # build + open in the browser
    python3 globe.py --no-open  # build only

Folders starting with "_" or "." are skipped (people/_example is the template).
A broken profile is reported and skipped, so one bad entry never blanks the globe.
"""
import json
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PEOPLE = ROOT / "people"
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
REQUIRED = ("name", "city", "country", "lat", "lon", "fun_fact", "photo")
MAX_PHOTO_MB = 2


def load(folder: Path) -> dict:
    f = folder / "profile.json"
    if not f.is_file():
        raise ValueError("no profile.json")
    p = json.loads(f.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if p.get(k) in (None, "")]
    if missing:
        raise ValueError("missing " + ", ".join(missing))
    lat, lon = float(p["lat"]), float(p["lon"])
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError(f"lat/lon out of range: {lat}, {lon}")
    photo = (folder / str(p["photo"])).resolve()
    if photo.parent != folder.resolve() or not photo.is_file():
        raise ValueError(f"photo not found in folder: {p['photo']}")
    if photo.suffix.lower() not in PHOTO_EXT:
        raise ValueError(f"photo type not supported: {photo.suffix}")
    mb = photo.stat().st_size / 1e6
    if mb > MAX_PHOTO_MB:
        print(f"  ! {folder.name}: photo is {mb:.1f} MB (keep it under {MAX_PHOTO_MB})")
    return {
        "id": folder.name,
        "name": str(p["name"]).strip(),
        "city": str(p["city"]).strip(),
        "country": str(p["country"]).strip(),
        "lat": lat,
        "lon": lon,
        "fun_fact": str(p["fun_fact"]).strip(),
        "photo": f"people/{folder.name}/{photo.name}",
    }


def main() -> None:
    people, skipped = [], []
    for folder in sorted(PEOPLE.iterdir(), key=lambda d: d.name.lower()):
        if not folder.is_dir() or folder.name[0] in "_.":
            continue
        try:
            people.append(load(folder))
        except (ValueError, json.JSONDecodeError) as e:
            skipped.append((folder.name, str(e)))

    out = ROOT / "people.js"
    out.write_text("window.PEOPLE = " + json.dumps(people, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")

    countries = {p["country"].lower() for p in people}
    print(f"✓ {len(people)} people · {len(countries)} countries → people.js")
    for name, why in skipped:
        print(f"  ✗ {name}: {why}")

    if "--no-open" not in sys.argv:
        webbrowser.open((ROOT / "index.html").as_uri())


if __name__ == "__main__":
    main()

# dry-run: a PR that edits a file outside people/
