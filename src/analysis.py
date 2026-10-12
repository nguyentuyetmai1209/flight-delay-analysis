from pathlib import Path

import gc

import pandas as pd


# ============================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT / "data" / "processed"

MONTHLY_FEATURES_DIR = (
    PROCESSED_DIR / "monthly_features"
)

ANALYSIS_DIR = (
    ROOT / "data" / "analysis"
)


# ============================================================
# 2. CẤU HÌNH PHÂN TÍCH
# ============================================================

DELAY_CAUSE_COLUMNS = [
    "CarrierDelay",
    "WeatherDelay",
    "NASDelay",
    "SecurityDelay",
    "LateAircraftDelay",
]

# Chỉ phân tích tuyến có ít nhất 100 chuyến
# để tránh trường hợp 1-2 chuyến nhưng Delay Rate = 100%
MIN_ROUTE_FLIGHTS = 100

TIME_ORDER = [
    "00-05",
    "06-08",
    "09-11",
    "12-14",
    "15-17",
    "18-20",
    "21-23",
]


# ============================================================
# 3. HÀM HỖ TRỢ
# ============================================================

def get_month_number(file_path):
    """
    Lấy số tháng từ tên file dạng:
    2025_1_features.parquet
    """
    try:
        return int(file_path.stem.split("_")[1])
    except (IndexError, ValueError):
        return 999


def safe_bool_mask(series):
    """
    Chuyển Series boolean có thể chứa NA thành mask True/False an toàn.
    """
    return series.fillna(False).astype(bool)


# ============================================================
# 4. TẠO SUMMARY DELAY THEO NHÓM
# ============================================================

def summarize_delay(df, group_cols):
    """
    Tạo bảng thống kê delay theo một hoặc nhiều cột.

    Kết quả trung gian gồm:
    - Total_Flights
    - Valid_Flights
    - Delayed_Flights
    - Arrival_Delay_Sum
    - Delayed_Minutes_Sum

    Các tổng được giữ lại để khi gộp 12 tháng có thể tính
    trung bình có trọng số chính xác.
    """

    # Tổng số chuyến
    total = (
        df.groupby(
            group_cols,
            dropna=False
        )
        .size()
        .rename("Total_Flights")
    )

    # Chuyến hợp lệ để phân tích ArrDelay
    valid_mask = safe_bool_mask(
        df["Valid_Arrival_Delay"]
    )

    valid_df = df[
        valid_mask
    ].copy()

    # Số chuyến hợp lệ
    valid = (
        valid_df.groupby(
            group_cols,
            dropna=False
        )
        .size()
        .rename("Valid_Flights")
    )

    # Số chuyến bị chậm
    delayed = (
        valid_df.groupby(
            group_cols,
            dropna=False
        )["Is_Delayed"]
        .sum()
        .rename("Delayed_Flights")
    )

    # Tổng ArrDelay của tất cả chuyến hợp lệ
    arrival_delay_sum = (
        valid_df.groupby(
            group_cols,
            dropna=False
        )["ArrDelay"]
        .sum()
        .rename("Arrival_Delay_Sum")
    )

    # Tổng phút trễ của các chuyến delayed
    delayed_mask = (
        safe_bool_mask(
            valid_df["Is_Delayed"]
        )
    )

    delayed_df = valid_df[
        delayed_mask
    ]

    delayed_minutes_sum = (
        delayed_df.groupby(
            group_cols,
            dropna=False
        )["ArrDelay"]
        .sum()
        .rename("Delayed_Minutes_Sum")
    )

    # Ghép kết quả
    result = pd.concat(
        [
            total,
            valid,
            delayed,
            arrival_delay_sum,
            delayed_minutes_sum,
        ],
        axis=1
    ).reset_index()

    fill_columns = [
        "Valid_Flights",
        "Delayed_Flights",
        "Arrival_Delay_Sum",
        "Delayed_Minutes_Sum",
    ]

    result[fill_columns] = (
        result[fill_columns]
        .fillna(0)
    )

    return result


