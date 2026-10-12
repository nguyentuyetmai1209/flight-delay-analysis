from pathlib import Path
import re
import sys

import pandas as pd
import streamlit as st


# ============================================================
# 1. ĐƯỜNG DẪN
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from charts import (
    chart_airline,
    chart_month,
    chart_day,
    chart_hour,
    chart_time_group,
    chart_origin,
    chart_destination,
    chart_route,
    chart_delay_causes,
    chart_heatmap,
)


MONTHLY_FEATURES_DIR = ROOT / "data" / "processed" / "monthly_features"
ANALYSIS_DIR = ROOT / "data" / "analysis"


# ============================================================
# 2. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Flight Delay Analysis 2025",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 3. HELPER RENDER HTML
# ============================================================

def render_html(html):
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(
            html,
            unsafe_allow_html=True,
        )


# ============================================================
# 4. CSS
# ============================================================

render_html(
    """
<style>
:root {
    --navy: #123A72;
    --blue: #1976E9;
    --blue-light: #74B9FF;
    --blue-soft: #E8F3FF;
    --orange: #FF9F43;
    --orange-soft: #FFF0E3;
    --teal: #20BFA9;
    --teal-soft: #E0F8F4;
    --red: #EF5350;
    --red-soft: #FFE9EA;
    --text: #23415F;
    --muted: #6E879E;
    --border: #DCEAF7;
    --page: #F5FAFF;
    --white: #FFFFFF;
}

.stApp {
    background:
        linear-gradient(
            180deg,
            #F2F8FE 0%,
            #F8FBFF 55%,
            #FFFFFF 100%
        );
}

.block-container {
    max-width: 1520px;
    padding-top: 1.1rem;
    padding-bottom: 3rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #EAF5FF 0%,
            #F5FAFF 100%
        );
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--navy);
}

div[data-baseweb="select"] > div {
    border-radius: 11px;
    border-color: #D5E6F5;
    background: #FFFFFF;
}

.stButton > button,
[data-testid="stFormSubmitButton"] > button {
    width: 100%;
    min-height: 43px;
    border: none;
    border-radius: 11px;
    background:
        linear-gradient(
            135deg,
            #1976E9 0%,
            #2A8CF0 100%
        );
    color: #FFFFFF;
    font-weight: 700;
    box-shadow:
        0 5px 15px
        rgba(25, 118, 233, 0.20);
}

.stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    color: #FFFFFF;
    background:
        linear-gradient(
            135deg,
            #1264C8 0%,
            #1976E9 100%
        );
}

.dashboard-header {
    position: relative;
    overflow: hidden;
    min-height: 180px;
    display: flex;
    align-items: center;
    padding: 30px 38px;
    border: 1px solid var(--border);
    border-radius: 24px;
    background:
        linear-gradient(
            110deg,
            #FFFFFF 0%,
            #EFF8FF 55%,
            #DFF1FF 100%
        );
    box-shadow:
        0 10px 30px
        rgba(31, 95, 150, 0.08);
    margin-bottom: 28px;
}

.dashboard-header::after {
    content: "✈";
    position: absolute;
    right: 55px;
    top: 15px;
    font-size: 112px;
    line-height: 1;
    opacity: 0.09;
    transform: rotate(-8deg);
}

.dashboard-title {
    margin: 0;
    color: var(--navy);
    font-size: clamp(32px, 3vw, 46px);
    font-weight: 850;
    letter-spacing: -0.8px;
}

.dashboard-subtitle {
    margin: 10px 0 0 0;
    max-width: 780px;
    color: #52708E;
    font-size: 16px;
    line-height: 1.55;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 26px 0 14px 0;
}

.section-icon {
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: var(--blue-soft);
    font-size: 18px;
}

.section-title {
    color: var(--navy);
    font-size: 24px;
    font-weight: 800;
    line-height: 1.2;
}

.kpi-card {
    height: 164px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 20px;
    background: rgba(255, 255, 255, 0.97);
    border: 1px solid var(--border);
    border-radius: 20px;
    box-shadow:
        0 7px 24px
        rgba(35, 90, 140, 0.075);
}

.kpi-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    font-size: 23px;
}

.kpi-icon.blue {
    background: var(--blue-soft);
}

.kpi-icon.orange {
    background: var(--orange-soft);
}

.kpi-icon.teal {
    background: var(--teal-soft);
}

.kpi-icon.red {
    background: var(--red-soft);
}

.kpi-label {
    margin-top: 13px;
    color: var(--muted);
    font-size: 14px;
    font-weight: 700;
}

.kpi-value {
    margin-top: 4px;
    color: var(--navy);
    font-size: 30px;
    font-weight: 850;
    letter-spacing: -0.5px;
}

.filter-summary {
    margin: 4px 0 16px 0;
    padding: 11px 15px;
    border: 1px solid #DCEAF7;
    border-radius: 13px;
    background: #F7FBFF;
    color: #456987;
    font-size: 13px;
}

.info-pill {
    display: inline-flex;
    align-items: center;
    padding: 7px 12px;
    border-radius: 999px;
    background: #E8F3FF;
    color: #2B5D91;
    font-size: 13px;
    font-weight: 650;
    margin-bottom: 8px;
}

[data-testid="stPlotlyChart"] {
    overflow: hidden;
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 6px;
    box-shadow:
        0 6px 22px
        rgba(35, 90, 140, 0.065);
}

[data-testid="stDataFrame"] {
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 16px;
}

button[data-baseweb="tab"] {
    font-weight: 700;
}

.dashboard-footer {
    text-align: center;
    padding: 18px 0 8px 0;
    color: var(--muted);
    font-size: 13px;
}

hr {
    border: none;
    border-top: 1px solid #E2EDF7;
    margin: 26px 0;
}
</style>
"""
)


