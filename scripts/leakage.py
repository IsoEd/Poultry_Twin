import sys
sys.path.insert(0, ".")

import numpy as np
import pandas as pd
from scripts.db_config import get_connection, get_engine
from scripts.utils import eggs_expected, egg_variance, egg_zscore, leakage_flag

# ── Leakage detection parameters ─────────────────────────────────────────────
MIN_WEEKS_FOR_ZSCORE = 4  # minimum history needed before Z-score is meaningful


def compute_leakage(df: pd.DataFrame) -> list[dict]:
    """
    For each week compute expected vs reported eggs, variance, Z-score, and flag.
    Z-score requires at least MIN_WEEKS_FOR_ZSCORE of history to be meaningful.
    """
    records = []

    variances = []

    for _, row in df.iterrows():
        week            = int(row["week_number"])
        wdate           = row["week_date"]
        surviving       = int(row["surviving_birds"])
        reported        = int(row["eggs_collected"])
        expected        = eggs_expected(surviving, week)
        variance        = egg_variance(expected, reported)

        variances.append(variance)

        # Z-score only meaningful once we have enough history
        if len(variances) >= MIN_WEEKS_FOR_ZSCORE:
            mean_var = float(np.mean(variances[:-1]))  # exclude current week
            std_var  = float(np.std(variances[:-1]))
            z        = egg_zscore(variance, mean_var, std_var)
        else:
            z = 0.0

        flag = leakage_flag(z)

        records.append({
            "week_number":   week,
            "week_date":     wdate,
            "expected_eggs": expected,
            "reported_eggs": reported,
            "variance":      variance,
            "z_score":       round(z, 3),
            "flag_level":    flag
        })

    return records


def run_leakage_engine():
    conn   = get_connection()
    engine = get_engine()

    # ── Load farm state and inputs jointly ────────────────────────────────────
    df = pd.read_sql("""
        SELECT fs.week_number, fs.week_date, fs.surviving_birds,
               fi.eggs_collected
        FROM farm_state fs
        JOIN farm_inputs fi ON fs.week_number = fi.week_number
        ORDER BY fs.week_number ASC
    """, engine)

    if df.empty:
        raise ValueError("No data found — run seed.py and state_engine.py first.")

    # ── Compute leakage records ───────────────────────────────────────────────
    records = compute_leakage(df)

    # ── Write to leakage_events ───────────────────────────────────────────────
    cur = conn.cursor()
    cur.execute("TRUNCATE leakage_events RESTART IDENTITY;")

    for r in records:
        cur.execute("""
            INSERT INTO leakage_events
            (week_number, week_date, expected_eggs, reported_eggs,
             variance, z_score, flag_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (r["week_number"], r["week_date"], r["expected_eggs"],
              r["reported_eggs"], r["variance"], r["z_score"], r["flag_level"]))

    conn.commit()
    cur.close()
    engine.dispose()

    # ── Summary output ────────────────────────────────────────────────────────
    flags  = [r for r in records if r["flag_level"] == "FLAG"]
    watches = [r for r in records if r["flag_level"] == "WATCH"]

    print(f"\n✅ Leakage engine complete — {len(records)} weeks processed.")
    print(f"   NORMAL : {len(records) - len(flags) - len(watches)} weeks")
    print(f"   WATCH  : {len(watches)} weeks")
    print(f"   FLAG   : {len(flags)} weeks")

    if flags:
        print(f"\n   🚨 Flagged weeks:")
        for f in flags:
            print(f"      Week {f['week_number']}: expected {f['expected_eggs']} "
                  f"got {f['reported_eggs']} — variance {f['variance']} "
                  f"Z-score {f['z_score']}")

    if watches:
        print(f"\n   ⚠️  Watch weeks:")
        for w in watches:
            print(f"      Week {w['week_number']}: expected {w['expected_eggs']} "
                  f"got {w['reported_eggs']} — variance {w['variance']} "
                  f"Z-score {w['z_score']}")


if __name__ == "__main__":
    run_leakage_engine()