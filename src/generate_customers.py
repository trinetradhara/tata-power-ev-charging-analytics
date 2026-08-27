import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# 1. Setup
# =========================================================

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

STATIONS_PATH = Path("data/raw/stations.csv")
OUTPUT_PATH = Path("data/raw/customers.csv")

N_CUSTOMERS = 8000


# =========================================================
# 2. Load network
# =========================================================

stations_df = pd.read_csv(STATIONS_PATH)

assert len(stations_df) == 150
assert stations_df["station_id"].is_unique


# Use network size to determine the relative customer
# population across cities.
city_weights = (
    stations_df["city"]
    .value_counts(normalize=True)
    .sort_index()
)

cities = city_weights.index.tolist()
city_probabilities = city_weights.values


# =========================================================
# 3. Customer segments
# =========================================================

SEGMENTS = [
    "Routine_Commuter",
    "Price_Sensitive",
    "Convenience_First",
    "High_Mileage",
]

SEGMENT_PROBABILITIES = [
    0.40,
    0.25,
    0.25,
    0.10,
]


# =========================================================
# 4. Behavioural parameters
# =========================================================
#
# These are population-level assumptions.
# Individual customers will receive variation around them.
#
# Values are intentionally overlapping so that segment
# membership does not perfectly determine behaviour.
# =========================================================

SEGMENT_PARAMETERS = {

    "Routine_Commuter": {
        "sessions_low": 8,
        "sessions_high": 14,
        "peak_mean": 0.72,
        "peak_sd": 0.12,
        "price_mean": 0.52,
        "price_sd": 0.14,
        "convenience_mean": 0.68,
        "convenience_sd": 0.12,
        "loyalty_mean": 0.72,
        "loyalty_sd": 0.12,
        "home_charge_prob": 0.65,
        "battery_mean": 55,
        "battery_sd": 8,
    },

    "Price_Sensitive": {
        "sessions_low": 6,
        "sessions_high": 12,
        "peak_mean": 0.50,
        "peak_sd": 0.16,
        "price_mean": 0.82,
        "price_sd": 0.10,
        "convenience_mean": 0.48,
        "convenience_sd": 0.15,
        "loyalty_mean": 0.55,
        "loyalty_sd": 0.16,
        "home_charge_prob": 0.45,
        "battery_mean": 52,
        "battery_sd": 9,
    },

    "Convenience_First": {
        "sessions_low": 5,
        "sessions_high": 10,
        "peak_mean": 0.82,
        "peak_sd": 0.09,
        "price_mean": 0.25,
        "price_sd": 0.10,
        "convenience_mean": 0.86,
        "convenience_sd": 0.08,
        "loyalty_mean": 0.80,
        "loyalty_sd": 0.10,
        "home_charge_prob": 0.35,
        "battery_mean": 60,
        "battery_sd": 9,
    },

    "High_Mileage": {
        "sessions_low": 15,
        "sessions_high": 25,
        "peak_mean": 0.58,
        "peak_sd": 0.14,
        "price_mean": 0.68,
        "price_sd": 0.13,
        "convenience_mean": 0.74,
        "convenience_sd": 0.11,
        "loyalty_mean": 0.86,
        "loyalty_sd": 0.08,
        "home_charge_prob": 0.15,
        "battery_mean": 70,
        "battery_sd": 10,
    },
}


# =========================================================
# 5. Station preferences by customer segment
# =========================================================

STATION_TYPE_PREFERENCES = {

    "Routine_Commuter": {
        "Office_Commercial": 0.35,
        "Residential": 0.30,
        "Mall_Retail": 0.15,
        "Transit_Public": 0.10,
        "Hotel": 0.05,
        "Highway": 0.04,
        "Fleet": 0.01,
    },

    "Price_Sensitive": {
        "Mall_Retail": 0.25,
        "Office_Commercial": 0.20,
        "Residential": 0.20,
        "Transit_Public": 0.15,
        "Highway": 0.10,
        "Hotel": 0.05,
        "Fleet": 0.05,
    },

    "Convenience_First": {
        "Highway": 0.25,
        "Mall_Retail": 0.20,
        "Office_Commercial": 0.15,
        "Residential": 0.10,
        "Hotel": 0.10,
        "Transit_Public": 0.10,
        "Fleet": 0.10,
    },

    "High_Mileage": {
        "Fleet": 0.35,
        "Highway": 0.30,
        "Office_Commercial": 0.10,
        "Mall_Retail": 0.10,
        "Transit_Public": 0.08,
        "Residential": 0.04,
        "Hotel": 0.03,
    },
}


# =========================================================
# 6. Helper function
# =========================================================

def bounded_normal(mean, sd, size=1):
    """
    Draw values from a normal distribution and keep
    behavioural scores between 0 and 1.
    """
    values = rng.normal(mean, sd, size)
    return np.clip(values, 0.01, 0.99)


# =========================================================
# 7. Generate customers
# =========================================================

customers = []

