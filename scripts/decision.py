import sys
sys.path.insert(0, ".")

import pandas as pd
from scripts.db_config import get_connection, get_engine
from scripts.utils import breakeven_price_per_crate, eggs_to_crates

# ── Alert thresholds ──────────────────────────────────────────────────────────
LAY_RATE_DEVIATION_AMBER = -0.05   # 5% below expected
LAY_RATE_DEVIATION_RED   = -0.10   # 10% below expected
FEED_STOCK_AMBER_WEEKS   = 3       # less than 3 weeks feed stock
FEED_STOCK_RED_WEEKS     = 2       # less than 2 weeks feed stock
CASH_RUNWAY_AMBER_WEEKS  = 4       # less than 4 weeks cash runway
CASH_RUNWAY_RED_WEEKS    = 2       # less than 2 weeks cash runway
CULL_WEEK_THRESHOLD      = 45      # start evaluating cull signal from week 45


def evaluate_tripwires(row: pd.Series, breakeven: float, price: float) -> list[dict]:
    """
    Evaluate four early warning tripwires for a given week.
    Returns a list of alerts to fire.
    """
    alerts = []

    # ── Tripwire 1: Lay rate deviation ───────────────────────────────────────
    deviation = float(row["lay_rate_deviation"])
    if deviation <= LAY_RATE_DEVIATION_RED:
        alerts.append({
            "alert_type":         "LAY_RATE",
            "severity":           "RED",
            "message":            f"Lay rate is {abs(deviation):.1%} below expected. Immediate investigation required.",
            "recommended_action": "Inspect flock for disease, nutrition deficiency, or stress. Contact vet."
        })
    elif deviation <= LAY_RATE_DEVIATION_AMBER:
        alerts.append({
            "alert_type":         "LAY_RATE",
            "severity":           "AMBER",
            "message":            f"Lay rate is {abs(deviation):.1%} below expected. Monitor closely.",
            "recommended_action": "Review feed quality and flock health. Check for early disease signs."
        })

    # ── Tripwire 2: Feed stock ────────────────────────────────────────────────
    feed_weeks = float(row["feed_stock_weeks"])
    if feed_weeks <= FEED_STOCK_RED_WEEKS:
        alerts.append({
            "alert_type":         "FEED_STOCK",
            "severity":           "RED",
            "message":            f"Feed stock critically low — {feed_weeks:.1f} weeks remaining.",
            "recommended_action": "Order feed immediately. Risk of production collapse within days."
        })
    elif feed_weeks <= FEED_STOCK_AMBER_WEEKS:
        alerts.append({
            "alert_type":         "FEED_STOCK",
            "severity":           "AMBER",
            "message":            f"Feed stock at {feed_weeks:.1f} weeks. Reorder window opening.",
            "recommended_action": "Place feed order within the next 7 days."
        })

    # ── Tripwire 3: Cash runway ───────────────────────────────────────────────
    runway = float(row["cash_runway_weeks"])
    if runway <= CASH_RUNWAY_RED_WEEKS:
        alerts.append({
            "alert_type":         "CASH_RUNWAY",
            "severity":           "RED",
            "message":            f"Cash runway critically low — {runway:.1f} weeks remaining.",
            "recommended_action": "Sell egg inventory immediately. Explore emergency credit options."
        })
    elif runway <= CASH_RUNWAY_AMBER_WEEKS:
        alerts.append({
            "alert_type":         "CASH_RUNWAY",
            "severity":           "AMBER",
            "message":            f"Cash runway at {runway:.1f} weeks. Monitor cash position closely.",
            "recommended_action": "Accelerate egg sales. Defer non-essential costs."
        })

    # ── Tripwire 4: Egg price vs break-even ───────────────────────────────────
    if breakeven > 0 and price > 0:
        margin_ratio = price / breakeven  # >1.0 means profitable
        if margin_ratio < 1.05:           # price within 5% of break-even
            alerts.append({
                "alert_type":         "EGG_PRICE",
                "severity":           "RED",
                "message":            f"Egg price NGN {price:,.0f} is within 5% of break-even NGN {breakeven:,.0f}. Margin critically thin.",
                "recommended_action": "Hold eggs if storage permits. Review all discretionary costs."
            })
        elif margin_ratio < 1.15:         # price within 15% of break-even
            alerts.append({
                "alert_type":         "EGG_PRICE",
                "severity":           "AMBER",
                "message":            f"Egg price NGN {price:,.0f} is within 15% of break-even NGN {breakeven:,.0f}. Monitor closely.",
                "recommended_action": "Monitor market prices daily. Prepare contingency plan."
            })

        return alerts


def run_decision_engine():
    conn   = get_connection()
    engine = get_engine()

    # ── Load latest farm state and inputs ─────────────────────────────────────
    state = pd.read_sql("""
        SELECT fs.*, fi.eggs_sold, fi.price_per_crate,
               fi.feed_bags_used, fi.diesel_litres
        FROM farm_state fs
        JOIN farm_inputs fi ON fs.week_number = fi.week_number
        ORDER BY fs.week_number DESC
        LIMIT 1
    """, engine)

    if state.empty:
        raise ValueError("farm_state is empty — run seed.py and state_engine.py first.")

    row          = state.iloc[0]
    week         = int(row["week_number"])
    eggs_sold    = int(row["eggs_sold"])
    price        = float(row["price_per_crate"])
    crates_sold  = eggs_to_crates(eggs_sold)

    # Weekly break-even — what price per crate covers this week's costs
    labor_cost   = round(90_000 / 4.33, 2)
    med_cost     = 9_000 if week % 4 == 0 else 0
    weekly_cost  = round(
        float(row["feed_bags_used"]) * 22_500 +
        float(row["diesel_litres"]) * 1_750 +
        labor_cost + med_cost, 2
    )
    breakeven    = breakeven_price_per_crate(weekly_cost, crates_sold)

    # ── Evaluate tripwires ────────────────────────────────────────────────────
    alerts = evaluate_tripwires(row, breakeven,price)

    # ── Pricing signal ────────────────────────────────────────────────────────
    sell_now = price >= breakeven

    # ── Cull signal ───────────────────────────────────────────────────────────
    cull_now = week >= CULL_WEEK_THRESHOLD and float(row["cumulative_pnl"]) < 0

    # ── Write alerts to database ──────────────────────────────────────────────
    cur = conn.cursor()
    for alert in alerts:
        cur.execute("""
            INSERT INTO alerts
            (week_number, alert_type, severity, message, recommended_action, delivery_channel)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (week, alert["alert_type"], alert["severity"],
              alert["message"], alert["recommended_action"], "dashboard"))

    conn.commit()
    cur.close()
    engine.dispose()

    # ── Summary output ────────────────────────────────────────────────────────
    print(f"\n✅ Decision engine complete — week {week}.")
    print(f"   Break-even price : NGN {breakeven:>10,.2f} per crate")
    print(f"   Current price    : NGN {price:>10,.2f} per crate")
    print(f"   Sell signal      : {sell_now}")
    print(f"   Cull signal      : {cull_now}")
    print(f"   Alerts fired     : {len(alerts)}")
    for a in alerts:
        print(f"   [{a['severity']}] {a['alert_type']} — {a['message']}")


if __name__ == "__main__":
    run_decision_engine()


