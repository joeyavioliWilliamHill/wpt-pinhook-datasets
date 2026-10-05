# Expand OBS historical matching coverage

Adds acquisition and cohort rebuilding for OBS 2020–2022. All links were located on official OBS sale pages on October 1, 2026. The remote workbook requests tested here returned HTTP 403; no new historical records or match counts are included in this package.

Run from your existing repository:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pinhook.expand_obs_history --download
```

If downloading fails on your computer, open the official pages listed in OBS_ARCHIVE_DOWNLOADS.json, click Results in Excel, save to the specified raw filename, and rerun without --download. A results export is required, not just the catalog index.

Each cohort requires all three OBS exports and its existing work/cohort_YYYY_to_YYYY_partial directory (yearling_entries.csv, juvenile_entries.csv, cohort_by_purchase.csv). Originals are preserved; updated directories end in _expanded. This expands juvenile coverage, not yearling coverage.

Inspect work/obs_expansion_comparison.csv for candidate purchases before/after, new purchase candidates, sold candidates before/after, and ambiguous identities. Repeated sale appearances are not counted as new purchase candidates. work/obs_expansion_sources.json records download or validation failures, raw hashes, excluded hips and result-status counts.

2020 Spring actually ran June 9–12; its supplements have session-specific dates. OBS July 2020 replaces the usual June sale. Racing-age sections are excluded: July 2020 hips 993–1005; June 2021 hips 860–879; June 2022 hips 1151 onward. Existing 2023 handling is preserved.

Validation: 13 tests passed, including existing workbook/status checks and new historical schedule boundaries. Missing-file execution was checked. Actual 2020–2022 exports could not be inspected here; the parser rejects unfamiliar layouts, unexpected statuses, missing DOBs and wrong foaling years. Such failures need inspection of the original export, not relaxed checks. No identity is automatically confirmed.

This package updates obs_legacy_excel.py and adds expand_obs_history.py. Keep your existing results and source files unchanged. The broader dataset and handoff inventory are not automatically replaced by this patch; reconcile totals after all expanded cohorts have been built.