for customer_number in range(1, N_CUSTOMERS + 1):

    customer_id = f"CUST{customer_number:05d}"

    city = rng.choice(
        cities,
        p=city_probabilities
    )

    segment = rng.choice(
        SEGMENTS,
        p=SEGMENT_PROBABILITIES
    )

    params = SEGMENT_PARAMETERS[segment]

    # ---------------------------------------------
    # Persistent behavioural characteristics
    # ---------------------------------------------

    peak_preference = bounded_normal(
        params["peak_mean"],
        params["peak_sd"]
    )[0]

    price_sensitivity = bounded_normal(
        params["price_mean"],
        params["price_sd"]
    )[0]

    convenience_score = bounded_normal(
        params["convenience_mean"],
        params["convenience_sd"]
    )[0]

    station_loyalty = bounded_normal(
        params["loyalty_mean"],
        params["loyalty_sd"]
    )[0]

    battery_capacity = np.clip(
        rng.normal(
            params["battery_mean"],
            params["battery_sd"]
        ),
        35,
        100
    )

    base_sessions = rng.integers(
        params["sessions_low"],
        params["sessions_high"] + 1
    )

    home_charging = (
        rng.random() < params["home_charge_prob"]
    )

    # ---------------------------------------------
    # Preferred station type
    # ---------------------------------------------

    preferences = STATION_TYPE_PREFERENCES[segment]

    preferred_station_type = rng.choice(
        list(preferences.keys()),
        p=list(preferences.values())
    )

    # ---------------------------------------------
    # Average session energy
    # ---------------------------------------------
    #
    # Drivers generally do not refill the entire
    # battery every public charging session.
    # ---------------------------------------------

    session_energy = np.clip(
        rng.normal(
            battery_capacity * 0.42,
            battery_capacity * 0.08
        ),
        8,
        60
    )

    # ---------------------------------------------
    # Derived behavioural indicators
    # ---------------------------------------------

    # Approximate probability of responding to a
    # well-designed monetary incentive.
    #
    # Price sensitivity increases response.
    # Strong peak preference creates more opportunity
    # but does not automatically imply response.
    incentive_response_score = np.clip(
        (
            0.55 * price_sensitivity
            + 0.20 * (1 - convenience_score)
            + 0.15 * (1 - station_loyalty)
            + 0.10 * peak_preference
        ),
        0.01,
        0.99
    )

    customers.append({
        "customer_id": customer_id,
        "city": city,
        "customer_segment": segment,

        "battery_capacity_kwh": round(
            battery_capacity,
            1
        ),

        "home_charging_access": int(
            home_charging
        ),

        "preferred_station_type":
            preferred_station_type,

        "base_sessions_per_month":
            int(base_sessions),

        "peak_preference_score":
            round(peak_preference, 3),

        "price_sensitivity_score":
            round(price_sensitivity, 3),

        "convenience_score":
            round(convenience_score, 3),

        "station_loyalty_score":
            round(station_loyalty, 3),

        "baseline_avg_session_kwh":
            round(session_energy, 1),

        "incentive_response_score":
            round(incentive_response_score, 3),
    })


# =========================================================
# 8. Create dataframe
# =========================================================

customers_df = pd.DataFrame(customers)


# =========================================================
# 9. Validation
# =========================================================

assert len(customers_df) == N_CUSTOMERS

assert customers_df["customer_id"].is_unique

assert customers_df["city"].isin(cities).all()

assert customers_df["customer_segment"].isin(
    SEGMENTS
).all()

assert customers_df[
    "peak_preference_score"
].between(0, 1).all()

assert customers_df[
    "price_sensitivity_score"
].between(0, 1).all()

assert customers_df[
    "convenience_score"
].between(0, 1).all()

assert customers_df[
    "station_loyalty_score"
].between(0, 1).all()

assert customers_df[
    "incentive_response_score"
].between(0, 1).all()


# =========================================================
# 10. Save
# =========================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

customers_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# =========================================================
# 11. Summary
# =========================================================

print("\nCustomer dataset created successfully.")

print(f"Rows: {len(customers_df)}")
print(f"Columns: {len(customers_df.columns)}")

print("\nCustomers by segment:")
print(
    customers_df["customer_segment"]
    .value_counts()
    .sort_index()
)

print("\nCustomers by city:")
print(
    customers_df["city"]
    .value_counts()
    .sort_index()
)

print("\nAverage behavioural scores by segment:")

print(
    customers_df
    .groupby("customer_segment")[
        [
            "peak_preference_score",
            "price_sensitivity_score",
            "convenience_score",
            "station_loyalty_score",
            "incentive_response_score",
        ]
    ]
    .mean()
    .round(3)
)

print("\nHome charging access:")
print(
    customers_df["home_charging_access"]
    .value_counts(normalize=True)
    .sort_index()
    .mul(100)
    .round(1)
    .astype(str)
    + "%"
)

print("\nAverage sessions per month:")
print(
    customers_df
    .groupby("customer_segment")[
        "base_sessions_per_month"
    ]
    .mean()
    .round(1)
)

print(f"\nSaved to: {OUTPUT_PATH}")