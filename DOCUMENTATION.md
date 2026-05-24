# Poultry Financial Twin — Technical Documentation

---

## 1. Project Overview

The Poultry Financial Twin is a farm management system, financial simulator, and early warning system built for a 500-bird ISA Brown layer operation in Kaduna State, Nigeria. It is designed to answer three questions a small-scale farmer cannot easily answer with a spreadsheet:

1. Is my farm financially healthy right now?
2. What is likely to happen to my finances over the next 12 weeks?
3. What should I do today — sell eggs, hold, reorder feed, or cull the flock?

---

## 2. Design Principles

The system is built on four underlying design principles that govern every architectural decision.

**Separation of Concerns**
Every component does one thing only. The database stores data. Python computes intelligence. The dashboard displays results. No calculation happens in SQL. No business logic lives in the dashboard. No data is stored in Python variables between runs.

**Single Source of Truth**
PostgreSQL is the only authoritative record of the farm's state. `utils.py` is the only place biological and financial functions are defined. If the laying curve changes, it changes in one place and every engine picks it up automatically.

**Progressive Computation**
Each engine builds on the output of the previous one in a deliberate dependency chain: raw inputs → farm state → simulation → decisions → alerts. Nothing downstream runs until what it depends on is ready.

**Stochastic Over Deterministic**
The system never produces a single number and calls it a prediction. Every forward-looking output is expressed as a probability distribution — P10, P50, P90 — because the future is uncertain and a system that pretends otherwise is misleading.

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────┐
│               FARMER DATA ENTRY                     │
│         Dash Form → farm_inputs + market_prices     │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│              POSTGRESQL DATABASE                    │
│                  poultry_twin                       │
│                                                     │
│  farm_profile     farm_inputs    market_prices      │
│  farm_state       simulation_results                │
│  alerts           leakage_events  volatility_       │
│                                   forecasts         │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│         AUTOMATED PIPELINE (Every Monday 06:00)     │
│                                                     │
│  1. state_engine.py   → computes farm state         │
│  2. simulation.py     → 10,000 Monte Carlo paths    │
│  3. decision.py       → evaluates tripwires         │
│  4. leakage.py        → detects theft/leakage       │
│  5. volatility.py     → forecasts price volatility  │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│           PLOTLY DASH OPERATOR DASHBOARD            │
│                                                     │
│  Tab 1: Live farm monitoring                        │
│  Tab 2: Weekly data entry form                      │
└─────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

**Database:** `poultry_twin` (PostgreSQL 15/16)

### 4.1 farm_profile
Static farm identity. One row only — never updated during operation.

| Column | Type | Description |
|---|---|---|
| id | SERIAL PK | Primary key |
| farm_name | VARCHAR | Name of the farm |
| location | VARCHAR | Physical location |
| starting_flock | INTEGER | Birds purchased at cycle start |
| cycle_start_date | DATE | Date of first week |
| target_cull_week | INTEGER | Week at which flock is culled |

### 4.2 farm_inputs
Farmer-entered weekly data. One row per week.

| Column | Type | Description |
|---|---|---|
| id | SERIAL PK | Primary key |
| week_number | INTEGER UNIQUE | Farm week (1–52+) |
| week_date | DATE | Calendar date of week start |
| eggs_collected | INTEGER | Total eggs collected that week |
| eggs_sold | INTEGER | Eggs sold to market |
| price_per_crate | NUMERIC | Price received per crate (NGN) |
| bird_deaths | INTEGER | Bird deaths recorded that week |
| feed_bags_used | NUMERIC | 25kg bags of feed consumed |
| diesel_litres | NUMERIC | Diesel consumed (litres) |
| cash_on_hand | NUMERIC | Cash available at week end (NGN) |

### 4.3 market_prices
External market data. One row per week.

| Column | Type | Description |
|---|---|---|
| id | SERIAL PK | Primary key |
| week_number | INTEGER UNIQUE | Farm week |
| week_date | DATE | Calendar date |
| egg_price_per_crate | NUMERIC | Market egg price (NGN) |
| feed_price_per_bag | NUMERIC | Feed cost per 25kg bag (NGN) |
| diesel_per_litre | NUMERIC | Diesel price per litre (NGN) |
| usd_ngn_rate | NUMERIC | Exchange rate |

