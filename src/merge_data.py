from pathlib import Path
import gc
import pandas as pd

from load_data import load_reference_data


# ============================================================
# 1. ĐƯỜNG DẪN
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT / "data" / "processed"

MONTHLY_CLEAN_DIR = PROCESSED_DIR / "monthly_clean"
MONTHLY_ENRICHED_DIR = PROCESSED_DIR / "monthly_enriched"


# ============================================================
# 2. CLEAN AIRLINES REFERENCE
# ============================================================

def clean_airlines_reference(airlines):
    airlines = airlines.copy()

    required = [
        "IATA_CODE",
        "AIRLINE",
    ]

    missing = [
        col
        for col in required
        if col not in airlines.columns
    ]

    if missing:
        raise KeyError(
            "airlines.csv thiếu cột: "
            + ", ".join(missing)
        )

    airlines = airlines[
        [
            "IATA_CODE",
            "AIRLINE",
        ]
    ].copy()

    airlines["IATA_CODE"] = (
        airlines["IATA_CODE"]
        .astype("string")
        .str.strip()
        .str.upper()
        .replace("", pd.NA)
    )

    airlines["AIRLINE"] = (
        airlines["AIRLINE"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    airlines = (
        airlines
        .dropna(subset=["IATA_CODE"])
        .drop_duplicates(
            subset=["IATA_CODE"],
            keep="first"
        )
        .reset_index(drop=True)
    )

    return airlines


# ============================================================
# 3. CLEAN AIRPORTS REFERENCE
# ============================================================

def clean_airports_reference(airports):
    airports = airports.copy()

    required = [
        "IATA_CODE",
        "AIRPORT",
    ]

    missing = [
        col
        for col in required
        if col not in airports.columns
    ]

    if missing:
        raise KeyError(
            "airports.csv thiếu cột: "
            + ", ".join(missing)
        )

    possible_columns = [
        "IATA_CODE",
        "AIRPORT",
        "CITY",
        "STATE",
        "COUNTRY",
        "LATITUDE",
        "LONGITUDE",
    ]

    available_columns = [
        col
        for col in possible_columns
        if col in airports.columns
    ]

    airports = airports[
        available_columns
    ].copy()

    airports["IATA_CODE"] = (
        airports["IATA_CODE"]
        .astype("string")
        .str.strip()
        .str.upper()
        .replace("", pd.NA)
    )

    for col in [
        "AIRPORT",
        "CITY",
        "STATE",
        "COUNTRY",
    ]:
        if col in airports.columns:
            airports[col] = (
                airports[col]
                .astype("string")
                .str.strip()
                .replace("", pd.NA)
            )

    for col in [
        "LATITUDE",
        "LONGITUDE",
    ]:
        if col in airports.columns:
            airports[col] = pd.to_numeric(
                airports[col],
                errors="coerce"
            )

    airports = (
        airports
        .dropna(subset=["IATA_CODE"])
        .drop_duplicates(
            subset=["IATA_CODE"],
            keep="first"
        )
        .reset_index(drop=True)
    )

    return airports


# ============================================================
# 4. TẠO REFERENCE CHO ORIGIN
# ============================================================

def make_origin_reference(airports):
    rename_map = {
        "IATA_CODE": "Origin",
        "AIRPORT": "Origin_Airport",
        "CITY": "Origin_City",
        "STATE": "Origin_State",
        "COUNTRY": "Origin_Country",
        "LATITUDE": "Origin_Latitude",
        "LONGITUDE": "Origin_Longitude",
    }

    existing_map = {
        key: value
        for key, value in rename_map.items()
        if key in airports.columns
    }

    return airports.rename(
        columns=existing_map
    ).copy()


# ============================================================
# 5. TẠO REFERENCE CHO DEST
# ============================================================

def make_dest_reference(airports):
    rename_map = {
        "IATA_CODE": "Dest",
        "AIRPORT": "Dest_Airport",
        "CITY": "Dest_City",
        "STATE": "Dest_State",
        "COUNTRY": "Dest_Country",
        "LATITUDE": "Dest_Latitude",
        "LONGITUDE": "Dest_Longitude",
    }

    existing_map = {
        key: value
        for key, value in rename_map.items()
        if key in airports.columns
    }

    return airports.rename(
        columns=existing_map
    ).copy()


# ============================================================
# 6. MERGE MỘT THÁNG
# ============================================================

def merge_month(
    flights,
    airlines,
    origin_airports,
    dest_airports
):
    before = len(flights)

    # Airline
    flights = flights.merge(
        airlines,
        how="left",
        left_on="Reporting_Airline",
        right_on="IATA_CODE",
        validate="m:1"
    )

    flights = flights.rename(
        columns={
            "AIRLINE": "Airline_Name"
        }
    )

    flights = flights.drop(
        columns=["IATA_CODE"]
    )

    # Origin
    flights = flights.merge(
        origin_airports,
        how="left",
        on="Origin",
        validate="m:1"
    )

    # Destination
    flights = flights.merge(
        dest_airports,
        how="left",
        on="Dest",
        validate="m:1"
    )

    if len(flights) != before:
        raise ValueError(
            "Số dòng thay đổi sau merge. "
            "Cần kiểm tra duplicate key trong reference."
        )

    return flights


# ============================================================
# 7. MERGE TẤT CẢ CÁC THÁNG
# ============================================================

def merge_all_months():
    MONTHLY_ENRICHED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    clean_files = sorted(
        MONTHLY_CLEAN_DIR.glob(
            "*_clean.parquet"
        )
    )

    if not clean_files:
        raise FileNotFoundError(
            f"Không tìm thấy file clean trong "
            f"{MONTHLY_CLEAN_DIR}"
        )

    print(
        f"Tìm thấy {len(clean_files)} file clean."
    )

    # Load reference
    airlines, airports = (
        load_reference_data()
    )

    print(
        f"Raw airlines: {airlines.shape}"
    )

    print(
        f"Raw airports: {airports.shape}"
    )

    # Clean reference
    airlines = clean_airlines_reference(
        airlines
    )

    airports = clean_airports_reference(
        airports
    )

    print(
        f"Clean airlines: {airlines.shape}"
    )

    print(
        f"Clean airports: {airports.shape}"
    )

    origin_airports = (
        make_origin_reference(
            airports
        )
    )

    dest_airports = (
        make_dest_reference(
            airports
        )
    )

    output_files = []

    for index, file_path in enumerate(
        clean_files,
        start=1
    ):
        print(
            "\n"
            + "=" * 70
        )

        print(
            f"[{index}/{len(clean_files)}] "
            f"{file_path.name}"
        )

        print(
            "=" * 70
        )

        flights = pd.read_parquet(
            file_path
        )

        print(
            f"Input: "
            f"{flights.shape[0]:,} rows, "
            f"{flights.shape[1]} columns"
        )

        enriched = merge_month(
            flights,
            airlines,
            origin_airports,
            dest_airports
        )

        # Kiểm tra unmatched
        airline_unmatched = (
            enriched["Airline_Name"]
            .isna()
            .sum()
        )

        origin_unmatched = (
            enriched["Origin_Airport"]
            .isna()
            .sum()
            if "Origin_Airport"
            in enriched.columns
            else 0
        )

        dest_unmatched = (
            enriched["Dest_Airport"]
            .isna()
            .sum()
            if "Dest_Airport"
            in enriched.columns
            else 0
        )

        print(
            f"Airline unmatched: "
            f"{airline_unmatched:,}"
        )

        print(
            f"Origin unmatched: "
            f"{origin_unmatched:,}"
        )

        print(
            f"Dest unmatched: "
            f"{dest_unmatched:,}"
        )

        output_name = (
            file_path.name
            .replace(
                "_clean.parquet",
                "_enriched.parquet"
            )
        )

        output_file = (
            MONTHLY_ENRICHED_DIR
            / output_name
        )

        enriched.to_parquet(
            output_file,
            index=False
        )

        print(
            f"Đã lưu: "
            f"{output_file.name}"
        )

        output_files.append(
            output_file
        )

        del flights
        del enriched

        gc.collect()

    return output_files


# ============================================================
# 8. MAIN
# ============================================================

if __name__ == "__main__":

    output_files = (
        merge_all_months()
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "MERGE HOÀN TẤT"
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