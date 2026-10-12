from pathlib import Path
import pandas as pd
import zipfile


# ============================================================
# 1. ĐƯỜNG DẪN
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

BTS_DIR = ROOT / "data" / "raw" / "bts"
REF_DIR = ROOT / "data" / "reference"


# ============================================================
# 2. CÁC CỘT CẦN DÙNG
# ============================================================

USE_COLUMNS = [
    "Year",
    "Quarter",
    "Month",
    "DayofMonth",
    "DayOfWeek",
    "FlightDate",

    "Reporting_Airline",
    "Flight_Number_Reporting_Airline",

    "Origin",
    "Dest",

    "CRSDepTime",
    "DepTime",
    "DepDelay",
    "DepDelayMinutes",

    "CRSArrTime",
    "ArrTime",
    "ArrDelay",
    "ArrDelayMinutes",

    "Cancelled",
    "CancellationCode",
    "Diverted",

    "Distance",

    "CarrierDelay",
    "WeatherDelay",
    "NASDelay",
    "SecurityDelay",
    "LateAircraftDelay",
]


# ============================================================
# 3. LẤY DANH SÁCH ZIP BTS
# ============================================================

def get_bts_zip_files():
    zip_files = sorted(
        BTS_DIR.glob("*.zip")
    )

    if not zip_files:
        raise FileNotFoundError(
            f"Không tìm thấy file ZIP trong: {BTS_DIR}"
        )

    return zip_files


# ============================================================
# 4. TÌM CSV BÊN TRONG ZIP
# ============================================================

def get_csv_name_from_zip(zip_path):
    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as z:

        csv_files = [
            name
            for name in z.namelist()
            if name.lower().endswith(".csv")
        ]

    if len(csv_files) == 0:
        raise ValueError(
            f"Không tìm thấy CSV trong {zip_path.name}"
        )

    if len(csv_files) > 1:
        raise ValueError(
            f"Có nhiều CSV trong {zip_path.name}: {csv_files}"
        )

    return csv_files[0]


# ============================================================
# 5. ĐỌC MỘT ZIP BTS
# ============================================================

def load_bts_zip(
    zip_path,
    usecols=USE_COLUMNS
):
    csv_name = get_csv_name_from_zip(
        zip_path
    )

    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as z:

        with z.open(
            csv_name
        ) as f:

            df = pd.read_csv(
                f,
                usecols=usecols,
                low_memory=False
            )

    return df


# ============================================================
# 6. ĐỌC REFERENCE DATA
# ============================================================

def load_reference_data():
    airlines_path = (
        REF_DIR / "airlines.csv"
    )

    airports_path = (
        REF_DIR / "airports.csv"
    )

    if not airlines_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {airlines_path}"
        )

    if not airports_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {airports_path}"
        )

    airlines = pd.read_csv(
        airlines_path
    )

    airports = pd.read_csv(
        airports_path
    )

    return airlines, airports


# ============================================================
# 7. TEST
# ============================================================

if __name__ == "__main__":

    files = get_bts_zip_files()

    print(
        f"Tìm thấy {len(files)} file BTS"
    )

    for file in files:
        print(file.name)

    print("\nĐọc thử file đầu tiên...")

    df = load_bts_zip(
        files[0]
    )

    print(
        f"Shape: {df.shape}"
    )

    print("\nColumns:")

    print(
        df.columns.tolist()
    )

    print("\n5 dòng đầu:")

    print(
        df.head()
    )