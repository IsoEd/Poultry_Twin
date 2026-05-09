import sys
sys.path.insert(0, ".")

import numpy as np
import pandas as pd
from scripts.db_config import get_connection, get_engine
from scripts.utils import (
    expected_lay_rate,
    weekly_revenue,
    feed_bags_expected,
    weekly_feed_cost
)

# ── Simulation parameters ─────────────────────────────────────────────────────
N_SIMULATIONS   = 10_000
HORIZON_WEEKS   = 12
LABOR_MONTHLY   = 90_000
MEDICATION_COST = 9_000

# ── Kaduna market distributions ───────────────────────────────────────────────
EGG_PRICE_MEAN  = 5_250
EGG_PRICE_STD   = 750
FEED_PRICE_MEAN = 22_500
FEED_PRICE_STD  = 2_500
DIESEL_MEAN     = 1_750
DIESEL_STD      = 250
SHOCK_PROB      = 0.008
SHOCK_MORTALITY = (0.02, 0.06)

# ── Opening cash ──────────────────────────────────────────────────────────────
OPENING_CASH    = 100_000   # tight launch


def get_current_state(engine) -> dict:
    """Read the most recent week from farm_state."""
    df = pd.read_sql("""
        SELECT * FROM farm_state
        ORDER BY week_number DESC
        LIMIT 1
    """, engine)

    if df.empty:
        raise ValueError("farm_state is empty — run seed.py and state_engine.py first.")

    row = df.iloc[0]
    return {
        "week":        int(row["week_number"]),
        "surviving":   int(row["surviving_birds"]),
        "cum_revenue": float(row["cumulative_revenue"]),
        "cum_cost":    float(row["cumulative_cost"]),
        "cash_on_hand": float(row["cumulative_revenue"]) - float(row["cumulative_cost"]) + OPENING_CASH,
    }


def run_single_path(state: dict, rng: np.random.Generator) -> dict:
    """
    Run one 12-week forward simulation path from current state.
    Crisis = 3 consecutive weeks where weekly revenue < weekly cost (drawdown).
    """
    surviving        = state["surviving"]
    cum_revenue      = state["cum_revenue"]
    cum_cost         = state["cum_cost"]
    cash             = state["cash_on_hand"]
    start_week       = state["week"]
    crisis           = False
    consecutive_loss = 0

    for i in range(HORIZON_WEEKS):
        week = start_week + i + 1

        # Stochastic mortality
        if rng.random() < SHOCK_PROB:
            pct    = rng.uniform(*SHOCK_MORTALITY)
            deaths = int(np.ceil(surviving * pct))
        else:
            deaths = rng.integers(0, 3)
        surviving = max(0, surviving - deaths)

        # Stochastic market prices
        egg_price  = max(3_000, rng.normal(EGG_PRICE_MEAN, EGG_PRICE_STD))
        feed_price = max(15_000, rng.normal(FEED_PRICE_MEAN, FEED_PRICE_STD))
        diesel     = max(1_000, rng.normal(DIESEL_MEAN, DIESEL_STD))

        # Production
        lay_rate       = expected_lay_rate(week)
        actual_lay     = float(np.clip(lay_rate + rng.normal(0, 0.03), 0, 1))
        eggs_collected = int(surviving * actual_lay * 7)
        eggs_sold      = int(eggs_collected * rng.uniform(0.92, 0.98))

        # Revenue and costs
        revenue     = weekly_revenue(eggs_sold, egg_price)
        feed_bags   = feed_bags_expected(surviving)
        feed_cost   = weekly_feed_cost(feed_bags, feed_price)
        diesel_cost = round(rng.uniform(20, 40) * diesel, 2)
        labor_cost  = round(LABOR_MONTHLY / 4.33, 2)
        med_cost    = MEDICATION_COST if week % 4 == 0 else 0
        total_cost  = round(feed_cost + diesel_cost + labor_cost + med_cost, 2)

        cum_revenue += revenue
        cum_cost    += total_cost
        cash         = round(cash + revenue - total_cost, 2)

        # ── Drawdown crisis logic ─────────────────────────────────────────────
        if revenue < total_cost:
            consecutive_loss += 1
            if consecutive_loss >= 3:
                crisis = True
        else:
            consecutive_loss = 0

    return {
        "pnl":    round(cum_revenue - cum_cost, 2),
        "crisis": crisis
    }


def run_simulation():
    conn   = get_connection()
    engine = get_engine()

    state = get_current_state(engine)
    print(f"  📊 Running {N_SIMULATIONS:,} simulations from week {state['week']} "
          f"over {HORIZON_WEEKS}-week horizon...")

    rng     = np.random.default_rng(seed=42)
    results = [run_single_path(state, rng) for _ in range(N_SIMULATIONS)]

    pnls   = np.array([r["pnl"]    for r in results])
    crises = np.array([r["crisis"] for r in results])

    p10         = round(float(np.percentile(pnls, 10)), 2)
    p50         = round(float(np.percentile(pnls, 50)), 2)
    p90         = round(float(np.percentile(pnls, 90)), 2)
    prob_crisis = round(float(crises.mean()), 4)
    sell_signal = bool(p50 > state["cum_revenue"] - state["cum_cost"])
    cull_signal = bool(state["week"] >= 45 and p50 < 0)

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO simulation_results
        (week_number, p10_profit, p50_profit, p90_profit,
         prob_cash_crisis, sell_signal, cull_signal)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (week_number) DO UPDATE SET
            p10_profit       = EXCLUDED.p10_profit,
            p50_profit       = EXCLUDED.p50_profit,
            p90_profit       = EXCLUDED.p90_profit,
            prob_cash_crisis = EXCLUDED.prob_cash_crisis,
            sell_signal      = EXCLUDED.sell_signal,
            cull_signal      = EXCLUDED.cull_signal,
            run_date         = NOW()
    """, (state["week"], p10, p50, p90, prob_crisis, sell_signal, cull_signal))

    conn.commit()
    cur.close()
    engine.dispose()

    print(f"\n✅ Simulation complete.")
    print(f"   P10 profit  : NGN {p10:>15,.2f}  (bad case)")
    print(f"   P50 profit  : NGN {p50:>15,.2f}  (median)")
    print(f"   P90 profit  : NGN {p90:>15,.2f}  (good case)")
    print(f"   Crisis prob : {prob_crisis:.1%}")
    print(f"   Sell signal : {sell_signal}")
    print(f"   Cull signal : {cull_signal}")


if __name__ == "__main__":
    run_simulation()