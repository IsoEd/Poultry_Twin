# components.py

# ---- THEME & STYLING SETUP ----

from dash import html, dcc
import pandas as pd
import plotly.graph_objects as go

# ---- COLOR PALETTE (Okabe-Ito Colorblind-Friendly) ----
BG_COLOR      = "#121212"   # Deep matte black background
CARD_COLOR    = "#1E1E1E"   # Slightly lighter grey for card surfaces
TEXT_MAIN     = "#FFFFFF"   # High-contrast white
TEXT_MUTED    = "#B0B0B0"   # Muted grey for labels

COLOR_SUCCESS = "#009E73"   # Bluish green  — healthy / good
COLOR_WARNING = "#E69F00"   # Orange        — declining / warning
COLOR_ALERT   = "#D55E00"   # Vermillion    — critical / danger
COLOR_NEUTRAL = "#0072B2"   # Blue          — baseline / normal state

# ---- CARD STYLE ----
CARD_STYLE = {
    "backgroundColor": CARD_COLOR,
    "padding":         "20px",
    "borderRadius":    "10px",
    "boxShadow":       "0 4px 6px rgba(0,0,0,0.3)",
    "marginBottom":    "15px",
    "color":           TEXT_MAIN
}

# ---- PLOTLY BASE TEMPLATE ----
PLOTLY_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor = BG_COLOR,
        plot_bgcolor  = CARD_COLOR,
        font          = dict(family="Inter, sans-serif", color=TEXT_MAIN, size=13),
        title         = dict(font=dict(color=TEXT_MAIN, size=16)),
        xaxis         = dict(gridcolor="#2E2E2E", linecolor="#2E2E2E", tickfont=dict(color=TEXT_MUTED)),
        yaxis         = dict(gridcolor="#2E2E2E", linecolor="#2E2E2E", tickfont=dict(color=TEXT_MUTED)),
        legend        = dict(bgcolor=CARD_COLOR, font=dict(color=TEXT_MUTED)),
        colorway      = [COLOR_NEUTRAL, COLOR_SUCCESS, COLOR_WARNING, COLOR_ALERT]
    )
)

#--- HEADER LAYOUT ---#

def create_header():
    """
    Dashboard header with logo, title, centre label, and live date/time display.
    Date/time updates via a dcc.Interval callback.
    """
    return html.Div(
        style={
            "backgroundColor": CARD_COLOR,
            "padding":         "12px 24px",
            "display":         "flex",
            "alignItems":      "center",
            "justifyContent":  "space-between",
            "borderBottom":    f"2px solid {COLOR_NEUTRAL}",
            "marginBottom":    "16px"
        },
        children=[

            # Left — Logo + Title
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "12px"},
                children=[
                    html.Span("🐔", style={"fontSize": "28px"}),
                    html.Div([
                        html.P(
                            "FINANCIAL POULTRY",
                            style={
                                "color":         TEXT_MAIN,
                                "fontSize":      "13px",
                                "fontWeight":    "bold",
                                "margin":        "0",
                                "letterSpacing": "1.5px"
                            }
                        ),
                        html.P(
                            "TWIN PROJECT DASHBOARD",
                            style={
                                "color":         TEXT_MUTED,
                                "fontSize":      "11px",
                                "margin":        "0",
                                "letterSpacing": "1px"
                            }
                        )
                    ])
                ]
            ),

            # Centre — Live Farm Snapshot label
            html.Div(
                "LIVE FARM SNAPSHOT",
                style={
                    "color":         TEXT_MAIN,
                    "fontSize":      "15px",
                    "fontWeight":    "bold",
                    "letterSpacing": "2px"
                }
            ),

            # Right — Live date/time
            html.Div(
                id="live-datetime",
                style={
                    "color":      TEXT_MUTED,
                    "fontSize":   "13px",
                    "textAlign":  "right"
                }
            )
        ]
    )

#--- KPI Cards ---#

