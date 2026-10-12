from pathlib import Path
import gc
import pandas as pd


# ============================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT / "data" / "processed"

MONTHLY_ENRICHED_DIR = (
    PROCESSED_DIR / "monthly_enriched"
)

MONTHLY_FEATURES_DIR = (
    PROCESSED_DIR / "monthly_features"
)


# ============================================================
# 2. BẢNG ÁNH XẠ THÁNG
# ============================================================

MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


# ============================================================
# 3. BẢNG ÁNH XẠ THỨ
# ============================================================

DAY_NAMES = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}


# ============================================================
# 4. LẤY GIỜ TỪ CRSDepTime
# ============================================================

def get_dep_hour(series):
    """
    CRSDepTime có dạng HHMM.

    Ví dụ:
        5     -> 0
        30    -> 0
        630   -> 6
        1530  -> 15
        2400  -> 0
    """

    hour = series // 100

    # BTS có thể dùng 2400 cho 00:00
    hour = hour.where(
        series != 2400,
        0
    )

    return hour.astype("Int64")


# ============================================================
# 5. PHÂN NHÓM KHUNG GIỜ
# ============================================================

def get_time_group(hour):
    """
    Chia giờ khởi hành dự kiến thành các khung giờ.
    """

    if pd.isna(hour):
        return pd.NA

    hour = int(hour)

    if 0 <= hour <= 5:
        return "00-05"

    elif 6 <= hour <= 8:
        return "06-08"

    elif 9 <= hour <= 11:
        return "09-11"

    elif 12 <= hour <= 14:
        return "12-14"

    elif 15 <= hour <= 17:
        return "15-17"

    elif 18 <= hour <= 20:
        return "18-20"

    elif 21 <= hour <= 23:
        return "21-23"

    return pd.NA


# ============================================================
# 6. PHÂN LOẠI MỨC ĐỘ TRỄ
# ============================================================

def get_delay_category(arr_delay):
    """
    Phân loại mức độ chậm dựa trên ArrDelay.

    Quy ước:
        <= 15 phút     -> On Time
        16-30 phút     -> 16-30 min
        31-60 phút     -> 31-60 min
        61-120 phút    -> 61-120 min
        > 120 phút     -> >120 min

    Giá trị âm vẫn thuộc On Time vì chuyến đến sớm.
    """

    if pd.isna(arr_delay):
        return pd.NA

    if arr_delay <= 15:
        return "On Time"

    elif arr_delay <= 30:
        return "16-30 min"

    elif arr_delay <= 60:
        return "31-60 min"

    elif arr_delay <= 120:
        return "61-120 min"

    return ">120 min"


# ============================================================
# 7. TẠO FEATURE CHO MỘT THÁNG
# ============================================================

def create_features(df):
    """
    Tạo các biến phục vụ phân tích và dashboard.
    """

    df = df.copy()

    # --------------------------------------------------------
    # 7.1. Tên tháng
    # --------------------------------------------------------

    df["Month_Name"] = (
        df["Month"]
        .map(MONTH_NAMES)
        .astype("string")
    )

    # --------------------------------------------------------
    # 7.2. Tên thứ
    # --------------------------------------------------------

    df["Day_Name"] = (
        df["DayOfWeek"]
        .map(DAY_NAMES)
        .astype("string")
    )

    # --------------------------------------------------------
    # 7.3. Giờ khởi hành dự kiến
    # --------------------------------------------------------

    df["Dep_Hour"] = get_dep_hour(
        df["CRSDepTime"]
    )

    # --------------------------------------------------------
    # 7.4. Khung giờ
    # --------------------------------------------------------

    df["Time_Group"] = (
        df["Dep_Hour"]
        .apply(get_time_group)
        .astype("string")
    )

    # --------------------------------------------------------
    # 7.5. Tuyến bay
    # --------------------------------------------------------

    df["Route"] = (
        df["Origin"].astype("string")
        + " → "
        + df["Dest"].astype("string")
    )

    # --------------------------------------------------------
    # 7.6. Xác định chuyến hợp lệ để phân tích arrival delay
    # --------------------------------------------------------

    df["Valid_Arrival_Delay"] = (
        (df["Cancelled"] == 0)
        &
        (df["Diverted"] == 0)
        &
        df["ArrDelay"].notna()
    )

    # --------------------------------------------------------
    # 7.7. Is_Delayed
    #
    # Chỉ xác định delayed cho những chuyến hợp lệ.
    # --------------------------------------------------------

    df["Is_Delayed"] = pd.Series(
        pd.NA,
        index=df.index,
        dtype="boolean"
    )

    valid_mask = (
        df["Valid_Arrival_Delay"]
    )

    df.loc[
        valid_mask,
        "Is_Delayed"
    ] = (
        df.loc[
            valid_mask,
            "ArrDelay"
        ] > 15
    )

    # --------------------------------------------------------
    # 7.8. Delay Category
    # --------------------------------------------------------

    df["Delay_Category"] = pd.Series(
        pd.NA,
        index=df.index,
        dtype="string"
    )

    df.loc[
        valid_mask,
        "Delay_Category"
    ] = (
        df.loc[
            valid_mask,
            "ArrDelay"
        ]
        .apply(get_delay_category)
    )

    # --------------------------------------------------------
    # 7.9. Cờ cancelled
    # --------------------------------------------------------

    df["Is_Cancelled"] = (
        df["Cancelled"] == 1
    )

    # --------------------------------------------------------
    # 7.10. Cờ diverted
    # --------------------------------------------------------

    df["Is_Diverted"] = (
        df["Diverted"] == 1
    )

    return df


