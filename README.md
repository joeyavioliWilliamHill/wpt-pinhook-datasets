# Thoroughbred sales, identity, racing, and pinhook datasets

A reproducible Python pipeline for official auction results, horse identity candidates, and yearling-to-two-year-old outcomes. The repo will also support pedigree performance features and joins to veterinary measurements. The existing Python package remains `pinhook` so current commands continue to work.

## Install and test

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[pdf]'
.venv/bin/python -m unittest discover -s tests -v
```

Python 3.11+. The PDF extra installs pypdf and fonttools; Excel parsing uses xlrd and openpyxl. Dependencies are declared in `pyproject.toml`.

## Repository contents

- `pinhook/`: source adapters, normalization, identity enrichment, match audits, and cohort builders.
- `sql/schema.sql`: the existing draft Postgres schema. It has not been deployed by this package. Read `docs/DATA_MODEL.md` before expanding it.
- `tests/`: identity, status, full-sibling, and catalog-enrichment checks.
- `examples/`: tiny reproducible sales samples and evidence notes.
- `SOURCE_MANIFEST.json`: source URLs and hashes for the initial three-cohort snapshot.
- `docs/`: data architecture, pedigree feature design, and initial Git instructions.

`raw/` and `work/` are local data directories excluded from Git. Raw auction exports must remain unchanged. Generated rows retain source hashes; source manifests retain acquisition locations. Store the full datasets in database/object storage and use Git for code, schema changes, documentation, and small examples.

## Current data scope

The original snapshot covers five 2022–2024 yearling sales per year and four 2023–2025 juvenile sales per year. Separate 2019 and 2020 extensions have narrower juvenile coverage. The 2021 extension exists in a separate delivered package but is missing from the uploaded project ZIP reviewed September 30, 2026; restore that package before counting it in a local total. See the cohort-specific READMEs and coverage manifests.

Match candidates are provisional. Repeated juvenile entries are retained. RNA bids are separate from sold proceeds; missing matches mean no entry identified within covered sales. No return is assigned to RNA, out, or unknown outcomes.

## Getting the inputs

```bash
.venv/bin/python -m pinhook.acquire              # all results into raw/, then work/*_full.csv for 2022-2025
.venv/bin/python -m pinhook.acquire --catalogs   # also Keeneland 2019-2024 books and the 2025 F-T catalog (~300 MB)
```

Every raw input is downloaded from the sale company: Keeneland results CSVs, OBS 2020-2023 result workbooks, and the public JSON feeds behind the Fasig-Tipton and 2024-2025 OBS results pages. Those two sites build their CSV in the browser, so the feed is saved as `<name>.json` next to the expected CSV name; the parsers map it to the same entries, and a hand-downloaded CSV takes precedence. Existing files are never overwritten. `raw/fetch_log.json` records URL, sha256, row count, fetch time, and agreement with `SOURCE_MANIFEST.json`.

What cannot be reproduced: the exact historical bytes of the browser-generated CSVs (the feeds are live, so later corrections show up; 6 of 15 Fasig-Tipton 2022-2025 sales and Keeneland 2024 now differ slightly from the snapshot), and the 2021 partial-cohort state assumed by `expand_obs_history`, since a fresh 2021 import already includes OBS 2022.

## Common commands

```bash
.venv/bin/python -m pinhook.rebuild_historical --work-dir work
.venv/bin/python -m pinhook.import_2019 --raw-dir raw --work-dir work
.venv/bin/python -m pinhook.import_2020 --raw-dir raw --work-dir work
.venv/bin/python -m pinhook.import_2021 --raw-dir raw --work-dir work --allow-partial
.venv/bin/python -m pinhook.expand_obs_history --raw-dir raw --work-dir work
.venv/bin/python explore_dataset.py --sale FTJUL22 --hip 8
```

The scripts operate on local files. Database loading and race-result acquisition are next implementation steps. See `docs/PEDIGREE_PRICE_FEATURES.md` for how dated race results will connect to sale prices.
