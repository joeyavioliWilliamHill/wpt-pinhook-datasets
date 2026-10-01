# Shared horse data model

The repository supports several analyses. Shared identity, pedigree, sales and racing records should have one owner and be reusable by the pinhook model and other studies. Keep the existing Python import paths while these modules evolve.

## Database domains

The supplied `sql/schema.sql` is the existing draft, currently all under `pinhook`. Before the first production deployment, split common tables into an `equine` schema and retain cohort-specific tables in `pinhook`. This document describes the intended next migration; it does not claim those extra tables already exist.

| Domain | Proposed tables | Purpose |
|---|---|---|
| Provenance | source_files, ingestion_runs | Source URL, content hash, acquisition time, parser version, coverage and storage pointer |
| Identity | horses, horse_identifiers, horse_aliases, horse_identity_matches | Internal horse ID, scoped provider/registry IDs, changing names, and reviewable links |
| Pedigree | horse_parentage | Resolved child and parent IDs, sire/dam role, supporting source, review state and known-at time |
| Sales | sales, sale_entries, sale_entry_evidence | Every offering; status, transaction price and RNA bid; catalog identity and original source records |
| Racing | races, race_results, race_result_versions | Race date, official finish, grade, earnings, provider IDs, corrections and availability time |
| Pinhooks | cohort_definitions, cohort_sale_coverage, pinhook_purchases, pinhook_events | Each yearling purchase, all linked juvenile events, outcome coverage and chosen resale |
| Features | feature_definitions, feature_snapshots | Calculation version, horse/entry, cutoff, source version, feature values and coverage |
| Imaging | imaging_examinations, imaging_measurements | Partner examination IDs and dated measurements joined to reviewed horse identity |

## Required additions to the current SQL draft

1. Preserve `foaling_date_as_cataloged` and catalog file/page evidence at sale-entry level. A canonical horse date cannot replace contradictory source observations.
2. Use relational parentage, not only sire/dam text, to retrieve other offspring. Create a parent horse even when it never appears in our auction exports; retain unresolved source names separately.
3. Keep aliases and provider identifiers so later race names can be linked to sale names.
4. Store coverage for each cohort and source. Do not turn incomplete juvenile coverage or missing race results into zero performance.
5. Keep provisional purchase/event summaries separate from accepted model labels. The current `horse_identity_matches.decision` supports `review`, `accepted`, and `rejected`.
6. Select the first accepted sold juvenile transaction for return calculations and retain the first offering separately. The last comment in the current SQL draft describes first offering selection; revise it before deployment to match this rule.
7. Store source publication/availability times and result versions. Download time alone does not prove what was known historically.

## Load order

Source files and sale definitions → sale entries → candidate links and evidence → reviewed canonical horse IDs/parentage → accepted pinhook events/outcomes → dated race results → feature snapshots. Unresolved sale entries can be loaded with `horse_id` null. Do not force a canonical identity just to load data.

Use versioned SQL migrations for new database changes. Commit migration files to Git; load dataset records into Supabase separately with a transactional, repeatable loader. Partner access should use explicitly selected datasets/views after the target project and access scope are agreed.
