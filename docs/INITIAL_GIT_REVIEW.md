# Initial Git commit review — September 30, 2026

Reviewed the uploaded `wpt-pinhook-datasets.zip` (5,303 archive entries). This clean code package keeps existing import names and does not deploy SQL or load a database.

## Commit now

`.gitignore`, `README.md`, `pyproject.toml`, `pinhook/`, `tests/`, `examples/`, `sql/`, `docs/`, `explore_dataset.py`, `SOURCE_MANIFEST.json`, and the cohort-specific README files.

Keep raw exports, PDFs, generated work tables, ZIP archives, environments, caches and credentials outside Git. The supplied `.gitignore` excludes them. The tiny `examples/` CSVs are the intended exception for reproducibility.

## Review findings and changes

- The upload includes `.venv`, package metadata, caches and macOS metadata. These are excluded from this package and ignored.
- `pinhook/"""Audit cross-sale identity coverage wi.py` is an accidental filename; it is ignored. Keep the canonical `match_audit.py`.
- `parse_catalog.py` and `pdf_catalog.py` were identical. `parse_catalog.py` now forwards to the canonical module so your earlier command still works.
- The PDF dependencies were not declared. `pip install -e '.[pdf]'` installs pypdf and fonttools.
- Catalog birth-date validation now rejects impossible calendar dates, with a regression test.
- The importer for 2021 is updated to the previously delivered version with explicit `--allow-partial` output and coverage metadata.
- Your uploaded data directories do not contain the five 2021 yearling export files or `work/cohort_2021_to_2022_partial/`. The three-cohort tables and 2019/2020 extensions are present. Restore the earlier 2021 dataset package separately; it is not included in this code-only ZIP.
- The SQL remains a draft. Shared horse/parentage/racing tables and dated feature snapshots are described in the architecture documents, not deployed tables. The database loader is still to be implemented.

## Apply in your existing VS Code terminal

Download `pinhook_git_initial.zip`, then run from the project root:

```bash
unzip -o ~/Downloads/pinhook_git_initial.zip -d .
.venv/bin/python -m pip install -e '.[pdf]'
.venv/bin/python -m unittest discover -s tests -v
```

Check whether generated data were previously tracked:

```bash
git ls-files raw work .venv pinhook_data.egg-info
```

If that prints paths, remove only their Git index entries (local files remain):

```bash
git rm -r --cached --ignore-unmatch raw work .venv pinhook_data.egg-info
```

Stage the initial source files explicitly:

```bash
git add .gitignore README.md pyproject.toml pinhook tests examples sql docs \
  explore_dataset.py SOURCE_MANIFEST.json README_DATASET.md \
  README_2019_ENRICHMENT.md README_2020_PARTIAL.md README_2021.md
git diff --cached --stat
git status --short
git remote -v
```

If these are the intended files and origin is your existing repository:

```bash
git commit -m "Add historical sales pipeline and shared horse data design"
git push -u origin HEAD
```

If `git push` reports the remote has commits missing locally, inspect and reconcile that history before pushing; do not force push. This package does not change your Git remote or branch.
