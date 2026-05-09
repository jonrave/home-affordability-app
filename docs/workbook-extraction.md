# Home Affordability Workbook Extraction

This document is the implementation companion to the workbook review. It captures the financial logic that should be preserved in code and the spreadsheet behavior that should be replaced.

## Workbook Scope

The source workbook has 20 visible tabs, no hidden sheets, no workbook-level named ranges, and no external workbook links. Its core model is a deterministic 30-year household liquidity projection with recast, wait-to-buy, stress-test, and Monte Carlo overlays.

## Sheet Map

| Sheet | Purpose | Implementation Treatment |
| --- | --- | --- |
| `Reader_Guide` | User instructions and model glossary. | Convert to in-app help text and documentation. |
| `Audit_Log` | Workbook change history. | Preserve as migration notes only. |
| `Dashboard` | Executive summary linked from output tabs. | Rebuild as frontend dashboard from API outputs. |
| `Assumptions` | Central editable inputs. | Map to typed API schemas with units and validation. |
| `Calculations` | Core deterministic formulas. | Rebuild as pure calculation engine. |
| `Liquidity_30Y` | Base 30-year liquidity projection. | Rebuild as deterministic projection output. |
| `Real_MC_30Y` | Base Monte Carlo output with local recast controls. | Replace local controls with scenario input object. |
| `MC_Paths_Base` | 500 volatile base Monte Carlo paths. | Replace with seeded NumPy simulation. |
| `PT_Y5_MC` | Alternate part-time year-5 scenario. | Represent as scenario override. |
| `MC_Paths_PT5` | 500 volatile part-time year-5 paths. | Replace with seeded simulation using scenario override. |
| `Validation` | Workbook wiring checks. | Replace with Pydantic and engine validation checks. |
| `Sources` | Provenance and model notes. | Preserve source/provenance fields in input schemas. |
| `Recast Scenario` | Principal paydown vs liquidity comparison. | Rebuild as recast calculation module. |
| `Stress Tests` | Deterministic stress cases. | Rebuild as named stress-test scenarios. |
| `Monte Carlo` | Summary dashboard for MC, bear, recast, wait-buy. | Rebuild as simulation summary endpoint. |
| `Outputs` | Plain-English recast answer. | Rebuild as reporting layer narrative fields. |
| `Audit Checks` | Recast/wait-buy validation. | Rebuild as validation checks in API response. |
| `MC_Paths_Recast_30Y` | Recast-aware volatile MC path engine. | Replace with seeded simulation and explicit shortfall tracking. |
| `MC_Paths_WaitBuy_30Y` | Wait-to-buy volatile MC path engine. | Rebuild later as scenario timing module. |
| `Model_Review` | Reviewer memo and assumption QA. | Preserve as product requirements and audit guidance. |

## Core Logic To Preserve

- Spendable cash before housing starts from gross household income, applies income growth, subtracts the part-time reduction when active, subtracts selected payroll deductions, applies the take-home rate, then subtracts after-tax retirement and ESPP-style deductions.
- Cash-to-close equals down payment, buyer closing costs, renovation/move-in costs, points, legal/appraisal extras, and buyer transfer tax, reduced by any family loan used at close.
- Starting liquid assets are post-closing portfolio assets multiplied by the liquid share. Retirement/non-liquid assets are the remaining post-closing portfolio share.
- Monthly ownership cost includes mortgage P&I, property tax, homeowners insurance, utilities, maintenance, capex, HOA, PMI, and family-loan service.
- Deterministic liquid assets roll forward by applying expected return and adding annual liquid contribution or draw.
- Retirement/non-liquid assets roll forward separately with expected return and retirement contributions.
- Recast paydown is capped by outstanding mortgage principal and available liquidity after the fee. Recast reduces monthly P&I only if payment recalculation is enabled.
- Real-dollar outputs divide nominal balances by the inflation factor.
- Reserve/risk outputs should distinguish liquid assets from total investable assets.

## Spreadsheet Logic Not Copied Directly

- Volatile `RAND()` path generation is replaced with seeded simulation.
- Fixed `500` path counts and rows `5:504` are replaced with configurable path counts.
- Fixed year columns `0..30` are replaced with horizon-driven arrays.
- Cached Excel formula outputs are not treated as authoritative for stochastic values.
- `MAX(0, balance)` clipping is retained for depletion probability but paired with explicit shortfall severity.
- String-formatted `TEXT()` outputs are replaced with structured numeric fields and separate presentation formatting.
- UI-facing spreadsheet controls are replaced with scenario schemas.

## Reconciliation Targets

The first deterministic implementation should match these workbook values for the default assumptions within floating-point tolerance:

| Output | Target |
| --- | ---: |
| Down payment | `790000` |
| Mortgage principal | `1185000` |
| Buyer closing costs | `49375` |
| Gross upfront cash | `839375` |
| Net cash from portfolio | `839375` |
| Portfolio after closing | `1210625` |
| Starting liquid investments | `1029031.25` |
| Starting retirement/non-liquid | `181593.75` |
| Monthly mortgage P&I | `6004.220921436686` |
| Monthly ownership cost | `11170.887588103351` |
| Monthly required outflow | `21970.887588103353` |
| Current reserve target | `363650.6510572402` |
| Year-30 deterministic liquid real | `3118276.084415098` |
| Recast balance before paydown | `1165883.263703539` |
| Recast monthly payment reduction | `1029.98663903343` |
| Recast breakeven years | `16.2218932752496` |
| Recast immediate liquid after paydown | `828531.25` |
