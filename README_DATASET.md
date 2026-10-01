# Pinhook historical sales dataset — three annual cohorts

Official auction-house result exports, acquired September 29, 2026. Five yearling sales per year (Keeneland September; Fasig-Tipton Kentucky October, Saratoga, New York Bred, July) are paired to four juvenile sales the next year (OBS March, Spring, June; Fasig-Tipton Midlantic May). The source snapshot and SHA-256 hashes are in `SOURCE_MANIFEST.json`.

| Yearlings → juveniles | Yearling entries | Juvenile entries | Sold yearling purchases | Purchases with candidate | Purchases with sold juvenile candidate |
|---|---:|---:|---:|---:|---:|
| 2022 → 2023 | 6,539 | 3,723 | 4,585 | 1,464 | 1,017 |
| 2023 → 2024 | 6,762 | 3,668 | 4,532 | 1,400 | 949 |
| 2024 → 2025 | 6,835 | 3,452 | 4,514 | 1,292 | 907 |
| **Total** | **20,136** | **10,843** | **13,631** | **4,156** | **2,873** |

Open `work/coverage_summary_three_cohorts.csv` for sale-level denominators and `work/cohort_2022_2024_yearlings_to_2023_2025_juveniles_by_purchase.csv` for one row per sold yearling purchase. `work/cohort_2022_to_2023_by_purchase.csv`, `work/cohort_2023_to_2024_by_purchase.csv`, and `work/cohort_2024_to_2025_by_purchase.csv` split it by year. The `juvenile_events_json` column preserves repeated juvenile entries. `work/yearling_YYYY_five_sales.csv` and `work/juvenile_YYYY_four_sales.csv` contain normalized source rows. `work/five_yearlingYY_four_juvenileZZ_candidates.csv` has identity candidates. All original auction exports are unchanged in `raw/`.

**Identity links are provisional.** Candidate files now distinguish `multiple_juvenile_events` (the same yearling has several 2YO appearances) from `competing_yearling_candidates` (one juvenile hip has several yearling candidates). The purchase cohort also records `conflicting_candidate_foaling_dates`. In this snapshot, 869 sold yearling purchases have multiple juvenile candidates, while no juvenile hip has competing yearling candidates. These counts do not confirm identities.

 Fasig results give exact foaling dates; Keeneland results omit DOB and need catalog confirmation. The candidate count includes ambiguous and duplicate pairs, so it is not a verified match rate. Sold yearling purchase rows are transactions, not deduplicated horses. “No entry identified” means none in these four juvenile sales only. RNA bids are never recorded as sale proceeds. Gross appreciation excludes fees and expenses. Post-sale transaction dates may differ from listed session dates.

The 2023 OBS exports are older `.xls` workbooks; `pinhook.obs_legacy_excel` uses `xlrd` and excludes racing-age and non-horse rows. Rerun the parser and cohort builder after installation:

```bash
unzip -o ~/Downloads/pinhook_dataset_three_cohorts_expanded.zip -d .
.venv/bin/python -m pip install -e .
.venv/bin/python -m pinhook.build_cohort_year --year 2022 \
  --yearlings work/kee_sep22_full.csv work/ft_ky_oct22_full.csv work/ft_saratoga22_full.csv work/ft_nybred22_full.csv work/ft_july22_full.csv \
  --juveniles work/obs_march23_full.csv work/obs_spring23_full.csv work/obs_june23_full.csv work/ft_may23_full.csv \
  --output-dir work/rebuilt_2022
```

Use the repo `sql/schema.sql` as the Supabase target. Review candidate identities before marking any as confirmed or treating outcome and appreciation as ground truth.

Rebuild all three cohorts and inspect a hip:

```bash
python3 -m pinhook.rebuild_historical --work-dir work
python3 explore_dataset.py --sale FTJUL22 --hip 8
```
