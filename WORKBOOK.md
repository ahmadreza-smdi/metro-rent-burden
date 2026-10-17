# Excel companion to the ACS 2024 study

[Download the workbook](https://github.com/ahmadreza-smdi/metro-rent-burden/releases/download/v1.1.0/Metro-Rent-Burden-2024.xlsx).

The workbook gives readers a filterable view of the same 386 metropolitan areas as the versioned CSV. It adds no observations, new data year or market forecasts. The analysis is by [Ahmadreza Samadi](https://a-samadi.com/about.html). This convenience export was prepared with AI assistance.

## Use the file

Open `Metro-Rent-Burden-2024.xlsx` in a spreadsheet application. In **Metros**, use a column-header filter to find a metro or sort the table. The 30% and 50% thresholds refer to gross rent as a share of household income. The 50% group is included in the 30% group. Both displayed shares exclude not-computed units from their denominator.

**Source** retains all 35 original CSV fields, including all 11 published estimate/margin-of-error pairs. Original CSV percentage fields use a 0–100 scale. The Metros formulas use fractional shares with percentage formatting. The source snapshot is historical and does not refresh automatically. Keep it intact when using the workbook as a reference.

Do not average metro percentages to obtain a US rate. The workbook is descriptive, and it supplies no percentage margins of error or statistical significance rankings. It is not a measure of current asking rents, property yields or investment returns. See the main README for the complete universe, denominator and source-reuse limits.

## Verification and limits

All 386 output rows and all original source fields were reconciled against the CSV. A temporary zero-denominator check returned `n.a.` and was restored before export. Both sheet previews were visually reviewed. The file contains formulas and their saved results, two filterable tables and frozen headers. Recalculation was checked in the authoring engine. Native Microsoft Excel execution and interactive sorting were not tested.

To independently check the saved workbook data and structure without installing packages, run:

```sh
python verify_workbook.py
```

This validator reads the file using Python's standard library. It checks stored formula results against the CSV; it does not execute formulas in Excel. The analysis still rebuilds from the original raw files using the main README's commands. Rebuilding the formatted XLSX itself is not part of that script.

Version 1.1.0 adds this workbook and its verification instructions. The underlying 2024 CSV, raw inputs, analysis code and chart are unchanged from version 1.0.0. Cite the analysis using `CITATION.cff` and cite Census table B25070 as well. Educational, not financial advice.
