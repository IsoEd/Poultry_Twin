import sys
sys.path.insert(0, ".")

import pandas as pd
from scripts.db_config import get_connection
from scripts.utils import (
    expected_lay_rate,
    compute_fcr,
    lay_rate_deviation,
    cash_runway,
    breakeven_price_per_crate,
    eggs_to_crates
)

# ── Farm constants ────────────────────────────────────────────────────────────
STARTING_FLOCK  = 500
LABOR_MONTHLY   = 90_000
MEDICATION_COST = 9_000
WEEK1_CAPITAL   = 5_110_000

def run_state_engine():
    conn = get_connection()
    cur  = conn.cursor()

    # ── Load farm_inputs and market_prices ────────────────────────────────────
    inputs  = pd.read_sql("SELECT * FROM farm_inputs ORDER BY week_number", conn)
    markets = pd.read_sql("SELECT * FROM market_prices ORDER BY week_number", conn)

    df = pd.merge(inputs, markets, on="week_number", suffixes=("_in", "_mkt"))

    # ── Recompute farm_state from scratch ─────────────────────────────────────
    cur.execute("TRUNCATE farm_state RESTART IDENTITY;")

    surviving    = STARTING_FLOCK
    cum_revenue  = 0
    cum_cost     = 0
    cash_on_hand = 500_000

    for _, row in df.iterrows():
        week         = int(row["week_number"])
        wdate        = row["week_date_in"]
        eggs_collected = int(row["eggs_collected"])
        eggs_sold    = int(row["eggs_sold"])
        feed_bags    = float(row["feed_bags_used"])
        diesel_l     = float(row["diesel_litres"])
        bird_deaths  = int(row["bird_deaths"])
        egg_price    = float(row["price_per_crate"])
        feed_price   = float(row["feed_price_per_bag"])
        diesel_price = float(row["diesel_per_litre"])

        # Update surviving birds
        surviving = max(0, surviving - bird_deaths)

        # Lay rates
        exp_lay    = expected_lay_rate(week)
        actual_lay = (eggs_collected / (surviving * 7)) if surviving > 0 else 0
        deviation  = lay_rate_deviation(actual_lay, exp_lay)

        # Revenue
        from scripts.utils import weekly_revenue
        revenue    = weekly_revenue(eggs_sold, egg_price)

        # Costs
        feed_cost   = round(feed_bags * feed_price, 2)
        diesel_cost = round(diesel_l * diesel_price, 2)
        labor_cost  = round(LABOR_MONTHLY / 4.33, 2)
        med_cost    = MEDICATION_COST if week % 4 == 0 else 0
        capital     = WEEK1_CAPITAL if week == 1 else 0
        total_cost  = round(feed_cost + diesel_cost + labor_cost + med_cost + capital, 2)

        cum_revenue += revenue
        cum_cost    += total_cost
        cum_pnl      = round(cum_revenue - cum_cost, 2)
        cash_on_hand = round(cash_on_hand + revenue - total_cost, 2)

        # Derived metrics
        fcr          = compute_fcr(feed_bags, eggs_collected)
        weekly_burn  = total_cost if total_cost > 0 else 1
        runway       = cash_runway(cash_on_hand, weekly_burn)
        crates_sold  = eggs_to_crates(eggs_sold)
        feed_stock_wks = round(cash_on_hand / (feed_bags * feed_price), 2) if feed_price > 0 else 0

        cur.execute("""
            INSERT INTO farm_state
            (week_number, week_date, surviving_birds, expected_lay_rate, actual_lay_rate,
             lay_rate_deviation, feed_stock_weeks, cumulative_revenue, cumulative_cost,
             cumulative_pnl, cash_runway_weeks, fcr)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (week, wdate, surviving, round(exp_lay, 4), round(actual_lay, 4),
              deviation, feed_stock_wks, cum_revenue, cum_cost,
              cum_pnl, runway, fcr))

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ State engine complete.")
    print(f"   Surviving birds at week {week} : {surviving}")
    print(f"   Cumulative revenue            : NGN {cum_revenue:>15,.2f}")
    print(f"   Cumulative cost               : NGN {cum_cost:>15,.2f}")
    print(f"   Cumulative P&L                : NGN {cum_pnl:>15,.2f}")
    print(f"   Final cash on hand            : NGN {cash_on_hand:>15,.2f}")

if __name__ == "__main__":
    run_state_engine()