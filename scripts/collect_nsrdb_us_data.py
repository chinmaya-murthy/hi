#!/usr/bin/env python3
"""Build (and optionally execute) NSRDB USA GOES v4 download requests for 1998-2024."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from pathlib import Path
from urllib.parse import urlencode

BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download"
YEARS = list(range(1998, 2025))
# Approximate CONUS bounding box in WKT POLYGON (lon lat).
USA_WKT = "POLYGON((-125 24,-66 24,-66 49,-125 49,-125 24))"


def build_query(args: argparse.Namespace, year: int) -> str:
    params = {
        "api_key": args.api_key,
        "wkt": args.wkt,
        "names": str(year),
        "attributes": args.attributes,
        "interval": args.interval,
        "utc": str(args.utc).lower(),
        "leap_day": str(args.leap_day).lower(),
        "full_name": args.full_name,
        "email": args.email,
        "affiliation": args.affiliation,
        "reason": args.reason,
        "mailing_list": "false",
    }
    return f"{BASE_URL}.json?{urlencode(params)}"


def run_curl(url: str) -> dict:
    proc = subprocess.run(
        ["curl", "-sS", "--fail", url],
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "curl failed")
    return json.loads(proc.stdout)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--api-key", default="DEMO_KEY")
    p.add_argument("--full-name", default="Data Collector")
    p.add_argument("--email", default="you@example.com")
    p.add_argument("--affiliation", default="research")
    p.add_argument("--reason", default="nsrdb us 1998-2024 collection")
    p.add_argument("--attributes", default="dhi,dni,ghi,air_temperature,wind_speed")
    p.add_argument("--interval", default="30")
    p.add_argument("--wkt", default=USA_WKT)
    p.add_argument("--utc", action="store_true")
    p.add_argument("--leap-day", action="store_true")
    p.add_argument("--manifest", default="data/nsrdb_us_1998_2024_manifest.csv")
    p.add_argument("--submit", action="store_true", help="Submit API requests via curl")
    p.add_argument(
        "--format",
        choices=("json", "csv"),
        default="json",
        help="Use json for async/archive requests, csv for direct point/year download.",
    )
    p.add_argument("--sleep", type=float, default=1.0)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.submit and args.api_key == "DEMO_KEY":
        print(
            "Warning: DEMO_KEY is often blocked for large NSRDB requests; use your own NREL API key.",
        )
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for year in YEARS:
        url = build_query(args, year)
        url = url.replace(".json?", f".{args.format}?")
        row = {"year": year, "request_url": url, "status": "planned", "download_url": "", "message": ""}

        if args.submit:
            try:
                payload = run_curl(url)
                row["status"] = "submitted"
                row["download_url"] = payload.get("outputs", {}).get("downloadUrl", "")
                row["message"] = payload.get("errors", "") or payload.get("warnings", "") or "ok"
            except Exception as exc:  # noqa: BLE001
                row["status"] = "failed"
                row["message"] = str(exc)
            time.sleep(args.sleep)

        rows.append(row)

    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "status", "download_url", "message", "request_url"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
