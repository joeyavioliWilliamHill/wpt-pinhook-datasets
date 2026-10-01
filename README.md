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

## Common commands

```bash
.venv/bin/python -m pinhook.rebuild_historical --work-dir work
.venv/bin/python -m pinhook.import_2019 --raw-dir raw --work-dir work
.venv/bin/python -m pinhook.import_2020 --raw-dir raw --work-dir work
.venv/bin/python -m pinhook.import_2021 --raw-dir raw --work-dir work --allow-partial
.venv/bin/python explore_dataset.py --sale FTJUL22 --hip 8
```

The scripts operate on local files. Database loading and race-result acquisition are next implementation steps. See `docs/PEDIGREE_PRICE_FEATURES.md` for how dated race results will connect to sale prices.
