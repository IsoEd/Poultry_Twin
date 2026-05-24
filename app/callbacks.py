# callbacks.py

from dash import Output, Input, State
from datetime import timedelta
import sys
import os
import pandas as pd
from datetime import datetime
from dash import Output, Input
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.db_config import get_engine
from components import (
    create_kpi_card,
    create_gauge_chart,
    create_financial_trend_chart,
    create_weekly_production_chart,
    create_resource_usage_chart,
    create_cash_crisis_gauge,
    create_signal_indicator,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_NEUTRAL, COLOR_ALERT
)


def register_callbacks(app):

    # ---- LIVE DATE/TIME — fires on load ----
    @app.callback(
        Output("live-datetime", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_datetime(n_intervals):
        now = datetime.now()
        return now.strftime("%b %d, %Y  |  %I:%M %p")


    # ---- FINANCIAL KPIs ----
    @app.callback(
        Output("net-profit-kpi", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_net_profit_kpi(n_clicks):
        query = """
            SELECT cumulative_pnl
            FROM farm_state
            ORDER BY week_number DESC
            LIMIT 1
        """
        df = pd.read_sql(query, get_engine())
        value = float(df["cumulative_pnl"].iloc[0])
        return create_kpi_card("Net Profit", f"₦{value:,.0f}", "Cumulative Cycle", COLOR_SUCCESS)


    @app.callback(
        Output("revenue-kpi", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_revenue_kpi(n_clicks):
        query = """
            SELECT cumulative_revenue
            FROM farm_state
            ORDER BY week_number DESC
            LIMIT 1
        """
        df = pd.read_sql(query, get_engine())
        value = float(df["cumulative_revenue"].iloc[0])
        return create_kpi_card("Revenue", f"₦{value:,.0f}", "Cumulative Cycle", COLOR_SUCCESS)


    @app.callback(
        Output("operating-costs-kpi", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_operating_costs_kpi(n_clicks):
        query = """
            SELECT cumulative_cost
            FROM farm_state
            ORDER BY week_number DESC
            LIMIT 1
        """
        df = pd.read_sql(query, get_engine())
        value = float(df["cumulative_cost"].iloc[0])
        return create_kpi_card("Operating Costs", f"₦{value:,.0f}", "Cumulative Cycle Cost", COLOR_WARNING)


    @app.callback(
        Output("profit-margin-kpi", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_profit_margin_kpi(n_clicks):
        query = """
            SELECT cumulative_pnl, cumulative_revenue
            FROM farm_state
            ORDER BY week_number DESC
            LIMIT 1
        """
        df = pd.read_sql(query, get_engine())
        pnl     = float(df["cumulative_pnl"].iloc[0])
        revenue = float(df["cumulative_revenue"].iloc[0])
        margin  = (pnl / revenue * 100) if revenue else 0
        return create_kpi_card("Profit Margin", f"{margin:.1f}%", "Cumulative Cycle Margin", COLOR_NEUTRAL)


    # ---- PRODUCTION METRICS ----
    @app.callback(
        Output("hdp-gauge", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_hdp_gauge(n_clicks):
        query = """
            SELECT actual_lay_rate, expected_lay_rate
            FROM farm_state
            ORDER BY week_number DESC
            LIMIT 1
        """
        df = pd.read_sql(query, get_engine())
        value  = float(df["actual_lay_rate"].iloc[0]) * 100
        target = float(df["expected_lay_rate"].iloc[0]) * 100
        return create_gauge_chart("Egg Production (HDP)", value, target, max_range=100, unit="%")


    @app.callback(
        Output("fcr-gauge", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_fcr_gauge(n_clicks):
        query = """
            SELECT fcr
            FROM farm_state
            ORDER BY week_number DESC
            LIMIT 1
        """
        df = pd.read_sql(query, get_engine())
        value = float(df["fcr"].iloc[0])
        return create_gauge_chart("Feed Conversion Ratio", value, target=2.0, max_range=4.0, unit="")


    @app.callback(
        Output("weekly-production-chart", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_weekly_production_chart(n_clicks):
        query = """
            SELECT week_number, actual_lay_rate, expected_lay_rate, lay_rate_deviation
            FROM farm_state
            ORDER BY week_number ASC
        """
        df = pd.read_sql(query, get_engine())
        return create_weekly_production_chart(df)


    # ---- FINANCIAL TREND ----
    @app.callback(
        Output("financial-trend-chart", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_financial_trend_chart(n_clicks):
        query = """
            SELECT week_number, p10_profit, p50_profit, p90_profit
            FROM simulation_results
            ORDER BY week_number ASC
        """
        df = pd.read_sql(query, get_engine())
        return create_financial_trend_chart(df)


    # ---- OPERATIONAL & INPUTS ----
    @app.callback(
        Output("cash-crisis-gauge", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_cash_crisis_gauge(n_clicks):
        query = """
            SELECT prob_cash_crisis
            FROM simulation_results
            ORDER BY week_number DESC
            LIMIT 1
        """
        df = pd.read_sql(query, get_engine())
        return create_cash_crisis_gauge(df)


    @app.callback(
        Output("resource-usage-chart", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_resource_usage_chart(n_clicks):
        query = """
            SELECT feed_stock_weeks, cash_runway_weeks
            FROM farm_state
            ORDER BY week_number DESC
            LIMIT 1
        """
        df = pd.read_sql(query, get_engine())
        return create_resource_usage_chart(df)


    @app.callback(
        Output("signal-indicators", "children"),
        Input("datetime-interval", "n_intervals")
    )
    def update_signal_indicators(n_clicks):
        query = """
            SELECT sell_signal, cull_signal
            FROM simulation_results
            ORDER BY week_number DESC
            LIMIT 1
        """
        df = pd.read_sql(query, get_engine())
        sell = bool(df["sell_signal"].iloc[0])
        cull = bool(df["cull_signal"].iloc[0])
        return create_signal_indicator(sell, cull)
    
    # ---- TAB ROUTING ----
    @app.callback(
        Output("tab-content", "children"),
        Input("main-tabs", "value")
    )
    def render_tab(tab):
        from layouts import build_dashboard, build_entry
        if tab == "dashboard":
            return build_dashboard()
        return build_entry()


    # ---- DATA ENTRY SUBMIT ----
    @app.callback(
        Output("submit-feedback", "children"),
        Input("submit-btn", "n_clicks"),
        [
            State("input-eggs-collected",  "value"),
            State("input-eggs-sold",       "value"),
            State("input-price-crate",     "value"),
            State("input-bird-deaths",     "value"),
            State("input-feed-bags",       "value"),
            State("input-diesel-litres",   "value"),
            State("input-cash",            "value"),
            State("input-market-egg",      "value"),
            State("input-market-feed",     "value"),
            State("input-market-diesel",   "value"),
            State("input-usd-ngn",         "value"),
        ],
        prevent_initial_call=True
    )
    def submit_entry(n_clicks, eggs_collected, eggs_sold, price_crate,
                     bird_deaths, feed_bags, diesel_litres, cash,
                     market_egg, market_feed, market_diesel, usd_ngn):

        fields = [eggs_collected, eggs_sold, price_crate, bird_deaths,
                  feed_bags, diesel_litres, cash, market_egg,
                  market_feed, market_diesel, usd_ngn]

        if any(f is None for f in fields):
            return html.P(
                "⚠️  Please fill in all fields before submitting.",
                style={"color": COLOR_WARNING, "fontSize": "13px"}
            )

        try:
            engine = get_engine()
            from scripts.db_config import get_connection
            conn = get_connection()

            last = pd.read_sql(
                "SELECT COALESCE(MAX(week_number), 0) AS w, "
                "COALESCE(MAX(week_date), CURRENT_DATE) AS d FROM farm_inputs",
                engine
            ).iloc[0]
            engine.dispose()

            next_week = int(last["w"]) + 1
            next_date = pd.to_datetime(last["d"]).date() + timedelta(weeks=1)

            cur = conn.cursor()

            cur.execute("""
                INSERT INTO farm_inputs
                (week_number, week_date, eggs_collected, eggs_sold,
                 price_per_crate, bird_deaths, feed_bags_used,
                 diesel_litres, cash_on_hand)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (next_week, next_date, int(eggs_collected), int(eggs_sold),
                  float(price_crate), int(bird_deaths), float(feed_bags),
                  float(diesel_litres), float(cash)))

            cur.execute("""
                INSERT INTO market_prices
                (week_number, week_date, egg_price_per_crate,
                 feed_price_per_bag, diesel_per_litre, usd_ngn_rate)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (next_week, next_date, float(market_egg), float(market_feed),
                  float(market_diesel), float(usd_ngn)))

            conn.commit()
            cur.close()
            conn.close()

            return html.P(
                f"✅  Week {next_week} data saved. Pipeline runs Monday at 06:00.",
                style={"color": COLOR_SUCCESS, "fontSize": "13px"}
            )

        except Exception as e:
            return html.P(
                f"❌  Error: {e}",
                style={"color": COLOR_ALERT, "fontSize": "13px"}
            )