# ============================================================
# 5. CẤU HÌNH DỮ LIỆU
# ============================================================

MONTH_MAP = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

TIME_ORDER = [
    "00-05",
    "06-08",
    "09-11",
    "12-14",
    "15-17",
    "18-20",
    "21-23",
]

DELAY_CAUSE_COLUMNS = [
    "CarrierDelay",
    "WeatherDelay",
    "NASDelay",
    "SecurityDelay",
    "LateAircraftDelay",
]

READ_COLUMNS = [
    "Month",
    "Month_Name",
    "Reporting_Airline",
    "Airline_Name",
    "Origin",
    "Dest",
    "Origin_Airport",
    "Dest_Airport",
    "DayOfWeek",
    "Day_Name",
    "Dep_Hour",
    "Time_Group",
    "Route",
    "ArrDelay",
    "Valid_Arrival_Delay",
    "Is_Delayed",
    "Is_Cancelled",
    "Is_Diverted",
    *DELAY_CAUSE_COLUMNS,
]


# ============================================================
# 6. LOAD OPTIONS NHẸ TỪ DATA/ANALYSIS
# ============================================================

@st.cache_data
def load_filter_options():
    airline_df = pd.read_csv(
        ANALYSIS_DIR / "delay_by_airline.csv"
    )

    origin_df = pd.read_csv(
        ANALYSIS_DIR / "delay_by_origin.csv"
    )

    destination_df = pd.read_csv(
        ANALYSIS_DIR / "delay_by_destination.csv"
    )

    airline_col = (
        "Airline_Name"
        if "Airline_Name" in airline_df.columns
        else "Reporting_Airline"
    )

    airlines = (
        airline_df[airline_col]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )

    origins = (
        origin_df["Origin"]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )

    destinations = (
        destination_df["Dest"]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )

    return airlines, origins, destinations


# ============================================================
# 7. FILE MONTHLY FEATURES
# ============================================================

def extract_month_number(path):
    match = re.search(
        r"2025_(\d+)_features\.parquet$",
        path.name,
    )

    if match:
        return int(match.group(1))

    return 999