def create_kpi_card(title, value, subtitle=None, border_color=None):
    """
    Generates a standalone, styled numerical KPI card.
    """
    card_border = f"3px solid {border_color}" if border_color else "none"

    return html.Div(
        style={**CARD_STYLE, "borderLeft": card_border},
        children=[
            html.H5(
                title,
                style={
                    "color":           TEXT_MUTED,
                    "margin":          "0 0 10px 0",
                    "fontSize":        "14px",
                    "textTransform":   "uppercase",
                    "letterSpacing":   "1px"
                }
            ),
            html.H2(
                str(value),
                style={
                    "color":      TEXT_MAIN,
                    "margin":     "0",
                    "fontWeight": "bold",
                    "fontSize":   "28px"
                }
            ),
            *([html.P(
                subtitle,
                style={
                    "color":    TEXT_MUTED,
                    "margin":   "5px 0 0 0",
                    "fontSize": "12px"
                }
            )] if subtitle else [])
        ]
    )

#--- FINANCIAL TREND CARDS ---#

def create_financial_trend_chart(df):
    """
    Renders a profit scenario fan chart from simulation_results.
    Expects df with columns: week_number, p10_profit, p50_profit, p90_profit
    """
    fig = go.Figure()

    # P90 upper bound — optimistic scenario
    fig.add_trace(go.Scatter(
        x=df["week_number"],
        y=df["p90_profit"],
        name="P90 — Optimistic",
        line=dict(color=COLOR_SUCCESS, width=1.5, dash="dot")
    ))

    # Confidence band fill between P10 and P90
    fig.add_trace(go.Scatter(
        x=pd.concat([df["week_number"], df["week_number"][::-1]]),
        y=pd.concat([df["p90_profit"], df["p10_profit"][::-1]]),
        fill="toself",
        fillcolor="rgba(0, 114, 178, 0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name="P10–P90 Range",
        showlegend=True
    ))

    # P50 median — base case
    fig.add_trace(go.Scatter(
        x=df["week_number"],
        y=df["p50_profit"],
        name="P50 — Base Case",
        line=dict(color=COLOR_NEUTRAL, width=3)
    ))

    # P10 lower bound — pessimistic scenario
    fig.add_trace(go.Scatter(
        x=df["week_number"],
        y=df["p10_profit"],
        name="P10 — Pessimistic",
        line=dict(color=COLOR_ALERT, width=1.5, dash="dot")
    ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
    
        xaxis=dict(title="Week", showgrid=False),
        yaxis=dict(title="Profit (₦)", gridcolor="#2A2A2A"),
        margin=dict(l=40, r=20, t=60, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False})

#--- GAUGE CHARTS ---#

def create_gauge_chart(title, value, target, max_range=100, unit="%"):
    """
    Renders a gauge chart comparing a live value against a benchmark target.
    Bar color responds dynamically to performance vs target.
    """
    # Dynamic bar color based on performance ratio
    ratio = value / target if target else 0
    if ratio >= 0.95:
        bar_color = COLOR_SUCCESS   # At or near target
    elif ratio >= 0.80:
        bar_color = COLOR_WARNING   # Declining — needs attention
    else:
        bar_color = COLOR_ALERT     # Critical — well below target

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={
            "suffix": unit,
            "font": {"color": TEXT_MAIN, "size": 24}
        },
        title={
            "text": title,
            "font": {"color": TEXT_MUTED, "size": 13}
        },
        gauge={
            "axis": {
                "range": [0, max_range],
                "tickwidth": 1,
                "tickcolor": TEXT_MUTED,
                "tickfont": {"color": TEXT_MUTED}
            },
            "bar": {"color": bar_color},
            "bgcolor": "#2A2A2A",
            "borderwidth": 0,
            "threshold": {
                "line": {"color": COLOR_WARNING, "width": 4},
                "thickness": 0.75,
                "value": target
            }
        }
    ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False})



