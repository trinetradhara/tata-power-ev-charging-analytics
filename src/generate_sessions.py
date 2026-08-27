import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# 1. Setup
# =========================================================

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

STATIONS_PATH = Path("data/raw/stations.csv")
CHARGERS_PATH = Path("data/raw/chargers.csv")
CUSTOMERS_PATH = Path("data/raw/customers.csv")

OUTPUT_PATH = Path("data/raw/sessions.csv")

START_DATE = "2026-01-01"
END_DATE = "2026-12-31"


# =========================================================
# 2. Load source tables
# =========================================================

stations_df = pd.read_csv(STATIONS_PATH)
chargers_df = pd.read_csv(CHARGERS_PATH)
customers_df = pd.read_csv(CUSTOMERS_PATH)


# =========================================================
# 3. Basic validation
# =========================================================

assert len(stations_df) == 150
assert len(chargers_df) == 1351
assert len(customers_df) == 8000

assert stations_df["station_id"].is_unique
assert chargers_df["charger_id"].is_unique
assert customers_df["customer_id"].is_unique

assert set(
    chargers_df["station_id"]
).issubset(
    set(stations_df["station_id"])
)


# =========================================================
# 4. Date range
# =========================================================

date_range = pd.date_range(
    START_DATE,
    END_DATE,
    freq="D"
)


# =========================================================
# 5. Session-volume assumptions
# =========================================================

# Approximate monthly public-charging sessions per
# customer are driven by their persistent customer
# characteristics.

# We will later introduce:
# - weekday/weekend effects
# - seasonal effects
# - peak/off-peak behaviour
# - station preferences
# - charger availability
# - treatment/control assignment


# =========================================================
# 6. Inspect source data
# =========================================================

print("\nSession engine setup successful.")

print(f"Stations loaded: {len(stations_df)}")
print(f"Chargers loaded: {len(chargers_df)}")
print(f"Customers loaded: {len(customers_df)}")

print(
    f"Simulation period: "
    f"{date_range.min().date()} "
    f"to "
    f"{date_range.max().date()}"
)

print(
    f"Simulation days: {len(date_range)}"
)
# =========================================================
# 7. Generate monthly session demand
# =========================================================

MONTHLY_SEASONALITY = {
    1: 0.95,
    2: 0.98,
    3: 1.02,
    4: 1.00,
    5: 1.03,
    6: 0.98,
    7: 0.94,
    8: 0.96,
    9: 1.02,
    10: 1.05,
    11: 1.08,
    12: 1.12,
}


# Segment-level frequency multipliers.
# These create behavioural differences without
# making segments completely deterministic.

SEGMENT_FREQUENCY_MULTIPLIER = {
    "Routine_Commuter": 1.00,
    "Price_Sensitive": 0.90,
    "Convenience_First": 0.85,
    "High_Mileage": 1.60,
}


monthly_sessions = []


for _, customer in customers_df.iterrows():

    customer_id = customer["customer_id"]
    segment = customer["customer_segment"]

    base_sessions = customer["base_sessions_per_month"]

    segment_multiplier = (
        SEGMENT_FREQUENCY_MULTIPLIER[segment]
    )

    for month in range(1, 13):

        seasonality = MONTHLY_SEASONALITY[month]

        # Customer-specific random variation.
        # Gamma noise keeps demand positive while
        # allowing some customers to be consistently
        # more active than others.
        customer_variation = rng.gamma(
            shape=8,
            scale=1 / 8
        )

        expected_sessions = (
            base_sessions
            * segment_multiplier
            * seasonality
            * customer_variation
        )

        session_count = max(
            0,
            rng.poisson(expected_sessions)
        )

        monthly_sessions.append({
            "customer_id": customer_id,
            "month": month,
            "session_count": session_count,
        })


monthly_sessions_df = pd.DataFrame(
    monthly_sessions
)


# =========================================================
# 8. Validate monthly demand
# =========================================================

assert len(monthly_sessions_df) == (
    len(customers_df) * 12
)

assert monthly_sessions_df[
    "customer_id"
].isin(
    customers_df["customer_id"]
).all()

assert (
    monthly_sessions_df["session_count"] >= 0
).all()


print("\nMonthly session demand generated.")

print(
    f"Customer-month rows: "
    f"{len(monthly_sessions_df)}"
)

print("\nAverage monthly sessions by segment:")

