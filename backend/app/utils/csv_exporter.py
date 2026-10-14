import io
import csv
import re
from typing import List, Dict, Any, Optional

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

def sanitize_csv_cell(value: Any) -> Any:
    """
    Mitigates spreadsheet formula injection (CSV Injection).
    If a string cell starts with '=', '+', '-', '@', tab, or carriage return,
    prepends a single quote "'" to neutralize formula interpretation in Excel/Calc.
    Preserves actual numeric types (int, float) intact.
    """
    if value is None:
        return ""

    if isinstance(value, (int, float)):
        return value

    val_str = str(value)
    # Check if string starts with formula characters and is not a plain number
    if val_str.startswith(FORMULA_PREFIXES):
        # Allow pure numbers like "-10" or "+5.2" without neutralization
        try:
            float(val_str)
            return val_str
        except ValueError:
            # It's a formula or text with leading special character
            return f"'{val_str}"

    return val_str


def sanitize_filename(name: str) -> str:
    """
    Sanitizes string for safe HTTP Content-Disposition attachment filenames.
    Prevents path traversal, control chars, and illegal Windows/Linux characters.
    """
    clean = re.sub(r"[^\w\-_.]", "_", name.strip())
    clean = re.sub(r"_+", "_", clean)
    return clean[:100]


def generate_csv_report(
    report_title: str,
    metadata: Optional[Dict[str, Any]] = None,
    summary_metrics: Optional[Dict[str, Any]] = None,
    columns: Optional[List[str]] = None,
    records: Optional[List[Dict[str, Any]]] = None,
    column_keys: Optional[List[str]] = None,
    include_bom: bool = True,
    metadata_lines: Optional[List[str]] = None,
) -> bytes:
    """
    Generates UTF-8 encoded CSV bytes with sanitized cells and metadata comments.
    """
    output = io.StringIO()
    writer = csv.writer(output, dialect="excel", quoting=csv.QUOTE_MINIMAL)

    # 1. Write Header Comments / Metadata
    writer.writerow([f"# NEXORA REPORT: {report_title}"])
    if metadata:
        for k, v in metadata.items():
            writer.writerow([f"# {k}: {v}"])
    if metadata_lines:
        for line in metadata_lines:
            writer.writerow([f"# {line}"])
    if summary_metrics:
        writer.writerow(["# SUMMARY METRICS:"])
        for k, v in summary_metrics.items():
            writer.writerow([f"#   {k}: {v}"])
    writer.writerow([])  # Blank separator

    # 2. Write Column Headers
    cols = columns or []
    writer.writerow(cols)

    # 3. Write Data Records
    keys = column_keys if column_keys else cols
    recs = records or []
    for row in recs:
        row_values = []
        for k in keys:
            val = row.get(k, "")
            row_values.append(sanitize_csv_cell(val))
        writer.writerow(row_values)

    csv_text = output.getvalue()
    if include_bom:
        # Prepend UTF-8 BOM (\xef\xbb\xbf) for Excel UTF-8 auto-detection
        return b"\xef\xbb\xbf" + csv_text.encode("utf-8")
    return csv_text.encode("utf-8")