# ============================================================
# 5. GỘP SUMMARY DELAY CỦA 12 THÁNG
# ============================================================

def combine_summaries(
    summary_list,
    group_cols
):
    """
    Gộp các bảng thống kê theo tháng thành một bảng toàn năm.
    """

    combined = pd.concat(
        summary_list,
        ignore_index=True
    )

    result = (
        combined
        .groupby(
            group_cols,
            dropna=False,
            as_index=False
        )
        .agg(
            Total_Flights=(
                "Total_Flights",
                "sum"
            ),
            Valid_Flights=(
                "Valid_Flights",
                "sum"
            ),
            Delayed_Flights=(
                "Delayed_Flights",
                "sum"
            ),
            Arrival_Delay_Sum=(
                "Arrival_Delay_Sum",
                "sum"
            ),
            Delayed_Minutes_Sum=(
                "Delayed_Minutes_Sum",
                "sum"
            ),
        )
    )

    # Tỷ lệ chuyến bị chậm
    result["Delay_Rate"] = (
        result["Delayed_Flights"]
        .div(
            result["Valid_Flights"]
            .replace(0, pd.NA)
        )
        * 100
    )

    # ArrDelay trung bình của tất cả chuyến hợp lệ
    # Có thể âm vì chuyến đến sớm vẫn là dữ liệu hợp lệ
    result["Avg_Arrival_Delay"] = (
        result["Arrival_Delay_Sum"]
        .div(
            result["Valid_Flights"]
            .replace(0, pd.NA)
        )
    )

    # Số phút trễ trung bình chỉ trên các chuyến delayed
    result["Avg_Delay_Minutes"] = (
        result["Delayed_Minutes_Sum"]
        .div(
            result["Delayed_Flights"]
            .replace(0, pd.NA)
        )
    )

    return result


# ============================================================
# 6. KPI CHO MỘT THÁNG
# ============================================================

def analyze_kpi(df):
    """
    Tính các thành phần KPI cho một file tháng.
    """

    valid_mask = safe_bool_mask(
        df["Valid_Arrival_Delay"]
    )

    valid_df = df[
        valid_mask
    ]

    delayed_mask = safe_bool_mask(
        valid_df["Is_Delayed"]
    )

    delayed_df = valid_df[
        delayed_mask
    ]

    return {
        "Total_Flights":
            len(df),

        "Valid_Flights":
            len(valid_df),

        "Delayed_Flights":
            int(
                delayed_mask.sum()
            ),

        "Cancelled_Flights":
            int(
                safe_bool_mask(
                    df["Is_Cancelled"]
                ).sum()
            ),

        "Diverted_Flights":
            int(
                safe_bool_mask(
                    df["Is_Diverted"]
                ).sum()
            ),

        "Arrival_Delay_Sum":
            valid_df["ArrDelay"]
            .sum(),

        "Delayed_Minutes_Sum":
            delayed_df["ArrDelay"]
            .sum(),
    }


# ============================================================
# 7. PHÂN TÍCH NGUYÊN NHÂN TRỄ
# ============================================================

def analyze_delay_causes(df):
    """
    Tính tổng số phút chậm theo từng nguyên nhân.
    """

    result = {}

    for column in DELAY_CAUSE_COLUMNS:

        if column in df.columns:

            values = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0)

            # Bảo vệ khỏi dữ liệu âm bất thường
            values = values.clip(lower=0)

            result[column] = values.sum()

    return result


# ============================================================
# 8. WEATHER DELAY - SUMMARY THEO NHÓM
# ============================================================

