import schedule
import time
import json
from datetime import datetime
from trademark_monitor import TrademarkMonitor


def load_schedule_config():





    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
        return config.get("scheduler", {})
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}




def run_monitor():

    print(f"\n{'='*60}")
    print(f"Scheduled Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        monitor = TrademarkMonitor()
        monitor.run()
    except Exception as e:
        print(f"Error during monitoring run: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"Run Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")





def main():

    print("=" * 60)
    print("USPTO Trademark Monitor - Scheduler")
    print("=" * 60)
    
    schedule_config = load_schedule_config()
    
    if not schedule_config.get("enabled", False):
        print("\n Scheduler is not enabled in config.json")
        print("\n To enable scheduling, add to config.json:")
        print('{')
        print('  "scheduler": {')
        print('    "enabled": true,')
        print('    "run_times": ["09:00", "13:00", "17:00", "22:00"],')
        print('    "run_on_start": false')
        print('  }')
        print('}')
        print("\nOr run manually with >>> python trademark_monitor.py")
        return
    



    run_times = schedule_config.get("run_times", [])
    




    if not run_times:
        hour = schedule_config.get("hour", 9)
        minute = schedule_config.get("minute", 0)
        run_times = [f"{hour:02d}:{minute:02d}"]
    



    for run_time in run_times:
        schedule.every().day.at(run_time).do(run_monitor)
        print(f"Daily run scheduled for {run_time}")
    
    run_on_start = schedule_config.get("run_on_start", False)
    
    print(f"\nScheduler running ...")
    print(f"  Total runs today: {len(run_times)}")
    print(f"\nTo stop, Ctrl+C \n")
    



    if run_on_start:
        print("Running initial check ...")
        run_monitor()
    



    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user")


if __name__ == "__main__":
    main()
