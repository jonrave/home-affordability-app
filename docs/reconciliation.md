# Workbook Reconciliation Report

## Scope

This report covers deterministic reconciliation between the Python calculation engine and the reviewed workbook. It intentionally excludes volatile Excel `RAND()` Monte Carlo paths and any outputs that depend on those paths.

Source workbook used for extraction in this checkpoint:

```text
/Users/jr/Downloads/home_affordability_model_reviewed.xlsx
```

The user-facing workbook name is `home_affordability_model_reviewed.xlsx`; `/home_affordability_model_reviewed.xlsx` was not present in the local filesystem during this pass.

## Fixture

Fixture file:

```text
tests/fixtures/workbook_reconciliation_targets.json
```

Extraction utility:

```text
scripts/extract_reconciliation_targets.py
```

Refresh command:

```sh
.venv/bin/python scripts/extract_reconciliation_targets.py /path/to/home_affordability_model_reviewed.xlsx --output tests/fixtures/workbook_reconciliation_targets.json
```

The extractor reads cached formula values directly from XLSX XML parts. It does not recalculate formulas. The fixture records the source workbook path, source ranges, and deterministic values used by the test suite.

## Source Ranges

| Reconciled area | Workbook source |
|---|---|
| Purchase and cash-to-close | `Calculations!C5:C25` |
| Year-by-year deterministic projection | `Liquidity_30Y!C5:AG23` |
| Recast mechanics | `Calculations!C36:C56` and `'Recast Scenario'!B12:C13` |
| Deterministic stress summaries | `'Stress Tests'!A5:I22` |

## Tolerances

| Value type | Tolerance |
|---|---:|
| Currency, balances, and cash-flow values | `$0.01` absolute |
| Inflation factors | `1e-9` absolute |
| Year, month, runway, and breakeven counters | `1e-6` absolute |
| Booleans and labels | exact match |

The tolerance policy is intentionally tight because these are deterministic formula outputs, not stochastic simulations.

## Reconciled Outputs

| Output | Workbook target | Test coverage |
|---|---:|---|
| Gross upfront cash needed | `$839,375.00` | `test_purchase_outputs_reconcile_to_workbook` |
| Net cash from portfolio | `$839,375.00` | `test_purchase_outputs_reconcile_to_workbook` |
| Mortgage principal | `$1,185,000.00` | `test_purchase_outputs_reconcile_to_workbook` |
| Monthly P&I | `$6,004.220921` | `test_purchase_outputs_reconcile_to_workbook` |
| Annual ownership cost, year 0 | `$134,050.651057` | `test_purchase_outputs_reconcile_to_workbook` and projection test |
| Initial reserve target | `$363,650.651057` | `test_purchase_outputs_reconcile_to_workbook` and projection test |
| Year-30 nominal liquid assets | `$6,540,794.817295` | `test_year_by_year_projection_reconciles_to_workbook` |
| Year-30 nominal retirement/non-liquid assets | `$1,201,127.555420` | `test_year_by_year_projection_reconciles_to_workbook` |
| Year-30 real liquid assets | `$3,118,276.084415` | `test_year_by_year_projection_reconciles_to_workbook` |
| Year-30 real retirement/non-liquid assets | `$572,628.776016` | `test_year_by_year_projection_reconciles_to_workbook` |
| Year-30 real total investable assets | `$3,690,904.860431` | `test_year_by_year_projection_reconciles_to_workbook` |
| Recast monthly payment reduction | `$1,029.986639` | `test_recast_outputs_reconcile_to_workbook` |
| Recast breakeven | `16.221893 years` | `test_recast_outputs_reconcile_to_workbook` |
| Worst monthly cash flow, no recast | `-$1,599.415976` | `test_recast_outputs_reconcile_to_workbook` |
| Worst monthly cash flow, `$200k` recast | `-$569.429337` | `test_recast_outputs_reconcile_to_workbook` |
| High inflation, no recast year-30 liquid | `$222,048.525363` | `test_deterministic_stress_outputs_reconcile_to_workbook` |
| High inflation, `$200k` recast year-30 liquid | `-$36,552.419329` | `test_deterministic_stress_outputs_reconcile_to_workbook` |
| Income reduction year 5, no recast year-30 liquid | `$4,468,866.954328` | `test_deterministic_stress_outputs_reconcile_to_workbook` |
| Income reduction year 5, `$200k` recast year-30 liquid | `$4,210,266.009637` | `test_deterministic_stress_outputs_reconcile_to_workbook` |

The projection test compares all 31 years and every extracted deterministic projection field, not only the year-30 values shown above.

The stress test compares every deterministic summary row in `'Stress Tests'!A5:I22`, including base expected return, immediate bear market, two-year bear market, flat decade, high inflation, income reduction in year 5, and the `$50k`, `$100k`, and `$150k` expense shocks for both no-recast and `$200k` recast paths.

## Test Commands

Run only workbook reconciliation:

```sh
.venv/bin/python -m unittest tests.test_workbook_reconciliation -v
```

Run the full backend test suite:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

## Not Reconciled Yet

The following outputs are explicitly not reconciled in this pass:

| Output area | Reason |
|---|---|
| `MC_Paths_Base`, `MC_Paths_Recast_30Y`, `MC_Paths_PT5`, and `MC_Paths_WaitBuy_30Y` path values | They depend on volatile Excel `RAND()` and should not be matched path-by-path. |
| Monte Carlo percentile and breach-probability dashboard values | They are downstream of volatile cached paths. App tests should use seeded simulation invariants instead. |
| `PT_Y5_MC` alternate part-time year-5 scenario outputs | The app does not yet expose a dedicated PT5 scenario output. The deterministic income-reduction stress summary is reconciled instead. |
| Wait-to-buy outputs | Wait-buy has not been implemented in the app yet. |
| `$300k`, `$400k`, and dynamic recast scenario columns | The current app output is the default `$200k` recast path only. |
| Plain-English `Outputs` tab narrative strings | These are presentation strings built with Excel `TEXT()` and references to Monte Carlo tabs. |
| `Audit Checks`, `Validation`, and `Audit_Log` rollups | These contain audit and cached-review checks rather than app output contracts. |
| Affordability score and safe purchase price | These are app-added v1 outputs and do not exist as workbook targets. |
| Detailed tax, refinance, persistence, import/export, and reporting outputs | These features are not implemented yet and were intentionally frozen for this pass. |

## Result

Current deterministic reconciliation status: passing.

The app ties to the workbook for the deterministic purchase outputs, full 31-year liquidity and retirement projection, real-dollar conversion, `$200k` recast mechanics, and deterministic stress summaries within the documented tolerances.