### 4.4 farm_state
System-computed farm intelligence. Written by `state_engine.py`. One row per week.

| Column | Type | Description |
|---|---|---|
| id | SERIAL PK | Primary key |
| week_number | INTEGER UNIQUE | Farm week |
| week_date | DATE | Calendar date |
| surviving_birds | INTEGER | Birds alive after this week's mortality |
| expected_lay_rate | NUMERIC | Curve-predicted lay rate for this week |
| actual_lay_rate | NUMERIC | Observed lay rate from farmer data |
| lay_rate_deviation | NUMERIC | Actual minus expected (signed) |
| feed_stock_weeks | NUMERIC | Estimated weeks of feed remaining |
| cumulative_revenue | NUMERIC | Total revenue since cycle start (NGN) |
| cumulative_cost | NUMERIC | Total cost since cycle start (NGN) |
| cumulative_pnl | NUMERIC | Cumulative profit/loss (NGN) |
| cash_runway_weeks | NUMERIC | Weeks of cash at current burn rate |
| fcr | NUMERIC | Feed Conversion Ratio |

### 4.5 simulation_results
Monte Carlo projection output. One row per week — overwritten on each run.

| Column | Type | Description |
|---|---|---|
| id | SERIAL PK | Primary key |
| week_number | INTEGER UNIQUE | Farm week simulation was run from |
| run_date | TIMESTAMP | When simulation was executed |
| p10_profit | NUMERIC | 10th percentile projected profit (NGN) |
| p50_profit | NUMERIC | 50th percentile projected profit (NGN) |
| p90_profit | NUMERIC | 90th percentile projected profit (NGN) |
| prob_cash_crisis | NUMERIC | Probability of drawdown crisis (0–1) |
| sell_signal | BOOLEAN | TRUE if current price favours selling |
| cull_signal | BOOLEAN | TRUE if culling is economically optimal |

### 4.6 alerts
Early warning alerts fired by `decision.py`. One row per alert event.

| Column | Type | Description |
|---|---|---|
| id | SERIAL PK | Primary key |
| week_number | INTEGER | Week alert was fired |
| alert_type | VARCHAR | LAY_RATE, FEED_STOCK, CASH_RUNWAY, EGG_PRICE |
| severity | VARCHAR | AMBER or RED |
| message | TEXT | Human-readable alert description |
| recommended_action | TEXT | Suggested response |
| delivery_channel | VARCHAR | dashboard |
| delivery_timestamp | TIMESTAMP | When alert was delivered |

### 4.7 leakage_events
Egg variance and theft detection. One row per week.

| Column | Type | Description |
|---|---|---|
| id | SERIAL PK | Primary key |
| week_number | INTEGER UNIQUE | Farm week |
| week_date | DATE | Calendar date |
| expected_eggs | INTEGER | Biologically expected egg count |
| reported_eggs | INTEGER | Farmer-reported egg count |
| variance | INTEGER | Expected minus reported |
| z_score | NUMERIC | Variance as % of expected |
| flag_level | VARCHAR | NORMAL, WATCH, or FLAG |

### 4.8 volatility_forecasts
4-week forward egg price volatility. One row per week — overwritten on each run.

| Column | Type | Description |
|---|---|---|
| id | SERIAL PK | Primary key |
| week_number | INTEGER UNIQUE | Farm week forecast was run from |
| run_date | TIMESTAMP | When forecast was executed |
| vol_week_1 | NUMERIC | Week +1 volatility estimate (%) |
| vol_week_2 | NUMERIC | Week +2 volatility estimate (%) |
| vol_week_3 | NUMERIC | Week +3 volatility estimate (%) |
| vol_week_4 | NUMERIC | Week +4 volatility estimate (%) |
| garch_alpha | NUMERIC | Not used — kept for schema compatibility |
| garch_beta | NUMERIC | Not used — kept for schema compatibility |
| garch_mu | NUMERIC | Mean weekly return |

