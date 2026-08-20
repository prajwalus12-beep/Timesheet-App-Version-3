"""
utils/xlsx_export.py
====================
Clean XLSX export utility for the Timesheet App.

Root causes of hidden/stale cells in exported XLSX files
---------------------------------------------------------
1. Cell-creation side-effect in the width loop: calling ws.cell(row, col)
   inside a nested for-loop creates Cell objects for every (row, col) pair
   even when there is no data. openpyxl then serialises those objects as
   <c> XML elements that external systems read as "populated".

2. Inflated worksheet dimensions: ws.max_row / ws.max_column are derived
   from every Cell ever touched, not just cells with data, so the
   <dimension ref> attribute in the XML may be e.g. A1:I1048576 even when
   only A1:I101 contains data.

3. Residual empty-cell objects: after Pandas writes the file some cells
   have value=None or value="" but still live in ws._cells. openpyxl
   serialises them as <c> elements that external systems treat as populated.

4. Incorrect style reset: the original code used
   cell._style = ws.cell(1,1)._style.__class__() which instantiates a
   generic object rather than a proper openpyxl StyleArray.

5. Pandas NaN/None serialisation: DataFrame.where(notna(), None) followed
   by to_excel can still produce empty-string cells for certain dtypes.

This module fixes all five issues.
"""

import io
import math
import openpyxl
import openpyxl.styles
import pandas as pd
from openpyxl.utils import get_column_letter


# ---------------------------------------------------------------------------
# DataFrame sanitisation
# ---------------------------------------------------------------------------