def get_feature_files(selected_month):
    if selected_month != "Tất cả":
        month_number = MONTH_MAP[selected_month]

        file_path = (
            MONTHLY_FEATURES_DIR
            / f"2025_{month_number}_features.parquet"
        )

        if not file_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy {file_path}"
            )

        return [file_path]

    files = sorted(
        MONTHLY_FEATURES_DIR.glob(
            "2025_*_features.parquet"
        ),
        key=extract_month_number,
    )

    if not files:
        raise FileNotFoundError(
            "Không tìm thấy file monthly_features."
        )

    return files


# ============================================================
# 8. SUMMARY DELAY
# ============================================================

def summarize_delay(df, group_cols):
    total = (
        df.groupby(
            group_cols,
            dropna=False,
        )
        .size()
        .rename("Total_Flights")
    )

    valid_df = df[
        df["Valid_Arrival_Delay"]
    ]

    valid = (
        valid_df.groupby(
            group_cols,
            dropna=False,
        )
        .size()
        .rename("Valid_Flights")
    )

    delayed = (
        valid_df.groupby(
            group_cols,
            dropna=False,
        )["Is_Delayed"]
        .sum()
        .rename("Delayed_Flights")
    )

    arrival_sum = (
        valid_df.groupby(
            group_cols,
            dropna=False,
        )["ArrDelay"]
        .sum()
        .rename("Arrival_Delay_Sum")
    )

    delayed_only = valid_df[
        valid_df["Is_Delayed"] == True
    ]

    delayed_sum = (
        delayed_only.groupby(
            group_cols,
            dropna=False,
        )["ArrDelay"]
        .sum()
        .rename("Delayed_Minutes_Sum")
    )

    result = pd.concat(
        [
            total,
            valid,
            delayed,
            arrival_sum,
            delayed_sum,
        ],
        axis=1,
    ).reset_index()

    numeric_fill = [
        "Valid_Flights",
        "Delayed_Flights",
        "Arrival_Delay_Sum",
        "Delayed_Minutes_Sum",
    ]

    result[numeric_fill] = (
        result[numeric_fill]
        .fillna(0)
    )

    return result


def combine_summaries(
    tables,
    group_cols,
):
    if not tables:
        return pd.DataFrame(
            columns=[
                *group_cols,
                "Total_Flights",
                "Valid_Flights",
                "Delayed_Flights",
                "Delay_Rate",
                "Avg_Arrival_Delay",
                "Avg_Delay_Minutes",
            ]
        )

    combined = pd.concat(
        tables,
        ignore_index=True,
    )

    result = (
        combined.groupby(
            group_cols,
            dropna=False,
            as_index=False,
        )
        .agg(
            Total_Flights=(
                "Total_Flights",
                "sum",
            ),
            Valid_Flights=(
                "Valid_Flights",
                "sum",
            ),
            Delayed_Flights=(
                "Delayed_Flights",
                "sum",
            ),
            Arrival_Delay_Sum=(
                "Arrival_Delay_Sum",
                "sum",
            ),
            Delayed_Minutes_Sum=(
                "Delayed_Minutes_Sum",
                "sum",
            ),
        )
    )

    result["Delay_Rate"] = (
        result["Delayed_Flights"]
        .div(
            result["Valid_Flights"]
            .replace(0, pd.NA)
        )
        * 100
    )

    result["Avg_Arrival_Delay"] = (
        result["Arrival_Delay_Sum"]
        .div(
            result["Valid_Flights"]
            .replace(0, pd.NA)
        )
    )

    result["Avg_Delay_Minutes"] = (
        result["Delayed_Minutes_Sum"]
        .div(
            result["Delayed_Flights"]
            .replace(0, pd.NA)
        )
    )

    return result


# ============================================================
# 9. BUILD DASHBOARD DATA THEO FILTER
# ============================================================

