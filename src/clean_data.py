from pathlib import Path
import gc
import pandas as pd

from load_data import get_bts_zip_files, load_bts_zip


# ============================================================
# 1. ĐƯỜNG DẪN
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT / "data" / "processed"
MONTHLY_DIR = PROCESSED_DIR / "monthly_clean"


# ============================================================
# 2. CÁC NHÓM CỘT
# ============================================================

REQUIRED_COLUMNS = [
    "FlightDate",
    "Reporting_Airline",
    "Origin",
    "Dest",
]

STRING_COLUMNS = [
    "Reporting_Airline",
    "Origin",
    "Dest",
]

NUMERIC_COLUMNS = [
    "Year",
    "Quarter",
    "Month",
    "DayofMonth",
    "DayOfWeek",
    "Flight_Number_Reporting_Airline",
    "CRSDepTime",
    "DepTime",
    "DepDelay",
    "DepDelayMinutes",
    "CRSArrTime",
    "ArrTime",
    "ArrDelay",
    "ArrDelayMinutes",
    "Cancelled",
    "Diverted",
    "Distance",
    "CarrierDelay",
    "WeatherDelay",
    "NASDelay",
    "SecurityDelay",
    "LateAircraftDelay",
]

TIME_COLUMNS = [
    "CRSDepTime",
    "DepTime",
    "CRSArrTime",
    "ArrTime",
]

DELAY_CAUSE_COLUMNS = [
    "CarrierDelay",
    "WeatherDelay",
    "NASDelay",
    "SecurityDelay",
    "LateAircraftDelay",
]


# ============================================================
# 3. KIỂM TRA CỘT
# ============================================================

def validate_columns(df):
    missing = [
        col
        for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        raise KeyError(
            "Thiếu cột bắt buộc: "
            + ", ".join(missing)
        )

    for col in ["Cancelled", "Diverted"]:
        if col not in df.columns:
            raise KeyError(
                f"Không tìm thấy cột {col}"
            )


# ============================================================
# 4. CHUẨN HÓA CHUỖI
# ============================================================

def clean_strings(df):
    for col in STRING_COLUMNS:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
                .str.upper()
                .replace("", pd.NA)
            )

    return df


# ============================================================
# 5. CHUYỂN KIỂU SỐ
# ============================================================

def convert_numeric(df):
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return df


# ============================================================
# 6. KIỂM TRA HHMM
# ============================================================

def is_valid_hhmm(value):
    if pd.isna(value):
        return True

    try:
        value = int(value)
    except (TypeError, ValueError):
        return False

    if value == 2400:
        return True

    if value < 0:
        return False

    hour = value // 100
    minute = value % 100

    return (
        0 <= hour <= 23
        and 0 <= minute <= 59
    )


def clean_time_columns(df):
    for col in TIME_COLUMNS:
        if col not in df.columns:
            continue

        valid_mask = df[col].apply(
            is_valid_hhmm
        )

        invalid_count = (
            ~valid_mask
        ).sum()

        print(
            f"  {col} invalid: "
            f"{invalid_count:,}"
        )

        df.loc[
            ~valid_mask,
            col
        ] = pd.NA

    return df


# ============================================================
# 7. CLEAN MỘT THÁNG
# ============================================================