def sanitise_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* where every empty-like value is Python None.

    Treated as empty:
    - float NaN / numpy NaN (any numeric dtype)
    - pd.NaT / pd.NA
    - None
    - Strings that are empty or whitespace-only after .strip()

    Important: df.where(notna(), None) does NOT replace NaN for float/numpy
    columns because the column stays float64 and NaN is a valid float.
    We must convert to object dtype first so Python None can be stored.
    """
    df = df.copy()
    for col in df.columns:
        # Convert to object so Python None can be stored (not numpy float NaN)
        series = df[col].astype(object)

        def _clean(v):
            if v is None:
                return None
            # Catch numpy NaN, float NaN, pd.NaT, pd.NA
            try:
                if pd.isna(v):
                    return None
            except (TypeError, ValueError):
                pass
            if isinstance(v, str):
                s = v.strip()
                return s if s else None
            return v

        df[col] = series.apply(_clean)
    return df


# ---------------------------------------------------------------------------
# Column-width calculation WITHOUT cell-creation side effects
# ---------------------------------------------------------------------------

def apply_column_widths(ws, data_rows: int, data_cols: int,
                         comment_col_name: str = "Comment",
                         comment_width: int = 40):
    """Set column widths by reading only already-existing cells in ws._cells.

    The critical fix: we do NOT call ws.cell(row, col) in a nested loop.
    Calling ws.cell() creates a new Cell object as a side-effect — those
    objects are then serialised as <c> elements in the XLSX XML.
    """
    comment_col_idx = None
    col_max_len: dict = {}

    for col_idx in range(1, data_cols + 1):
        cell = ws._cells.get((1, col_idx))
        if cell and cell.value == comment_col_name:
            comment_col_idx = col_idx

    for (row, col), cell in ws._cells.items():
        if row < 1 or col < 1 or row > data_rows or col > data_cols:
            continue
        if cell.value is not None:
            length = len(str(cell.value))
            if length > col_max_len.get(col, 0):
                col_max_len[col] = length

    if comment_col_idx:
        for row_idx in range(2, data_rows + 1):
            cell = ws._cells.get((row_idx, comment_col_idx))
            if cell and cell.value is not None:
                cell.alignment = openpyxl.styles.Alignment(wrap_text=True)

    for col_idx in range(1, data_cols + 1):
        letter = get_column_letter(col_idx)
        if col_idx == comment_col_idx:
            ws.column_dimensions[letter].width = comment_width
        else:
            ws.column_dimensions[letter].width = col_max_len.get(col_idx, 8) + 2


# ---------------------------------------------------------------------------
# Deep clean — delete empty Cell objects, reset dimensions
# ---------------------------------------------------------------------------

def deep_clean_worksheet(ws, data_rows: int, data_cols: int):
    """Remove empty/stale Cell objects from ws._cells and fix dimensions."""
    keys_to_delete = []
    for (row, col), cell in list(ws._cells.items()):
        val = cell.value
        is_empty = (
            val is None
            or (isinstance(val, float) and math.isnan(val))
            or (isinstance(val, str) and not val.strip())
        )
        is_out_of_range = row > data_rows or col > data_cols
        if is_empty or is_out_of_range:
            keys_to_delete.append((row, col))

    for key in keys_to_delete:
        ws._cells.pop(key, None)

    # ws.dimensions is a read-only property in openpyxl 3.1.5 that calculates
    # the dimensions dynamically. Removing empty cells from ws._cells
    # automatically fixes the computed dimensions.

    valid_letters = {get_column_letter(c) for c in range(1, data_cols + 1)}
    for letter in list(ws.column_dimensions.keys()):
        if letter not in valid_letters:
            del ws.column_dimensions[letter]

    for r in list(ws.row_dimensions.keys()):
        if r > data_rows:
            del ws.row_dimensions[r]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_clean_xlsx(df: pd.DataFrame,
                     sheet_name: str = "Sheet1",
                     comment_col_name: str = "Comment") -> bytes:
    """Write *df* to a structurally clean XLSX and return the bytes.

    Steps:
    1. Sanitise the DataFrame (NaN/None/whitespace -> None).
    2. Write with index=False via ExcelWriter.
    3. Post-process:
       a. Remove bold/border from header row (reading from _cells only).
       b. Calculate and set column widths without creating extra cells.
       c. Delete empty Cell objects from ws._cells.
       d. Reset worksheet dimensions to the true data bounding box.
    4. Return clean bytes.
    """
    clean_df = sanitise_dataframe(df)
    n_data_rows = len(clean_df) + 1   # +1 for header row
    n_data_cols = len(clean_df.columns)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        clean_df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.sheets[sheet_name]

        # Remove bold/border from header — read from _cells, no side effects
        for col_idx in range(1, n_data_cols + 1):
            cell = ws._cells.get((1, col_idx))
            if cell:
                cell.font = openpyxl.styles.Font(bold=False)
                cell.border = openpyxl.styles.Border()

        apply_column_widths(ws, n_data_rows, n_data_cols, comment_col_name)
        deep_clean_worksheet(ws, n_data_rows, n_data_cols)

    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Validation helper (used by tests)
# ---------------------------------------------------------------------------

def validate_xlsx(xlsx_bytes: bytes,
                  expected_rows: int,
                  expected_cols: int,
                  sheet_name: str = "Sheet1") -> dict:
    """Programmatically validate a generated XLSX for cleanliness.

    Parameters
    ----------
    xlsx_bytes     : XLSX file bytes to validate.
    expected_rows  : total expected rows including the header row.
    expected_cols  : expected number of columns.
    sheet_name     : sheet to inspect.

    Returns dict with: ok, issues, unexpected_cells, used_rows, used_cols.
    """
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
    ws = wb[sheet_name]

    issues = []
    unexpected = []
    max_row_found = 0
    max_col_found = 0

    for row in ws.iter_rows():
        for cell in row:
            val = cell.value
            has_value = (
                val is not None
                and not (isinstance(val, float) and math.isnan(val))
                and not (isinstance(val, str) and not val.strip())
            )
            if has_value:
                if cell.row > max_row_found:
                    max_row_found = cell.row
                if cell.column > max_col_found:
                    max_col_found = cell.column
                if cell.row > expected_rows or cell.column > expected_cols:
                    unexpected.append("{coord}={val!r}".format(
                        coord=cell.coordinate, val=val))

    if unexpected:
        issues.append(
            "{n} unexpected cell(s) outside A1:{col}{row}: {cells}".format(
                n=len(unexpected),
                col=get_column_letter(expected_cols),
                row=expected_rows,
                cells=", ".join(unexpected[:10]),
            )
        )

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "unexpected_cells": unexpected,
        "used_rows": max_row_found,
        "used_cols": max_col_found,
    }

