import sys
sys.path.insert(0, ".")

import numpy as np
import pandas as pd
from scripts.db_config import get_connection, get_engine

# ── Volatility forecast parameters ────────────────────────────────────────────
MIN_WEEKS_FOR_FORECAST = 4   # minimum price history needed
FORECAST_HORIZON       = 4   # weeks ahead to forecast


def compute_volatility(prices: np.ndarray) -> dict:
    """
    Compute forward price volatility using standard deviation of weekly returns.
    Returns 4-week forward volatility estimates and descriptive statistics.
    """
    # Weekly log returns
    returns = np.diff(np.log(prices)) * 100

    # Historical mean and standard deviation of returns
    mu  = round(float(np.mean(returns)), 6)
    std = round(float(np.std(returns)), 6)

    # Forward volatility — constant std projection over 4 weeks
    # Scales by sqrt(t) consistent with random walk assumption
    vol_forecasts = [
        round(float(std * np.sqrt(t)), 4) for t in range(1, FORECAST_HORIZON + 1)
    ]

    return {
        "mu":         mu,
        "alpha":      0.0,    # not applicable — kept for schema compatibility
        "beta":       0.0,    # not applicable — kept for schema compatibility
        "vol_week_1": vol_forecasts[0],
        "vol_week_2": vol_forecasts[1],
        "vol_week_3": vol_forecasts[2],
        "vol_week_4": vol_forecasts[3],
    }


def run_volatility_engine():
    conn   = get_connection()
    engine = get_engine()

    # ── Load historical egg prices ────────────────────────────────────────────
    df = pd.read_sql("""
        SELECT week_number, egg_price_per_crate
        FROM market_prices
        ORDER BY week_number ASC
    """, engine)

    engine.dispose()

    if len(df) < MIN_WEEKS_FOR_FORECAST:
        print(f"⚠️  Not enough price history — need at least {MIN_WEEKS_FOR_FORECAST} weeks.")
        conn.close()
        return

    prices      = df["egg_price_per_crate"].values.astype(float)
    week_number = int(df["week_number"].iloc[-1])

    print(f"  📈 Computing price volatility from {len(prices)} weeks of data...")

    # ── Compute volatility ────────────────────────────────────────────────────
    vol = compute_volatility(prices)

    # ── Write to volatility_forecasts ─────────────────────────────────────────
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO volatility_forecasts
        (week_number, vol_week_1, vol_week_2, vol_week_3, vol_week_4,
         garch_alpha, garch_beta, garch_mu)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (week_number) DO UPDATE SET
            vol_week_1  = EXCLUDED.vol_week_1,
            vol_week_2  = EXCLUDED.vol_week_2,
            vol_week_3  = EXCLUDED.vol_week_3,
            vol_week_4  = EXCLUDED.vol_week_4,
            garch_alpha = EXCLUDED.garch_alpha,
            garch_beta  = EXCLUDED.garch_beta,
            garch_mu    = EXCLUDED.garch_mu,
            run_date    = NOW()
    """, (week_number,
          vol["vol_week_1"], vol["vol_week_2"],
          vol["vol_week_3"], vol["vol_week_4"],
          vol["alpha"], vol["beta"], vol["mu"]))

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n✅ Volatility engine complete — week {week_number}.")
    print(f"   Mean weekly return : {vol['mu']:.4f}%")
    print(f"   Weekly std dev     : {vol['vol_week_1']:.4f}%")
    print(f"\n   4-week volatility forecast:")
    print(f"      Week +1 : {vol['vol_week_1']:.4f}%")
    print(f"      Week +2 : {vol['vol_week_2']:.4f}%")
    print(f"      Week +3 : {vol['vol_week_3']:.4f}%")
    print(f"      Week +4 : {vol['vol_week_4']:.4f}%")


if __name__ == "__main__":
    run_volatility_engine()