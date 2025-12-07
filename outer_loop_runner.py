# outer_loop_runner.py
from outer_loop_graph import outer_loop_graph, OuterLoopState

if __name__ == "__main__":
    print("=== Running Outer Loop Pipeline ===")
    state = OuterLoopState()
    final = outer_loop_graph.invoke(state)
    if final:
        print("\nFINAL MANUFACTURING REPORT:\n", final.get("summary", "No summary available"))
    else:
        print("\nERROR: Graph returned None")
