
import json
import os
from datetime import datetime
from typing import Optional


class StateManager:
    
    def __init__(self, state_file: str = "state.json"):
        self.state_file = state_file
        self.state = self._load_state()
    



    def _load_state(self) -> dict:

        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f" !!! Could not load state file: {e}")
                return self._create_default_state()
        else:
            return self._create_default_state()




    def _create_default_state(self) -> dict:

        return {
            "last_processed_sn": 0,
            "last_updated": None,
            "total_matches": 0,
            "total_batches_processed": 0
        }






    def get_next_sn(self) -> int:
        return self.state["last_processed_sn"] + 1




    def update_position(self, sn: int, reason: str = "batch_complete"):

        self.state["last_processed_sn"] = sn
        self.state["last_updated"] = datetime.now().isoformat()
        
        if reason == "match_found":
            self.state["total_matches"] = self.state.get("total_matches", 0) + 1
        elif reason == "batch_complete":
            self.state["total_batches_processed"] = self.state.get("total_batches_processed", 0) + 1
        
        self._save_state()
    





    def _save_state(self):


        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except IOError as e:
            print(f" !!! Failed to save state file: {e}")
    
    def get_state(self) -> dict:
        return self.state.copy()





    def reset_state(self, start_sn: int = 0):

        self.state = self._create_default_state()
        self.state["last_processed_sn"] = start_sn
        self._save_state()
