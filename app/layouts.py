# layouts.py

import pandas as pd
from dash import dcc, html
from components import (
    create_header,
    create_entry_form,
    CARD_STYLE, BG_COLOR, TEXT_MUTED
)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.db_config import get_engine


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


# ---- DASHBOARD TAB CONTENT ----
def build_dashboard():
    return html.Div(
        style={
            "backgroundColor": BG_COLOR,
            "minHeight":       "100vh",
            "padding":         "0 0 24px 0",
            "fontFamily":      "Inter, sans-serif"
        },
        children=[
            # ---- MAIN BODY — THREE COLUMNS ----
            html.Div(
                style={
                    "display":             "grid",
                    "gridTemplateColumns": "1fr 1fr 1fr",
                    "gap":                 "16px",
                    "padding":             "0 24px"
                },
                children=[

                    # LEFT COLUMN — Financial KPIs
                    html.Div(
                        children=[
                            section_header("Financial KPIs"),
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
                            section_header("Financial Performance Trend"),
                            html.Div(id="financial-trend-chart", style=CARD_STYLE)
                        ]
                    ),

                    # CENTRE COLUMN — Production Metrics
                    html.Div(
                        children=[
                            section_header("Production Metrics"),
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
                            section_header("Weekly Egg Production"),
                            html.Div(id="weekly-production-chart", style=CARD_STYLE)
                        ]
                    ),

                    # RIGHT COLUMN — Operational & Inputs
                    html.Div(
                        children=[
                            section_header("Operational & Inputs"),
                            section_header("Cash Crisis Probability"),
                            html.Div(id="cash-crisis-gauge", style=CARD_STYLE),
                            section_header("Quarterly Performance"),
                            html.Div(id="resource-usage-chart", style=CARD_STYLE),
                            section_header("Operational Signals"),
                            html.Div(id="signal-indicators")
                        ]
                    )
                ]
            )
        ]
    )


# ---- ENTRY FORM TAB CONTENT ----
def build_entry():
    engine    = get_engine()
    last_week = pd.read_sql(
        "SELECT COALESCE(MAX(week_number), 0) AS last_week FROM farm_inputs",
        engine
    ).iloc[0]["last_week"]
    engine.dispose()
    next_week = int(last_week) + 1
    return create_entry_form(next_week)


# ---- MAIN LAYOUT ----
layout = html.Div(
    style={
        "backgroundColor": BG_COLOR,
        "minHeight":       "100vh",
        "fontFamily":      "Inter, sans-serif"
    },
    children=[

        # Interval for live clock
        dcc.Interval(
            id="datetime-interval",
            interval=60 * 1000,
            n_intervals=0
        ),

        # Header — always visible
        create_header(),

        # Tabs
        dcc.Tabs(
            id="main-tabs",
            value="dashboard",
            style={"backgroundColor": "#1E1E1E"},
            colors={
                "border":     "#2E2E2E",
                "primary":    "#0072B2",
                "background": "#1E1E1E"
            },
            children=[
                dcc.Tab(
                    label="📊  Operator Dashboard",
                    value="dashboard",
                    style={"backgroundColor": "#1E1E1E", "color": "#B0B0B0",
                           "borderColor": "#2E2E2E", "padding": "10px 20px"},
                    selected_style={"backgroundColor": "#121212", "color": "#FFFFFF",
                                    "borderTop": "2px solid #0072B2",
                                    "borderColor": "#2E2E2E", "padding": "10px 20px"}
                ),
                dcc.Tab(
                    label="📝  Weekly Data Entry",
                    value="entry",
                    style={"backgroundColor": "#1E1E1E", "color": "#B0B0B0",
                           "borderColor": "#2E2E2E", "padding": "10px 20px"},
                    selected_style={"backgroundColor": "#121212", "color": "#FFFFFF",
                                    "borderTop": "2px solid #0072B2",
                                    "borderColor": "#2E2E2E", "padding": "10px 20px"}
                ),
            ]
        ),

        # Tab content rendered by callback
        html.Div(id="tab-content")
    ]
)