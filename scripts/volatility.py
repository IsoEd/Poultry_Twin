import sys
sys.path.insert(0, ".")

import numpy as np
import pandas as pd
from arch import arch_model
from scripts.db_config import get_connection, get_engine

# ── Volatility forecast parameters ────────────────────────────────────────────
MIN_WEEKS_FOR_GARCH = 12  # minimum price history needed to fit GARCH
FORECAST_HORIZON    = 4   # weeks ahead to forecast volatility


def fit_garch(prices: np.ndarray) -> dict:
    """
    Fit a GARCH(1,1) model to weekly egg price returns.
    Returns model parameters and 4-week forward volatility forecasts.
    """
    # Convert prices to percentage returns
    returns = pd.Series(np.diff(np.log(prices)) * 100)

    # Fit GARCH(1,1)
    model  = arch_model(returns, vol="Garch", p=1, q=1, dist="normal", rescale=False)
    result = model.fit(disp="off")

    # Extract parameters
    params = result.params
    mu     = float(params.get("mu", params.iloc[0]))
    alpha  = float(params.get("alpha[1]", params.iloc[2]))
    beta   = float(params.get("beta[1]", params.iloc[3]))

    # 4-week forward volatility forecast
    forecast    = result.forecast(horizon=FORECAST_HORIZON, reindex=False)
    vol_forecasts = np.sqrt(forecast.variance.iloc[-1].values)

    return {
        "mu":    round(mu, 6),
        "alpha": round(alpha, 6),
        "beta":  round(beta, 6),
        "vol_week_1": round(float(vol_forecasts[0]), 4),
        "vol_week_2": round(float(vol_forecasts[1]), 4),
        "vol_week_3": round(float(vol_forecasts[2]), 4),
        "vol_week_4": round(float(vol_forecasts[3]), 4),
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

    if len(df) < MIN_WEEKS_FOR_GARCH:
        print(f"⚠️  Not enough price history — need at least {MIN_WEEKS_FOR_GARCH} weeks.")
        engine.dispose()
        return

    prices     = df["egg_price_per_crate"].values.astype(float)
    week_number = int(df["week_number"].iloc[-1])

    print(f"  📈 Fitting GARCH(1,1) on {len(prices)} weeks of egg price data...")

    # ── Fit GARCH model ───────────────────────────────────────────────────────
    garch = fit_garch(prices)

    # ── Write to volatility_forecasts ─────────────────────────────────────────
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO volatility_forecasts
        (week_number, vol_week_1, vol_week_2, vol_week_3, vol_week_4,
         garch_alpha, garch_beta, garch_mu)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (week_number) DO UPDATE SET
            vol_week_1 = EXCLUDED.vol_week_1,
            vol_week_2 = EXCLUDED.vol_week_2,
            vol_week_3 = EXCLUDED.vol_week_3,
            vol_week_4 = EXCLUDED.vol_week_4,
            garch_alpha = EXCLUDED.garch_alpha,
            garch_beta  = EXCLUDED.garch_beta,
            garch_mu    = EXCLUDED.garch_mu,
            run_date    = NOW()
    """, (week_number,
          garch["vol_week_1"], garch["vol_week_2"],
          garch["vol_week_3"], garch["vol_week_4"],
          garch["alpha"], garch["beta"], garch["mu"]))

    conn.commit()
    cur.close()
    engine.dispose()

    # ── Summary output ────────────────────────────────────────────────────────
    print(f"\n✅ Volatility engine complete — week {week_number}.")
    print(f"   GARCH parameters:")
    print(f"      mu    : {garch['mu']}")
    print(f"      alpha : {garch['alpha']}")
    print(f"      beta  : {garch['beta']}")
    print(f"\n   4-week volatility forecast:")
    print(f"      Week +1 : {garch['vol_week_1']:.4f}%")
    print(f"      Week +2 : {garch['vol_week_2']:.4f}%")
    print(f"      Week +3 : {garch['vol_week_3']:.4f}%")
    print(f"      Week +4 : {garch['vol_week_4']:.4f}%")


if __name__ == "__main__":
    run_volatility_engine()