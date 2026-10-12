from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


# ============================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "analysis"
FIGURES_DIR = ROOT / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. BẢNG MÀU DÙNG CHUNG
# ============================================================

COLORS = {
    "navy": "#123A72",
    "blue": "#1976E9",
    "blue_light": "#74B9FF",
    "blue_soft": "#DCEEFF",
    "orange": "#FF9F43",
    "orange_light": "#FFC078",
    "orange_soft": "#FFF0E3",
    "teal": "#20BFA9",
    "teal_light": "#77D8CB",
    "red": "#EF5350",
    "text": "#23415F",
    "muted": "#6E879E",
    "grid": "#E8F0F7",
    "white": "#FFFFFF",
    "background": "#FFFFFF",
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


# ============================================================
# 3. STYLE CHUNG
# ============================================================

def apply_common_layout(fig, title=None):
    """Áp dụng style đồng bộ cho tất cả biểu đồ."""

    fig.update_layout(
        title={
            "text": title if title else fig.layout.title.text,
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 18,
                "color": COLORS["navy"],
                "family": "Arial",
            },
        },
        font={
            "family": "Arial",
            "color": COLORS["text"],
            "size": 12,
        },
        paper_bgcolor=COLORS["white"],
        plot_bgcolor=COLORS["white"],
        margin={"l": 55, "r": 45, "t": 70, "b": 55},
        hoverlabel={
            "bgcolor": COLORS["white"],
            "font_color": COLORS["text"],
            "bordercolor": COLORS["grid"],
        },
        legend={
            "title": None,
            "font": {"color": COLORS["text"]},
        },
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor=COLORS["grid"],
        tickfont={"color": COLORS["muted"]},
        title_font={"color": COLORS["muted"]},
    )

    fig.update_yaxes(
        gridcolor=COLORS["grid"],
        zeroline=False,
        linecolor=COLORS["grid"],
        tickfont={"color": COLORS["muted"]},
        title_font={"color": COLORS["muted"]},
    )

    return fig


# ============================================================
# 4. LOAD DỮ LIỆU PHÂN TÍCH
# ============================================================

def load_analysis_data():
    """Đọc các file CSV được tạo bởi analysis.py."""

    data = {
        "kpi": pd.read_csv(ANALYSIS_DIR / "kpi_summary.csv"),
        "airline": pd.read_csv(ANALYSIS_DIR / "delay_by_airline.csv"),
        "origin": pd.read_csv(ANALYSIS_DIR / "delay_by_origin.csv"),
        "destination": pd.read_csv(ANALYSIS_DIR / "delay_by_destination.csv"),
        "month": pd.read_csv(ANALYSIS_DIR / "delay_by_month.csv"),
        "day": pd.read_csv(ANALYSIS_DIR / "delay_by_day.csv"),
        "hour": pd.read_csv(ANALYSIS_DIR / "delay_by_hour.csv"),
        "time_group": pd.read_csv(ANALYSIS_DIR / "delay_by_time_group.csv"),
        "route": pd.read_csv(ANALYSIS_DIR / "delay_by_route.csv"),
        "causes": pd.read_csv(ANALYSIS_DIR / "delay_causes.csv"),
        "heatmap": pd.read_csv(ANALYSIS_DIR / "delay_heatmap.csv"),
    }

    optional_files = {
        "weather_summary": "weather_summary.csv",
        "weather_month": "weather_delay_by_month.csv",
        "weather_airline": "weather_delay_by_airline.csv",
        "weather_origin": "weather_delay_by_origin.csv",
    }

    for key, filename in optional_files.items():
        path = ANALYSIS_DIR / filename
        if path.exists():
            data[key] = pd.read_csv(path)

    return data


# ============================================================
# 5. HÀM HỖ TRỢ NHÃN HÃNG
# ============================================================

