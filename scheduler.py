#!/usr/bin/env python3

import json
import time
from datetime import datetime

import schedule

from trademark_monitor import run
from config import load_config


def run_monitor():
    print(f"\n{'=' * 60}")
    print(f"Scheduled Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}")

    try:
        cfg = load_config()
        run(cfg)
    except Exception as e:
        print(f"Error during monitoring run: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"Run Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")


def main():
    print("=" * 60)
    print("Trademark Monitor - Scheduler")
    print("=" * 60)

    cfg = load_config()

    if not cfg.get("scheduler_enabled", False):
        print("\nScheduler not enabled in config.json")
        print("Set scheduler_enabled: true to enable")
        print("Or run directly: python trademark_monitor.py")
        return

    run_times = cfg.get("scheduler_run_times", [])
    if not run_times:
        run_times = ["09:00"]

    for rt in run_times:
        schedule.every().day.at(rt).do(run_monitor)
        print(f"  Scheduled daily at {rt}")

    print(f"\nScheduler running ({len(run_times)} daily run(s))")
    print("Ctrl+C to stop\n")

    if cfg.get("scheduler_run_on_start", False):
        print("Running initial check ...")
        run_monitor()

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nScheduler stopped")


if __name__ == "__main__":
    main()