---

## 5. Biological Model

### 5.1 Point-of-Lay Purchase
The model assumes the farmer purchases ISA Brown birds at 18 weeks biological age — already at or near peak laying production. This is standard practice for small-scale commercial layer operations in northern Nigeria because:

- It eliminates 18 weeks of rearing costs (feed, brooding, high early mortality risk)
- Revenue begins in week 1 of farm operation
- The POL price premium (NGN 8,500 vs NGN 900 for day-old chicks) is roughly offset by avoided rearing costs

### 5.2 Laying Curve
A piecewise linear curve calibrated for ISA Brown in tropical Nigerian conditions:

| Phase | Farm Weeks | Lay Rate | Rationale |
|---|---|---|---|
| Early peak | 1 → 4 | 85% → 87% | Short adjustment period after transport |
| Peak plateau | 4 → 15 | 87% → 82% | Prime production window |
| Production decline | 15 → 52 | 82% → 62% | Natural biological decline |

The curve is implemented in `utils.py` as `expected_lay_rate(week)` and is the single source of truth for all biological projections across the system.

### 5.3 Mortality Model
Two mortality sources are modelled:

**Normal mortality:** 0–2 birds per week — reflects background losses from natural causes.

**Disease shock:** 0.8% weekly probability of a shock event, causing 2–6% flock mortality. The 0.8% probability reflects a vaccinated flock (Newcastle, Gumboro, ILT at purchase; boosters at weeks 8 and 16). An unvaccinated flock would carry 3–5% weekly shock probability.

### 5.4 Feed Conversion Ratio
FCR is calculated as:

```
FCR = feed consumed (kg) / eggs produced (kg)
    = (feed_bags × 25kg) / (eggs_collected × 0.06kg)
```

A FCR below 2.0 is considered efficient for a layer operation. Values above 3.0 indicate a problem — overfeeding, poor feed quality, or declining production.

---

## 6. Financial Model

### 6.1 Capital Structure
Week 1 capital outlay:

| Item | Cost (NGN) |
|---|---|
| 500 ISA Brown POL birds @ NGN 8,500 | 4,250,000 |
| 4 battery cages @ NGN 200,000 (incl. feeders, drinkers, egg trays) | 800,000 |
| Egg crates and trays (bulk) | 60,000 |
| **Total week 1 capital** | **5,110,000** |

Opening cash reserve (tight launch): NGN 100,000

### 6.2 Weekly Operating Costs

| Item | Cost |
|---|---|
| Feed | feed_bags_used × market feed price per bag |
| Diesel | diesel_litres × market diesel price per litre |
| Labor | NGN 90,000 ÷ 4.33 per week |
| Medication | NGN 9,000 every 4th week |

### 6.3 Revenue
```
crates_sold = eggs_sold / 30
revenue = crates_sold × price_per_crate
```

### 6.4 Break-even Price
The minimum egg price per crate needed to cover weekly operating costs:

```
breakeven = total_weekly_cost / crates_sold
```

If market price is within 5% of break-even a RED alert fires. Within 15% triggers AMBER.

---

## 7. Engine Documentation

### 7.1 state_engine.py
**Purpose:** Reads farmer-entered data from `farm_inputs` and `market_prices`, recomputes all derived financial and biological metrics, and writes the results to `farm_state`.

**Inputs:** `farm_inputs`, `market_prices`
**Outputs:** `farm_state`
**Approach:** Full recomputation from scratch on every run — simpler and safer than incremental updates.

**Key computations:**
- Surviving birds (cumulative mortality subtracted)
- Actual lay rate (eggs_collected ÷ surviving_birds ÷ 7)
- Lay rate deviation (actual minus expected)
- Cumulative revenue, cost, and P&L
- Cash runway (cash_on_hand ÷ weekly_burn)
- FCR (feed_kg ÷ eggs_kg)

### 7.2 simulation.py
**Purpose:** Runs 10,000 Monte Carlo forward simulations from the current farm state across a 12-week horizon. Produces probabilistic profit projections and crisis probability.

