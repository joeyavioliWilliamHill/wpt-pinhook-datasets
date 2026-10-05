# Historical pinhook dataset update — October 2, 2026

Real data included: 2021 and 2022 Fasig-Tipton Gulfstream official results JSON (182 and 100 entries), normalized entries, rebuilt six-cohort purchase dataset, identity candidate evidence, and Keeneland catalog identity extracts and provenance. No local download is needed to inspect the delivered CSVs.

From your existing repo, unzip this package with -o -d . . Open work/dataset_20261002/coverage_summary.csv and work/dataset_20261002/cohort_all_six_by_purchase.csv. These are the new current snapshot; old work files are intentionally preserved and explore_dataset.py's default still points at the earlier snapshot. Each annual subdirectory contains normalized source entries, identity_candidates.csv, audit_metrics.json and cohort_by_purchase.csv.

Totals: 25,262 sold yearling purchase transactions; 5,026 with juvenile candidates; 3,383 sold juvenile candidates; 612 RNA; 1,031 out; 20,236 no entry identified within covered sales. Change from previous snapshot: +137 candidate purchase rows and +70 sold candidate outcomes. These are unconfirmed identities, not a verified unique-horse count. Repeated appearances are retained; RNA bids are not proceeds. Gross returns exclude expenses.

Coverage: 2019 still Keeneland to Fasig-Tipton Midlantic only. 2020 and 2021 now add Gulfstream to Midlantic. 2022–2024 retain five yearling sales to four juvenile sales each. Missing OBS 2020–2022 exports remain blocked and were not added. Gulfstream feed omits four catalog hips in 2021 and three in 2022; the manifest lists them. Missing source records are not invented or labeled out.

Catalog identity improvements: all six 2024 Keeneland books downloaded; 4,085 catalog identities parsed, 531 pages quarantined for review, and 4,073 result rows gained birth dates after agreement on hip, sire, dam, sex, birth year and provenance. Counts refer to all result entries, not only sold purchases. For 2019, 120 previously matched sold purchase PDFs downloaded; 114 were parsed and enriched, six require review. Purchase candidate totals did not change from catalog enrichment. Original result hashes/prices/statuses remain intact; evidence sidecars retain catalog URL/page/PDF hash. The parsed catalog consignor may be truncated across lines; retain result consignor as authoritative.

The public JSON adapter preserves source horse-row IDs and raw JSON hashes. Source tjc_ref_num is retained only in JSON until its identifier meaning is verified. No registry identity was inferred. Source session dates are used; later private-sale timing may be unavailable.

Validation: 13 automated tests passed; six cohorts rebuilt, purchase keys checked for duplicates, event counts checked against JSON, and sold proceeds checked positive. No identity is automatically confirmed. Database loading and imaging joins are still separate steps.

This update adds pinhook/fasig_api_results.py and broadens the catalog header parser for the 2019 layout. raw/ and work/ remain excluded from Git; code/tests/docs may be committed. The draft Supabase schema is unchanged and has not been deployed.

This lightweight replacement excludes original catalog PDF bytes. Catalog URLs, pages, hashes and extracted evidence remain included.
