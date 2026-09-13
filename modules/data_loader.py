"""Upload parsing and sales-data normalization for SmartStock AI."""

from __future__ import annotations

import io
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd


UNIFIED_COLUMNS = ["date", "product_id", "product_name", "category", "units_sold", "stock_on_hand"]

COLUMN_ALIASES = {
    "date": ("date", "sale_date", "sales_date", "order_date", "transaction_date", "datetime"),
    "product_id": ("product_id", "item_id", "sku", "sku_id", "product_code", "item_code"),
    "product_name": ("product_name", "item_name", "item", "product", "name"),
    "category": ("category", "product_category", "item_category", "department"),
    "units_sold": ("units_sold", "qty_sold", "quantity_sold", "quantity", "qty", "units"),
    "stock_on_hand": ("stock_on_hand", "stock", "inventory", "on_hand", "current_stock", "available_stock"),
}


def _file_bytes(uploaded_file: Any) -> bytes:
    """Extract bytes from a Streamlit UploadedFile or ordinary binary file object."""
    if uploaded_file is None:
        raise ValueError("No file was uploaded.")
    if hasattr(uploaded_file, "getvalue"):
        content = uploaded_file.getvalue()
    elif hasattr(uploaded_file, "read"):
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        content = uploaded_file.read()
    else:
        raise TypeError("uploaded_file must be a file-like object with a name and read method.")
    if isinstance(content, str):
        content = content.encode("utf-8")
    if not content:
        raise ValueError("The uploaded file is empty.")
    return content


def load_raw_data(uploaded_file: Any) -> pd.DataFrame:
    """Load a CSV, Excel, JSON, or SQLite upload into a DataFrame.

    When a SQLite database contains several tables, the first user table is loaded.
    """
    filename = getattr(uploaded_file, "name", "")
    extension = Path(filename).suffix.lower()
    supported = {".csv", ".xlsx", ".xls", ".json", ".db", ".sqlite", ".sqlite3"}
    if not filename or extension not in supported:
        raise ValueError("Unsupported upload. Use CSV, Excel (.xlsx/.xls), JSON, or SQLite (.db).")

    content = _file_bytes(uploaded_file)
    source = io.BytesIO(content)
    try:
        if extension == ".csv":
            return pd.read_csv(source)
        if extension in {".xlsx", ".xls"}:
            return pd.read_excel(source)
        if extension == ".json":
            return pd.read_json(source)
        return _load_sqlite(content, extension)
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError, OSError, sqlite3.Error) as exc:
        raise ValueError(f"Could not read '{filename}': {exc}") from exc


def _load_sqlite(content: bytes, extension: str) -> pd.DataFrame:
    """Read the first non-system table from an uploaded SQLite database."""
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        with sqlite3.connect(temp_path) as connection:
            tables = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
                connection,
            )["name"].tolist()
            if not tables:
                raise ValueError("The SQLite database does not contain a user table.")
            table_name = tables[0].replace('"', '""')
            return pd.read_sql_query(f'SELECT * FROM "{table_name}"', connection)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def standardize_sales_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Map a raw sales export to the unified schema and return a status report."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("standardize_sales_data expects a pandas DataFrame.")

    normalized_names = {_normalise_name(column): column for column in df.columns}
    clean = pd.DataFrame(index=df.index)
    report: dict[str, Any] = {
        "status": "success",
        "input_rows": len(df),
        "output_rows": len(df),
        "mapped_columns": {},
        "defaults_applied": [],
        "warnings": [],
    }
    for target, aliases in COLUMN_ALIASES.items():
        source_column = next((normalized_names.get(alias) for alias in aliases if alias in normalized_names), None)
        if source_column is not None:
            clean[target] = df[source_column]
            report["mapped_columns"][target] = source_column
        else:
            clean[target] = _default_series(target, df.index)
            report["defaults_applied"].append(target)

    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    invalid_dates = int(clean["date"].isna().sum())
    if invalid_dates:
        report["warnings"].append(f"{invalid_dates} row(s) have a missing or invalid date.")
    for column in ("units_sold", "stock_on_hand"):
        clean[column] = pd.to_numeric(clean[column], errors="coerce").fillna(0)
        if (clean[column] < 0).any():
            report["warnings"].append(f"Negative values were retained in '{column}'.")

    clean["product_id"] = clean["product_id"].fillna("").astype(str)
    clean["product_name"] = clean["product_name"].fillna("Unknown Product").astype(str)
    clean["category"] = clean["category"].fillna("Uncategorized").astype(str)
    clean = clean[UNIFIED_COLUMNS]
    if df.empty:
        report["warnings"].append("The uploaded file contains no data rows.")
    if report["defaults_applied"] or report["warnings"]:
        report["status"] = "success_with_warnings"
    return clean, report


def _normalise_name(value: object) -> str:
    """Make source headers comparable: 'Qty Sold' becomes 'qty_sold'."""
    return "_".join("".join(char if char.isalnum() else " " for char in str(value)).lower().split())


def _default_series(column: str, index: pd.Index) -> pd.Series:
    """Provide conservative defaults when a source export lacks a mapped field."""
    defaults = {
        "date": pd.NaT, "product_id": "", "product_name": "Unknown Product",
        "category": "Uncategorized", "units_sold": 0, "stock_on_hand": 0,
    }
    return pd.Series(defaults[column], index=index)


def load_tabular_data(file: Any) -> pd.DataFrame:
    """Backward-compatible alias for existing Streamlit pages."""
    return load_raw_data(file)
