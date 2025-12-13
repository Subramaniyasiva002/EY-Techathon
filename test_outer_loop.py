from rca_capa_agent import RCACAPAAgent

# Test the outer loop with existing data
print("Testing Outer Loop Manufacturing Insights...")
print("=" * 70)

rca = RCACAPAAgent()
insight = rca.generate_outer_loop_insight()

if insight:
    print("\n[SUCCESS] Manufacturing insights generated!")
    print(f"Saved to: manufacturing_insights.json")
else:
    print("\n[INFO] Not enough data yet (need 8+ completed services)")
