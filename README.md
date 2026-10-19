# How much household income goes to gross rent?

A reproducible descriptive study by [Ahmadreza Samadi](https://a-samadi.com/about.html). Versioned source and aggregate data; no DOI is assigned. [Read the study and methods](https://a-samadi.com/studies/rent-burden/) on the author’s website, including the chart, data downloads and limitations.

## Vintage and scope

As checked 17 October 2026, the latest released ACS 1-year detailed tables are 2024. The Census Bureau's 2025 release notice schedules the next 1-year estimates for 29 October 2026. This package therefore uses 2024 and must never be presented as 2025 data or current asking rents. This version preserves its stated source vintage; consult the release notice before using a later data year.

Sources:
- [2025 release notice](https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release.html).
- [2024 release schedule](https://www.census.gov/programs-surveys/acs/news/data-releases/2024/release-schedule.html): 1-year release 11 September 2025.
- [ACS table-based summary files](https://www.census.gov/programs-surveys/acs/data/summary-file.html); exact raw URLs/checksums in source-2024.json.
- [Table B25070](https://data.census.gov/table/ACSDT1Y2024.B25070); live interface identifies its universe as **renter-occupied housing units**. Do not mislabel its total as cash-rent units only.
- [2024 subject definitions](https://www2.census.gov/programs-surveys/acs/tech_docs/subject_definitions/2024_ACSSubjectDefinitions.pdf), printed pages 19–20: gross rent includes contract rent plus separately renter-paid utilities and fuels. Units with no rent paid and households reporting no income or a net loss enter the not-computed category.
- [B25070 API metadata](https://api.census.gov/data/2024/acs/acs1/groups/B25070.html): category labels. Metadata works without an API key; data-query access does not. No key was obtained or account created.

## Denominator before headline

Use the published bins; thresholds include 30.0 and 50.0 percent. They describe the Census-tabulated ratio, which is rounded, not an unrounded household microdata calculation.

- Denominator = B25070_E001(total renter-occupied units) − B25070_E011(not computed).
- At least 30% numerator = E007+E008+E009+E010.
- At least 50% numerator = E010.
- Share = 100 × numerator/denominator.
- Report not-computed units and their share of all renter-occupied units alongside the derived shares.

These are shares of units with a computable gross-rent-to-household-income ratio. They are not shares of all people, all renter-occupied units or only new tenancies. A zero denominator produces an unavailable percentage; missing/sentinel estimates never become zero.

The 50% group is inside the 30% group. Do not add the two percentages. Income and rent have different measurement windows in the ACS; the table is not a current listing-rent index, property yield, investment ranking, rent forecast or causal explanation.

## Geography

Join the raw table to its official geography labels by exact GEO_ID. Select SUMLEVEL 310 and COMPONENT 00 and labels ending ` Metro Area`; exclude the labels ending `, PR Metro Area` to keep a 50 states/DC scope. Keep the published whole metropolitan area, including cross-state metros; do not add its state portions or divisions again. Do not assume a fixed GEO_ID prefix because the published 2024 IDs contain geography-vintage markers.

The snapshot supplies 386 selected metropolitan areas, 140 micropolitan areas excluded by scope and 6 Puerto Rico metropolitan areas excluded by scope. The 1-year product does not cover every small area. Do not silently substitute 5-year data or claim this is the same geography universe as the earlier 393-metro HUD study. Excluded CBSA rows and reasons are retained.

## Uncertainty and chart

ACS figures are survey estimates, not an exact respondent count. The CSV preserves all 11 published estimate/margin-of-error pairs. Derived percentage margins of error are **not calculated** here. Differences between displayed estimates are not established as statistically significant.

The chart chooses the ten largest computable renter-unit denominators and displays them alphabetically. It does not choose the highest burden figures or rank statistical differences. Both threshold series overlap. See chart-alt-2024.txt for full alt text. No Census logo, endorsement, agency certification or new visual identity is implied.

## Reading the results

[Two property studies, two different questions](READING-GUIDE.txt) is a short reading card explaining rent-burden estimates versus hypothetical ownership budgets, overlapping thresholds, missing values and the limits of investment comparisons. It adds no observations or calculations; the ownership study remains a separate dataset.

[See why the two thresholds must not be added](docs/nested-thresholds.md): a single-metro illustration separates three disjoint income-share groups, using the same stored ACS 2024 data. It adds no new observations.

## CSV field dictionary

The [35-column field guide](DATA-DICTIONARY.txt) and [custom JSON dictionary](data-dictionary.json) describe every column in CSV order, including the two different percentage denominators, the 0–100 percentage scale and all 11 source estimate/margin-of-error pairs. Run `python verify_dictionary.py` from the current repository root to check this fixed 2024 snapshot against the dictionary and preserved source metadata. The checker does not validate future vintages, derive percentage uncertainty or test Excel. This repository documentation companion is newer than the v1.1.1 release archive; the published CSV, chart and workbook are unchanged.

### Unavailable inputs in rebuilt outputs

In the source containing the unavailable-row correction, a row with a missing or sentinel required estimate keeps all 35 CSV columns. Its derived measures are blank, its status identifies the unavailable source estimate, and the raw estimate/MOE strings remain stored. This applies even when the first selected row is unavailable.

The JSON summary reports `not_computed_total_selected` as `null` if any selected row lacks that derived count. It does not present a sum of only the available rows as the complete total. This is a conservative completeness rule, not a claim that every individual raw count in that row is missing.

Synthetic boundary tests exercise these cases; they are not new observations in the fixed 2024 snapshot. Older tagged archives and the pinned offline lookup kit are not rebuilt by this source change. Record the exact source commit used.

## Look up a metro locally

From a checkout of this repository, use Python's standard library to search the stored metro names or select exact CBSA codes:

```sh
python3 lookup_metro.py --search "Phoenix"
python3 lookup_metro.py --code 38060
python3 lookup_metro.py --code 38060 --code 31080
```

The command verifies the fixed CSV and source metadata against the dictionary, then prints JSON with every original field, including all 11 estimate/MOE pairs. Values remain CSV strings; percentages are on the 0–100 scale. Results preserve CSV order and do not rank metros. A name search returns every substring match; use the displayed exact code to select a specific metro. An unknown code fails instead of returning partial results. No name matches means no matching row, not zero burden.

The output states the two denominator definitions, nested thresholds and uncertainty limits. It makes no network request or dataset change. This repository helper adds no data year, observations or derived percentage MOEs and is not included in the existing v1.1.1 release archive.

For a readable summary of the same stored values, add `--format text`:

```sh
python3 lookup_metro.py --code 38060 --format text
python3 lookup_metro.py --search "Phoenix" --format text
```

The text view names both denominators, keeps the original stored percentage precision, and distinguishes blank values from zero. It does not calculate new values or percentage uncertainty. It is a summary: use the default JSON (or `--format json`) for all 35 fields and all 11 source estimate/MOE pairs. An empty search result is not a zero-burden metro. Both formats retain the fixed 2024 survey year and source checksum.

The current main-branch text view also records the normalized name substring or the requested CBSA codes, so a saved summary retains its selection context even when no row matches. Name queries are quoted with ASCII escapes for non-ASCII characters and line breaks; this keeps the selection on one line in restrictive terminals. Requested codes retain their input order; result rows still follow the original CSV order. Matching rules, stored values and JSON output are unchanged. This selection-context addition is not included in the pinned offline lookup ZIP or the v1.1.1 release archive.

Prefer a compact offline download? [Get the 11-file lookup companion](downloads/Metro-Rent-Burden-Offline-Lookup.zip), extract the entire archive and read `START-HERE.txt`. It includes the same fixed CSV, dictionary, source metadata and Python lookup—not the full raw-data rebuild, chart or workbook. Python 3.12 or newer; no third-party packages or network needed for lookup. The included source/guide manifest records the exact helper commit. This main-branch companion is separate from the v1.1.1 release archive and adds no data observations or derived percentage uncertainty. Maintainers can rebuild it with `python3 -B scripts/build_lookup_kit.py` from a Git checkout containing the pinned source commit.

## Excel companion

[Download the filterable workbook](https://github.com/ahmadreza-smdi/metro-rent-burden/releases/download/v1.1.0/Metro-Rent-Burden-2024.xlsx) for the same 386 metros. It includes formulas, original CSV fields and source uncertainty notes. [Workbook instructions and verification limits](WORKBOOK.md). No new observations or data year are added.

## Rebuild

```sh
python3 download.py --year 2024
python3 build.py --year 2024
python3 -m unittest discover -s . -p "test*.py"
python3 -m pip install -r requirements.txt
python3 plot.py --year 2024
```

Saved raw snapshots are retained, not silently replaced. Before calculating or writing outputs, the build checks both raw files against the year-specific source receipt's SHA-256 hashes and byte counts. A missing receipt, changed file or mismatched year stops the build. Keep the receipt alongside the raw files; these checks detect drift relative to that receipt, not malicious changes to both files and receipt. Missing raw files are downloaded directly from the documented Census URLs, without requiring another workspace folder.

`build.py` needs only Python's standard library. Plotting additionally uses Matplotlib. Source 2024 metadata is preserved for provenance; calculations use the public pipe-delimited summary file. Input hashes and deterministic output CSV allow independent checking. No credentials, telemetry or upload is required.

## Reuse and citation

Original code in this package is MIT; see LICENSE. Input federal Census statistics are not relicensed MIT. Census [DS027, page 9](https://www2.census.gov/foia/ds_policies/ds027.pdf) states that employee-created data/works generally are not protected by copyright within the United States, with foreign-country and third-party exceptions. This package uses the Bureau's public aggregate statistical files, not third-party imagery or confidential records. Retain source attribution and applicable exceptions; do not claim worldwide CC0.

CITATION.cff identifies the analysis author and data year. Cite the underlying Census table as well as this analysis.

## Suggested plain-text credits

For the analysis and code:

> Samadi, Ahmadreza (2026). Metro rent burden: reproducible ACS 2024 point estimates (software version 1.1.1). https://github.com/ahmadreza-smdi/metro-rent-burden/releases/tag/v1.1.1

For the underlying statistics:

> U.S. Census Bureau. 2024 American Community Survey, 1-year estimates, Table B25070. https://data.census.gov/table/ACSDT1Y2024.B25070

If you also use the field dictionary:

> Samadi, Ahmadreza (2026). Rent-burden CSV field guide — ACS 2024 (repository commit 12005f17005124c1485e093de12f59312af5c430). https://github.com/ahmadreza-smdi/metro-rent-burden/blob/12005f17005124c1485e093de12f59312af5c430/DATA-DICTIONARY.txt

These are suggested credits, not a certified citation style. The survey year is 2024; the analysis software release is dated 2026. Record the version or full commit you actually used. The field guide is a separate documentation companion and is not included in the version 1.1.1 archive. No DOI, agency endorsement, peer review or independent reuse is implied by these examples.

## More public tools by [Ahmadreza Samadi](https://a-samadi.com/about.html)

- **Record AI workflow costs:** [ai-workflow-cost](https://github.com/ahmadreza-smdi/ai-workflow-cost) totals caller-recorded attempt costs and accepted-result labels. It does not independently check output quality or calculate ROI.

- **Inspect video publication dates:** [video-date-lint](https://github.com/ahmadreza-smdi/video-date-lint) checks dates and consistency in local video metadata. It does not certify actual publication, indexing or copyright clearance.

Read each project's input rules and limits before use. Running one tool does not verify another tool's inputs or results.
