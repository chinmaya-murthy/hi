# hi

## Setup (scikit-fda)

Run:

```bash
./setup_env.sh
```

This script creates a local virtual environment (`.venv`) and installs `scikit-fda`.

## Collect NSRDB USA data (1998-2024)

I added a collection script and generated a manifest for the years 1998 through 2024.

### 1) Generate/update the year manifest

```bash
python3 scripts/collect_nsrdb_us_data.py
```

This writes `data/nsrdb_us_1998_2024_manifest.csv` with one request per year.

### 2) Submit collection requests to NSRDB API

```bash
python3 scripts/collect_nsrdb_us_data.py \
  --submit \
  --api-key "<YOUR_NREL_API_KEY>" \
  --full-name "<YOUR_NAME>" \
  --email "<YOUR_EMAIL>" \
  --affiliation "<ORG>"
```

By default the script targets the USA bounding box via NSRDB GOES Aggregated v4 data and creates one request URL per year (1998-2024).

> Important: use your own NREL API key (`--api-key`). `DEMO_KEY` commonly fails for large USA-wide requests.