**Inputs:** `farm_state` (latest week)
**Outputs:** `simulation_results`
**Paths:** 10,000
**Horizon:** 12 weeks

**Stochastic variables per path per week:**
- Egg price: Normal distribution (mean NGN 5,250, std NGN 750), floored at NGN 3,000
- Feed price: Normal distribution (mean NGN 22,500, std NGN 2,500), floored at NGN 15,000
- Diesel price: Normal distribution (mean NGN 1,750, std NGN 250), floored at NGN 1,000
- Shock mortality: 0.8% weekly probability, 2–6% flock loss
- Normal mortality: 0–2 birds per week
- Lay rate noise: Normal distribution (mean 0, std 3%)

**Crisis definition:** 3 or more consecutive weeks where weekly revenue < weekly cost (drawdown crisis), regardless of cash balance.

**Why 10,000 paths:** Sufficient to produce stable P10/P50/P90 percentile estimates. Fewer paths produce noisy, inconsistent projections. More paths add compute time without meaningful precision gain.

**Sell signal logic:** TRUE if P50 projected profit exceeds current cumulative P&L.
**Cull signal logic:** TRUE if farm week >= 45 and P50 projected profit < 0.

### 7.3 decision.py
**Purpose:** Evaluates four early warning tripwires against the latest farm state and writes alerts to the database.

**Inputs:** `farm_state`, `farm_inputs`, `market_prices` (latest week)
**Outputs:** `alerts`

**Four tripwires:**

| Tripwire | AMBER threshold | RED threshold |
|---|---|---|
| Lay rate deviation | Actual > 5% below expected | Actual > 10% below expected |
| Feed stock | Below 3 weeks remaining | Below 2 weeks remaining |
| Cash runway | Below 4 weeks remaining | Below 2 weeks remaining |
| Egg price margin | Price within 15% of break-even | Price within 5% of break-even |

### 7.4 leakage.py
**Purpose:** Compares expected egg output (birds x lay rate x 7 days) against farmer-reported eggs collected. Flags statistically significant shortfalls that may indicate theft, collection losses, or systematic under-reporting.

**Inputs:** `farm_state`, `farm_inputs`
**Outputs:** `leakage_events`

**Detection method:** Variance expressed as a percentage of expected eggs.

| Flag level | Threshold | Interpretation |
|---|---|---|
| NORMAL | Variance < 5% | Within expected biological variation |
| WATCH | Variance 5–10% | Unusual — monitor closely |
| FLAG | Variance > 10% | Investigate immediately |

**Design decision:** A simpler percentage threshold was chosen over Z-score anomaly detection. Z-scores require sufficient historical variance data to be meaningful — for a single farm with limited history, a fixed percentage threshold is more interpretable and equally effective.

### 7.5 volatility.py
**Purpose:** Computes forward egg price volatility from historical price data. Used to inform the simulation engine's price distribution width.

**Inputs:** `market_prices`
**Outputs:** `volatility_forecasts`

**Method:** Standard deviation of weekly log returns, scaled by sqrt(t) for each forward week (random walk assumption).

```
returns = diff(log(prices)) x 100
vol_week_t = std(returns) x sqrt(t)
```

**Design decision:** A standard deviation approach was chosen over GARCH(1,1) modelling. With 52 weeks of data — particularly synthetic data generated from a uniform distribution — GARCH adds mathematical complexity without producing meaningfully different output. The random walk scaling produces honest increasing uncertainty the further out the forecast goes.

### 7.6 scheduler.py
**Purpose:** Wires all engines together and runs the full pipeline automatically every Monday at 06:00, after the farmer has logged the previous week's data.

**Dependency order:**
1. `state_engine` — must run before simulation (needs current farm state)
2. `simulation` — must run before decision (decision reads simulation signals)
3. `decision` — evaluates tripwires against current state
4. `leakage` — independent, but logically follows state computation
5. `volatility` — independent, runs last

**Manual trigger for testing:**
```bash
python scripts/scheduler.py --now
```

---

## 8. Dashboard Architecture

The operator dashboard is built with Plotly Dash and follows a modular architecture:

