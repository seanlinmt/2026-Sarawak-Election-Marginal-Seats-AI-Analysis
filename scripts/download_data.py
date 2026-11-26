"""Download official electiondata.my parquet and GeoJSON datasets into data/raw/."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "download_manifest.json"

DATASETS: list[tuple[str, str]] = [
    (
        "headline_ballots_state_swk.parquet",
        "https://lake.electiondata.my/results_headline/headline_ballots_state_swk.parquet",
    ),
    (
        "headline_stats_state_swk.parquet",
        "https://lake.electiondata.my/results_headline/headline_stats_state_swk.parquet",
    ),
    (
        "headline_ballots_byelections.parquet",
        "https://lake.electiondata.my/results_headline/headline_ballots_byelections.parquet",
    ),
    (
        "headline_stats_byelections.parquet",
        "https://lake.electiondata.my/results_headline/headline_stats_byelections.parquet",
    ),
    (
        "swk_se12_ballots.parquet",
        "https://lake.electiondata.my/results_saluran/swk_se12_ballots.parquet",
    ),
    (
        "swk_se12_stats.parquet",
        "https://lake.electiondata.my/results_saluran/swk_se12_stats.parquet",
    ),
    (
        "headline_ballots_federal.parquet",
        "https://lake.electiondata.my/results_headline/headline_ballots_federal.parquet",
    ),
    (
        "headline_stats_federal.parquet",
        "https://lake.electiondata.my/results_headline/headline_stats_federal.parquet",
    ),
    (
        "ge15_stats.parquet",
        "https://lake.electiondata.my/results_saluran/ge15_stats.parquet",
    ),
    (
        "ge15_ballots.parquet",
        "https://lake.electiondata.my/results_saluran/ge15_ballots.parquet",
    ),
    (
        "sarawak_2015_dun.geojson",
        "https://lake.electiondata.my/maps/delimitations/sarawak_2015_dun.geojson",
    ),
]


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_previous_manifest() -> dict[str, dict]:
    """Return prior manifest entries keyed by filename if available."""
    if not MANIFEST_PATH.exists():
        return {}
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {entry["filename"]: entry for entry in payload.get("files", []) if "filename" in entry}


def download_all(force: bool = False) -> list[dict]:
    """Download all configured datasets and write download_manifest.json."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    previous = _load_previous_manifest()
    entries: list[dict] = []

    with requests.Session() as session:
        for filename, url in DATASETS:
            dest = RAW_DIR / filename
            if dest.exists() and dest.stat().st_size > 0 and not force:
                prev = previous.get(filename, {})
                downloaded_at_utc = prev.get(
                    "downloaded_at_utc",
                    datetime.fromtimestamp(dest.stat().st_mtime, tz=timezone.utc).isoformat(),
                )
                http_status = prev.get("http_status", "cached")
                print(f"[skip] {filename} already exists ({dest.stat().st_size:,} bytes)")
            else:
                print(f"[get ] {url}")
                resp = session.get(url, timeout=120)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
                downloaded_at_utc = datetime.now(timezone.utc).isoformat()
                http_status = resp.status_code
                print(f"[ok  ] {filename} ({dest.stat().st_size:,} bytes, HTTP {http_status})")

            entries.append(
                {
                    "filename": filename,
                    "url": url,
                    "downloaded_at_utc": downloaded_at_utc,
                    "size_bytes": dest.stat().st_size,
                    "sha256": _sha256_file(dest),
                    "http_status": http_status,
                }
            )

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "https://electiondata.my/data-catalogue/",
        "file_count": len(entries),
        "files": entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote manifest: {MANIFEST_PATH} ({len(entries)} files)")
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download all files even if they already exist in data/raw/.",
    )
    args = parser.parse_args()
    download_all(force=args.force)


if __name__ == "__main__":
    main()
