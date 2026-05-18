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
        title="Weekly Profit Scenarios",
        xaxis=dict(title="Week", showgrid=False),
        yaxis=dict(title="Profit (₦)", gridcolor="#2A2A2A"),
        margin=dict(l=40, r=20, t=40, b=30),
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

#--- WEEKLY PRODUCTION CHARTS ---#

def create_weekly_production_chart(df):
    """
    Grouped bar chart comparing actual vs expected lay rate by week.
    Expects df with columns: week_number, actual_lay_rate, expected_lay_rate
    Bar color responds to lay_rate_deviation — green if on target, orange if declining.
    """
    # Dynamic bar colors based on deviation
    bar_colors = [
        COLOR_SUCCESS if dev >= 0 else COLOR_WARNING
        for dev in df["lay_rate_deviation"]
    ]

    fig = go.Figure()

    # Actual lay rate bars — color driven by deviation
    fig.add_trace(go.Bar(
        x=df["week_number"],
        y=df["actual_lay_rate"],
        name="Actual Lay Rate",
        marker=dict(color=bar_colors)
    ))

    # Expected lay rate bars — muted reference
    fig.add_trace(go.Bar(
        x=df["week_number"],
        y=df["expected_lay_rate"],
        name="Expected Lay Rate",
        marker=dict(color=COLOR_NEUTRAL, opacity=0.35)
    ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        barmode="group",
        title="Weekly Lay Rate: Actual vs Expected",
        xaxis=dict(title="Week", showgrid=False),
        yaxis=dict(title="Lay Rate", gridcolor="#2A2A2A"),
        margin=dict(l=40, r=20, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False})

#--- WEEKLY PRODUCTION CHARTS ---#

def create_weekly_production_chart(df):
    """
    Grouped bar chart comparing actual vs expected lay rate by week.
    Expects df with columns: week_number, actual_lay_rate, expected_lay_rate
    Bar color responds to lay_rate_deviation — green if on target, orange if declining.
    """
    # Dynamic bar colors based on deviation
    bar_colors = [
        COLOR_SUCCESS if dev >= 0 else COLOR_WARNING
        for dev in df["lay_rate_deviation"]
    ]

    fig = go.Figure()

    # Actual lay rate bars — color driven by deviation
    fig.add_trace(go.Bar(
        x=df["week_number"],
        y=df["actual_lay_rate"],
        name="Actual Lay Rate",
        marker=dict(color=bar_colors)
    ))

    # Expected lay rate bars — muted reference
    fig.add_trace(go.Bar(
        x=df["week_number"],
        y=df["expected_lay_rate"],
        name="Expected Lay Rate",
        marker=dict(color=COLOR_NEUTRAL, opacity=0.35)
    ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        barmode="group",
        title="Weekly Lay Rate: Actual vs Expected",
        xaxis=dict(title="Week", showgrid=False),
        yaxis=dict(title="Lay Rate", gridcolor="#2A2A2A"),
        margin=dict(l=40, r=20, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False})

#--- RESOURCE USAGE CHARTS ---#

def create_resource_usage_chart(df):
    """
    Horizontal bar chart showing feed and cash runway levels.
    Expects df with columns: feed_stock_weeks, cash_runway_weeks
    pulled from the most recent week in farm_state.
    """
    resources = pd.DataFrame({
        "Resource": ["Feed Stock", "Cash Runway"],
        "Weeks":    [df["feed_stock_weeks"].iloc[0], df["cash_runway_weeks"].iloc[0]],
        "Threshold": [4, 8]  # critical threshold per resource
    })

    # Color logic: below threshold = critical, within 1.5x = warning, above = healthy
    colors = []
    for _, row in resources.iterrows():
        ratio = row["Weeks"] / row["Threshold"]
        if ratio >= 1.5:
            colors.append(COLOR_SUCCESS)
        elif ratio >= 1.0:
            colors.append(COLOR_WARNING)
        else:
            colors.append(COLOR_ALERT)

    fig = go.Figure(go.Bar(
        x=resources["Weeks"],
        y=resources["Resource"],
        orientation="h",
        marker_color=colors,
        text=resources["Weeks"].apply(lambda x: f"{x:.1f} wks"),
        textposition="inside",
        textfont=dict(color=TEXT_MAIN)
    ))

    # Threshold markers
    for _, row in resources.iterrows():
        fig.add_vline(
            x=row["Threshold"],
            line=dict(color=COLOR_WARNING, width=2, dash="dash"),
            annotation_text=f"Min: {row['Threshold']} wks",
            annotation_font=dict(color=TEXT_MUTED, size=11)
        )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Resource Runway",
        margin=dict(l=100, r=20, t=40, b=20),
        xaxis=dict(title="Weeks Remaining", showgrid=False),
        yaxis=dict(showgrid=False)
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