def create_weekly_production_chart(df):
    """
    Grouped bar chart comparing average actual vs expected lay rate by month.
    Weeks are grouped into 12 months for readability.
    Expects df with columns: week_number, actual_lay_rate, expected_lay_rate
    """
    # ── Month mapping ─────────────────────────────────────────────────────────
    month_map = {
        "Jan": (1,  4),  "Feb": (5,  8),  "Mar": (9,  13),
        "Apr": (14, 17), "May": (18, 21), "Jun": (22, 26),
        "Jul": (27, 30), "Aug": (31, 35), "Sep": (36, 39),
        "Oct": (40, 43), "Nov": (44, 48), "Dec": (49, 52)
    }

    months, actual_rates, expected_rates, colors = [], [], [], []

    for month, (start, end) in month_map.items():
        month_df = df[(df["week_number"] >= start) & (df["week_number"] <= end)]
        if month_df.empty:
            continue
        avg_actual   = month_df["actual_lay_rate"].mean()
        avg_expected = month_df["expected_lay_rate"].mean()
        months.append(month)
        actual_rates.append(round(avg_actual, 4))
        expected_rates.append(round(avg_expected, 4))
        colors.append(COLOR_SUCCESS if avg_actual >= (avg_expected - 0.03) else COLOR_WARNING)

    fig = go.Figure()

    # Actual lay rate — color driven by performance vs expected
    fig.add_trace(go.Bar(
        x=months,
        y=actual_rates,
        name="Actual Lay Rate",
        marker=dict(color=colors)
    ))

    # Expected lay rate — muted reference
    fig.add_trace(go.Bar(
        x=months,
        y=expected_rates,
        name="Expected Lay Rate",
        marker=dict(color=COLOR_NEUTRAL, opacity=0.4)
    ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Monthly Lay Rate — Actual vs Expected",
        barmode="group",
        xaxis=dict(title="Month", showgrid=False),
        yaxis=dict(title="Lay Rate", gridcolor="#2A2A2A",
                   tickformat=".0%"),
        margin=dict(l=40, r=20, t=60, b=30),
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1)
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False})

#--- RESOURCE USAGE CHARTS ---#

def create_resource_usage_chart(df):
    """
    Donut chart showing quarterly net profit breakdown.
    Pulls cumulative P&L from farm_state and differences by quarter.
    Expects df with columns: feed_stock_weeks, cash_runway_weeks (unused now)
    """
    # ── Load farm_state for quarterly P&L ────────────────────────────────────
    from scripts.db_config import get_engine
    engine = get_engine()
    fs = pd.read_sql(
        "SELECT week_number, cumulative_pnl FROM farm_state ORDER BY week_number ASC",
        engine
    )
    engine.dispose()

    # ── Quarter mapping ───────────────────────────────────────────────────────
    quarters = {
        "Q1 (Jan–Mar)": (1,  13),
        "Q2 (Apr–Jun)": (14, 26),
        "Q3 (Jul–Sep)": (27, 39),
        "Q4 (Oct–Dec)": (40, 52)
    }

    labels, values, colors = [], [], []

    prev_pnl = 0
    for label, (start, end) in quarters.items():
        q_df = fs[(fs["week_number"] >= start) & (fs["week_number"] <= end)]
        if q_df.empty:
            continue
        q_pnl  = float(q_df["cumulative_pnl"].iloc[-1]) - prev_pnl
        prev_pnl = float(q_df["cumulative_pnl"].iloc[-1])
        labels.append(label)
        values.append(round(q_pnl, 2))
        colors.append(COLOR_SUCCESS if q_pnl >= 0 else COLOR_ALERT)

    total_pnl = float(fs["cumulative_pnl"].iloc[-1])

    fig = go.Figure(go.Pie(
        labels=labels,
        values=[abs(v) for v in values],  # abs for slice size
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#121212", width=2)),
        textinfo="label+percent",
        textfont=dict(color=TEXT_MAIN, size=12),
        hovertemplate="<b>%{label}</b><br>₦%{value:,.0f}<extra></extra>",
        customdata=values,
        direction="clockwise",
        sort=False
    ))

    # ── Centre annotation — total annual P&L ─────────────────────────────────
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Quarterly Net Profit",
        annotations=[
            dict(
                text=f"<b>Total</b><br>₦{total_pnl:,.0f}",
                x=0.5, y=0.5,
                font=dict(size=13, color=TEXT_MAIN),
                showarrow=False
            )
        ],
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.2,
            xanchor="center", x=0.5,
            font=dict(color=TEXT_MUTED, size=11)
        ),
        margin=dict(l=20, r=20, t=50, b=20),
        height=300
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False})