def summarize_weather(df, group_cols):
    """
    Phân tích WeatherDelay theo nhóm.

    Weather-Affected Flight:
        WeatherDelay > 0

    Kết quả trung gian:
    - Total_Flights
    - Weather_Affected_Flights
    - Weather_Delay_Minutes
    """

    if "WeatherDelay" not in df.columns:
        raise KeyError(
            "Không tìm thấy cột WeatherDelay."
        )

    work = df[
        group_cols + ["WeatherDelay"]
    ].copy()

    work["WeatherDelay"] = (
        pd.to_numeric(
            work["WeatherDelay"],
            errors="coerce"
        )
        .fillna(0)
        .clip(lower=0)
    )

    # Tổng số chuyến trong từng nhóm
    total = (
        work.groupby(
            group_cols,
            dropna=False
        )
        .size()
        .rename("Total_Flights")
    )

    # Chỉ các chuyến bị ảnh hưởng bởi thời tiết
    weather_df = work[
        work["WeatherDelay"] > 0
    ]

    weather_affected = (
        weather_df.groupby(
            group_cols,
            dropna=False
        )
        .size()
        .rename(
            "Weather_Affected_Flights"
        )
    )

    weather_minutes = (
        weather_df.groupby(
            group_cols,
            dropna=False
        )["WeatherDelay"]
        .sum()
        .rename(
            "Weather_Delay_Minutes"
        )
    )

    result = pd.concat(
        [
            total,
            weather_affected,
            weather_minutes,
        ],
        axis=1
    ).reset_index()

    result[
        [
            "Weather_Affected_Flights",
            "Weather_Delay_Minutes",
        ]
    ] = (
        result[
            [
                "Weather_Affected_Flights",
                "Weather_Delay_Minutes",
            ]
        ]
        .fillna(0)
    )

    return result


# ============================================================
# 9. WEATHER DELAY - GỘP 12 THÁNG
# ============================================================

def combine_weather_summaries(
    summary_list,
    group_cols
):
    """
    Gộp WeatherDelay của 12 tháng và tính:
    - Weather_Affected_Rate
    - Avg_Weather_Delay
    """

    combined = pd.concat(
        summary_list,
        ignore_index=True
    )

    result = (
        combined
        .groupby(
            group_cols,
            dropna=False,
            as_index=False
        )
        .agg(
            Total_Flights=(
                "Total_Flights",
                "sum"
            ),
            Weather_Affected_Flights=(
                "Weather_Affected_Flights",
                "sum"
            ),
            Weather_Delay_Minutes=(
                "Weather_Delay_Minutes",
                "sum"
            ),
        )
    )

    result[
        "Weather_Affected_Rate"
    ] = (
        result[
            "Weather_Affected_Flights"
        ]
        .div(
            result["Total_Flights"]
            .replace(0, pd.NA)
        )
        * 100
    )

    result[
        "Avg_Weather_Delay"
    ] = (
        result[
            "Weather_Delay_Minutes"
        ]
        .div(
            result[
                "Weather_Affected_Flights"
            ]
            .replace(0, pd.NA)
        )
    )

    return result


# ============================================================
# 10. CHẠY PHÂN TÍCH
# ============================================================

