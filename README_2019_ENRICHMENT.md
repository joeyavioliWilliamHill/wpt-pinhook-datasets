# 2019 Keeneland extension and catalog identity enrichment

The 2019 Keeneland September result export has 4,644 hip records, including 2,974 sold purchases. Fasig-Tipton's 2020 Midlantic juvenile sale took place June 29–30, 2020 and has 559 hip records. This **partial** cohort has 120 sold-yearling purchases with 214 provisional candidate pairs; 59 of the purchases have a sold juvenile candidate. The OBS 2020 sales are not included, so an unmatched purchase means only no candidate in the covered Midlantic sale.

Open `work/cohort_2019_to_2020_partial/cohort_by_purchase.csv` for purchase outcomes and `identity_candidates.csv` for evidence. Raw auction exports are `raw/kee_sep19_results.csv` and `raw/ft_may20_results.csv`. The sale source manifest includes URLs, row counts, status counts and SHA-256 checksums.

To rebuild:

```bash
python3 -m pinhook.import_2019 --raw-dir raw --work-dir work
```

## Exact birth-date enrichment

Keeneland's official results CSV lacks foaling date. Its 2019 hip links point to `https://secure.keeneland.com/sales/Sep19/pdfs/{hip}.pdf`. Archive the relevant catalog pages and extract identity fields to a CSV with `hip,foaling_date,sex,sire,dam,source_url,source_page,raw_pdf_sha256`. The parser for downloaded book PDFs is `pinhook.keeneland_catalog`. Supply `--base-url https://secure.keeneland.com/sales/Sep19/pdfs/` for 2019 books. It preserves the source page and PDF hash.

Then run:

```bash
python3 -m pinhook.enrich_catalog \
  work/kee_sep19_full.csv work/kee_sep19_catalog_identity.csv \
  work/kee_sep19_enriched.csv
python3 -m pinhook.build_cohort_year --year 2019 \
  --yearlings work/kee_sep19_enriched.csv \
  --juveniles work/ft_may20_full.csv \
  --output-dir work/cohort_2019_to_2020_enriched_partial
```

The sidecar `work/kee_sep19_enriched.csv.evidence.csv` distinguishes accepted birth dates from pedigree, sex, birth-year, duplicate-hip, and provenance conflicts. The matcher continues to mark every link `review` until an explicit review decision. The code does **not** manufacture a DOB for any of the 120 existing candidates in this snapshot.
