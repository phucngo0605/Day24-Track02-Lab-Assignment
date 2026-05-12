# src/quality/validation.py
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
import great_expectations.expectations as gxe

def build_patient_expectation_suite() -> ExpectationSuite:
    """
    Tạo expectation suite cho anonymized patient data.
    """
    context = gx.get_context()
    suite = ExpectationSuite(name="patient_data_suite")
    valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]

    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="patient_id"))
    suite.add_expectation(gxe.ExpectColumnValueLengthsToEqual(column="cccd", value=12))
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(
            column="ket_qua_xet_nghiem",
            min_value=0,
            max_value=50,
        )
    )
    suite.add_expectation(gxe.ExpectColumnValuesToBeInSet(column="benh", value_set=valid_conditions))
    suite.add_expectation(
        gxe.ExpectColumnValuesToMatchRegex(
            column="email",
            regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        )
    )
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="patient_id"))

    return context.suites.add_or_update(suite)


def validate_anonymized_data(filepath: str) -> dict:
    """
    Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: Không còn CCCD gốc dạng số thuần túy
    # (sau anonymization, cccd phải là fake hoặc masked)
    original_df = pd.read_csv("data/raw/patients_raw.csv")
    for original_cccd in original_df["cccd"].values:
        if str(original_cccd) in df["cccd"].astype(str).values:
            results["success"] = False
            results["failed_checks"].append(f"Original CCCD {original_cccd} found in anonymized data")

    # Check 2: Không có null values trong các cột quan trọng
    important_cols = ["patient_id", "benh", "ket_qua_xet_nghiem"]
    for col in important_cols:
        if df[col].isnull().any():
            results["success"] = False
            results["failed_checks"].append(f"Null values found in column {col}")

    # Check 3: Số rows phải bằng original
    if len(df) != len(original_df):
        results["success"] = False
        results["failed_checks"].append(f"Row count mismatch: {len(df)} vs {len(original_df)}")

    return results