@st.cache_data(show_spinner=False)
def build_dashboard_data(
    selected_month,
    selected_airline,
    selected_origin,
    selected_destination,
):
    files = get_feature_files(
        selected_month
    )

    total_flights = 0
    valid_flights = 0
    delayed_flights = 0
    cancelled_flights = 0
    diverted_flights = 0
    arrival_delay_sum = 0.0
    delayed_minutes_sum = 0.0

    cause_totals = {
        col: 0.0
        for col in DELAY_CAUSE_COLUMNS
    }

    airline_tables = []
    origin_tables = []
    destination_tables = []
    month_tables = []
    day_tables = []
    hour_tables = []
    time_tables = []
    route_tables = []
    heatmap_tables = []

    for file_path in files:
        df = pd.read_parquet(
            file_path,
            columns=READ_COLUMNS,
        )

        # ----------------------------------------------
        # Filter Airline
        # ----------------------------------------------

        if selected_airline != "Tất cả":
            df = df[
                df["Airline_Name"]
                == selected_airline
            ]

        # ----------------------------------------------
        # Filter Origin
        # ----------------------------------------------

        if selected_origin != "Tất cả":
            df = df[
                df["Origin"]
                == selected_origin
            ]

        # ----------------------------------------------
        # Filter Destination
        # ----------------------------------------------

        if selected_destination != "Tất cả":
            df = df[
                df["Dest"]
                == selected_destination
            ]

        if df.empty:
            continue

        # ----------------------------------------------
        # KPI
        # ----------------------------------------------

        valid_df = df[
            df["Valid_Arrival_Delay"]
        ]

        delayed_df = valid_df[
            valid_df["Is_Delayed"] == True
        ]

        total_flights += len(df)
        valid_flights += len(valid_df)

        delayed_flights += int(
            valid_df["Is_Delayed"]
            .sum()
        )

        cancelled_flights += int(
            df["Is_Cancelled"]
            .sum()
        )

        diverted_flights += int(
            df["Is_Diverted"]
            .sum()
        )

        arrival_delay_sum += float(
            valid_df["ArrDelay"]
            .sum()
        )

        delayed_minutes_sum += float(
            delayed_df["ArrDelay"]
            .sum()
        )

        # ----------------------------------------------
        # GROUP TABLES
        # ----------------------------------------------

        airline_tables.append(
            summarize_delay(
                df,
                [
                    "Reporting_Airline",
                    "Airline_Name",
                ],
            )
        )

        origin_tables.append(
            summarize_delay(
                df,
                [
                    "Origin",
                    "Origin_Airport",
                ],
            )
        )

        destination_tables.append(
            summarize_delay(
                df,
                [
                    "Dest",
                    "Dest_Airport",
                ],
            )
        )

        month_tables.append(
            summarize_delay(
                df,
                [
                    "Month",
                    "Month_Name",
                ],
            )
        )

        day_tables.append(
            summarize_delay(
                df,
                [
                    "DayOfWeek",
                    "Day_Name",
                ],
            )
        )

        hour_tables.append(
            summarize_delay(
                df,
                ["Dep_Hour"],
            )
        )

        time_tables.append(
            summarize_delay(
                df,
                ["Time_Group"],
            )
        )

        route_tables.append(
            summarize_delay(
                df,
                [
                    "Origin",
                    "Dest",
                    "Route",
                ],
            )
        )

        heatmap_tables.append(
            summarize_delay(
                df,
                [
                    "DayOfWeek",
                    "Day_Name",
                    "Time_Group",
                ],
            )
        )

        # ----------------------------------------------
        # DELAY CAUSES
        # ----------------------------------------------

        for col in DELAY_CAUSE_COLUMNS:
            cause_totals[col] += float(
                df[col]
                .fillna(0)
                .sum()
            )

    # ====================================================
    # NO DATA
    # ====================================================

    if total_flights == 0:
        return None

    # ====================================================
    # KPI
    # ====================================================

    delay_rate = (
        delayed_flights
        / valid_flights
        * 100
        if valid_flights
        else 0
    )

    avg_arrival_delay = (
        arrival_delay_sum
        / valid_flights
        if valid_flights
        else 0
    )

    avg_delay_minutes = (
        delayed_minutes_sum
        / delayed_flights
        if delayed_flights
        else 0
    )

    cancel_rate = (
        cancelled_flights
        / total_flights
        * 100
    )

    diverted_rate = (
        diverted_flights
        / total_flights
        * 100
    )

    kpi = pd.DataFrame(
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

    # ====================================================
    # COMBINE
    # ====================================================

    airline = combine_summaries(
        airline_tables,
        [
            "Reporting_Airline",
            "Airline_Name",
        ],
    )

    origin = combine_summaries(
        origin_tables,
        [
            "Origin",
            "Origin_Airport",
        ],
    )

    destination = combine_summaries(
        destination_tables,
        [
            "Dest",
            "Dest_Airport",
        ],
    )

    month = combine_summaries(
        month_tables,
        [
            "Month",
            "Month_Name",
        ],
    )

    day = combine_summaries(
        day_tables,
        [
            "DayOfWeek",
            "Day_Name",
        ],
    )

    hour = combine_summaries(
        hour_tables,
        ["Dep_Hour"],
    )

    time_group = combine_summaries(
        time_tables,
        ["Time_Group"],
    )

    route = combine_summaries(
        route_tables,
        [
            "Origin",
            "Dest",
            "Route",
        ],
    )

    heatmap_long = combine_summaries(
        heatmap_tables,
        [
            "DayOfWeek",
            "Day_Name",
            "Time_Group",
        ],
    )

    # ----------------------------------------------
    # Route threshold
    # ----------------------------------------------

    filters_active = any(
        value != "Tất cả"
        for value in [
            selected_month,
            selected_airline,
            selected_origin,
            selected_destination,
        ]
    )

    min_route_flights = (
        20 if filters_active else 100
    )

    route = route[
        route["Total_Flights"]
        >= min_route_flights
    ].copy()

    # ----------------------------------------------
    # Delay causes
    # ----------------------------------------------

    cause_name_map = {
        "CarrierDelay": "Carrier",
        "WeatherDelay": "Weather",
        "NASDelay": "NAS",
        "SecurityDelay": "Security",
        "LateAircraftDelay": "Late Aircraft",
    }

    causes = pd.DataFrame(
        {
            "Delay_Cause": [
                cause_name_map[col]
                for col in DELAY_CAUSE_COLUMNS
            ],
            "Delay_Minutes": [
                cause_totals[col]
                for col in DELAY_CAUSE_COLUMNS
            ],
        }
    )

    total_cause_minutes = (
        causes["Delay_Minutes"]
        .sum()
    )

    causes["Percentage"] = (
        causes["Delay_Minutes"]
        / total_cause_minutes
        * 100
        if total_cause_minutes > 0
        else 0
    )

    # ----------------------------------------------
    # Heatmap
    # ----------------------------------------------

    if not heatmap_long.empty:
        heatmap = (
            heatmap_long.pivot(
                index=[
                    "DayOfWeek",
                    "Day_Name",
                ],
                columns="Time_Group",
                values="Delay_Rate",
            )
            .reset_index()
            .sort_values("DayOfWeek")
        )
    else:
        heatmap = pd.DataFrame(
            columns=[
                "DayOfWeek",
                "Day_Name",
                *TIME_ORDER,
            ]
        )

    # ----------------------------------------------
    # Sort
    # ----------------------------------------------

    airline = airline.sort_values(
        "Delay_Rate",
        ascending=False,
    )

    origin = origin.sort_values(
        "Delay_Rate",
        ascending=False,
    )

    destination = destination.sort_values(
        "Delay_Rate",
        ascending=False,
    )

    month = month.sort_values("Month")
    day = day.sort_values("DayOfWeek")
    hour = hour.sort_values("Dep_Hour")

    time_group["Time_Group"] = pd.Categorical(
        time_group["Time_Group"],
        categories=TIME_ORDER,
        ordered=True,
    )

    time_group = time_group.sort_values(
        "Time_Group"
    )

    route = route.sort_values(
        "Delay_Rate",
        ascending=False,
    )

    causes = causes.sort_values(
        "Delay_Minutes",
        ascending=False,
    )

    # ----------------------------------------------
    # Drop intermediate sums
    # ----------------------------------------------

    final_tables = [
        airline,
        origin,
        destination,
        month,
        day,
        hour,
        time_group,
        route,
        heatmap_long,
    ]

    for table in final_tables:
        table.drop(
            columns=[
                "Arrival_Delay_Sum",
                "Delayed_Minutes_Sum",
            ],
            errors="ignore",
            inplace=True,
        )

    return {
        "kpi": kpi,
        "airline": airline,
        "origin": origin,
        "destination": destination,
        "month": month,
        "day": day,
        "hour": hour,
        "time_group": time_group,
        "route": route,
        "causes": causes,
        "heatmap": heatmap,
        "min_route_flights": min_route_flights,
    }


# ============================================================
# 10. UI HELPERS
# ============================================================

def get_kpi(data, metric_name):
    result = data["kpi"].loc[
        data["kpi"]["Metric"]
        == metric_name,
        "Value",
    ]

    if result.empty:
        return 0

    return result.iloc[0]


def show_chart(fig):
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


def section_title(icon, title):
    render_html(
        f"""
<div class="section-header">
    <div class="section-icon">{icon}</div>
    <div class="section-title">{title}</div>
</div>
"""
    )


# ============================================================
# 11. FILTER OPTIONS
# ============================================================

airlines, origins, destinations = (
    load_filter_options()
)


# ============================================================
# 12. SIDEBAR FILTER FORM
# ============================================================

with st.sidebar:
    st.markdown("## ✈️ Flight Delay")
    st.caption("Dashboard Analytics · 2025")

    st.divider()

    st.markdown("### Bộ lọc dữ liệu")

    with st.form(
        "filter_form",
        clear_on_submit=False,
    ):
        selected_month = st.selectbox(
            "Month",
            [
                "Tất cả",
                *MONTH_MAP.keys(),
            ],
        )

        selected_airline = st.selectbox(
            "Airline (Hãng bay)",
            [
                "Tất cả",
                *airlines,
            ],
        )

        selected_origin = st.selectbox(
            "Origin (Sân bay đi)",
            [
                "Tất cả",
                *origins,
            ],
        )

        selected_destination = st.selectbox(
            "Destination (Sân bay đến)",
            [
                "Tất cả",
                *destinations,
            ],
        )

        submitted = st.form_submit_button(
            "↻ Áp dụng bộ lọc",
            use_container_width=True,
        )

    st.divider()

    st.caption(
        "Nguồn chính: BTS Reporting Carrier "
        "On-Time Performance"
    )


# ============================================================
# 13. BUILD FILTERED DATA
# ============================================================

with st.spinner(
    "Đang xử lý dữ liệu theo bộ lọc..."
):
    data = build_dashboard_data(
        selected_month,
        selected_airline,
        selected_origin,
        selected_destination,
    )


# ============================================================
# 14. HEADER
# ============================================================

render_html(
    """
<div class="dashboard-header">
    <div>
        <h1 class="dashboard-title">
            ✈️ Flight Delay Analysis 2025
        </h1>
        <p class="dashboard-subtitle">
            Phân tích tình trạng chậm chuyến bay theo hãng hàng không,
            sân bay, tuyến bay và thời gian.
        </p>
    </div>
</div>
"""
)


# ============================================================
# 15. FILTER SUMMARY
# ============================================================

render_html(
    f"""
<div class="filter-summary">
    <b>Bộ lọc hiện tại:</b>
    Month: {selected_month}
    &nbsp;·&nbsp;
    Airline: {selected_airline}
    &nbsp;·&nbsp;
    Origin: {selected_origin}
    &nbsp;·&nbsp;
    Destination: {selected_destination}
</div>
"""
)


# ============================================================
# 16. NO DATA
# ============================================================

if data is None:
    st.warning(
        "Không có chuyến bay phù hợp với "
        "tổ hợp bộ lọc hiện tại."
    )

    st.stop()


# ============================================================
# 17. KPI
# ============================================================

section_title(
    "▦",
    "Tổng quan",
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_html(
        f"""
<div class="kpi-card">
    <div class="kpi-icon blue">✈️</div>
    <div>
        <div class="kpi-label">Tổng số chuyến</div>
        <div class="kpi-value">{get_kpi(data, "Total Flights"):,.0f}</div>
    </div>
</div>
"""
    )

with col2:
    render_html(
        f"""
<div class="kpi-card">
    <div class="kpi-icon orange">◷</div>
    <div>
        <div class="kpi-label">Tỷ lệ chậm</div>
        <div class="kpi-value">{get_kpi(data, "Delay Rate (%)"):.2f}%</div>
    </div>
</div>
"""
    )

with col3:
    render_html(
        f"""
<div class="kpi-card">
    <div class="kpi-icon teal">⌛</div>
    <div>
        <div class="kpi-label">Trễ trung bình</div>
        <div class="kpi-value">{get_kpi(data, "Average Delay Minutes"):.1f} phút</div>
    </div>
</div>
"""
    )

with col4:
    render_html(
        f"""
<div class="kpi-card">
    <div class="kpi-icon red">✕</div>
    <div>
        <div class="kpi-label">Tỷ lệ hủy</div>
        <div class="kpi-value">{get_kpi(data, "Cancel Rate (%)"):.2f}%</div>
    </div>
</div>
"""
    )


# ============================================================
# 18. THỜI GIAN
# ============================================================

section_title(
    "◷",
    "Phân tích theo thời gian",
)

col1, col2 = st.columns(
    [1.15, 1],
    gap="large",
)

with col1:
    show_chart(
        chart_month(data)
    )

with col2:
    show_chart(
        chart_day(data)
    )

col1, col2 = st.columns(
    2,
    gap="large",
)

with col1:
    show_chart(
        chart_time_group(data)
    )

with col2:
    show_chart(
        chart_hour(data)
    )

show_chart(
    chart_heatmap(data)
)


# ============================================================
# 19. HÃNG
# ============================================================

section_title(
    "✈",
    "Hãng hàng không",
)

render_html(
    """
<div class="info-pill">
    Cam = giá trị cao nhất · Xanh = các giá trị còn lại
</div>
"""
)

show_chart(
    chart_airline(data)
)


# ============================================================
# 20. SÂN BAY
# ============================================================

section_title(
    "⌖",
    "Sân bay",
)

col1, col2 = st.columns(
    2,
    gap="large",
)

with col1:
    show_chart(
        chart_origin(data)
    )

with col2:
    show_chart(
        chart_destination(data)
    )


# ============================================================
# 21. TUYẾN + NGUYÊN NHÂN
# ============================================================

section_title(
    "↝",
    "Tuyến bay và nguyên nhân chậm",
)

col1, col2 = st.columns(
    [1.2, 1],
    gap="large",
)

with col1:
    if data["route"].empty:
        st.info(
            "Không có tuyến nào đạt ngưỡng "
            f"{data['min_route_flights']} chuyến "
            "với bộ lọc hiện tại."
        )
    else:
        show_chart(
            chart_route(data)
        )

with col2:
    show_chart(
        chart_delay_causes(data)
    )


# ============================================================
# 22. TABLES
# ============================================================

section_title(
    "▤",
    "Dữ liệu chi tiết",
)

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "✈️ Hãng hàng không",
        "📍 Sân bay đi",
        "📍 Sân bay đến",
        "🔗 Tuyến bay",
    ]
)

with tab1:
    st.dataframe(
        data["airline"],
        use_container_width=True,
        hide_index=True,
    )

with tab2:
    st.dataframe(
        data["origin"],
        use_container_width=True,
        hide_index=True,
    )

with tab3:
    st.dataframe(
        data["destination"],
        use_container_width=True,
        hide_index=True,
    )

with tab4:
    st.dataframe(
        data["route"],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 23. FOOTER
# ============================================================

st.divider()

render_html(
    """
<div class="dashboard-footer">
    Flight Delay Analysis 2025
    · BTS Reporting Carrier On-Time Performance
</div>
"""
)
