# feedback_agent_backup.py - Backup Feedback Agent
"""
Backup Feedback Agent with limited capabilities
"""
import sys
import json
from feedback_agent import FeedbackAgent

class BackupFeedbackAgent(FeedbackAgent):
    def __init__(self, safe_mode=False):
        super().__init__()
        self.safe_mode = safe_mode
        self.agent_name = "FeedbackAgent_BACKUP"
        
        if safe_mode:
            print(f"[{self.agent_name}] Running in SAFE MODE (read-only)")
        else:
            print(f"[{self.agent_name}] Running as backup agent")
    
    def record_service(self, vehicle_id, booking, diagnosis):
        """Override with safety checks"""
        if self.safe_mode:
            print(f"[{self.agent_name}] SAFE MODE: Cannot write to database")
            return False
        
        print(f"[{self.agent_name}] Recording service (backup mode)")
        return super().record_service(vehicle_id, booking, diagnosis)

if __name__ == "__main__":
    safe_mode = "--safe-mode" in sys.argv
    agent = BackupFeedbackAgent(safe_mode=safe_mode)
    print(f"[{agent.agent_name}] Started and ready")
    
    import time
    while True:
        time.sleep(60)
