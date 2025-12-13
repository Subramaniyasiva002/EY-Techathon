# supervisor_daemon.py - Run Agent Supervisor as Background Service
"""
Run this to start the agent supervisor that monitors and auto-recovers agents
"""
from agent_supervisor import AgentSupervisor
import time

def main():
    print("=" * 70)
    print("INTELLIGENT AGENT SUPERVISOR")
    print("=" * 70)
    print("Features:")
    print("  - Auto-restart on accidental failures")
    print("  - Quarantine on suspicious failures (UEBA)")
    print("  - Automatic failover to backup agents")
    print("  - Security incident logging")
    print("=" * 70)
    
    # Create supervisor
    supervisor = AgentSupervisor()
    
    # Start all agents
    print("\nStarting all agents under supervision...")
    agents_to_start = ["DiagnosisAgent", "SchedulingAgent", "FeedbackAgent", "RCACAPAAgent"]
    
    for agent_name in agents_to_start:
        success = supervisor.start_agent(agent_name)
        if success:
            print(f"  [OK] {agent_name} started")
        else:
            print(f"  [FAIL] {agent_name} failed to start")
        time.sleep(2)
    
    print("\n" + "=" * 70)
    print("All agents started. Monitoring for failures...")
    print("Press Ctrl+C to stop")
    print("=" * 70 + "\n")
    
    # Start monitoring loop
    try:
        supervisor.monitor_and_recover()
    except KeyboardInterrupt:
        print("\n\nStopping supervisor...")
        print("Agents will continue running in background")

if __name__ == "__main__":
    main()
