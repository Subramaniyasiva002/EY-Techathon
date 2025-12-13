# test_agent_failover.py - Test Agent Failover System
from agent_supervisor import AgentSupervisor
import time
import os
import signal

print("Testing Intelligent Agent Failover System")
print("=" * 70)

# Create supervisor
supervisor = AgentSupervisor()

# Test 1: Normal agent start
print("\n[TEST 1] Starting agents normally...")
supervisor.start_agent("DiagnosisAgent")
time.sleep(2)

# Test 2: Check status
print("\n[TEST 2] Checking supervisor status...")
status = supervisor.get_status()
print(f"Status: {status}")

# Test 3: Simulate accidental failure (kill process)
print("\n[TEST 3] Simulating accidental agent failure...")
print("Killing DiagnosisAgent process...")
if "DiagnosisAgent" in supervisor.agents:
    pid = supervisor.agents["DiagnosisAgent"]["pid"]
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Killed process {pid}")
    except:
        print("Could not kill process (may not exist)")

# Wait for supervisor to detect and recover
print("\nWaiting for supervisor to detect failure and recover...")
time.sleep(15)

# Check status after recovery
print("\n[TEST 4] Checking status after recovery...")
status = supervisor.get_status()
print(f"Status: {status}")

# Test 5: Simulate suspicious failure
print("\n[TEST 5] Simulating suspicious failure...")
print("Creating fake UEBA violations...")

# Add fake violations to UEBA log
from ueba_agent import UEBAAgent
ueba = UEBAAgent()
for i in range(5):
    ueba.log_event("DiagnosisAgent", "unauthorized_action")

# Kill agent again
if "DiagnosisAgent" in supervisor.agents:
    pid = supervisor.agents["DiagnosisAgent"]["pid"]
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Killed process {pid} (with UEBA violations)")
    except:
        print("Could not kill process")

# Wait for supervisor to detect
print("\nWaiting for supervisor to detect suspicious failure...")
time.sleep(15)

# Check final status
print("\n[TEST 6] Final status check...")
status = supervisor.get_status()
print(f"Status: {status}")
print(f"Quarantined agents: {status['quarantined']}")

print("\n" + "=" * 70)
print("Failover testing complete!")
print("Check security_incidents.json for logged incidents")
