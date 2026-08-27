import pandas as pd
import numpy as np
from pathlib import Path


# Reproducibility
RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)


# ---------------------------------------------------------
# 1. Network configuration
# ---------------------------------------------------------

CITY_STATIONS = {
    "Delhi NCR": 18,
    "Mumbai": 18,
    "Bengaluru": 18,
    "Hyderabad": 14,
    "Chennai": 14,
    "Pune": 14,
    "Ahmedabad": 10,
    "Kolkata": 10,
    "Jaipur": 9,
    "Kochi": 8,
    "Chandigarh": 8,
    "Lucknow": 9,
}

STATION_TYPE_SHARE = {
    "Highway": 0.15,
    "Mall_Retail": 0.20,
    "Office_Commercial": 0.20,
    "Residential": 0.20,
    "Hotel": 0.10,
    "Fleet": 0.10,
    "Transit_Public": 0.05,
}


# City-level demand index.
# This is a simulation parameter, NOT a claim about Tata Power.
CITY_DEMAND_INDEX = {
    "Delhi NCR": 1.20,
    "Mumbai": 1.18,
    "Bengaluru": 1.22,
    "Hyderabad": 1.05,
    "Chennai": 1.03,
    "Pune": 1.08,
    "Ahmedabad": 0.92,
    "Kolkata": 0.88,
    "Jaipur": 0.82,
    "Kochi": 0.78,
    "Chandigarh": 0.80,
    "Lucknow": 0.75,
}


# ---------------------------------------------------------
# 2. Generate station records
# ---------------------------------------------------------

stations = []

station_number = 1

for city, station_count in CITY_STATIONS.items():

    # Create the station-type distribution for this city.
    station_types = list(STATION_TYPE_SHARE.keys())
    probabilities = list(STATION_TYPE_SHARE.values())

    # Assign station types using a controlled network-wide mix.
# This avoids accidental over/under-representation caused by
# random sampling while retaining randomness in station characteristics.

TOTAL_STATIONS = sum(CITY_STATIONS.values())

TARGET_STATION_COUNTS = {
    "Highway": 23,
    "Mall_Retail": 30,
    "Office_Commercial": 30,
    "Residential": 30,
    "Hotel": 15,
    "Fleet": 15,
    "Transit_Public": 7,
}

all_station_types = []

for station_type, count in TARGET_STATION_COUNTS.items():
    all_station_types.extend([station_type] * count)

# Randomize the order of station types across the network.
all_station_types = rng.permutation(all_station_types)

# Assign the appropriate number to each city.
city_start = 0
assigned_city_types = {}

for city, count in CITY_STATIONS.items():
    city_end = city_start + count
    assigned_city_types[city] = all_station_types[city_start:city_end]
    city_start = city_end

    for station_type in assigned_city_types[city]:

        station_id = f"ST{station_number:04d}"

        # Number of chargers varies by station type.
        charger_ranges = {
            "Highway": (8, 16),
            "Mall_Retail": (6, 12),
            "Office_Commercial": (6, 12),
            "Residential": (4, 10),
            "Hotel": (4, 8),
            "Fleet": (8, 14),
            "Transit_Public": (6, 12),
        }

        min_chargers, max_chargers = charger_ranges[station_type]

        charger_count = int(
            rng.integers(min_chargers, max_chargers + 1)
        )

        # Station-level demand varies around the city's baseline.
        demand_index = CITY_DEMAND_INDEX[city]

        baseline_utilization = np.clip(
            0.25
            + 0.20 * (demand_index - 0.75)
            + rng.normal(0, 0.06),
            0.15,
            0.75,
        )

        # Peak concentration differs by station type.
        peak_factors = {
            "Highway": 0.90,
            "Mall_Retail": 1.10,
            "Office_Commercial": 1.25,
            "Residential": 1.15,
            "Hotel": 0.95,
            "Fleet": 1.20,
            "Transit_Public": 1.05,
        }

        peak_demand_factor = np.clip(
            peak_factors[station_type] + rng.normal(0, 0.08),
            0.70,
            1.40,
        )

        # Operational reliability.
        operational_reliability = np.clip(
            rng.normal(0.97, 0.015),
            0.90,
            0.995,
        )

        # Representative capacity estimate.
        avg_daily_capacity_kwh = (
            charger_count
            * rng.uniform(80, 130)
        )

        stations.append({
            "station_id": station_id,
            "city": city,
            "station_type": station_type,
            "charger_count": charger_count,
            "avg_daily_capacity_kwh": round(avg_daily_capacity_kwh, 2),
            "baseline_utilization": round(baseline_utilization, 4),
            "peak_demand_factor": round(peak_demand_factor, 4),
            "operational_reliability": round(
                operational_reliability, 4
            ),
        })

        station_number += 1


# ---------------------------------------------------------
# 3. Create dataframe
# ---------------------------------------------------------

stations_df = pd.DataFrame(stations)


# ---------------------------------------------------------
# 4. Validation checks
# ---------------------------------------------------------

assert len(stations_df) == 150, (
    f"Expected 150 stations, got {len(stations_df)}"
)

assert stations_df["station_id"].is_unique

assert stations_df["charger_count"].min() >= 4

assert stations_df["baseline_utilization"].between(
    0.15, 0.75
).all()


# ---------------------------------------------------------
# 5. Save
# ---------------------------------------------------------

output_path = Path("data/raw/stations.csv")

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

stations_df.to_csv(
    output_path,
    index=False
)


# ---------------------------------------------------------
# 6. Print validation summary
# ---------------------------------------------------------

print("\nStation dataset created successfully.")
print(f"Rows: {len(stations_df)}")
print(f"Columns: {len(stations_df.columns)}")

print("\nStations by city:")
print(
    stations_df["city"]
    .value_counts()
    .sort_index()
)

print("\nStations by type:")
print(
    stations_df["station_type"]
    .value_counts()
    .sort_index()
)

print("\nTotal chargers:")
print(stations_df["charger_count"].sum())

print("\nAverage baseline utilization:")
print(
    round(
        stations_df["baseline_utilization"].mean(),
        3
    )
)

print(f"\nSaved to: {output_path}")