segment_session_summary = (
    monthly_sessions_df
    .merge(
        customers_df[
            [
                "customer_id",
                "customer_segment"
            ]
        ],
        on="customer_id",
        how="left"
    )
    .groupby("customer_segment")[
        "session_count"
    ]
    .mean()
    .round(2)
)

print(segment_session_summary)

print("\nTotal simulated sessions:")

print(
    monthly_sessions_df[
        "session_count"
    ].sum()
)

MONTHLY_OUTPUT_PATH = Path("data/raw/monthly_sessions.csv")

monthly_sessions_df.to_csv(
    MONTHLY_OUTPUT_PATH,
    index=False
)

print(f"Saved to: {MONTHLY_OUTPUT_PATH}")

# =========================================================
# 9. Generate individual charging sessions
# =========================================================

# Customer attributes used for behavioural choices.
customer_lookup = customers_df.set_index("customer_id")

# Group chargers by station for fast session assignment.
chargers_by_station = {
    station_id: group.reset_index(drop=True)
    for station_id, group in chargers_df.groupby("station_id")
}

# Station lookup by city and station type.
stations_by_city_type = {}

for (city, station_type), group in stations_df.groupby(
    ["city", "station_type"]
):
    stations_by_city_type[(city, station_type)] = (
        group.reset_index(drop=True)
    )

# Base public-charging prices.
# These are deliberately different by charger type.
BASE_PRICE_PER_KWH = {
    "AC": 12.0,
    "DC_Fast": 18.0,
    "DC_Ultra": 24.0,
}

# Typical session-duration ranges by charger type.
DURATION_RANGE = {
    "AC": (45, 180),
    "DC_Fast": (20, 75),
    "DC_Ultra": (12, 45),
}

# Charging-speed assumptions.
# Used only to make energy and duration internally consistent.
CHARGER_EFFICIENCY = {
    "AC": 0.88,
    "DC_Fast": 0.92,
    "DC_Ultra": 0.94,
}

# Station-type preference adjustments.
# These represent realistic behavioural tendencies rather
# than deterministic rules.
STATION_TYPE_BONUS = {
    "Routine_Commuter": {
        "Office_Commercial": 1.40,
        "Transit_Public": 1.25,
        "Mall_Retail": 1.00,
        "Highway": 0.70,
        "Hotel": 0.70,
        "Fleet": 0.50,
        "Residential": 1.10,
    },
    "Price_Sensitive": {
        "Mall_Retail": 1.25,
        "Residential": 1.20,
        "Office_Commercial": 1.00,
        "Transit_Public": 1.00,
        "Highway": 0.80,
        "Hotel": 0.60,
        "Fleet": 0.50,
    },
    "Convenience_First": {
        "Mall_Retail": 1.30,
        "Office_Commercial": 1.20,
        "Hotel": 1.15,
        "Transit_Public": 1.10,
        "Highway": 1.00,
        "Residential": 0.80,
        "Fleet": 0.50,
    },
    "High_Mileage": {
        "Highway": 1.50,
        "Office_Commercial": 1.15,
        "Transit_Public": 1.10,
        "Mall_Retail": 1.00,
        "Hotel": 0.85,
        "Residential": 0.70,
        "Fleet": 0.60,
    },
}

# Session records.
session_records = []

session_counter = 1