| File | Responsibility |
|---|---|
| `app.py` | Dash initialisation, layout registration, callback registration |
| `layouts.py` | Page structure, tab definitions, component placement |
| `callbacks.py` | All interactivity — data fetching and UI updates |
| `components.py` | Reusable visual components — charts, gauges, KPI cards |

**Tab 1 — Operator Dashboard:**
All charts update via a `dcc.Interval` firing every 60 seconds. Each visual is a separate callback reading from PostgreSQL via SQLAlchemy engine.

**Tab 2 — Weekly Data Entry:**
A two-column form collecting 11 fields across farm inputs and market prices. On submit, data is written directly to `farm_inputs` and `market_prices`. The pipeline picks it up on the next scheduled Monday run.

---

## 9. Shared Library — utils.py

All biological and financial functions are centralised in `utils.py` and imported by every engine. This ensures single source of truth for all core calculations.

| Function | Purpose |
|---|---|
| `expected_lay_rate(week)` | Piecewise laying curve |
| `eggs_expected(surviving, week)` | Expected weekly egg count |
| `eggs_to_crates(eggs)` | Convert eggs to crates (div 30) |
| `weekly_revenue(eggs_sold, price)` | Weekly egg revenue |
| `weekly_feed_cost(bags, price)` | Weekly feed cost |
| `feed_bags_expected(surviving)` | Scaled feed consumption |
| `compute_fcr(bags, eggs)` | Feed Conversion Ratio |
| `lay_rate_deviation(actual, expected)` | Signed lay rate deviation |
| `cash_runway(cash, burn)` | Weeks of cash remaining |
| `egg_variance(expected, reported)` | Absolute egg shortfall |
| `variance_pct(expected, reported)` | Shortfall as % of expected |
| `leakage_flag(variance_pct)` | NORMAL / WATCH / FLAG classification |
| `breakeven_price_per_crate(cost, crates)` | Minimum viable egg price |
| `is_above_breakeven(price, breakeven)` | Boolean profitability check |

---

## 10. Known Limitations

**Synthetic data only at launch**
The system ships with 52 weeks of synthetic data generated by `seed.py`. Real utility begins when the farmer starts entering actual weekly data through the data entry form.

**Feed stock calculation**
`feed_stock_weeks` in `farm_state` is currently estimated. A complete implementation would require a `feed_bags_purchased` field in `farm_inputs` to track inventory accurately as: stock = previous_stock + purchased - consumed.

**Single farm only**
The schema is designed for a single farm. Multi-tenancy would require a `farm_id` foreign key across all tables and user authentication.

**No mobile optimisation**
The Dash dashboard is designed for desktop browser use. A farmer checking on a mobile phone would benefit from a responsive layout or a dedicated mobile view.

**Scheduler requires running process**
APScheduler runs as a blocking process. In production this would need to be deployed as a background service or replaced with a task queue like Celery.

---

## 11. Future Improvements

- Add `feed_bags_purchased` to the data entry form and fix feed stock calculation
- Add SMS alert delivery via Twilio for farmers without reliable internet access
- Extend the simulation horizon to 24 weeks for longer-range planning
- Add Sallah and Christmas seasonal price spike modelling (northern Nigeria demand patterns)
- Build a multi-farm version with farm_id partitioning
- Add a cull value calculator — expected revenue from selling remaining birds vs continuing operation
- Deploy on a cloud server (Railway, Render, or AWS) for remote access

---

## 12. Data Flow Summary

```
Farmer enters weekly data (Dash form)
        ↓
farm_inputs + market_prices (PostgreSQL)
        ↓
state_engine.py reads inputs → computes → writes farm_state
        ↓
simulation.py reads farm_state → runs 10,000 paths → writes simulation_results
        ↓
decision.py reads farm_state + market_prices → evaluates tripwires → writes alerts
        ↓
leakage.py reads farm_state + farm_inputs → computes variance → writes leakage_events
        ↓
volatility.py reads market_prices → computes std dev → writes volatility_forecasts
        ↓
Dash dashboard reads all tables → renders live monitoring view
```

---

*Documentation version 1.0 — Poultry Financial Twin*
