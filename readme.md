🐔 Poultry Financial Twin
A stochastic financial simulation and early warning system for a 500-bird ISA Brown layer operation in Kaduna State, Nigeria.

What This Project Does
Most farm management tools tell you what happened. This system tells you what is likely to happen next — and what to do about it.
The Poultry Financial Twin maintains a live digital replica of a layer farm's financial and biological state, runs 10,000 Monte Carlo simulations every week to project probable outcomes 12 weeks forward, detects egg leakage and theft using statistical anomaly detection, and fires early warning alerts before problems become crises.

The Problem It Solves
A small-scale poultry farmer in northern Nigeria operates with thin margins, volatile feed and egg prices, and limited access to financial analysis tools. A bad week — a disease shock, a feed price spike, a drop in lay rate — can cascade into a cash crisis before the farmer realises what is happening.
This system gives that farmer the same forward-looking risk intelligence that a large agribusiness would have, built specifically for the Kaduna State market.

System Architecture
Weekly Data Entry (Dash Form)
        ↓
PostgreSQL Database (poultry_twin)
        ↓
Automated Pipeline (APScheduler — every Monday 06:00)
        ↓
┌─────────────────────────────────────────────┐
│  state_engine.py   →  Farm state computed   │
│  simulation.py     →  10,000 MC paths       │
│  decision.py       →  Tripwires evaluated   │
│  leakage.py        →  Theft detection       │
│  volatility.py     →  Price volatility      │
└─────────────────────────────────────────────┘
        ↓
Plotly Dash Operator Dashboard

Tech Stack
LayerToolPurposeDatabasePostgreSQL 15/16Stores all farm, market, and computed dataDB AdminpgAdmin 4Database GUILanguagePython 3.12All simulation, detection, and forecastingDB Connectorpsycopg2 + SQLAlchemyPython to PostgreSQLNumericalNumPy, SciPyMonte Carlo simulationDataPandasData manipulationCredentialspython-dotenvSecure environment variable managementDashboardPlotly DashOperator monitoring panelSchedulerAPSchedulerAutomated weekly pipelineVersion ControlGit + GitHubCode versioning

Farm Parameters
ParameterValueLocationKaduna, Kaduna State, NigeriaFlock500 ISA Brown layersPurchase typePoint-of-lay (18 weeks biological age)Target cull weekWeek 72Disease shock probability0.8% per week (vaccinated flock)Shock mortality range2–6% of flock per eventLaborFarm hand NGN 55,000 + Security NGN 35,000/monthMedicationNGN 9,000 every 4th week
Laying Curve
Piecewise curve calibrated for ISA Brown POL birds in tropical Nigerian conditions:
PhaseWeeksLay RateEarly peak1 → 485% → 87%Peak plateau4 → 1587% → 82%Production decline15 → 5282% → 62%
Kaduna Market Calibration
InputRangeEgg price per crate (30 eggs)NGN 5,000 – 5,500Layers mash per 25kg bagNGN 20,000 – 25,000Diesel per litreNGN 1,500 – 2,000USD/NGN exchange rateNGN 1,350 – 1,450

Database Schema
Eight tables in PostgreSQL database poultry_twin:
TablePurposefarm_profileStatic farm identity — one rowfarm_inputsFarmer-entered weekly datamarket_pricesExternal market data per weekfarm_stateSystem-computed farm intelligence per weeksimulation_resultsMonte Carlo P10/P50/P90 projections per weekalertsEarly warning alerts firedleakage_eventsEgg variance and theft detection per weekvolatility_forecasts4-week forward price volatility estimates

