import numpy as np
import random
import os

NUM_STATES = 3      # 0=low, 1=medium, 2=high demand
NUM_ACTIONS = 6   # 6 slots
EPISODES = 10000
ALPHA = 0.1
GAMMA = 0.95
EPSILON = 0.15

# Higher = customer prefers this slot
CUSTOMER_PREFERENCE = [5, 6, 4, 3, 2, 1]  # 09AM best, 04PM worst

Q = np.zeros((NUM_STATES, NUM_ACTIONS))

for _ in range(EPISODES):
    state = random.randint(0, 2)
    if random.random() < EPSILON:
        action = random.randint(0, 5)
    else:
        action = np.argmax(Q[state])

    # Reward logic
    base = CUSTOMER_PREFERENCE[action]
    penalty = state * 3                     # high demand → punish early slots
    overload_penalty = 8 if (state == 2 and action <= 2) else 0
    reward = base - penalty - overload_penalty

    next_state = random.randint(0, 2)
    Q[state, action] += ALPHA * (reward + GAMMA * np.max(Q[next_state]) - Q[state, action])

os.makedirs("models", exist_ok=True)
np.save("models/q_table.npy", Q)
print("New Q-table saved – smarter scheduling ready for tomorrow!")