def build_airline_label(df):
    """
    Nếu Airline_Name bị thiếu do reference Kaggle 2015,
    dùng mã Reporting_Airline thay thế.
    """

    if "Airline_Name" not in df.columns:
        return df["Reporting_Airline"].astype("string")

    names = df["Airline_Name"].astype("string").str.strip()
    codes = df["Reporting_Airline"].astype("string").str.strip()

    missing_name = (
        names.isna()
        | names.eq("")
        | names.str.lower().eq("none")
        | names.str.lower().eq("nan")
    )

    return names.mask(missing_name, codes + " - Unknown")


# ============================================================
# 6. HÃNG HÀNG KHÔNG
# ============================================================

def chart_airline(data):
    airline = data["airline"].copy()
    airline["Airline_Display"] = build_airline_label(airline)

    top_airlines = (
        airline
        .sort_values("Delay_Rate", ascending=False)
        .head(15)
        .sort_values("Delay_Rate", ascending=True)
    )

    max_value = top_airlines["Delay_Rate"].max()
    colors = [
        COLORS["orange"] if value == max_value else COLORS["blue_light"]
        for value in top_airlines["Delay_Rate"]
    ]

    fig = go.Figure(
        go.Bar(
            x=top_airlines["Delay_Rate"],
            y=top_airlines["Airline_Display"],
            orientation="h",
            marker_color=colors,
            text=top_airlines["Delay_Rate"],
            texttemplate="%{text:.2f}%",
            textposition="outside",
            customdata=top_airlines[
                [
                    "Reporting_Airline",
                    "Total_Flights",
                    "Valid_Flights",
                    "Delayed_Flights",
                    "Avg_Delay_Minutes",
                ]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Mã hãng: %{customdata[0]}<br>"
                "Tổng chuyến: %{customdata[1]:,.0f}<br>"
                "Chuyến hợp lệ: %{customdata[2]:,.0f}<br>"
                "Chuyến chậm: %{customdata[3]:,.0f}<br>"
                "Tỷ lệ chậm: %{x:.2f}%<br>"
                "Trễ TB khi bị chậm: %{customdata[4]:.2f} phút"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Tỷ lệ chậm (%)",
        yaxis_title="",
        height=560,
    )

    return apply_common_layout(
        fig,
        "Tỷ lệ chậm chuyến theo hãng hàng không"
    )


# ============================================================
# 7. THEO THÁNG
# ============================================================

def chart_month(data):
    month = data["month"].sort_values("Month").copy()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=month["Month_Name"],
            y=month["Delay_Rate"],
            mode="lines+markers",
            line={"color": COLORS["blue"], "width": 3},
            marker={
                "size": 8,
                "color": COLORS["blue"],
                "line": {"color": COLORS["white"], "width": 2},
            },
            fill="tozeroy",
            fillcolor="rgba(25, 118, 233, 0.10)",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Tỷ lệ chậm: %{y:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Tháng",
        yaxis_title="Tỷ lệ chậm (%)",
    )

    return apply_common_layout(
        fig,
        "Xu hướng tỷ lệ chậm chuyến theo tháng"
    )


# ============================================================
# 8. THEO NGÀY TRONG TUẦN
# ============================================================

def chart_day(data):
    day = data["day"].sort_values("DayOfWeek").copy()
    max_value = day["Delay_Rate"].max()

    colors = [
        COLORS["orange"] if value == max_value else COLORS["blue_light"]
        for value in day["Delay_Rate"]
    ]

    fig = go.Figure(
        go.Bar(
            x=day["Day_Name"],
            y=day["Delay_Rate"],
            marker_color=colors,
            text=day["Delay_Rate"],
            texttemplate="%{text:.2f}%",
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Tỷ lệ chậm: %{y:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Ngày",
        yaxis_title="Tỷ lệ chậm (%)",
    )

    return apply_common_layout(
        fig,
        "Tỷ lệ chậm chuyến theo ngày trong tuần"
    )


# ============================================================
# 9. THEO GIỜ
# ============================================================

def chart_hour(data):
    hour = (
        data["hour"]
        .dropna(subset=["Dep_Hour"])
        .sort_values("Dep_Hour")
        .copy()
    )

    # Chỉ giữ 0-23 để tránh NA/giá trị ngoài miền xuất hiện trên trục.
    hour = hour[hour["Dep_Hour"].between(0, 23)].copy()

    fig = go.Figure(
        go.Scatter(
            x=hour["Dep_Hour"],
            y=hour["Delay_Rate"],
            mode="lines+markers",
            line={"color": COLORS["teal"], "width": 3},
            marker={"size": 7, "color": COLORS["teal"]},
            hovertemplate=(
                "<b>%{x}:00</b><br>"
                "Tỷ lệ chậm: %{y:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Giờ khởi hành dự kiến",
        yaxis_title="Tỷ lệ chậm (%)",
    )

    fig.update_xaxes(dtick=1, range=[0, 23])

    return apply_common_layout(
        fig,
        "Tỷ lệ chậm chuyến theo giờ khởi hành"
    )


# ============================================================
# 10. THEO KHUNG GIỜ
# ============================================================

def chart_time_group(data):
    time_group = data["time_group"].copy()

    time_group = time_group[
        time_group["Time_Group"].isin(TIME_ORDER)
    ].copy()

    time_group["Time_Group"] = pd.Categorical(
        time_group["Time_Group"],
        categories=TIME_ORDER,
        ordered=True,
    )

    time_group = time_group.sort_values("Time_Group")
    max_value = time_group["Delay_Rate"].max()

    colors = [
        COLORS["orange"] if value == max_value else COLORS["blue_light"]
        for value in time_group["Delay_Rate"]
    ]

    fig = go.Figure(
        go.Bar(
            x=time_group["Time_Group"].astype(str),
            y=time_group["Delay_Rate"],
            marker_color=colors,
            text=time_group["Delay_Rate"],
            texttemplate="%{text:.2f}%",
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Tỷ lệ chậm: %{y:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Khung giờ",
        yaxis_title="Tỷ lệ chậm (%)",
    )

    # Quan trọng: ép Plotly coi 00-05, 06-08... là category.
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=TIME_ORDER,
    )

    return apply_common_layout(
        fig,
        "Tỷ lệ chậm chuyến theo khung giờ"
    )


# ============================================================
# 11. SÂN BAY ĐI
# ============================================================

def chart_origin(data):
    origin = data["origin"].copy()

    top_origin = (
        origin
        .sort_values("Delay_Rate", ascending=False)
        .head(15)
        .sort_values("Delay_Rate", ascending=True)
    )

    max_value = top_origin["Delay_Rate"].max()
    colors = [
        COLORS["orange"] if value == max_value else COLORS["blue_light"]
        for value in top_origin["Delay_Rate"]
    ]

    fig = go.Figure(
        go.Bar(
            x=top_origin["Delay_Rate"],
            y=top_origin["Origin"],
            orientation="h",
            marker_color=colors,
            text=top_origin["Delay_Rate"],
            texttemplate="%{text:.2f}%",
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Tỷ lệ chậm: %{x:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Tỷ lệ chậm (%)",
        yaxis_title="Sân bay đi",
        height=560,
    )

    return apply_common_layout(
        fig,
        "Top sân bay đi có tỷ lệ chậm cao nhất"
    )


# ============================================================
# 12. SÂN BAY ĐẾN
# ============================================================

def chart_destination(data):
    destination = data["destination"].copy()

    top_destination = (
        destination
        .sort_values("Delay_Rate", ascending=False)
        .head(15)
        .sort_values("Delay_Rate", ascending=True)
    )

    max_value = top_destination["Delay_Rate"].max()
    colors = [
        COLORS["orange"] if value == max_value else COLORS["blue_light"]
        for value in top_destination["Delay_Rate"]
    ]

    fig = go.Figure(
        go.Bar(
            x=top_destination["Delay_Rate"],
            y=top_destination["Dest"],
            orientation="h",
            marker_color=colors,
            text=top_destination["Delay_Rate"],
            texttemplate="%{text:.2f}%",
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Tỷ lệ chậm: %{x:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Tỷ lệ chậm (%)",
        yaxis_title="Sân bay đến",
        height=560,
    )

    return apply_common_layout(
        fig,
        "Top sân bay đến có tỷ lệ chậm cao nhất"
    )


# ============================================================
# 13. TUYẾN BAY
# ============================================================

def chart_route(data):
    route = data["route"].copy()

    # Dashboard có thể tạo Delay_Rate với dtype object sau khi lọc.
    # Ép về numeric trước khi sort/nlargest để tránh TypeError.
    route["Delay_Rate"] = pd.to_numeric(
        route["Delay_Rate"],
        errors="coerce"
    )

    for column in [
        "Total_Flights",
        "Valid_Flights",
        "Delayed_Flights",
        "Avg_Delay_Minutes",
    ]:
        if column in route.columns:
            route[column] = pd.to_numeric(
                route[column],
                errors="coerce"
            )

    route = route.dropna(
        subset=["Delay_Rate", "Route"]
    )

    top_routes = (
        route
        .sort_values("Delay_Rate", ascending=False)
        .head(15)
        .copy()
    )

    if top_routes.empty:
        fig = go.Figure()
        return apply_common_layout(
            fig,
            "Top tuyến bay có tỷ lệ chậm cao nhất"
        )

    top_three_indices = set(
        top_routes.nlargest(3, "Delay_Rate").index
    )

    top_routes = top_routes.sort_values(
        "Delay_Rate",
        ascending=True
    )

    colors = [
        COLORS["orange"] if idx in top_three_indices else COLORS["blue_light"]
        for idx in top_routes.index
    ]

    fig = go.Figure(
        go.Bar(
            x=top_routes["Delay_Rate"],
            y=top_routes["Route"],
            orientation="h",
            marker_color=colors,
            text=top_routes["Delay_Rate"],
            texttemplate="%{text:.2f}%",
            textposition="outside",
            customdata=top_routes[
                ["Total_Flights", "Valid_Flights", "Delayed_Flights"]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Tổng chuyến: %{customdata[0]:,.0f}<br>"
                "Chuyến hợp lệ: %{customdata[1]:,.0f}<br>"
                "Chuyến chậm: %{customdata[2]:,.0f}<br>"
                "Tỷ lệ chậm: %{x:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Tỷ lệ chậm (%)",
        yaxis_title="Tuyến bay",
        height=620,
    )

    return apply_common_layout(
        fig,
        "Top tuyến bay có tỷ lệ chậm cao nhất"
    )


# ============================================================
# 14. NGUYÊN NHÂN CHẬM
# ============================================================

def chart_delay_causes(data):
    causes = (
        data["causes"]
        .sort_values("Delay_Minutes", ascending=False)
        .copy()
    )

    cause_color_map = {
        "Late Aircraft": COLORS["blue"],
        "Carrier": COLORS["orange"],
        "NAS": COLORS["orange_light"],
        "Weather": COLORS["teal"],
        "Security": COLORS["blue_light"],
    }

    colors = [
        cause_color_map.get(cause, COLORS["blue_light"])
        for cause in causes["Delay_Cause"]
    ]

    fig = go.Figure(
        go.Pie(
            labels=causes["Delay_Cause"],
            values=causes["Delay_Minutes"],
            hole=0.58,
            marker={"colors": colors},
            textinfo="percent",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Tổng phút chậm: %{value:,.0f}<br>"
                "Tỷ trọng: %{percent}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_annotation(
        text="<b>Nguyên nhân<br>chậm chuyến</b>",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 14, "color": COLORS["navy"]},
    )

    fig.update_layout(
        showlegend=True,
        legend={
            "orientation": "v",
            "x": 1.02,
            "y": 0.5,
            "yanchor": "middle",
        },
    )

    return apply_common_layout(
        fig,
        "Nguyên nhân chậm chuyến"
    )


# ============================================================
# 15. HEATMAP
# ============================================================

def chart_heatmap(data):
    df = data["heatmap"].copy()

    time_columns = [col for col in TIME_ORDER if col in df.columns]

    if "DayOfWeek" in df.columns:
        df = df.sort_values("DayOfWeek")

    z = (
        df[time_columns]
        .apply(pd.to_numeric, errors="coerce")
        .to_numpy()
    )

    y_labels = df["Day_Name"].astype(str).tolist()

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=time_columns,
            y=y_labels,
            colorscale=[
                [0.00, COLORS["blue_soft"]],
                [0.40, COLORS["blue_light"]],
                [0.70, COLORS["orange_light"]],
                [0.88, COLORS["orange"]],
                [1.00, COLORS["red"]],
            ],
            colorbar={"title": "Delay %"},
            text=z,
            texttemplate="%{text:.1f}%",
            hovertemplate=(
                "Ngày: %{y}<br>"
                "Khung giờ: %{x}<br>"
                "Tỷ lệ chậm: %{z:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    apply_common_layout(
        fig,
        "Heatmap tỷ lệ chậm chuyến (Ngày × Khung giờ)"
    )

    fig.update_layout(
        height=520,
        margin={"l": 80, "r": 80, "t": 80, "b": 70},
    )

    fig.update_xaxes(
        title="Khung giờ",
        type="category",
        categoryorder="array",
        categoryarray=TIME_ORDER,
    )

    fig.update_yaxes(
        title="Ngày",
        type="category",
        categoryorder="array",
        categoryarray=[
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ],
    )

    return fig


# ============================================================
# 16. WEATHER DELAY THEO THÁNG
# ============================================================

def chart_weather_month(data):
    if "weather_month" not in data:
        raise FileNotFoundError(
            "Chưa có weather_delay_by_month.csv. Hãy chạy analysis.py mới trước."
        )

    weather = data["weather_month"].sort_values("Month").copy()
    max_value = weather["Weather_Delay_Minutes"].max()

    colors = [
        COLORS["orange"] if value == max_value else COLORS["blue_light"]
        for value in weather["Weather_Delay_Minutes"]
    ]

    fig = go.Figure(
        go.Bar(
            x=weather["Month_Name"],
            y=weather["Weather_Delay_Minutes"],
            marker_color=colors,
            text=weather["Weather_Delay_Minutes"],
            texttemplate="%{text:,.0f}",
            textposition="outside",
            customdata=weather[
                [
                    "Weather_Affected_Flights",
                    "Weather_Affected_Rate",
                    "Avg_Weather_Delay",
                ]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Tổng phút chậm do thời tiết: %{y:,.0f}<br>"
                "Số chuyến bị ảnh hưởng: %{customdata[0]:,.0f}<br>"
                "Tỷ lệ chuyến bị ảnh hưởng: %{customdata[1]:.2f}%<br>"
                "WeatherDelay TB: %{customdata[2]:.2f} phút"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Tháng",
        yaxis_title="Tổng WeatherDelay (phút)",
        height=500,
    )

    return apply_common_layout(
        fig,
        "Tổng số phút chậm do thời tiết theo tháng"
    )


# ============================================================
# 17. WEATHER DELAY THEO HÃNG
# ============================================================

def chart_weather_airline(data):
    if "weather_airline" not in data:
        raise FileNotFoundError(
            "Chưa có weather_delay_by_airline.csv. Hãy chạy analysis.py mới trước."
        )

    weather = data["weather_airline"].copy()
    weather["Airline_Display"] = build_airline_label(weather)

    top_weather = (
        weather
        .sort_values("Weather_Delay_Minutes", ascending=False)
        .head(15)
        .sort_values("Weather_Delay_Minutes", ascending=True)
    )

    max_value = top_weather["Weather_Delay_Minutes"].max()
    colors = [
        COLORS["orange"] if value == max_value else COLORS["blue_light"]
        for value in top_weather["Weather_Delay_Minutes"]
    ]

    fig = go.Figure(
        go.Bar(
            x=top_weather["Weather_Delay_Minutes"],
            y=top_weather["Airline_Display"],
            orientation="h",
            marker_color=colors,
            text=top_weather["Weather_Delay_Minutes"],
            texttemplate="%{text:,.0f}",
            textposition="outside",
            customdata=top_weather[
                [
                    "Weather_Affected_Flights",
                    "Weather_Affected_Rate",
                    "Avg_Weather_Delay",
                ]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Tổng WeatherDelay: %{x:,.0f} phút<br>"
                "Số chuyến bị ảnh hưởng: %{customdata[0]:,.0f}<br>"
                "Tỷ lệ bị ảnh hưởng: %{customdata[1]:.2f}%<br>"
                "WeatherDelay TB: %{customdata[2]:.2f} phút"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Tổng WeatherDelay (phút)",
        yaxis_title="Hãng hàng không",
        height=580,
    )

    return apply_common_layout(
        fig,
        "Top hãng có tổng thời gian chậm do thời tiết cao nhất"
    )


# ============================================================
# 18. WEATHER DELAY THEO SÂN BAY ĐI
# ============================================================

def chart_weather_origin(data):
    if "weather_origin" not in data:
        raise FileNotFoundError(
            "Chưa có weather_delay_by_origin.csv. Hãy chạy analysis.py mới trước."
        )

    weather = data["weather_origin"].copy()

    top_weather = (
        weather
        .sort_values("Weather_Delay_Minutes", ascending=False)
        .head(15)
        .sort_values("Weather_Delay_Minutes", ascending=True)
    )

    max_value = top_weather["Weather_Delay_Minutes"].max()
    colors = [
        COLORS["orange"] if value == max_value else COLORS["teal_light"]
        for value in top_weather["Weather_Delay_Minutes"]
    ]

    fig = go.Figure(
        go.Bar(
            x=top_weather["Weather_Delay_Minutes"],
            y=top_weather["Origin"],
            orientation="h",
            marker_color=colors,
            text=top_weather["Weather_Delay_Minutes"],
            texttemplate="%{text:,.0f}",
            textposition="outside",
            customdata=top_weather[
                [
                    "Weather_Affected_Flights",
                    "Weather_Affected_Rate",
                    "Avg_Weather_Delay",
                ]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Tổng WeatherDelay: %{x:,.0f} phút<br>"
                "Số chuyến bị ảnh hưởng: %{customdata[0]:,.0f}<br>"
                "Tỷ lệ bị ảnh hưởng: %{customdata[1]:.2f}%<br>"
                "WeatherDelay TB: %{customdata[2]:.2f} phút"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Tổng WeatherDelay (phút)",
        yaxis_title="Sân bay đi",
        height=580,
    )

    return apply_common_layout(
        fig,
        "Top sân bay đi có tổng thời gian chậm do thời tiết cao nhất"
    )


# ============================================================
# 19. TẠO TẤT CẢ BIỂU ĐỒ
# ============================================================

def create_all_charts():
    data = load_analysis_data()

    charts = {
        "airline": chart_airline(data),
        "month": chart_month(data),
        "day": chart_day(data),
        "hour": chart_hour(data),
        "time_group": chart_time_group(data),
        "origin": chart_origin(data),
        "destination": chart_destination(data),
        "route": chart_route(data),
        "delay_causes": chart_delay_causes(data),
        "heatmap": chart_heatmap(data),
    }

    # Chỉ tạo biểu đồ Weather nếu analysis.py mới đã tạo dữ liệu.
    if "weather_month" in data:
        charts["weather_month"] = chart_weather_month(data)

    if "weather_airline" in data:
        charts["weather_airline"] = chart_weather_airline(data)

    if "weather_origin" in data:
        charts["weather_origin"] = chart_weather_origin(data)

    return charts


# ============================================================
# 20. LƯU HTML
# ============================================================

def save_charts(charts):
    for name, fig in charts.items():
        output_file = FIGURES_DIR / f"{name}.html"
        fig.write_html(output_file)
        print(f"Đã lưu: {output_file.name}")


# ============================================================
# 21. MAIN
# ============================================================

if __name__ == "__main__":
    charts = create_all_charts()
    save_charts(charts)

    print("\n" + "=" * 70)
    print("TẠO BIỂU ĐỒ HOÀN TẤT")
    print("=" * 70)
    print(f"Biểu đồ được lưu tại:\n{FIGURES_DIR}")
