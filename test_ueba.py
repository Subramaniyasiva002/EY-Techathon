from ueba_agent import UEBAAgent

# Test UEBA Security Layer
print("Testing UEBA Whitelist-Based Security...")
print("=" * 70)

ueba = UEBAAgent()

# Test 1: Allowed action
print("\n[TEST 1] Allowed Action")
result = ueba.log_event("MasterAgent", "call_scheduler")
print(f"Result: {result}")

# Test 2: Unauthorized action
print("\n[TEST 2] Unauthorized Action (should be BLOCKED)")
result = ueba.log_event("MasterAgent", "access_database")
print(f"Result: {result}")

# Test 3: Another agent's action
print("\n[TEST 3] Scheduling Agent - Allowed")
result = ueba.log_event("SchedulingAgent", "recommend_slot")
print(f"Result: {result}")

# Test 4: Scheduling Agent trying unauthorized action
print("\n[TEST 4] Scheduling Agent - Unauthorized (should be BLOCKED)")
result = ueba.log_event("SchedulingAgent", "access_telematics")
print(f"Result: {result}")

# Test 5: Rate anomaly (rapid fire)
print("\n[TEST 5] Rate Anomaly Detection")
for i in range(12):
    result = ueba.log_event("MasterAgent", "call_scheduler")
print(f"Last result: {result}")

# Security Report
print("\n" + "=" * 70)
print("SECURITY REPORT")
print("=" * 70)
report = ueba.get_security_report()
for key, value in report.items():
    print(f"{key}: {value}")
