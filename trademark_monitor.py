import json
import os
import sys
from typing import List, Dict, Any

from state_manager import StateManager
from uspto_client import USPTOClient
from filter_engine import FilterEngine
from email_generator import EmailGenerator





class TrademarkMonitor:



    def __init__(self, config_path: str = "config.json"):

        self.config = self._load_config(config_path)
        self.state_manager = StateManager("state.json")



        api_key = self.config.get("uspto_api_key")
        if not api_key:
            raise ValueError("uspto_api_key not found in config.json")
        
        rate_limit = self._get_rate_limit()
        
        self.client = USPTOClient(api_key, rate_limit_delay=rate_limit)
        self.filter_engine = FilterEngine(self.config)



        email_config = self.config.get("email", {})
        email_config["api_key"] = api_key
        self.email_generator = EmailGenerator(email_config)
        
        self.batch_size = 20
        self.max_empty_batches = 3
        self.max_results_per_email = self.config.get("max_results_per_email", 100)
    




    def _load_config(self, config_path: str) -> Dict[str, Any]:

        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f" !!! Error loading config: {e}")
            sys.exit(1)



    def _get_rate_limit(self) -> float:
        


        from datetime import datetime
        import pytz
        


        est = pytz.timezone('US/Eastern')
        current_time = datetime.now(est)
        hour = current_time.hour
        

        is_off_peak = hour >= 22 or hour < 5
        
        if is_off_peak:
            delay = 0.5
            print(f"Off-peak time - use faster rate (120 req/min)")
        else:
            delay = 1.0
            print(f"Peak time - use standard rate (60 req/min)")
        






        config_delay = self.config.get("rate_limit_delay")
        if config_delay:
            delay = config_delay
            print(f"Use custom rate-limit from config: {delay}s per request")
        
        return delay
    



    def run(self):


        print("=" * 60)
        print("Trademark Monitor")
        print("=" * 60)
        



        start_sn = self.state_manager.get_next_sn()
        print(f"\nStarting from Serial No.: {start_sn}")
    

        current_sn = start_sn
        empty_batch_count = 0
        all_matches = []
        total_processed = 0
    


        while True:



            batch_sns = list(range(current_sn, current_sn + self.batch_size))
            print(f"\nQuerying batch: {batch_sns[0]} - {batch_sns[-1]}")
            


            response = self.client.query_batch(batch_sns)
        


            if response is None:
                print(" !!! API failed")
                break
            




            trademarks = self.client.extract_trademark_data(response)
            print(f"  Found {len(trademarks)} trademark applications")





            if len(trademarks) == 0:
                empty_batch_count += 1
                print(f"  Empty batch ({empty_batch_count}/{self.max_empty_batches})")



                if empty_batch_count >= self.max_empty_batches:
                    print(f"\n Reached end of data after {self.max_empty_batches} empty batches")


                    last_valid_sn = current_sn - (self.batch_size * empty_batch_count)
                    self.state_manager.update_position(last_valid_sn, "no_data")
                    break
            else:
                empty_batch_count = 0 
                total_processed += len(trademarks)
                




                matches = self.filter_engine.filter_trademarks(trademarks)
                
                if matches:
                    print(f" Captured {len(matches)} hits")
                    all_matches.extend(matches)
                    
                    last_match_sn = matches[-1].get("serialNumber", current_sn + self.batch_size - 1)
                    self.state_manager.update_position(last_match_sn, "match_found")
                else:
                    print(f"  No matches")
            





            batch_end_sn = batch_sns[-1]
            self.state_manager.update_position(batch_end_sn, "batch_complete")
            





            if len(all_matches) >= self.max_results_per_email:
                print(f"\nHit max results per email ({self.max_results_per_email})")
                self._send_digest(all_matches, start_sn, batch_end_sn, total_processed)
                all_matches = []
                start_sn = batch_end_sn + 1
            
            current_sn += self.batch_size
        





        if all_matches:
            final_sn = current_sn - 1
            self._send_digest(all_matches, start_sn, final_sn, total_processed)
        





        print("\n" + "=" * 60)
        print("API Pull Finished")
        print("=" * 60)
        state = self.state_manager.get_state()

    def _send_digest(self, matches: List[Dict], start_sn: int, end_sn: int, total_processed: int):
        batch_info = {
            "start_sn": start_sn,
            "end_sn": end_sn,
            "total_processed": total_processed
        }

        print(f"\nSend email with {len(matches)} matches ...")
        success = self.email_generator.send_email(matches, batch_info)
        
        if success:
            print(" Email sent successfully")
        else:
            print("!!! Email not sent (check config)")
            self._save_matches_to_file(matches, start_sn, end_sn)





    def _save_matches_to_file(self, matches: List[Dict], start_sn: int, end_sn: int):


        filename = f"matches_{start_sn}_{end_sn}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(matches, f, indent=2)
            print(f"Matches saved >>> {filename}")
        except IOError as e:
            print(f" !!! Couldn't save matches: {e}")







def main():
    try:
        monitor = TrademarkMonitor()
        monitor.run()
    except KeyboardInterrupt:
        print("\n\nMonitoring interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
