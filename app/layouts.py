# layouts.py

from dash import dcc, html
from components import (
    create_header,
    create_kpi_card,
    create_gauge_chart,
    create_financial_trend_chart,
    create_weekly_production_chart,
    create_resource_usage_chart,
    create_cash_crisis_gauge,
    create_signal_indicator,
    CARD_STYLE, BG_COLOR, TEXT_MUTED
)

# ---- SECTION HEADER HELPER ----
def section_header(title):
    return html.P(
        title,
        style={
            "color":         TEXT_MUTED,
            "fontSize":      "11px",
            "fontWeight":    "bold",
            "letterSpacing": "2px",
            "textTransform": "uppercase",
            "margin":        "0 0 10px 0"
        }
    )

# ---- MAIN LAYOUT ----
layout = html.Div(
    style={
        "backgroundColor": BG_COLOR,
        "minHeight":       "100vh",
        "padding":         "0 0 24px 0",
        "fontFamily":      "Inter, sans-serif"
    },
    children=[

        # Interval for live clock
        dcc.Interval(
            id="datetime-interval",
            interval=60 * 1000,
            n_intervals=0
        ),

        # ---- HEADER ----
        create_header(),

        # ---- MAIN BODY — THREE COLUMNS ----
        html.Div(
            style={
                "display":             "grid",
                "gridTemplateColumns": "1fr 1fr 1fr",
                "gap":                 "16px",
                "padding":             "0 24px"
            },
            children=[

                # ==============================
                # LEFT COLUMN — Financial KPIs
                # ==============================
                html.Div(
                    children=[
                        section_header("Financial KPIs"),

                        # KPI Cards — 2x2 grid
                        html.Div(
                            style={
                                "display":             "grid",
                                "gridTemplateColumns": "1fr 1fr",
                                "gap":                 "12px",
                                "marginBottom":        "16px"
                            },
                            children=[
                                html.Div(id="net-profit-kpi"),
                                html.Div(id="revenue-kpi"),
                                html.Div(id="operating-costs-kpi"),
                                html.Div(id="profit-margin-kpi")
                            ]
                        ),

                        # Financial Trend Chart
                        section_header("Financial Performance Trend"),
                        html.Div(
                            id="financial-trend-chart",
                            style=CARD_STYLE
                        )
                    ]
                ),

                # ==============================
                # CENTRE COLUMN — Production Metrics
                # ==============================
                html.Div(
                    children=[
                        section_header("Production Metrics"),

                        # HDP + FCR Gauges side by side
                        html.Div(
                            style={
                                "display":             "grid",
                                "gridTemplateColumns": "1fr 1fr",
                                "gap":                 "12px",
                                "marginBottom":        "16px"
                            },
                            children=[
                                html.Div(id="hdp-gauge",  style=CARD_STYLE),
                                html.Div(id="fcr-gauge",  style=CARD_STYLE)
                            ]
                        ),

                        # Weekly Production Chart
                        section_header("Weekly Egg Production"),
                        html.Div(
                            id="weekly-production-chart",
                            style=CARD_STYLE
                        )
                    ]
                ),

                # ==============================
                # RIGHT COLUMN — Operational & Inputs
                # ==============================
                html.Div(
                    children=[
                        section_header("Operational & Inputs"),

                        # Cash Crisis Gauge
                        section_header("Cash Crisis Probability"),
                        html.Div(
                            id="cash-crisis-gauge",
                            style=CARD_STYLE
                        ),

                        # Resource Runway
                        section_header("Resource Runway"),
                        html.Div(
                            id="resource-usage-chart",
                            style=CARD_STYLE
                        ),

                        # Sell / Cull Signals
                        section_header("Operational Signals"),
                        html.Div(id="signal-indicators")
                    ]
                )
            ]
        )
    ]
)