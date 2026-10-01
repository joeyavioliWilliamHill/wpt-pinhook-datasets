# Add the 2021 yearlings → 2022 2YO cohort

Download the **final results Excel/CSV** from each official sale page below. The Fasig-Tipton “Excel File” button exports a CSV, despite its label. OBS uses two `.xls` workbooks and one `.xlsx`. Rename the downloaded files as shown and place them in `raw/` without editing the contents. The Keeneland export comes from Sales Summaries: choose the 2021 September Yearling Sale, all sessions, CSV download.

| Yearling sale | Official results page | Save as |
|---|---|---|
| Keeneland September 2021 | https://flex.keeneland.com/summaries/summaries.html | `raw/kee_sep21_results.csv` |
| Fasig-Tipton Kentucky October 2021 | https://www.fasigtipton.com/2021/Kentucky-October-Yearlings | `raw/ft_ky_oct21_results.csv` |
| Fasig-Tipton Saratoga 2021 | https://www.fasigtipton.com/2021/The-Saratoga-Sale | `raw/ft_saratoga21_results.csv` |
| Fasig-Tipton NY Bred 2021 | https://www.fasigtipton.com/2021/New-York-Bred-Yearlings | `raw/ft_nybred21_results.csv` |
| Fasig-Tipton July 2021 | https://www.fasigtipton.com/2021/The-July-Sale | `raw/ft_july21_results.csv` |
| OBS March 2022 | https://obssales.com/blog/2022/01/31/2022-march-sale/ | `raw/obs_march22_results.xls` |
| OBS Spring 2022 | https://obssales.com/blog/2022/03/17/spring-sale-2022/ | `raw/obs_spring22_results.xlsx` |
| OBS June 2022 | https://obssales.com/blog/2022/04/29/2022-june-two-year-olds-horses-of-racing-age/ | `raw/obs_june22_results.xls` |
| Fasig-Tipton Midlantic May 2022 | https://www.fasigtipton.com/2022/Midlantic-Two-Year-Olds-in-Training | `raw/ft_may22_results.csv` |

For OBS, choose **Results in Excel format**, not the sale catalog or master index. For F-T, wait until “ALL RESULTS” shows the completed sale before clicking Excel File. If your Mac adds `(1)` to a filename, rename it to the exact name above. Do not rename an `.xlsx` to `.xls` or vice versa.

Run from your repository in VS Code:

```bash
.venv/bin/python -m pip install -e .
.venv/bin/python -m pinhook.import_2021 --raw-dir raw --work-dir work
```

The importer reports missing files and their pages. It normalizes available files individually, validates headers, foaling dates, statuses, and prices, then builds `work/cohort_2021_to_2022/` **only after all nine exports are present**. The original downloads stay in `raw/`; `work/cohort_2021_source_manifest.json` records hashes and counts. If an older OBS file has an unexpected layout, the importer stops with an error rather than guessing values. Send that error and the first few column names to adapt the parser.

This adds a fourth cohort but does not automatically append it to the existing combined 2022–2024 CSV. Review coverage and identity candidates first. The Keeneland result export lacks exact birth dates; its candidates still need catalog DOB corroboration. Do not mark a candidate as an accepted horse identity merely because the pedigree matches.