for _, monthly_row in monthly_sessions_df.iterrows():

    customer_id = monthly_row["customer_id"]
    month = int(monthly_row["month"])
    session_count = int(monthly_row["session_count"])

    if session_count == 0:
        continue

    customer = customer_lookup.loc[customer_id]

    city = customer["city"]
    segment = customer["customer_segment"]
    preferred_station_type = customer["preferred_station_type"]

    # -----------------------------------------------------
    # Generate dates inside the customer's month
    # -----------------------------------------------------

    month_start = pd.Timestamp(
        year=2026,
        month=month,
        day=1
    )

    month_end = (
        month_start
        + pd.offsets.MonthEnd(1)
    )

    available_dates = pd.date_range(
        month_start,
        month_end,
        freq="D"
    )

    # Weekday preference depends on customer segment.
    weekday_weights = np.array([
        1.10 if segment == "Routine_Commuter" else 1.00
        for d in available_dates
    ])

    # High-mileage customers have slightly higher
    # probability of charging on weekends.
    if segment == "High_Mileage":
        for i, date in enumerate(available_dates):
            if date.dayofweek >= 5:
                weekday_weights[i] *= 1.15

    weekday_weights = (
        weekday_weights / weekday_weights.sum()
    )

    chosen_dates = rng.choice(
        available_dates,
        size=session_count,
        replace=True,
        p=weekday_weights
    )

    for session_date in chosen_dates:

        # -------------------------------------------------
        # Time-of-day behaviour
        # -------------------------------------------------

        peak_score = float(
            customer["peak_preference_score"]
        )

        # Create a mixture of morning, afternoon,
        # evening and off-peak sessions.
        time_buckets = [
            ("morning", 7, 10, 0.20 + 0.20 * peak_score),
            ("midday", 10, 16, 0.25),
            ("evening", 16, 21, 0.25 + 0.25 * peak_score),
            ("off_peak", 21, 7, 0.30 - 0.20 * peak_score),
        ]

        bucket_names = [x[0] for x in time_buckets]
        bucket_weights = np.array([x[3] for x in time_buckets])

        bucket_weights = np.maximum(
            bucket_weights,
            0.05
        )

        bucket_weights = (
            bucket_weights / bucket_weights.sum()
        )

        bucket = rng.choice(
            bucket_names,
            p=bucket_weights
        )

        bucket_info = next(
            x for x in time_buckets if x[0] == bucket
        )

        if bucket == "off_peak":
            # 21:00-07:00 crossing midnight.
            if rng.random() < 0.55:
                hour = rng.integers(21, 24)
            else:
                hour = rng.integers(0, 7)
        else:
            hour = rng.integers(
                bucket_info[1],
                bucket_info[2]
            )

        minute = int(
            rng.integers(0, 60)
        )

        start_timestamp = (
            pd.Timestamp(session_date)
            + pd.Timedelta(hours=int(hour))
            + pd.Timedelta(minutes=minute)
        )

        # -------------------------------------------------
        # Station selection
        # -------------------------------------------------

        station_candidates = []

        for station_type in stations_df[
            stations_df["city"] == city
        ]["station_type"].unique():

            candidates = stations_by_city_type.get(
                (city, station_type)
            )

            if candidates is None or len(candidates) == 0:
                continue

            # Segment preference.
            segment_bonus = STATION_TYPE_BONUS.get(
                segment,
                {}
            ).get(
                station_type,
                1.0
            )

            # Explicit customer preference gets an
            # additional boost.
            preference_bonus = (
                2.0
                if station_type == preferred_station_type
                else 1.0
            )

            for _, station in candidates.iterrows():

                # Higher reliability and lower utilization
                # make a station more attractive.
                availability_score = max(
                    0.10,
                    float(
                        station["operational_reliability"]
                    )
                )

                utilization_penalty = max(
                    0.30,
                    1.20
                    - float(
                        station["baseline_utilization"]
                    )
                )

                weight = (
                    segment_bonus
                    * preference_bonus
                    * availability_score
                    * utilization_penalty
                )

                station_candidates.append(
                    (
                        station,
                        weight
                    )
                )

        if not station_candidates:
            continue

        station_weights = np.array([
            item[1]
            for item in station_candidates
        ])

        station_weights = (
            station_weights
            / station_weights.sum()
        )

        selected_index = rng.choice(
            len(station_candidates),
            p=station_weights
        )

        selected_station = (
            station_candidates[selected_index][0]
        )

        station_id = selected_station["station_id"]
        station_type = selected_station["station_type"]

        # -------------------------------------------------
        # Charger selection
        # -------------------------------------------------

        available_chargers = chargers_by_station.get(
            station_id
        )

        if (
            available_chargers is None
            or len(available_chargers) == 0
        ):
            continue

        # Charger preference depends on customer segment.
        charger_preferences = {
            "Routine_Commuter": {
                "AC": 1.30,
                "DC_Fast": 1.00,
                "DC_Ultra": 0.80,
            },
            "Price_Sensitive": {
                "AC": 1.60,
                "DC_Fast": 0.90,
                "DC_Ultra": 0.50,
            },
            "Convenience_First": {
                "AC": 0.70,
                "DC_Fast": 1.20,
                "DC_Ultra": 1.40,
            },
            "High_Mileage": {
                "AC": 0.60,
                "DC_Fast": 1.30,
                "DC_Ultra": 1.50,
            },
        }

        charger_weights = []

        for _, charger in available_chargers.iterrows():

            charger_type = charger["charger_type"]

            segment_weight = (
                charger_preferences
                .get(segment, {})
                .get(charger_type, 1.0)
            )

            availability_weight = max(
                0.20,
                float(charger["availability_rate"])
            )

            charger_weights.append(
                segment_weight
                * availability_weight
            )

        charger_weights = np.array(
            charger_weights
        )

        charger_weights = (
            charger_weights
            / charger_weights.sum()
        )

        charger_index = rng.choice(
            len(available_chargers),
            p=charger_weights
        )

        selected_charger = (
            available_chargers.iloc[
                charger_index
            ]
        )

        charger_id = selected_charger["charger_id"]
        charger_type = selected_charger["charger_type"]
        power_kw = float(selected_charger["power_kw"])

        # -------------------------------------------------
        # Energy and duration
        # -------------------------------------------------

        battery_capacity = float(
            customer["battery_capacity_kwh"]
        )

        baseline_energy = float(
            customer["baseline_avg_session_kwh"]
        )

        # Energy is bounded by battery size and follows
        # a log-normal distribution to avoid artificial
        # identical sessions.
        energy_kwh = (
            baseline_energy
            * rng.lognormal(
                mean=0,
                sigma=0.18
            )
        )

        energy_kwh = np.clip(
            energy_kwh,
            5.0,
            battery_capacity * 0.80
        )

        efficiency = CHARGER_EFFICIENCY[
            charger_type
        ]

        theoretical_minutes = (
            energy_kwh
            / max(power_kw * efficiency, 1)
            * 60
        )

        min_duration, max_duration = (
            DURATION_RANGE[charger_type]
        )

        duration_minutes = np.clip(
            theoretical_minutes
            * rng.normal(
                1.0,
                0.10
            ),
            min_duration,
            max_duration
        )

        duration_minutes = int(
            round(duration_minutes)
        )

        # -------------------------------------------------
        # Pricing
        # -------------------------------------------------

        base_price = BASE_PRICE_PER_KWH[
            charger_type
        ]

        # Slight peak-period price premium.
        if bucket in ["morning", "evening"]:
            base_price *= 1.05

        base_price = round(
            base_price,
            2
        )

        # -------------------------------------------------
        # Session status
        # -------------------------------------------------

        # Most sessions complete successfully.
        # A small fraction fail/cancel, with slightly
        # higher failure probability for lower-availability
        # chargers.
        availability_rate = float(
            selected_charger["availability_rate"]
        )

        failure_probability = np.clip(
            0.015
            + (1 - availability_rate) * 0.08,
            0.01,
            0.10
        )

        status = (
            "Completed"
            if rng.random() > failure_probability
            else rng.choice(
                ["Cancelled", "Failed"],
                p=[0.65, 0.35]
            )
        )

        session_records.append({
            "session_id": f"SES{session_counter:07d}",
            "customer_id": customer_id,
            "station_id": station_id,
            "charger_id": charger_id,
            "city": city,
            "station_type": station_type,
            "charger_type": charger_type,
            "start_timestamp": start_timestamp,
            "duration_minutes": duration_minutes,
            "energy_kwh": round(
                float(energy_kwh),
                2
            ),
            "base_price_per_kwh": base_price,
            "session_status": status,
        })

        session_counter += 1


