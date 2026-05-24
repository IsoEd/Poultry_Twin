import math

# ── Laying curve ──────────────────────────────────────────────────────────────
def expected_lay_rate(week: int) -> float:
    """
    Piecewise laying curve for ISA Brown POL birds in tropical Nigerian conditions.
    Week 1 = arrival at ~18 weeks biological age, already near peak production.
    """
    if week <= 4:
        return 0.85 + (0.87 - 0.85) * (week - 1) / 3
    elif week <= 15:
        return 0.87 - (0.87 - 0.82) * (week - 4) / 11
    else:
        return 0.82 - (0.82 - 0.62) * (week - 15) / 37


# ── Egg production ────────────────────────────────────────────────────────────
def eggs_expected(surviving_birds: int, week: int) -> int:
    """Expected eggs for the week based on surviving birds and lay curve."""
    return math.floor(surviving_birds * expected_lay_rate(week) * 7)


def eggs_to_crates(eggs: int) -> float:
    """Convert egg count to crates (30 eggs per crate)."""
    return eggs / 30


# ── Revenue ───────────────────────────────────────────────────────────────────
def weekly_revenue(eggs_sold: int, price_per_crate: float) -> float:
    """Revenue from eggs sold in a given week."""
    return round(eggs_to_crates(eggs_sold) * price_per_crate, 2)


# ── Feed ──────────────────────────────────────────────────────────────────────
def weekly_feed_cost(feed_bags_used: float, feed_price_per_bag: float) -> float:
    """Total feed cost for the week."""
    return round(feed_bags_used * feed_price_per_bag, 2)


def feed_bags_expected(surviving_birds: int, base_flock: int = 500,
                        bags_per_500: float = 7.5) -> float:
    """Expected feed bags for the week scaled to surviving flock."""
    return round((surviving_birds / base_flock) * bags_per_500, 2)


# ── Feed conversion ratio ─────────────────────────────────────────────────────
def compute_fcr(feed_bags: float, eggs_collected: int,
                kg_per_bag: float = 25, kg_per_egg: float = 0.06) -> float:
    """
    Feed Conversion Ratio: feed consumed (kg) / eggs produced (kg).
    Lower is better.
    """
    feed_kg = feed_bags * kg_per_bag
    eggs_kg = eggs_collected * kg_per_egg
    return round(feed_kg / eggs_kg, 4) if eggs_kg > 0 else 0.0


# ── Lay rate deviation ────────────────────────────────────────────────────────
def lay_rate_deviation(actual: float, expected: float) -> float:
    """Signed deviation of actual from expected lay rate."""
    return round(actual - expected, 4)


# ── Cash runway ───────────────────────────────────────────────────────────────
def cash_runway(cash_on_hand: float, weekly_burn: float) -> float:
    """
    Weeks of cash remaining at current burn rate.
    Returns 99 if burn rate is zero to avoid division errors.
    """
    if weekly_burn <= 0:
        return 99.0
    return round(cash_on_hand / weekly_burn, 2)


# ── Leakage detection ─────────────────────────────────────────────────────────
def egg_variance(expected: int, reported: int) -> int:
    """Absolute difference between expected and reported eggs."""
    return expected - reported


def variance_pct(expected: int, reported: int) -> float:
    """
    Variance as a percentage of expected eggs.
    More interpretable than Z-score for a single farm operator.
    """
    if expected == 0:
        return 0.0
    return round((expected - reported) / expected * 100, 2)


def leakage_flag(variance_percentage: float) -> str:
    """
    Classify leakage severity by variance percentage.
    NORMAL < 5% | WATCH 5-10% | FLAG > 10%
    """
    if variance_percentage > 10:
        return "FLAG"
    elif variance_percentage > 5:
        return "WATCH"
    return "NORMAL"


# ── Break-even ────────────────────────────────────────────────────────────────
def breakeven_price_per_crate(total_weekly_cost: float, crates_sold: float) -> float:
    """Minimum price per crate needed to cover weekly costs."""
    if crates_sold <= 0:
        return 0.0
    return round(total_weekly_cost / crates_sold, 2)


def is_above_breakeven(price_per_crate: float, breakeven: float) -> bool:
    """True if current market price covers costs."""
    return price_per_crate >= breakeven