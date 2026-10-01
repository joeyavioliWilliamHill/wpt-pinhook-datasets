# Other offspring performance and sale-price changes

Question: does information about other offspring of a sale horse's sire or dam help explain changes in that horse's market value between its yearling purchase and two-year-old resale?

## Population and targets

Use reviewed identity links. Analyze sold-to-sold price changes first, retaining RNA/out outcomes in a separate sell-through model. The primary continuous target can be log(resale price / purchase price), with gross dollar appreciation as a companion. Fees, training and veterinary costs are not currently available, so this is gross price movement rather than net investment profit. A horse that never appears in covered sales is not automatically a negative example.

An analysis at the resale date can use racing developments between transactions. A prediction made at the yearling purchase cannot use that later information. Keep these two prediction tasks separate in model definitions.

## Relatives

- Sire progeny: other resolved horses with the same sire.
- Dam offspring: other resolved horses with the same dam; separate full siblings and maternal half-siblings.
- Dam family: expand through a defined maternal ancestry depth only after parentage is resolved.
- Exclude the subject horse's own results from all other-offspring metrics.

## Two dated snapshots

For each purchase/resale pair, calculate features immediately before the purchase and immediately before the resale, then calculate their differences. If only session dates exist, exclude the entire sale day. Race occurrence time must precede cutoff; the source's publication/known-at time must also precede cutoff. For corrected results, choose the version available at cutoff. If historical availability cannot be reconstructed, label the feature as retrospective and document the limitation.

## Initial features

| Group | Snapshot and interval measures |
|---|---|
| Exposure | Progeny starters, starts, distinct runners, countries/tracks covered |
| Winning | Wins, unique winners, wins per start, winners per starter |
| Stakes | Stakes wins and unique stakes winners; graded stakes wins; Grade 1 wins |
| Earnings | Reported progeny earnings and earnings per start, with consistent currency conventions |
| Maternal siblings | Starts, wins, stakes/graded/G1 wins and earnings, separating full and half siblings |
| Timing | Days since latest stakes/G1 win, wins in recent 30/90-day windows |
| Poor performance | Start-normalized change in win/place rate, finishing percentile adjusted for field size; avoid treating every non-win as a bad run |
| Coverage | Provider/jurisdiction completeness and unknown amounts; missing data stays unknown |

Use both lifetime-to-cutoff and recent-window measures. Absolute win counts need exposure denominators: a sire with 1,000 runners cannot be compared directly to one with 30. Avoid double-counting the same race through multiple providers. Separate race wins from the number of unique winning offspring.

## Price attribution

Start with a sale-price baseline using purchase price, sale/year/session, sex, age, sire, dam history, and available horse-level information. Add interval pedigree developments and compare performance on later held-out cohorts. Inspect feature contributions and uncertainty. This estimates association and added predictive value, not causality: changing market conditions, horse condition, consignor, breeze performance, and selection into resale can confound the relationship.

Later join imaging measurements by reviewed horse ID and examination date. The usable modeling sample is the overlap with correctly timed imaging, not the total sales candidate count.

## Next engineering steps

1. Finish catalog DOB confirmation and identity reviews.
2. Add parentage plus race-provider identifiers for relatives.
3. Obtain licensed historical runner-level results with race date, official finish, grade and earnings; determine whether publication/correction history is available.
4. Build a versioned snapshot calculation with cutoff rules and source coverage checks.
5. Validate one known pedigree event before scaling; a race after resale must never alter the earlier snapshot.
