import sys
sys.path.insert(0, ".")

import random
import math
from datetime import date, timedelta
from scripts.db_config import get_connection
from scripts.utils import (
    expected_lay_rate,
    feed_bags_expected,
    weekly_feed_cost,
    weekly_revenue,
    compute_fcr,
    lay_rate_deviation,
    cash_runway
)

# ── Seed for reproducibility ──────────────────────────────────────────────────
random.seed(42)

# ── Farm parameters ───────────────────────────────────────────────────────────
STARTING_FLOCK        = 500
CYCLE_START           = date(2024, 1, 1)
LABOR_MONTHLY         = 90_000      # farm hand NGN 55,000 + security NGN 35,000
MEDICATION_COST       = 9_000       # every 4th week
SHOCK_PROB            = 0.008       # 0.8% per week
SHOCK_MORTALITY       = (0.02, 0.06)
POL_COST_PER_BIRD     = 8_500
BIRD_PURCHASE_COST    = STARTING_FLOCK * POL_COST_PER_BIRD  # NGN 4,250,000
INFRASTRUCTURE_COST   = 860_000     # 4 battery cages + egg crates/trays
WEEK1_CAPITAL         = BIRD_PURCHASE_COST + INFRASTRUCTURE_COST  # NGN 5,110,000

# ── Kaduna market ranges ──────────────────────────────────────────────────────
EGG_PRICE_RANGE       = (5_000, 5_500)
FEED_PRICE_RANGE      = (20_000, 25_000)
DIESEL_RANGE          = (1_500, 2_000)
USD_NGN_RANGE         = (1_350, 1_450)

# ── Helpers ───────────────────────────────────────────────────────────────────
def week_date(week: int) -> date:
    return CYCLE_START + timedelta(weeks=week - 1)

def apply_shock(surviving: int, week: int) -> int:
    if random.random() < SHOCK_PROB:
        pct = random.uniform(*SHOCK_MORTALITY)
        deaths = math.ceil(surviving * pct)
        print(f"  ⚡ Shock at week {week}: {deaths} birds lost ({pct:.1%})")
        return deaths
    return 0

# ── Main seed function ────────────────────────────────────────────────────────
def seed():
    conn = get_connection()
    cur  = conn.cursor()

    # Clear existing data
    cur.execute("TRUNCATE farm_profile, farm_inputs, market_prices, farm_state, "
                "simulation_results, alerts, leakage_events, volatility_forecasts "
                "RESTART IDENTITY CASCADE;")

    # ── farm_profile ──────────────────────────────────────────────────────────
    cur.execute("""
        INSERT INTO farm_profile (farm_name, location, starting_flock, cycle_start_date, target_cull_week)
        VALUES (%s, %s, %s, %s, %s)
    """, ("Kaduna Layer Farm", "Kaduna, Kaduna State, Nigeria", STARTING_FLOCK, CYCLE_START, 72))

    # ── Weekly loop ───────────────────────────────────────────────────────────
    surviving    = STARTING_FLOCK
    cum_revenue  = 0
    cum_cost     = 0
    cash_on_hand = 100_000  # tight launch — most capital spent on birds and infrastructure

    print(f"  🐔 Week 1 capital outlay: NGN {WEEK1_CAPITAL:,.0f} (birds + infrastructure)")

    for week in range(1, 53):
        wdate    = week_date(week)
        lay_rate = expected_lay_rate(week)

        # Mortality
        shock_deaths  = apply_shock(surviving, week)
        normal_deaths = random.randint(0, 2)
        total_deaths  = shock_deaths + normal_deaths
        surviving     = max(0, surviving - total_deaths)

        # Production
        actual_lay     = max(0, min(1, lay_rate + random.uniform(-0.03, 0.03)))
        eggs_collected = math.floor(surviving * actual_lay * 7)
        eggs_sold      = math.floor(eggs_collected * random.uniform(0.92, 0.98))

        # Market prices
        egg_price  = round(random.uniform(*EGG_PRICE_RANGE), 2)
        feed_price = round(random.uniform(*FEED_PRICE_RANGE), 2)
        diesel     = round(random.uniform(*DIESEL_RANGE), 2)
        usd_ngn    = round(random.uniform(*USD_NGN_RANGE), 2)

        # Costs — using utils functions
        feed_bags   = feed_bags_expected(surviving)
        diesel_l    = round(random.uniform(20, 40), 2)
        feed_cost   = weekly_feed_cost(feed_bags, feed_price)
        diesel_cost = round(diesel_l * diesel, 2)
        labor_cost  = round(LABOR_MONTHLY / 4.33, 2)
        med_cost    = MEDICATION_COST if week % 4 == 0 else 0
        capital     = WEEK1_CAPITAL if week == 1 else 0
        total_cost  = round(feed_cost + diesel_cost + labor_cost + med_cost + capital, 2)

        # Revenue — using utils function
        revenue      = weekly_revenue(eggs_sold, egg_price)

        cum_revenue  += revenue
        cum_cost     += total_cost
        cum_pnl       = round(cum_revenue - cum_cost, 2)
        cash_on_hand  = round(cash_on_hand + revenue - total_cost, 2)

        # Derived metrics — using utils functions
        deviation      = lay_rate_deviation(actual_lay, lay_rate)
        feed_stock_wks = round(random.uniform(2, 6), 2)
        fcr            = compute_fcr(feed_bags, eggs_collected)
        weekly_burn    = total_cost if total_cost > 0 else 1
        runway         = cash_runway(cash_on_hand, weekly_burn)

        # ── farm_inputs ───────────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO farm_inputs
            (week_number, week_date, eggs_collected, eggs_sold, price_per_crate,
             bird_deaths, feed_bags_used, diesel_litres, cash_on_hand)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (week, wdate, eggs_collected, eggs_sold, egg_price,
              total_deaths, feed_bags, diesel_l, cash_on_hand))

        # ── market_prices ─────────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO market_prices
            (week_number, week_date, egg_price_per_crate, feed_price_per_bag,
             diesel_per_litre, usd_ngn_rate)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (week, wdate, egg_price, feed_price, diesel, usd_ngn))

        # ── farm_state ────────────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO farm_state
            (week_number, week_date, surviving_birds, expected_lay_rate, actual_lay_rate,
             lay_rate_deviation, feed_stock_weeks, cumulative_revenue, cumulative_cost,
             cumulative_pnl, cash_runway_weeks, fcr)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (week, wdate, surviving, round(lay_rate, 4), round(actual_lay, 4),
              deviation, feed_stock_wks, cum_revenue, cum_cost,
              cum_pnl, runway, fcr))

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n✅ Seed complete.")
    print(f"   Surviving birds at week 52 : {surviving}")
    print(f"   Cumulative revenue         : NGN {cum_revenue:>15,.2f}")
    print(f"   Cumulative cost            : NGN {cum_cost:>15,.2f}")
    print(f"   Cumulative P&L             : NGN {cum_pnl:>15,.2f}")
    print(f"   Final cash on hand         : NGN {cash_on_hand:>15,.2f}")

if __name__ == "__main__":
    seed()