# Concrete cross-sale matching pilot — 24 September 2026

## Example 1: Keeneland Hip 1956 → Fasig-Tipton Hip 64

| Field | 2024 Keeneland September | 2025 Fasig-Tipton Midlantic May |
|---|---|---|
| Catalog hip | 1956 | 64 |
| Catalog name | Blame Kate | Blame Kate |
| Foaled | April 8, 2023 | April 8, 2023 |
| Sex | Dark bay/brown filly | Dark bay/brown filly |
| Sire | Blame | Blame |
| Dam | Collections Choice (Bernardini) | Collections Choice (Bernardini) |
| Consignor | Warrendale for Mesingw Farm | Crane Thoroughbred Services, agent |
| Price | $22,000 | $350,000 |

Original catalogs: [Keeneland individual hip PDF](https://secure.keeneland.com/sales/k224/pdfs/1956.pdf); [Fasig-Tipton complete 2025 catalog](https://www.fasigtipton.com/catalogs/2025/0520/web.pdf), printed Hip 64 on PDF page 64. Keeneland [confirms the yearling price and buyer](https://www.keeneland.com/media/news/graduates-keeneland-sales-prepare-kentucky-derby-and-oaks). Equibase's [sale-history account](https://cms.equibase.com/node/311566) reports the $350,000 resale. The official Fasig-Tipton hip-level final result was not separately extracted, so preserve the distinction between catalog identity and reported price.

The recorded price appreciation is **$328,000**, or **1,490.9% gross price return**. No transaction costs are deducted. Actual days between transactions remain null until the yearling session date is verified at hip level; Fasig-Tipton sold on May 20, 2025. The later racing name is **Explora**, while the two sale catalogs used **Blame Kate**. This establishes why racing names belong in an alias table rather than the sole matching key.

**Decision:** confirmed catalog-to-catalog identity. The exact foaling date plus identical sex and pedigree provides evidence independent of the later race name and reported sale-history narrative. No registration number appears in these catalog text extracts.

## Example 2: Keeneland Hip 2003 → OBS March Hip 119

[Keeneland Book 4 catalog](https://secure.keeneland.com/sales/k224/pdfs/Book4.pdf) identifies Hip 2003 as a bay colt, foaled April 8, 2023, by Maxfield out of Eyeinthesky, consigned by War Horse Place. OBS's [official March 11 release](https://obssales.com/blog/2025/03/11/son-of-maxfield-brings-1-million-to-top-opening-day-of-obs-march/) identifies Hip 119 as a Maxfield colt out of Eyeinthesky sold for **$1 million**. An [Equibase-hosted sale report](https://cms.equibase.com/node/292664) states this same OBS hip was purchased for **$75,000** at 2024 Keeneland September. This gives **$925,000 appreciation** and **1,233.3% gross price return**.

**Decision:** confirmed pedigree and explicit sale-history link, pending the original OBS Hip 119 catalog page for exact DOB corroboration and original Keeneland hip-level final price row. The same sire and dam can produce full siblings in different years; the independently reported sale history resolves this case, while the DOB should be cross-checked before making the general rule automatic.

## What the first example proves operationally

1. Keeneland's older individual PDF URL follows `/sales/k224/pdfs/{hip}.pdf`, and its complete book PDFs are also available. The 2026 sync's JSON feed parser cannot simply be assumed to apply to 2024; inspect the older feed or parse the archived PDFs. Save the original PDF URL and the extracted page/hip text.
2. Fasig-Tipton's complete catalog contains one page per hip, including exact birth date and pedigree. Extract PDF pages by printed hip, preserving original page and source URL. Pair these with final sale results and outs.
3. Build a candidate index on normalized `(foaling_year, sire, dam)`, then verify `(foaling_date, sex)` and uniqueness. Store source hip IDs separately. For named horses, compare aliases as additional evidence.
4. Price and status must be ingested from sale results, not catalog PDFs. Maintain an evidence pointer for each asserted price and status. Never infer sold from catalog presence.
5. Before bulk matching, cross-check 20 known published pinhooks and 20 same-pedigree negative candidates, especially full siblings with different foaling years. Report catalog extraction coverage, exact-DOB match coverage, ambiguous pairs, and match audit findings.

`confirmed_pilot_links.csv` contains these two traceable rows. It is a pilot evidence file, **not a complete historical cohort**.
