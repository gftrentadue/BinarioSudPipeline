#!/usr/bin/env python3
"""Impacchetta il GTFS gia' generato (assets/gtfs/*.txt) e i side-car di attributi
estesi (assets/attributes/*.json) in due zip versionati con lo stesso feed_version,
e produce il manifest.json corrispondente, secondo il contratto Fase 2 (spec SS1.3,
schema_version 2). Va eseguito dopo build_gtfs.py; scrive in dist/ (non versionato)."""
import csv, hashlib, json, os, zipfile
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GTFS_DIR = os.path.join(ROOT, "assets", "gtfs")
ATTRIBUTES_DIR = os.path.join(ROOT, "assets", "attributes")
DIST_DIR = os.path.join(ROOT, "dist")
REPO_URL = "https://github.com/gftrentadue/BinarioSudPipeline"


def read_feed_info():
    with open(os.path.join(GTFS_DIR, "feed_info.txt"), newline="", encoding="utf-8") as f:
        return next(csv.DictReader(f))


def iso_date(yyyymmdd):
    return datetime.strptime(yyyymmdd, "%Y%m%d").strftime("%Y-%m-%d")


def zip_dir(dir_path, names, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in names:
            zf.write(os.path.join(dir_path, name), arcname=name)
    return zip_path


def sha256_and_size(path):
    size_bytes = os.path.getsize(path)
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return size_bytes, sha256.hexdigest()


def main():
    os.makedirs(DIST_DIR, exist_ok=True)
    info = read_feed_info()
    feed_version = info["feed_version"]

    gtfs_zip_name = f"gtfs-{feed_version}.zip"
    gtfs_zip_path = os.path.join(DIST_DIR, gtfs_zip_name)
    txt_files = sorted(f for f in os.listdir(GTFS_DIR) if f.endswith(".txt"))
    zip_dir(GTFS_DIR, txt_files, gtfs_zip_path)
    feed_size_bytes, feed_sha256 = sha256_and_size(gtfs_zip_path)

    attributes_zip_name = f"attributes-{feed_version}.zip"
    attributes_zip_path = os.path.join(DIST_DIR, attributes_zip_name)
    json_files = sorted(f for f in os.listdir(ATTRIBUTES_DIR) if f.endswith(".json"))
    zip_dir(ATTRIBUTES_DIR, json_files, attributes_zip_path)
    attributes_size_bytes, attributes_sha256 = sha256_and_size(attributes_zip_path)

    manifest = {
        "schema_version": 2,
        "feed_version": feed_version,
        "feed_url": f"{REPO_URL}/releases/download/{feed_version}/{gtfs_zip_name}",
        "feed_published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feed_valid_from": iso_date(info["feed_start_date"]),
        "feed_valid_to": iso_date(info["feed_end_date"]),
        "feed_size_bytes": feed_size_bytes,
        "feed_sha256": feed_sha256,
        "attributes_url": f"{REPO_URL}/releases/download/{feed_version}/{attributes_zip_name}",
        "attributes_size_bytes": attributes_size_bytes,
        "attributes_sha256": attributes_sha256,
    }
    manifest_path = os.path.join(DIST_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"feed_version={feed_version}")
    print(f"gtfs_zip={gtfs_zip_path} ({feed_size_bytes} bytes)")
    print(f"attributes_zip={attributes_zip_path} ({attributes_size_bytes} bytes)")
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()