def clean_month(df):
    print(
        f"  Raw rows: {len(df):,}"
    )

    df = df.copy()

    validate_columns(df)

    # --------------------------------------------------------
    # Duplicate
    # --------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates()

    print(
        f"  Duplicates removed: "
        f"{before - len(df):,}"
    )

    # --------------------------------------------------------
    # String
    # --------------------------------------------------------

    df = clean_strings(df)

    # --------------------------------------------------------
    # FlightDate
    # --------------------------------------------------------

    df["FlightDate"] = pd.to_datetime(
        df["FlightDate"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Missing required
    # --------------------------------------------------------

    before = len(df)

    df = df.dropna(
        subset=REQUIRED_COLUMNS
    )

    print(
        f"  Missing required removed: "
        f"{before - len(df):,}"
    )

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    df = convert_numeric(df)

    # --------------------------------------------------------
    # Cancelled / Diverted
    # --------------------------------------------------------

    before = len(df)

    valid_status = (
        df["Cancelled"].isin([0, 1])
        &
        df["Diverted"].isin([0, 1])
    )

    df = df.loc[
        valid_status
    ]

    print(
        f"  Invalid status removed: "
        f"{before - len(df):,}"
    )

    # --------------------------------------------------------
    # Tạo lại date dimension
    # --------------------------------------------------------

    df["Year"] = (
        df["FlightDate"]
        .dt.year
    )

    df["Month"] = (
        df["FlightDate"]
        .dt.month
    )

    df["DayofMonth"] = (
        df["FlightDate"]
        .dt.day
    )

    df["DayOfWeek"] = (
        df["FlightDate"]
        .dt.dayofweek
        + 1
    )

    df["Quarter"] = (
        df["FlightDate"]
        .dt.quarter
    )

    # --------------------------------------------------------
    # Chỉ giữ 2025
    # --------------------------------------------------------

    before = len(df)

    df = df[
        df["Year"] == 2025
    ]

    print(
        f"  Rows outside 2025 removed: "
        f"{before - len(df):,}"
    )

    # --------------------------------------------------------
    # HHMM
    # --------------------------------------------------------

    df = clean_time_columns(df)

    # --------------------------------------------------------
    # Distance
    # --------------------------------------------------------

    if "Distance" in df.columns:
        invalid_distance = (
            df["Distance"].notna()
            &
            (df["Distance"] <= 0)
        )

        print(
            f"  Invalid Distance: "
            f"{invalid_distance.sum():,}"
        )

        df.loc[
            invalid_distance,
            "Distance"
        ] = pd.NA

    # --------------------------------------------------------
    # Delay causes
    # --------------------------------------------------------

    existing_delay_cols = [
        col
        for col in DELAY_CAUSE_COLUMNS
        if col in df.columns
    ]

    for col in existing_delay_cols:
        negative_mask = (
            df[col].notna()
            &
            (df[col] < 0)
        )

        print(
            f"  {col} negative: "
            f"{negative_mask.sum():,}"
        )

        df.loc[
            negative_mask,
            col
        ] = pd.NA

    if existing_delay_cols:
        df[existing_delay_cols] = (
            df[existing_delay_cols]
            .fillna(0)
        )

    # --------------------------------------------------------
    # Reset index
    # --------------------------------------------------------

    df = df.reset_index(
        drop=True
    )

    print(
        f"  Clean rows: {len(df):,}"
    )

    return df


# ============================================================
# 8. MISSING REPORT CHO MỘT THÁNG
# ============================================================

def print_missing_report(df):
    report = (
        df.isna()
        .sum()
        .sort_values(
            ascending=False
        )
        .head(10)
    )

    print(
        "\n  Top missing:"
    )

    print(report)


# ============================================================
# 9. CLEAN TỪNG FILE ZIP
# ============================================================

def clean_all_months():
    MONTHLY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    zip_files = get_bts_zip_files()

    print(
        f"Tìm thấy {len(zip_files)} file BTS."
    )

    outputs = []

    for index, file_path in enumerate(
        zip_files,
        start=1
    ):
        print(
            "\n"
            + "=" * 70
        )

        print(
            f"[{index}/{len(zip_files)}] "
            f"ĐANG XỬ LÝ {file_path.name}"
        )

        print(
            "=" * 70
        )

        # ----------------------------------------------------
        # Load chỉ 1 tháng
        # ----------------------------------------------------

        df = load_bts_zip(
            file_path
        )

        print(
            f"Loaded: "
            f"{df.shape[0]:,} rows, "
            f"{df.shape[1]} columns"
        )

        # ----------------------------------------------------
        # Clean
        # ----------------------------------------------------

        df_clean = clean_month(
            df
        )

        print_missing_report(
            df_clean
        )

        # ----------------------------------------------------
        # Save Parquet
        # ----------------------------------------------------

        output_file = (
            MONTHLY_DIR
            / f"{file_path.stem}_clean.parquet"
        )

        df_clean.to_parquet(
            output_file,
            index=False
        )

        print(
            f"\nĐã lưu: "
            f"{output_file}"
        )

        outputs.append(
            output_file
        )

        # ----------------------------------------------------
        # Giải phóng RAM
        # ----------------------------------------------------

        del df
        del df_clean

        gc.collect()

    return outputs


# ============================================================
# 10. TỔNG HỢP THÔNG TIN FILE CLEAN
# ============================================================

def print_clean_files_summary(files):
    print(
        "\n"
        + "=" * 70
    )

    print(
        "HOÀN TẤT CLEANING 12 THÁNG"
    )

    print(
        "=" * 70
    )

    print(
        f"Số file clean: {len(files)}"
    )

    for file in files:
        size_mb = (
            file.stat().st_size
            / 1024
            / 1024
        )

        print(
            f"{file.name}: "
            f"{size_mb:.2f} MB"
        )


# ============================================================
# 11. MAIN
# ============================================================

if __name__ == "__main__":

    cleaned_files = clean_all_months()

    print_clean_files_summary(
        cleaned_files
    )