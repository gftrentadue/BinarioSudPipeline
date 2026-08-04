#!/usr/bin/env python3
"""Impacchetta il GTFS gia' generato (assets/gtfs/*.txt) in uno zip versionato
e produce il manifest.json corrispondente, secondo il contratto Fase 2 (spec SS1.3).
Va eseguito dopo build_gtfs.py; scrive in dist/ (non versionato)."""
import csv, hashlib, json, os, zipfile
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GTFS_DIR = os.path.join(ROOT, "assets", "gtfs")
DIST_DIR = os.path.join(ROOT, "dist")
REPO_URL = "https://github.com/gftrentadue/BinarioSudPipeline"


def read_feed_info():
    with open(os.path.join(GTFS_DIR, "feed_info.txt"), newline="", encoding="utf-8") as f:
        return next(csv.DictReader(f))


def iso_date(yyyymmdd):
    return datetime.strptime(yyyymmdd, "%Y%m%d").strftime("%Y-%m-%d")


def main():
    os.makedirs(DIST_DIR, exist_ok=True)
    info = read_feed_info()
    feed_version = info["feed_version"]

    zip_name = f"gtfs-{feed_version}.zip"
    zip_path = os.path.join(DIST_DIR, zip_name)
    txt_files = sorted(f for f in os.listdir(GTFS_DIR) if f.endswith(".txt"))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in txt_files:
            zf.write(os.path.join(GTFS_DIR, name), arcname=name)

    size_bytes = os.path.getsize(zip_path)
    sha256 = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)

    manifest = {
        "schema_version": 1,
        "feed_version": feed_version,
        "feed_url": f"{REPO_URL}/releases/download/{feed_version}/{zip_name}",
        "feed_published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feed_valid_from": iso_date(info["feed_start_date"]),
        "feed_valid_to": iso_date(info["feed_end_date"]),
        "feed_size_bytes": size_bytes,
        "feed_sha256": sha256.hexdigest(),
    }
    manifest_path = os.path.join(DIST_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"feed_version={feed_version}")
    print(f"zip={zip_path} ({size_bytes} bytes)")
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()
