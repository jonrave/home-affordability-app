"""Extract deterministic reconciliation targets from the reviewed workbook.

The extractor reads cached workbook values from the XLSX XML parts. It does not
recalculate formulas and intentionally skips volatile RAND-driven Monte Carlo
path outputs.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "office_rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "package_rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def col_to_index(col: str) -> int:
    index = 0
    for char in col:
        index = index * 26 + ord(char.upper()) - 64
    return index


def index_to_col(index: int) -> str:
    out = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        out = chr(remainder + 65) + out
    return out


def cell_ref(col: str, row: int, offset: int = 0) -> str:
    return f"{index_to_col(col_to_index(col) + offset)}{row}"


class WorkbookCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.archive = zipfile.ZipFile(path)
        self.shared_strings = self._load_shared_strings()
        self.sheet_paths = self._load_sheet_paths()
        self._sheet_cache: dict[str, dict[str, Any]] = {}

    def _load_shared_strings(self) -> list[str]:
        if "xl/sharedStrings.xml" not in self.archive.namelist():
            return []
        root = ET.fromstring(self.archive.read("xl/sharedStrings.xml"))
        return [
            "".join(text.text or "" for text in item.findall(".//main:t", NS))
            for item in root.findall("main:si", NS)
        ]

    def _load_sheet_paths(self) -> dict[str, str]:
        workbook = ET.fromstring(self.archive.read("xl/workbook.xml"))
        rels = ET.fromstring(self.archive.read("xl/_rels/workbook.xml.rels"))
        relmap = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("package_rel:Relationship", NS)
        }
        sheets = {}
        for sheet in workbook.findall("main:sheets/main:sheet", NS):
            rel_id = sheet.attrib[f"{{{NS['office_rel']}}}id"]
            target = relmap[rel_id]
            sheets[sheet.attrib["name"]] = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
        return sheets

    def _cell_value(self, cell: ET.Element) -> Any:
        raw_value = cell.find("main:v", NS)
        inline = cell.find("main:is/main:t", NS)
        cell_type = cell.attrib.get("t")
        raw = raw_value.text if raw_value is not None else None
        if cell_type == "s" and raw is not None:
            return self.shared_strings[int(raw)]
        if cell_type == "b" and raw is not None:
            return raw == "1"
        if inline is not None:
            return inline.text or ""
        if raw is None:
            return None
        try:
            return float(raw)
        except ValueError:
            return raw

    def sheet(self, name: str) -> dict[str, Any]:
        if name not in self._sheet_cache:
            root = ET.fromstring(self.archive.read(self.sheet_paths[name]))
            self._sheet_cache[name] = {
                cell.attrib["r"]: self._cell_value(cell)
                for cell in root.findall(".//main:c", NS)
            }
        return self._sheet_cache[name]

    def value(self, sheet: str, ref: str) -> Any:
        return self.sheet(sheet).get(ref)

    def row_values(self, sheet: str, row: int, start_col: str, count: int) -> list[Any]:
        return [self.value(sheet, cell_ref(start_col, row, offset)) for offset in range(count)]


def yes_no(value: Any) -> bool:
    if value == "Yes":
        return True
    if value == "No":
        return False
    if isinstance(value, bool):
        return value
    raise ValueError(f"Expected Yes/No or boolean, got {value!r}")


def normalize_path(value: str) -> str:
    if value == "No recast":
        return "no_recast"
    if value == "$200k recast":
        return "recast"
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def extract_purchase(book: WorkbookCache) -> dict[str, Any]:
    cells = {
        "down_payment_amount": "C5",
        "mortgage_principal": "C6",
        "buyer_closing_costs": "C7",
        "buyer_transfer_tax": "C8",
        "gross_upfront_cash": "C9",
        "family_loan_used": "C10",
        "net_cash_from_portfolio": "C11",
        "portfolio_after_closing": "C12",
        "starting_liquid_investments": "C13",
        "starting_retirement_nonliquid": "C14",
        "monthly_mortgage_pi": "C15",
        "monthly_property_tax": "C16",
        "monthly_insurance": "C17",
        "monthly_maintenance": "C18",
        "monthly_capex": "C19",
        "family_loan_monthly_service": "C20",
        "monthly_ownership_cost": "C21",
        "annual_ownership_cost": "C22",
        "monthly_nonhousing_burn": "C23",
        "monthly_required_outflow": "C24",
        "liquidity_reserve_target": "C25",
    }
    return {field: book.value("Calculations", ref) for field, ref in cells.items()}


def extract_projection(book: WorkbookCache) -> list[dict[str, Any]]:
    rows = {
        "year": 5,
        "annual_spendable_cash_before_housing": 6,
        "annual_employee_retirement_hsa_savings": 7,
        "annual_employer_match": 8,
        "total_retirement_savings": 9,
        "annual_ownership_cost": 10,
        "annual_nonhousing_burn": 11,
        "annual_taxable_savings_target": 12,
        "annual_liquid_contribution_draw": 13,
        "liquid_investments": 14,
        "retirement_nonliquid_investments": 15,
        "total_investable_assets": 16,
        "inflation_factor": 17,
        "liquid_real": 18,
        "retirement_nonliquid_real": 19,
        "total_real": 20,
        "required_monthly_outflow": 21,
        "liquidity_reserve_target": 22,
        "runway_months": 23,
    }
    values_by_field = {
        field: book.row_values("Liquidity_30Y", row, "C", 31) for field, row in rows.items()
    }
    return [
        {field: values[index] for field, values in values_by_field.items()}
        for index in range(31)
    ]


def extract_recast(book: WorkbookCache) -> dict[str, Any]:
    fields = {
        "active": ("Calculations", "C37"),
        "recast_model_year": ("Calculations", "C39"),
        "months_elapsed_pre_recast": ("Calculations", "C41"),
        "remaining_term_months": ("Calculations", "C42"),
        "mortgage_balance_before_recast": ("Calculations", "C43"),
        "principal_paydown_requested": ("Calculations", "C44"),
        "principal_paydown_applied": ("Calculations", "C46"),
        "recast_fee": ("Calculations", "C45"),
        "mortgage_balance_after_recast": ("Calculations", "C47"),
        "original_monthly_pi": ("Calculations", "C36"),
        "new_monthly_pi_after_recast": ("Calculations", "C49"),
        "monthly_payment_reduction": ("Calculations", "C50"),
        "annual_cash_flow_improvement": ("Calculations", "C51"),
        "breakeven_years": ("Calculations", "C52"),
        "starting_liquid_before_recast": ("Calculations", "C53"),
        "starting_liquid_after_recast": ("Calculations", "C54"),
        "worst_monthly_cash_flow_no_recast": ("Recast Scenario", "B12"),
        "worst_monthly_cash_flow_recast": ("Recast Scenario", "C12"),
    }
    recast = {field: book.value(sheet, ref) for field, (sheet, ref) in fields.items()}
    recast["adequate_liquidity_after_recast"] = yes_no(book.value("Calculations", "C56"))
    recast["cash_flow_positive_after_recast"] = yes_no(book.value("Recast Scenario", "C13"))
    return recast


def extract_stress_tests(book: WorkbookCache) -> list[dict[str, Any]]:
    rows = []
    for row in range(5, 23):
        scenario = book.value("Stress Tests", f"A{row}")
        path = book.value("Stress Tests", f"B{row}")
        rows.append(
            {
                "scenario": scenario,
                "path": normalize_path(path),
                "year_30_liquid_assets": book.value("Stress Tests", f"C{row}"),
                "minimum_liquid_assets": book.value("Stress Tests", f"D{row}"),
                "year_30_total_investable_assets": book.value("Stress Tests", f"E{row}"),
                "falls_below_zero": yes_no(book.value("Stress Tests", f"F{row}")),
                "falls_below_reserve": yes_no(book.value("Stress Tests", f"G{row}")),
                "cash_flow_positive_after_recast": yes_no(book.value("Stress Tests", f"H{row}")),
                "takeaway": book.value("Stress Tests", f"I{row}"),
            }
        )
    return rows


def extract_targets(workbook_path: Path) -> dict[str, Any]:
    book = WorkbookCache(workbook_path)
    return {
        "metadata": {
            "source_workbook": str(workbook_path),
            "source_type": "cached XLSX formula values",
            "excluded": "volatile RAND Monte Carlo paths and percentile outputs",
        },
        "tolerances": {
            "currency_abs": 0.01,
            "factor_abs": 1e-9,
            "years_abs": 1e-6,
            "months_abs": 1e-6,
        },
        "source_ranges": {
            "purchase": "Calculations!C5:C25",
            "projection": "Liquidity_30Y!C5:AG23",
            "recast": "Calculations!C36:C56 and 'Recast Scenario'!B12:C13",
            "stress_tests": "'Stress Tests'!A5:I22",
        },
        "purchase": extract_purchase(book),
        "projection": extract_projection(book),
        "recast": extract_recast(book),
        "stress_tests": extract_stress_tests(book),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/fixtures/workbook_reconciliation_targets.json"),
    )
    args = parser.parse_args()

    targets = extract_targets(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(targets, indent=2) + "\n")


if __name__ == "__main__":
    main()