Project Structure
PoultryTwin/
├── .env                    ← credentials (never on GitHub)
├── .env.example            ← template for collaborators
├── .gitignore
├── requirements.txt
├── README.md
├── DOCUMENTATION.md
├── scripts/
│   ├── db_config.py        ← database connection
│   ├── utils.py            ← shared biological and financial functions
│   ├── seed.py             ← generates 52 weeks of synthetic data
│   ├── state_engine.py     ← computes farm state from weekly inputs
│   ├── simulation.py       ← Monte Carlo engine, 10,000 paths
│   ├── decision.py         ← tripwires, pricing signal, cull logic
│   ├── leakage.py          ← theft and leakage detection
│   ├── volatility.py       ← price volatility forecasting
│   └── scheduler.py        ← automated weekly pipeline
├── app/
│   ├── app.py              ← Dash entry point
│   ├── layouts.py          ← page structure and tab definitions
│   ├── callbacks.py        ← all callback functions
│   └── components.py       ← reusable UI components
└── data/                   ← local data files

Installation
Prerequisites

Python 3.12
PostgreSQL 15 or 16
pgAdmin 4

1. Clone the repository
bashgit clone https://github.com/YOUR_USERNAME/PoultryTwin.git
cd PoultryTwin
2. Create and activate virtual environment
bashpython -m venv venv
venv\Scripts\Activate.ps1   # Windows PowerShell
3. Install dependencies
bashpip install -r requirements.txt
4. Configure environment variables
Copy .env.example to .env and fill in your credentials:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=poultry_twin
DB_USER=postgres
DB_PASSWORD=your_password_here
5. Create the database
In pgAdmin 4, create a database named poultry_twin.
6. Deploy the schema
Run the SQL schema file in pgAdmin Query Tool to create all 8 tables.
7. Seed synthetic data
bashpython scripts/seed.py
8. Run the pipeline
bashpython scripts/scheduler.py --now
9. Launch the dashboard
bashpython app/app.py
Open your browser at http://127.0.0.1:8050

Dashboard
The operator dashboard provides a live view of the farm's financial and biological state across two tabs:
Operator Dashboard

Financial KPIs — Net Profit, Revenue, Operating Costs, Profit Margin
Production Metrics — Egg Production gauge, Feed Conversion Ratio
Financial Performance Trend — monthly revenue, costs, and profit
Weekly Egg Production — actual vs target by month
Cash Crisis Probability — from Monte Carlo simulation
Quarterly Net Profit — donut chart showing Q1–Q4 breakdown
Operational Signals — Sell and Cull signals

Weekly Data Entry

Form for the farmer to log weekly farm inputs and market prices
Auto-detects the next week number from the database
Data saved to PostgreSQL — pipeline recomputes every Monday at 06:00


Early Warning Tripwires
The decision engine monitors four conditions continuously:
TripwireAMBERREDLay rate deviation5% below expected10% below expectedFeed stockBelow 3 weeksBelow 2 weeksCash runwayBelow 4 weeksBelow 2 weeksEgg price marginWithin 15% of break-evenWithin 5% of break-even

Monte Carlo Simulation

Paths: 10,000 forward simulations per week
Horizon: 12 weeks
Stochastic variables: egg price, feed price, diesel price, shock mortality
Outputs: P10 (bad case), P50 (median), P90 (good case), crisis probability
Crisis definition: 3 consecutive weeks where weekly revenue < weekly cost


Leakage Detection
Expected eggs are computed from surviving birds × lay rate × 7 days. Reported eggs from the farmer's weekly entry are compared against this figure. Variance expressed as a percentage of expected:
FlagThresholdNORMALVariance below 5%WATCHVariance 5–10%FLAGVariance above 10%

What Makes This Portfolio-Worthy
Most financial analysis portfolio projects are static — a CSV, a chart, a notebook. This project is an operational system:

A live PostgreSQL database written to by automated Python engines
A probabilistic simulation engine producing risk-adjusted outputs
Statistical anomaly detection running on real weekly data
Two dashboard tabs — live monitoring and farmer data entry
An automated pipeline running on a weekly schedule
Applied to a real Nigerian agricultural problem with genuine economic stakes

It demonstrates Python, SQL, statistical modelling, dashboard development, database design, and systems thinking in a single coherent project.

License
MIT License — free to use, modify, and distribute with attribution.

Author
Built as a financial data analyst portfolio project demonstrating proficiency across Python, SQL, PostgreSQL, and Plotly Dash.