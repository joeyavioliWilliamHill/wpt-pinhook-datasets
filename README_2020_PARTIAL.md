# 2020 yearlings → 2021 juveniles: partial extension

Acquired September 30, 2026 from official Keeneland and Fasig-Tipton hip-level result exports. This extension covers Keeneland September, Fasig-Tipton Kentucky October, Selected Yearlings Showcase, and Midlantic Fall Yearlings in 2020, paired to Fasig-Tipton Midlantic May 2021. Fasig-Tipton consolidated the usual July, Saratoga and NY Bred yearling sales into the Selected Yearlings Showcase in 2020. OBS March, Spring and June 2021 are not covered.

| Metric | Count |
|---|---:|
| Yearling entries | 7,051 |
| Sold yearling purchase rows | 4,169 |
| Midlantic May juvenile entries | 583 |
| Purchases with at least one provisional juvenile candidate | 284 |
| Candidate pairs | 503 |
| Purchases with a sold juvenile candidate | 179 |
| Purchases with RNA juvenile candidate | 29 |
| Purchases with out juvenile candidate | 76 |

The purchase outcomes are candidate-linked and require identity review. Fasig yearling results provide exact foaling date; Keeneland's result export does not. The 2020 Keeneland session dates follow the official 12-session schedule, September 13–14 and 16–25. Repeated candidate events must not be read as distinct horses. An unmatched purchase means only no candidate at the **covered** Midlantic sale.

The normalized files are `work/kee_sep20_full.csv`, `work/ft_ky_oct20_full.csv`, `work/ft_showcase20_full.csv`, `work/ft_midfall20_full.csv`, and `work/ft_may21_full.csv`. The raw source CSV files remain in `raw/`. Open `work/cohort_2020_to_2021_partial/cohort_by_purchase.csv` and `identity_candidates.csv` to explore. Source hashes and URLs are in `work/cohort_2020_source_manifest.json`; sale coverage is in `work/cohort_2020_to_2021_partial/coverage_manifest.json`.

Rebuild in the repo with:

```bash
python3 -m pinhook.import_2020 --raw-dir raw --work-dir work
```

This extension is separate from the 2021 partial cohort and the three later four-juvenile-sale cohorts. It must not be summed into a uniform-coverage match rate until OBS 2021 is added.
