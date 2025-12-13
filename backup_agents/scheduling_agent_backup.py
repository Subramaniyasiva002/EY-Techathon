# scheduling_agent_backup.py - Backup Scheduling Agent
"""
Backup Scheduling Agent
"""
import sys
from scheduling_agent import SchedulingAgent

class BackupSchedulingAgent(SchedulingAgent):
    def __init__(self, safe_mode=False):
        super().__init__()
        self.safe_mode = safe_mode
        self.agent_name = "SchedulingAgent_BACKUP"
        
        if safe_mode:
            print(f"[{self.agent_name}] Running in SAFE MODE")
        else:
            print(f"[{self.agent_name}] Running as backup agent")

if __name__ == "__main__":
    safe_mode = "--safe-mode" in sys.argv
    agent = BackupSchedulingAgent(safe_mode=safe_mode)
    print(f"[{agent.agent_name}] Started and ready")
    
    import time
    while True:
        time.sleep(60)
