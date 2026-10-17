# How much household income goes to gross rent?

A reproducible descriptive study by [Ahmadreza Samadi](https://a-samadi.com/about.html). Versioned source and aggregate data; no DOI is assigned. The companion website page is being prepared separately.

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

## CSV field dictionary

The [35-column field guide](DATA-DICTIONARY.txt) and [custom JSON dictionary](data-dictionary.json) describe every column in CSV order, including the two different percentage denominators, the 0–100 percentage scale and all 11 source estimate/margin-of-error pairs. Run `python verify_dictionary.py` from the current repository root to check this fixed 2024 snapshot against the dictionary and preserved source metadata. The checker does not validate future vintages, derive percentage uncertainty or test Excel. This repository documentation companion is newer than the v1.1.1 release archive; the published CSV, chart and workbook are unchanged.

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

