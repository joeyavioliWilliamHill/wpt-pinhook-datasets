# 2021 data restoration

Five 2021 yearling sales (Keeneland September; Fasig-Tipton Kentucky October, Saratoga, New York Bred, July) and Fasig-Tipton Midlantic May 2022. OBS March, Spring and June 2022 are still missing. This is partial juvenile coverage.

4,488 sold yearling purchases; 329 purchases with provisional juvenile candidates; 202 with a sold juvenile candidate. These counts are transactions and unreviewed candidate links, not confirmed unique horses.

Extract into the existing repo root. Rebuild with:

```bash
.venv/bin/python -m pinhook.import_2021 --raw-dir raw --work-dir work --allow-partial
```

Open work/cohort_2021_to_2022_partial/cohort_by_purchase.csv and identity_candidates.csv. Raw source exports are unchanged and source URLs/hashes are in work/cohort_2021_source_manifest.json. Data folders are already ignored by Git.