sessions_df = pd.DataFrame(
    session_records
)


# =========================================================
# 10. Validate individual sessions
# =========================================================

assert sessions_df["session_id"].is_unique

assert sessions_df[
    "customer_id"
].isin(
    customers_df["customer_id"]
).all()

assert sessions_df[
    "station_id"
].isin(
    stations_df["station_id"]
).all()

assert sessions_df[
    "charger_id"
].isin(
    chargers_df["charger_id"]
).all()

assert (
    sessions_df["energy_kwh"] > 0
).all()

assert (
    sessions_df["duration_minutes"] > 0
).all()

assert sessions_df[
    "start_timestamp"
].min() >= pd.Timestamp(START_DATE)

assert sessions_df[
    "start_timestamp"
].max() < (
    pd.Timestamp(END_DATE)
    + pd.Timedelta(days=1)
)


# =========================================================
# 11. Save individual sessions
# =========================================================

sessions_df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nIndividual charging sessions generated.")

print(
    f"Session rows: {len(sessions_df)}"
)

print(
    "\nSession status:"
)

print(
    sessions_df[
        "session_status"
    ].value_counts()
)

print(
    "\nEnergy delivered (kWh):"
)

print(
    sessions_df[
        "energy_kwh"
    ].describe().round(2)
)

print(
    f"\nSaved to: {OUTPUT_PATH}"
)