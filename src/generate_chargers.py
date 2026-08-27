import pandas as pd
import numpy as np
from pathlib import Path


# ---------------------------------------------------------
# 1. Setup
# ---------------------------------------------------------

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

STATIONS_PATH = Path("data/raw/stations.csv")
OUTPUT_PATH = Path("data/raw/chargers.csv")


# ---------------------------------------------------------
# 2. Charger configuration by station type
# ---------------------------------------------------------
# Probabilities are simulation assumptions.
# They are designed to make charger composition differ
# realistically across station archetypes.

CHARGER_MIX = {
    "Highway": {
        "AC": 0.10,
        "DC_Fast": 0.55,
        "DC_Ultra": 0.35,
    },
    "Mall_Retail": {
        "AC": 0.35,
        "DC_Fast": 0.50,
        "DC_Ultra": 0.15,
    },
    "Office_Commercial": {
        "AC": 0.45,
        "DC_Fast": 0.45,
        "DC_Ultra": 0.10,
    },
    "Residential": {
        "AC": 0.65,
        "DC_Fast": 0.30,
        "DC_Ultra": 0.05,
    },
    "Hotel": {
        "AC": 0.55,
        "DC_Fast": 0.35,
        "DC_Ultra": 0.10,
    },
    "Fleet": {
        "AC": 0.10,
        "DC_Fast": 0.65,
        "DC_Ultra": 0.25,
    },
    "Transit_Public": {
        "AC": 0.25,
        "DC_Fast": 0.55,
        "DC_Ultra": 0.20,
    },
}


# ---------------------------------------------------------
# 3. Charger specifications
# ---------------------------------------------------------

CHARGER_SPECS = {
    "AC": {
        "power_options": [7, 11, 22],
        "power_probabilities": [0.30, 0.35, 0.35],
        "connector": "Type2",
    },
    "DC_Fast": {
        "power_options": [30, 50, 60],
        "power_probabilities": [0.20, 0.50, 0.30],
        "connector": "CCS2",
    },
    "DC_Ultra": {
        "power_options": [120, 150, 180],
        "power_probabilities": [0.25, 0.50, 0.25],
        "connector": "CCS2",
    },
}


# ---------------------------------------------------------
# 4. Load stations
# ---------------------------------------------------------

stations_df = pd.read_csv(STATIONS_PATH)

assert len(stations_df) == 150
assert stations_df["station_id"].is_unique


# ---------------------------------------------------------
# 5. Generate chargers
# ---------------------------------------------------------

chargers = []

for _, station in stations_df.iterrows():

    station_id = station["station_id"]
    station_type = station["station_type"]
    charger_count = int(station["charger_count"])

    charger_types = list(CHARGER_MIX[station_type].keys())
    charger_probabilities = list(
        CHARGER_MIX[station_type].values()
    )

    assigned_types = rng.choice(
        charger_types,
        size=charger_count,
        p=charger_probabilities
    )

    for charger_number, charger_type in enumerate(
        assigned_types,
        start=1
    ):

        specs = CHARGER_SPECS[charger_type]

        power_kw = rng.choice(
            specs["power_options"],
            p=specs["power_probabilities"]
        )

        # Small charger-level variation around the
        # station's operational reliability.
        station_reliability = float(
            station["operational_reliability"]
        )

        availability_rate = np.clip(
            station_reliability
            + rng.normal(0, 0.008),
            0.88,
            0.995,
        )

        charger_id = (
            f"{station_id}-C{charger_number:02d}"
        )

        chargers.append({
            "charger_id": charger_id,
            "station_id": station_id,
            "station_type": station_type,
            "charger_type": charger_type,
            "power_kw": int(power_kw),
            "connector_type": specs["connector"],
            "availability_rate": round(
                availability_rate,
                4
            ),
        })


# ---------------------------------------------------------
# 6. Create dataframe
# ---------------------------------------------------------

chargers_df = pd.DataFrame(chargers)


# ---------------------------------------------------------
# 7. Validation
# ---------------------------------------------------------

expected_chargers = int(
    stations_df["charger_count"].sum()
)

assert len(chargers_df) == expected_chargers

assert chargers_df["charger_id"].is_unique

assert (
    chargers_df["station_id"]
    .isin(stations_df["station_id"])
    .all()
)

assert chargers_df["availability_rate"].between(
    0.88,
    0.995
).all()


# Every station should have the expected number of chargers.
station_counts = (
    chargers_df
    .groupby("station_id")
    .size()
)

expected_counts = (
    stations_df
    .set_index("station_id")["charger_count"]
)

assert station_counts.equals(expected_counts)


# ---------------------------------------------------------
# 8. Save
# ---------------------------------------------------------

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

chargers_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ---------------------------------------------------------
# 9. Validation summary
# ---------------------------------------------------------

print("\nCharger dataset created successfully.")

print(f"Rows: {len(chargers_df)}")
print(f"Columns: {len(chargers_df.columns)}")

print("\nChargers by type:")
print(
    chargers_df["charger_type"]
    .value_counts()
    .sort_index()
)

print("\nChargers by station type:")
print(
    pd.crosstab(
        chargers_df["station_type"],
        chargers_df["charger_type"]
    )
)

print("\nAverage power by charger type:")
print(
    chargers_df
    .groupby("charger_type")["power_kw"]
    .mean()
    .round(1)
)

print("\nAverage charger availability:")
print(
    round(
        chargers_df["availability_rate"].mean(),
        4
    )
)

print(f"\nSaved to: {OUTPUT_PATH}")