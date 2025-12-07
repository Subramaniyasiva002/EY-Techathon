# rl_train.py
# Trains a Q-learning model for service slot scheduling
import numpy as np
import random
import os

# ---------------------------
# RL SETTINGS
# ---------------------------
NUM_STATES = 3         # 0=low, 1=medium, 2=high demand
NUM_ACTIONS = 6        # 6 time slots
EPISODES = 2000
ALPHA = 0.1            # learning rate
GAMMA = 0.9            # discount
EPSILON = 0.1          # exploration probability

# preference map (can be replaced by real patterns)
CUSTOMER_PREF = [3, 4, 2, 1, 0, 0]  # higher = more preferred slot


def get_next_state():
    """Simulate demand patterns"""
    r = random.random()
    if r < 0.33: return 0  # low demand
    if r < 0.66: return 1  # medium
    return 2               # high


def compute_reward(state, action):
    """
    Reward function:
    Higher reward for choosing preferred slots during low/medium demand.
    Penalize choosing early slots when demand is high.
    """
    preference = CUSTOMER_PREF[action]

    # simple waiting penalty approximation
    wait_penalty = state * 2  

    # avoid overloading midday slots
    overload_penalty = 3 if (state == 2 and action in [2, 3]) else 0

    reward = preference - wait_penalty - overload_penalty
    return reward


# Initialize Q-table
Q = np.zeros((NUM_STATES, NUM_ACTIONS))

# ---------------------------
# TRAINING LOOP
# ---------------------------
for ep in range(EPISODES):
    state = get_next_state()

    # choose action
    if random.random() < EPSILON:
        action = random.randint(0, NUM_ACTIONS - 1)   # explore
    else:
        action = np.argmax(Q[state])                  # exploit

    reward = compute_reward(state, action)
    next_state = get_next_state()

    # Q-learning update
    Q[state, action] += ALPHA * (reward + GAMMA * np.max(Q[next_state]) - Q[state, action])


# ---------------------------
# SAVE TRAINED MODEL
# ---------------------------
os.makedirs("models", exist_ok=True)
np.save("models/q_table.npy", Q)
print("Q-table saved → models/q_table.npy")

print("Training complete.\nFinal Q-table:")
print(Q)