# ============================================================
# 8. KIỂM TRA FEATURE
# ============================================================

def check_features(df):
    """
    Kiểm tra nhanh dữ liệu sau khi tạo feature.
    """

    print(
        f"Rows: {df.shape[0]:,}"
    )

    print(
        f"Columns: {df.shape[1]}"
    )

    valid_count = (
        df["Valid_Arrival_Delay"]
        .sum()
    )

    delayed_count = (
        df["Is_Delayed"]
        .sum(skipna=True)
    )

    cancelled_count = (
        df["Is_Cancelled"]
        .sum()
    )

    diverted_count = (
        df["Is_Diverted"]
        .sum()
    )

    print(
        f"Valid arrival delay: "
        f"{valid_count:,}"
    )

    print(
        f"Delayed flights: "
        f"{delayed_count:,}"
    )

    print(
        f"Cancelled flights: "
        f"{cancelled_count:,}"
    )

    print(
        f"Diverted flights: "
        f"{diverted_count:,}"
    )

    print("\nTime Group:")

    print(
        df["Time_Group"]
        .value_counts(
            dropna=False
        )
        .sort_index()
    )

    print("\nDelay Category:")

    print(
        df["Delay_Category"]
        .value_counts(
            dropna=False
        )
    )


# ============================================================
# 9. XỬ LÝ TỪNG THÁNG
# ============================================================

def create_all_features():
    """
    Đọc từng file enriched, tạo feature rồi lưu riêng từng tháng.
    """

    MONTHLY_FEATURES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    files = sorted(
        MONTHLY_ENRICHED_DIR.glob(
            "*_enriched.parquet"
        )
    )

    if not files:
        raise FileNotFoundError(
            "Không tìm thấy file enriched trong: "
            f"{MONTHLY_ENRICHED_DIR}"
        )

    print(
        f"Tìm thấy {len(files)} file enriched."
    )

    output_files = []

    for index, file_path in enumerate(
        files,
        start=1
    ):

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"[{index}/{len(files)}] "
            f"{file_path.name}"
        )

        print(
            "=" * 70
        )

        # ----------------------------------------------------
        # Đọc một tháng
        # ----------------------------------------------------

        df = pd.read_parquet(
            file_path
        )

        print(
            f"Input: "
            f"{df.shape[0]:,} rows, "
            f"{df.shape[1]} columns"
        )

        # ----------------------------------------------------
        # Tạo feature
        # ----------------------------------------------------

        df_features = (
            create_features(
                df
            )
        )

        # ----------------------------------------------------
        # Kiểm tra
        # ----------------------------------------------------

        check_features(
            df_features
        )

        # ----------------------------------------------------
        # Tạo tên output
        # ----------------------------------------------------

        output_name = (
            file_path.name
            .replace(
                "_enriched.parquet",
                "_features.parquet"
            )
        )

        output_file = (
            MONTHLY_FEATURES_DIR
            / output_name
        )

        # ----------------------------------------------------
        # Lưu
        # ----------------------------------------------------

        df_features.to_parquet(
            output_file,
            index=False
        )

        print(
            f"\nĐã lưu: "
            f"{output_file.name}"
        )

        output_files.append(
            output_file
        )

        # ----------------------------------------------------
        # Giải phóng RAM
        # ----------------------------------------------------

        del df
        del df_features

        gc.collect()

    return output_files


# ============================================================
# 10. MAIN
# ============================================================

if __name__ == "__main__":

    output_files = (
        create_all_features()
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "FEATURE ENGINEERING HOÀN TẤT"
    )

    print(
        "=" * 70
    )

    print(
        f"Số file tạo ra: "
        f"{len(output_files)}"
    )

    for file in output_files:
        print(
            file.name
        )