#--- CASH CRISIS GAUGE ---#

def create_cash_crisis_gauge(df):
    """
    Gauge chart showing probability of cash crisis from simulation_results.
    Expects df with columns: prob_cash_crisis
    Low probability = good. Color logic is inverted vs performance gauges.
    """
    value = float(df["prob_cash_crisis"].iloc[0]) * 100  # convert to percentage

    # Inverted logic — high probability is dangerous
    if value <= 20:
        bar_color = COLOR_SUCCESS   # Low risk
    elif value <= 50:
        bar_color = COLOR_WARNING   # Moderate risk
    else:
        bar_color = COLOR_ALERT     # High risk

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={
            "suffix": "%",
            "font": {"color": TEXT_MAIN, "size": 24}
        },
        title={
            "text": "Cash Crisis Probability",
            "font": {"color": TEXT_MUTED, "size": 13}
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": TEXT_MUTED,
                "tickfont": {"color": TEXT_MUTED}
            },
            "bar": {"color": bar_color},
            "bgcolor": "#2A2A2A",
            "borderwidth": 0,
            "threshold": {
                "line": {"color": COLOR_ALERT, "width": 4},
                "thickness": 0.75,
                "value": 50  # danger threshold
            }
        }
    ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False})

def create_signal_indicator(sell_signal, cull_signal):
    """
    Renders sell and cull signal indicators from simulation_results.
    Boolean values drive color and label — critical operational alerts.
    """
    def signal_badge(label, active, active_color):
        return html.Div(
            style={
                "backgroundColor": active_color if active else "#2A2A2A",
                "borderRadius":    "8px",
                "padding":         "12px 20px",
                "textAlign":       "center",
                "flex":            "1"
            },
            children=[
                html.P(
                    label,
                    style={
                        "color":         TEXT_MAIN if active else TEXT_MUTED,
                        "fontSize":      "12px",
                        "fontWeight":    "bold",
                        "letterSpacing": "1.5px",
                        "textTransform": "uppercase",
                        "margin":        "0 0 6px 0"
                    }
                ),
                html.H4(
                    "ACTIVE" if active else "INACTIVE",
                    style={
                        "color":      TEXT_MAIN if active else TEXT_MUTED,
                        "fontSize":   "18px",
                        "fontWeight": "bold",
                        "margin":     "0"
                    }
                )
            ]
        )

    return html.Div(
        style={**CARD_STYLE, "display": "flex", "gap": "12px"},
        children=[
            signal_badge("Sell Signal", sell_signal,  COLOR_WARNING),
            signal_badge("Cull Signal", cull_signal, COLOR_ALERT)
        ]
    )

# ---- DATA ENTRY FORM ----

