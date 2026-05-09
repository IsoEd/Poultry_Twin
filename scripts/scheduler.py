import sys
sys.path.insert(0, ".")

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from scripts.state_engine  import run_state_engine
from scripts.simulation    import run_simulation
from scripts.decision      import run_decision_engine
from scripts.leakage       import run_leakage_engine
from scripts.volatility    import run_volatility_engine

# ── Scheduler configuration ───────────────────────────────────────────────────
# All engines run every Monday at 06:00 AM — after the farmer logs weekend data
SCHEDULE_DAY  = "mon"
SCHEDULE_HOUR = 6


def run_pipeline():
    """
    Full weekly pipeline — runs all engines in dependency order.
    State must be computed before simulation, decision, and leakage can run.
    Volatility runs last as it feeds into simulation on the next cycle.
    """
    print(f"\n{'='*60}")
    print(f"  🚀 Pipeline started — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    try:
        print("\n[1/5] Running state engine...")
        run_state_engine()

        print("\n[2/5] Running simulation engine...")
        run_simulation()

        print("\n[3/5] Running decision engine...")
        run_decision_engine()

        print("\n[4/5] Running leakage engine...")
        run_leakage_engine()

        print("\n[5/5] Running volatility engine...")
        run_volatility_engine()

        print(f"\n{'='*60}")
        print(f"  ✅ Pipeline complete — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n  ❌ Pipeline failed: {e}")
        raise


def start_scheduler():
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_pipeline,
        trigger=CronTrigger(day_of_week=SCHEDULE_DAY, hour=SCHEDULE_HOUR),
        id="weekly_pipeline",
        name="Poultry Financial Twin — Weekly Pipeline",
        replace_existing=True
    )

    print(f"  ⏰ Scheduler started — pipeline runs every "
          f"{SCHEDULE_DAY.upper()} at {SCHEDULE_HOUR:02d}:00")
    print(f"     Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n  🛑 Scheduler stopped.")
        scheduler.shutdown()


if __name__ == "__main__":
    # For testing — run the pipeline immediately without waiting for schedule
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        run_pipeline()
    else:
        start_scheduler()