def run_analysis():

    ANALYSIS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Lấy danh sách file features theo đúng thứ tự tháng
    # --------------------------------------------------------

    files = sorted(
        MONTHLY_FEATURES_DIR.glob(
            "*_features.parquet"
        ),
        key=get_month_number
    )

    if not files:

        raise FileNotFoundError(
            "Không tìm thấy file feature trong: "
            f"{MONTHLY_FEATURES_DIR}"
        )

    print(
        f"Tìm thấy {len(files)} file features."
    )

    # ========================================================
    # 10.1 BIẾN TÍCH LŨY KPI
    # ========================================================

    total_flights = 0
    valid_flights = 0
    delayed_flights = 0

    cancelled_flights = 0
    diverted_flights = 0

    arrival_delay_sum = 0
    delayed_minutes_sum = 0

    # ========================================================
    # 10.2 BIẾN TÍCH LŨY NGUYÊN NHÂN
    # ========================================================

    delay_cause_totals = {
        column: 0
        for column in DELAY_CAUSE_COLUMNS
    }

    # ========================================================
    # 10.3 CÁC BẢNG TRUNG GIAN DELAY
    # ========================================================

    airline_tables = []
    origin_tables = []
    destination_tables = []
    month_tables = []
    day_tables = []
    hour_tables = []
    time_group_tables = []
    route_tables = []
    heatmap_tables = []

    # ========================================================
    # 10.4 CÁC BẢNG TRUNG GIAN WEATHER
    # ========================================================

    weather_month_tables = []
    weather_airline_tables = []
    weather_origin_tables = []

    # ========================================================
    # 11. ĐỌC TỪNG THÁNG
    # ========================================================

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
        # Đọc dữ liệu
        # ----------------------------------------------------

        df = pd.read_parquet(
            file_path
        )

        print(
            f"Rows: {len(df):,}"
        )

        # ====================================================
        # 11.1 KPI
        # ====================================================

        kpi = analyze_kpi(
            df
        )

        total_flights += (
            kpi["Total_Flights"]
        )

        valid_flights += (
            kpi["Valid_Flights"]
        )

        delayed_flights += (
            kpi["Delayed_Flights"]
        )

        cancelled_flights += (
            kpi["Cancelled_Flights"]
        )

        diverted_flights += (
            kpi["Diverted_Flights"]
        )

        arrival_delay_sum += (
            kpi["Arrival_Delay_Sum"]
        )

        delayed_minutes_sum += (
            kpi["Delayed_Minutes_Sum"]
        )

        # ====================================================
        # 11.2 AIRLINE
        # ====================================================

        airline_group = [
            "Reporting_Airline"
        ]

        if "Airline_Name" in df.columns:

            airline_group.append(
                "Airline_Name"
            )

        airline_tables.append(
            summarize_delay(
                df,
                airline_group
            )
        )

        # ====================================================
        # 11.3 ORIGIN AIRPORT
        # ====================================================

        origin_group = [
            "Origin"
        ]

        if "Origin_Airport" in df.columns:

            origin_group.append(
                "Origin_Airport"
            )

        origin_tables.append(
            summarize_delay(
                df,
                origin_group
            )
        )

        # ====================================================
        # 11.4 DESTINATION AIRPORT
        # ====================================================

        destination_group = [
            "Dest"
        ]

        if "Dest_Airport" in df.columns:

            destination_group.append(
                "Dest_Airport"
            )

        destination_tables.append(
            summarize_delay(
                df,
                destination_group
            )
        )

        # ====================================================
        # 11.5 MONTH
        # ====================================================

        month_tables.append(
            summarize_delay(
                df,
                [
                    "Month",
                    "Month_Name",
                ]
            )
        )

        # ====================================================
        # 11.6 DAY OF WEEK
        # ====================================================

        day_tables.append(
            summarize_delay(
                df,
                [
                    "DayOfWeek",
                    "Day_Name",
                ]
            )
        )

        # ====================================================
        # 11.7 DEPARTURE HOUR
        # ====================================================

        hour_tables.append(
            summarize_delay(
                df,
                [
                    "Dep_Hour"
                ]
            )
        )

        # ====================================================
        # 11.8 TIME GROUP
        # ====================================================

        time_group_tables.append(
            summarize_delay(
                df,
                [
                    "Time_Group"
                ]
            )
        )

        # ====================================================
        # 11.9 ROUTE
        # ====================================================

        route_tables.append(
            summarize_delay(
                df,
                [
                    "Origin",
                    "Dest",
                    "Route",
                ]
            )
        )

        # ====================================================
        # 11.10 HEATMAP DAY × TIME
        # ====================================================

        heatmap_tables.append(
            summarize_delay(
                df,
                [
                    "DayOfWeek",
                    "Day_Name",
                    "Time_Group",
                ]
            )
        )

        # ====================================================
        # 11.11 DELAY CAUSES
        # ====================================================

        causes = analyze_delay_causes(
            df
        )

        for column, value in causes.items():

            delay_cause_totals[
                column
            ] += value

        # ====================================================
        # 11.12 WEATHER DELAY THEO THÁNG
        # ====================================================

        weather_month_tables.append(
            summarize_weather(
                df,
                [
                    "Month",
                    "Month_Name",
                ]
            )
        )

        # ====================================================
        # 11.13 WEATHER DELAY THEO HÃNG
        # ====================================================

        weather_airline_group = [
            "Reporting_Airline"
        ]

        if "Airline_Name" in df.columns:

            weather_airline_group.append(
                "Airline_Name"
            )

        weather_airline_tables.append(
            summarize_weather(
                df,
                weather_airline_group
            )
        )

        # ====================================================
        # 11.14 WEATHER DELAY THEO SÂN BAY ĐI
        # ====================================================

        weather_origin_group = [
            "Origin"
        ]

        if "Origin_Airport" in df.columns:

            weather_origin_group.append(
                "Origin_Airport"
            )

        weather_origin_tables.append(
            summarize_weather(
                df,
                weather_origin_group
            )
        )

        # ----------------------------------------------------
        # Giải phóng RAM
        # ----------------------------------------------------

        del df
        gc.collect()

    # ========================================================
    # 12. KPI TOÀN BỘ NĂM
    # ========================================================

    delay_rate = (
        delayed_flights
        / valid_flights
        * 100
        if valid_flights > 0
        else 0
    )

    cancel_rate = (
        cancelled_flights
        / total_flights
        * 100
        if total_flights > 0
        else 0
    )

    diverted_rate = (
        diverted_flights
        / total_flights
        * 100
        if total_flights > 0
        else 0
    )

    avg_arrival_delay = (
        arrival_delay_sum
        / valid_flights
        if valid_flights > 0
        else 0
    )

    avg_delay_minutes = (
        delayed_minutes_sum
        / delayed_flights
        if delayed_flights > 0
        else 0
    )

    kpi_df = pd.DataFrame(
        {
            "Metric": [
                "Total Flights",
                "Valid Flights",
                "Delayed Flights",
                "Delay Rate (%)",
                "Average Arrival Delay",
                "Average Delay Minutes",
                "Cancelled Flights",
                "Cancel Rate (%)",
                "Diverted Flights",
                "Diverted Rate (%)",
            ],

            "Value": [
                total_flights,
                valid_flights,
                delayed_flights,
                delay_rate,
                avg_arrival_delay,
                avg_delay_minutes,
                cancelled_flights,
                cancel_rate,
                diverted_flights,
                diverted_rate,
            ],
        }
    )

    # ========================================================
    # 13. GỘP AIRLINE
    # ========================================================

    airline_group = [
        "Reporting_Airline"
    ]

    if "Airline_Name" in airline_tables[0].columns:

        airline_group.append(
            "Airline_Name"
        )

    airline_df = combine_summaries(
        airline_tables,
        airline_group
    )

    # ========================================================
    # 14. GỘP ORIGIN
    # ========================================================

    origin_group = [
        "Origin"
    ]

    if "Origin_Airport" in origin_tables[0].columns:

        origin_group.append(
            "Origin_Airport"
        )

    origin_df = combine_summaries(
        origin_tables,
        origin_group
    )

    # ========================================================
    # 15. GỘP DESTINATION
    # ========================================================

    destination_group = [
        "Dest"
    ]

    if (
        "Dest_Airport"
        in destination_tables[0].columns
    ):

        destination_group.append(
            "Dest_Airport"
        )

    destination_df = combine_summaries(
        destination_tables,
        destination_group
    )

    # ========================================================
    # 16. MONTH
    # ========================================================

    month_df = combine_summaries(
        month_tables,
        [
            "Month",
            "Month_Name",
        ]
    )

    # ========================================================
    # 17. DAY
    # ========================================================

    day_df = combine_summaries(
        day_tables,
        [
            "DayOfWeek",
            "Day_Name",
        ]
    )

    # ========================================================
    # 18. HOUR
    # ========================================================

    hour_df = combine_summaries(
        hour_tables,
        [
            "Dep_Hour"
        ]
    )

    # ========================================================
    # 19. TIME GROUP
    # ========================================================

    time_group_df = combine_summaries(
        time_group_tables,
        [
            "Time_Group"
        ]
    )

    # ========================================================
    # 20. ROUTE
    # ========================================================

    route_df = combine_summaries(
        route_tables,
        [
            "Origin",
            "Dest",
            "Route",
        ]
    )

    # Chỉ giữ tuyến có đủ số chuyến
    route_df = route_df[
        route_df["Total_Flights"]
        >= MIN_ROUTE_FLIGHTS
    ].copy()

    # ========================================================
    # 21. HEATMAP
    # ========================================================

    heatmap_long_df = combine_summaries(
        heatmap_tables,
        [
            "DayOfWeek",
            "Day_Name",
            "Time_Group",
        ]
    )

    # ========================================================
    # 22. NGUYÊN NHÂN TRỄ
    # ========================================================

    cause_names = {
        "CarrierDelay":
            "Carrier",

        "WeatherDelay":
            "Weather",

        "NASDelay":
            "NAS",

        "SecurityDelay":
            "Security",

        "LateAircraftDelay":
            "Late Aircraft",
    }

    causes_df = pd.DataFrame(
        {
            "Delay_Cause": [
                cause_names[column]
                for column
                in DELAY_CAUSE_COLUMNS
            ],

            "Delay_Minutes": [
                delay_cause_totals[column]
                for column
                in DELAY_CAUSE_COLUMNS
            ],
        }
    )

    total_cause_minutes = (
        causes_df["Delay_Minutes"]
        .sum()
    )

    if total_cause_minutes > 0:

        causes_df["Percentage"] = (
            causes_df["Delay_Minutes"]
            / total_cause_minutes
            * 100
        )

    else:

        causes_df["Percentage"] = 0

    # ========================================================
    # 23. WEATHER DELAY THEO THÁNG
    # ========================================================

    weather_month_df = (
        combine_weather_summaries(
            weather_month_tables,
            [
                "Month",
                "Month_Name",
            ]
        )
    )

    # ========================================================
    # 24. WEATHER DELAY THEO HÃNG
    # ========================================================

    weather_airline_group = [
        "Reporting_Airline"
    ]

    if (
        "Airline_Name"
        in weather_airline_tables[0].columns
    ):

        weather_airline_group.append(
            "Airline_Name"
        )

    weather_airline_df = (
        combine_weather_summaries(
            weather_airline_tables,
            weather_airline_group
        )
    )

    # ========================================================
    # 25. WEATHER DELAY THEO SÂN BAY ĐI
    # ========================================================

    weather_origin_group = [
        "Origin"
    ]

    if (
        "Origin_Airport"
        in weather_origin_tables[0].columns
    ):

        weather_origin_group.append(
            "Origin_Airport"
        )

    weather_origin_df = (
        combine_weather_summaries(
            weather_origin_tables,
            weather_origin_group
        )
    )

    # ========================================================
    # 26. WEATHER KPI TOÀN NĂM
    # ========================================================

    total_weather_affected = int(
        weather_month_df[
            "Weather_Affected_Flights"
        ].sum()
    )

    total_weather_minutes = float(
        weather_month_df[
            "Weather_Delay_Minutes"
        ].sum()
    )

    avg_weather_delay = (
        total_weather_minutes
        / total_weather_affected
        if total_weather_affected > 0
        else 0
    )

    weather_affected_rate = (
        total_weather_affected
        / total_flights
        * 100
        if total_flights > 0
        else 0
    )

    weather_share = (
        delay_cause_totals[
            "WeatherDelay"
        ]
        / total_cause_minutes
        * 100
        if total_cause_minutes > 0
        else 0
    )

    weather_summary_df = pd.DataFrame(
        {
            "Metric": [
                "Weather Affected Flights",
                "Weather Affected Rate (%)",
                "Weather Delay Minutes",
                "Average Weather Delay",
                "Weather Share of Delay Causes (%)",
            ],
            "Value": [
                total_weather_affected,
                weather_affected_rate,
                total_weather_minutes,
                avg_weather_delay,
                weather_share,
            ],
        }
    )

    # ========================================================
    # 27. SORT DỮ LIỆU
    # ========================================================

    airline_df = (
        airline_df
        .sort_values(
            "Delay_Rate",
            ascending=False
        )
    )

    origin_df = (
        origin_df
        .sort_values(
            "Delay_Rate",
            ascending=False
        )
    )

    destination_df = (
        destination_df
        .sort_values(
            "Delay_Rate",
            ascending=False
        )
    )

    month_df = (
        month_df
        .sort_values(
            "Month"
        )
    )

    day_df = (
        day_df
        .sort_values(
            "DayOfWeek"
        )
    )

    hour_df = (
        hour_df
        .sort_values(
            "Dep_Hour"
        )
    )

    route_df = (
        route_df
        .sort_values(
            "Delay_Rate",
            ascending=False
        )
    )

    causes_df = (
        causes_df
        .sort_values(
            "Delay_Minutes",
            ascending=False
        )
    )

    weather_month_df = (
        weather_month_df
        .sort_values(
            "Month"
        )
    )

    weather_airline_df = (
        weather_airline_df
        .sort_values(
            "Weather_Delay_Minutes",
            ascending=False
        )
    )

    weather_origin_df = (
        weather_origin_df
        .sort_values(
            "Weather_Delay_Minutes",
            ascending=False
        )
    )

    # ========================================================
    # 28. SẮP XẾP TIME GROUP
    # ========================================================

    time_group_df[
        "Time_Group"
    ] = pd.Categorical(
        time_group_df["Time_Group"],
        categories=TIME_ORDER,
        ordered=True
    )

    time_group_df = (
        time_group_df
        .sort_values(
            "Time_Group"
        )
    )

    # ========================================================
    # 29. HEATMAP PIVOT
    # ========================================================

    heatmap_long_df[
        "Time_Group"
    ] = pd.Categorical(
        heatmap_long_df["Time_Group"],
        categories=TIME_ORDER,
        ordered=True
    )

    heatmap_df = (
        heatmap_long_df
        .pivot(
            index=[
                "DayOfWeek",
                "Day_Name",
            ],
            columns="Time_Group",
            values="Delay_Rate"
        )
        .reset_index()
        .sort_values(
            "DayOfWeek"
        )
    )

    # Đảm bảo đúng thứ tự các cột khung giờ
    heatmap_columns = [
        "DayOfWeek",
        "Day_Name",
    ] + [
        col
        for col in TIME_ORDER
        if col in heatmap_df.columns
    ]

    heatmap_df = heatmap_df[
        heatmap_columns
    ]

    # ========================================================
    # 30. XÓA CỘT TRUNG GIAN KHÔNG CẦN HIỂN THỊ
    # ========================================================

    final_tables = [
        airline_df,
        origin_df,
        destination_df,
        month_df,
        day_df,
        hour_df,
        time_group_df,
        route_df,
        heatmap_long_df,
    ]

    for table in final_tables:

        table.drop(
            columns=[
                "Arrival_Delay_Sum",
                "Delayed_Minutes_Sum",
            ],
            inplace=True,
            errors="ignore"
        )

    # ========================================================
    # 31. ROUND
    # ========================================================

    tables_to_round = [
        kpi_df,
        airline_df,
        origin_df,
        destination_df,
        month_df,
        day_df,
        hour_df,
        time_group_df,
        route_df,
        causes_df,
        heatmap_long_df,
        heatmap_df,
        weather_summary_df,
        weather_month_df,
        weather_airline_df,
        weather_origin_df,
    ]

    for table in tables_to_round:

        numeric_columns = (
            table
            .select_dtypes(
                include="number"
            )
            .columns
        )

        table[
            numeric_columns
        ] = (
            table[
                numeric_columns
            ]
            .round(2)
        )

    # ========================================================
    # 32. LƯU KẾT QUẢ
    # ========================================================

    kpi_df.to_csv(
        ANALYSIS_DIR
        / "kpi_summary.csv",
        index=False
    )

    airline_df.to_csv(
        ANALYSIS_DIR
        / "delay_by_airline.csv",
        index=False
    )

    origin_df.to_csv(
        ANALYSIS_DIR
        / "delay_by_origin.csv",
        index=False
    )

    destination_df.to_csv(
        ANALYSIS_DIR
        / "delay_by_destination.csv",
        index=False
    )

    month_df.to_csv(
        ANALYSIS_DIR
        / "delay_by_month.csv",
        index=False
    )

    day_df.to_csv(
        ANALYSIS_DIR
        / "delay_by_day.csv",
        index=False
    )

    hour_df.to_csv(
        ANALYSIS_DIR
        / "delay_by_hour.csv",
        index=False
    )

    time_group_df.to_csv(
        ANALYSIS_DIR
        / "delay_by_time_group.csv",
        index=False
    )

    route_df.to_csv(
        ANALYSIS_DIR
        / "delay_by_route.csv",
        index=False
    )

    causes_df.to_csv(
        ANALYSIS_DIR
        / "delay_causes.csv",
        index=False
    )

    heatmap_long_df.to_csv(
        ANALYSIS_DIR
        / "delay_heatmap_long.csv",
        index=False
    )

    heatmap_df.to_csv(
        ANALYSIS_DIR
        / "delay_heatmap.csv",
        index=False
    )

    # Weather outputs
    weather_summary_df.to_csv(
        ANALYSIS_DIR
        / "weather_summary.csv",
        index=False
    )

    weather_month_df.to_csv(
        ANALYSIS_DIR
        / "weather_delay_by_month.csv",
        index=False
    )

    weather_airline_df.to_csv(
        ANALYSIS_DIR
        / "weather_delay_by_airline.csv",
        index=False
    )

    weather_origin_df.to_csv(
        ANALYSIS_DIR
        / "weather_delay_by_origin.csv",
        index=False
    )

    # ========================================================
    # 33. HIỂN THỊ KẾT QUẢ
    # ========================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "PHÂN TÍCH HOÀN TẤT"
    )

    print(
        "=" * 70
    )

    print(
        f"\nKết quả lưu tại:\n"
        f"{ANALYSIS_DIR}"
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "KPI TOÀN BỘ NĂM 2025"
    )

    print(
        "=" * 70
    )

    print(
        kpi_df.to_string(
            index=False
        )
    )

    print(
        "\nTop 10 hãng có Delay Rate cao nhất:"
    )

    print(
        airline_df
        .head(10)
        .to_string(
            index=False
        )
    )

    print(
        "\nTop 10 tuyến có Delay Rate cao nhất "
        f"(>= {MIN_ROUTE_FLIGHTS} chuyến):"
    )

    print(
        route_df
        .head(10)
        .to_string(
            index=False
        )
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "WEATHER DELAY - TỔNG QUAN"
    )

    print(
        "=" * 70
    )

    print(
        weather_summary_df.to_string(
            index=False
        )
    )

    print(
        "\nWeatherDelay theo tháng:"
    )

    print(
        weather_month_df
        .to_string(
            index=False
        )
    )

    print(
        "\nTop 10 hãng có tổng WeatherDelay cao nhất:"
    )

    print(
        weather_airline_df
        .head(10)
        .to_string(
            index=False
        )
    )

    print(
        "\nTop 10 sân bay đi có tổng WeatherDelay cao nhất:"
    )

    print(
        weather_origin_df
        .head(10)
        .to_string(
            index=False
        )
    )


# ============================================================
# 34. MAIN
# ============================================================

if __name__ == "__main__":
    run_analysis()