def create_entry_form(next_week: int):
    """
    Weekly data entry form for the farmer to log farm and market data.
    """
    def form_field(label: str, field_id: str, placeholder: str = "0"):
        return html.Div(
            style={"marginBottom": "14px"},
            children=[
                html.Label(
                    label,
                    style={
                        "color":         TEXT_MUTED,
                        "fontSize":      "10px",
                        "fontWeight":    "bold",
                        "textTransform": "uppercase",
                        "letterSpacing": "1px",
                        "marginBottom":  "4px",
                        "display":       "block"
                    }
                ),
                dcc.Input(
                    id=field_id,
                    type="number",
                    placeholder=placeholder,
                    style={
                        "width":           "100%",
                        "backgroundColor": "#2A2A2A",
                        "color":           TEXT_MAIN,
                        "border":          "1px solid #3A3A3A",
                        "borderRadius":    "6px",
                        "padding":         "8px 12px",
                        "fontSize":        "13px",
                        "boxSizing":       "border-box",
                        "outline":         "none"
                    }
                )
            ]
        )

    return html.Div(
        style={
            "backgroundColor": BG_COLOR,
            "minHeight":       "100vh",
            "padding":         "24px",
            "fontFamily":      "Inter, sans-serif"
        },
        children=[

            # ---- Form header ----
            html.Div(
                style={"marginBottom": "24px"},
                children=[
                    html.H2(
                        f"Weekly Data Entry — Week {next_week}",
                        style={"color": TEXT_MAIN, "margin": "0",
                               "fontSize": "18px", "fontWeight": "bold"}
                    ),
                    html.P(
                        "Enter this week's farm and market data. "
                        "The pipeline will recompute automatically every Monday at 06:00.",
                        style={"color": TEXT_MUTED, "fontSize": "12px",
                               "margin": "6px 0 0"}
                    )
                ]
            ),

            # ---- Two column form ----
            html.Div(
                style={"display": "grid",
                       "gridTemplateColumns": "1fr 1fr",
                       "gap": "16px",
                       "marginBottom": "20px"},
                children=[

                    # Column 1 — Farm inputs
                    html.Div(
                        style=CARD_STYLE,
                        children=[
                            html.P("Farm Inputs",
                                   style={"color": TEXT_MUTED, "fontSize": "11px",
                                          "fontWeight": "bold", "letterSpacing": "2px",
                                          "textTransform": "uppercase",
                                          "marginBottom": "16px"}),
                            form_field("Eggs Collected",      "input-eggs-collected", "e.g. 2800"),
                            form_field("Eggs Sold",           "input-eggs-sold",      "e.g. 2700"),
                            form_field("Price Per Crate (₦)", "input-price-crate",    "e.g. 5200"),
                            form_field("Bird Deaths",         "input-bird-deaths",    "e.g. 2"),
                            form_field("Feed Bags Used",      "input-feed-bags",      "e.g. 7.5"),
                            form_field("Diesel Litres",       "input-diesel-litres",  "e.g. 30"),
                            form_field("Cash On Hand (₦)",    "input-cash",           "e.g. 500000"),
                        ]
                    ),

                    # Column 2 — Market prices
                    html.Div(
                        style=CARD_STYLE,
                        children=[
                            html.P("Market Prices",
                                   style={"color": TEXT_MUTED, "fontSize": "11px",
                                          "fontWeight": "bold", "letterSpacing": "2px",
                                          "textTransform": "uppercase",
                                          "marginBottom": "16px"}),
                            form_field("Egg Price Per Crate (₦)",  "input-market-egg",    "e.g. 5250"),
                            form_field("Feed Price Per Bag (₦)",   "input-market-feed",   "e.g. 22000"),
                            form_field("Diesel Per Litre (₦)",     "input-market-diesel", "e.g. 1750"),
                            form_field("USD/NGN Rate",             "input-usd-ngn",       "e.g. 1400"),
                        ]
                    ),
                ]
            ),

            # ---- Submit button ----
            html.Button(
                f"Submit Week {next_week} Data",
                id="submit-btn",
                n_clicks=0,
                style={
                    "backgroundColor": COLOR_NEUTRAL,
                    "color":           TEXT_MAIN,
                    "border":          "none",
                    "borderRadius":    "6px",
                    "padding":         "12px 32px",
                    "fontSize":        "14px",
                    "fontWeight":      "bold",
                    "cursor":          "pointer",
                    "marginBottom":    "12px"
                }
            ),

            # ---- Feedback message ----
            html.Div(id="submit-feedback")
        ]
    )