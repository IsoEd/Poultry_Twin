import sys
sys.path.insert(0, ".")

import pandas as pd
from scripts.db_config import get_connection, get_engine
from scripts.utils import eggs_expected, egg_variance, variance_pct, leakage_flag


def compute_leakage(df: pd.DataFrame) -> list[dict]:
    """
    For each week compute expected vs reported eggs, variance,
    variance percentage, and flag level.
    Simpler and more interpretable than Z-score for a single farm.
    """
    records = []

    for _, row in df.iterrows():
        week     = int(row["week_number"])
        wdate    = row["week_date"]
        surviving = int(row["surviving_birds"])
        reported  = int(row["eggs_collected"])
        expected  = eggs_expected(surviving, week)
        variance  = egg_variance(expected, reported)
        var_pct   = variance_pct(expected, reported)
        flag      = leakage_flag(var_pct)

        records.append({
            "week_number":   week,
            "week_date":     wdate,
            "expected_eggs": expected,
            "reported_eggs": reported,
            "variance":      variance,
            "z_score":       var_pct,   # repurposing column for variance %
            "flag_level":    flag
        })

    return records


def run_leakage_engine():
    conn   = get_connection()
    engine = get_engine()

    # ── Load farm state and inputs ────────────────────────────────────────────
    df = pd.read_sql("""
        SELECT fs.week_number, fs.week_date, fs.surviving_birds,
               fi.eggs_collected
        FROM farm_state fs
        JOIN farm_inputs fi ON fs.week_number = fi.week_number
        ORDER BY fs.week_number ASC
    """, engine)

    engine.dispose()

    if df.empty:
        print("⚠️  No data found — run seed.py and state_engine.py first.")
        conn.close()
        return

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
    conn.close()

    # ── Summary output ────────────────────────────────────────────────────────
    flags   = [r for r in records if r["flag_level"] == "FLAG"]
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
                  f"({f['z_score']:.1f}% shortfall)")

    if watches:
        print(f"\n   ⚠️  Watch weeks:")
        for w in watches:
            print(f"      Week {w['week_number']}: expected {w['expected_eggs']} "
                  f"got {w['reported_eggs']} — variance {w['variance']} "
                  f"({w['z_score']:.1f}% shortfall)")


if __name__ == "__main__":
    run_leakage_engine()