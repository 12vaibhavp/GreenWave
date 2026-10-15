"""
Tabular Q-Learning Agent Implementation from Scratch.
Implements the Bellman optimality update equation:
    Q(s, a) <- Q(s, a) + alpha * [ r + gamma * max_a' Q(s', a') - Q(s, a) ]
"""
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from reinforcement_learning.actions import ACTION_KEEP, ACTION_SWITCH, NUM_ACTIONS
from reinforcement_learning.state import state_to_string, string_to_state


class QLearningAgent:
    """
    Tabular Q-Learning Agent for Traffic Signal Optimization.
    """

    def __init__(
        self,
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        num_actions: int = NUM_ACTIONS
    ):
        self.alpha = float(alpha)
        self.gamma = float(gamma)
        self.epsilon = float(epsilon)
        self.epsilon_decay = float(epsilon_decay)
        self.epsilon_min = float(epsilon_min)
        self.num_actions = num_actions
        
        # Q-table: Dict[state_str, List[float of length num_actions]]
        self.q_table: Dict[str, List[float]] = {}

    def _get_q_values(self, state_key: str) -> List[float]:
        """Retrieve or initialize Q-values for a state."""
        if state_key not in self.q_table:
            # Initialize with small zeros
            self.q_table[state_key] = [0.0] * self.num_actions
        return self.q_table[state_key]

    def choose_action(
        self,
        state: Tuple[int, int, int, int],
        legal_actions: Optional[List[int]] = None,
        deterministic: bool = False
    ) -> int:
        """
        Choose action using epsilon-greedy exploration or greedy policy (when deterministic=True).
        """
        available = legal_actions if legal_actions is not None else list(range(self.num_actions))
        state_key = state_to_string(state)
        q_vals = self._get_q_values(state_key)

        # Epsilon-greedy exploration
        if not deterministic and random.random() < self.epsilon:
            return random.choice(available)

        # Greedy choice among legal actions
        best_action = available[0]
        max_q = q_vals[best_action]
        for a in available[1:]:
            if q_vals[a] > max_q:
                max_q = q_vals[a]
                best_action = a

        return best_action

    def update(
        self,
        state: Tuple[int, int, int, int],
        action: int,
        reward: float,
        next_state: Tuple[int, int, int, int],
        legal_next_actions: Optional[List[int]] = None,
        done: bool = False
    ) -> float:
        """
        Update Q-value using the standard Bellman equation.
        Returns the TD error magnitude.
        """
        state_key = state_to_string(state)
        next_key = state_to_string(next_state)

        current_q = self._get_q_values(state_key)[action]

        if done:
            target = reward
        else:
            next_q_vals = self._get_q_values(next_key)
            legal = legal_next_actions if legal_next_actions is not None else list(range(self.num_actions))
            max_next_q = max(next_q_vals[a] for a in legal)
            target = reward + (self.gamma * max_next_q)

        td_error = target - current_q
        self.q_table[state_key][action] = current_q + (self.alpha * td_error)
        return float(abs(td_error))

    def decay_epsilon(self) -> None:
        """Decay exploration rate epsilon after each episode."""
        if self.epsilon > self.epsilon_min:
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, filepath: Path) -> None:
        """Save Q-table and agent hyperparameters to JSON."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "alpha": self.alpha,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "epsilon_decay": self.epsilon_decay,
            "epsilon_min": self.epsilon_min,
            "num_actions": self.num_actions,
            "state_count": len(self.q_table),
            "q_table": self.q_table
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: Path) -> None:
        """Load Q-table from JSON file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Q-table file '{filepath}' not found.")
        with open(filepath, "r") as f:
            data = json.load(f)

        self.alpha = float(data.get("alpha", self.alpha))
        self.gamma = float(data.get("gamma", self.gamma))
        self.epsilon = float(data.get("epsilon", self.epsilon))
        self.epsilon_decay = float(data.get("epsilon_decay", self.epsilon_decay))
        self.epsilon_min = float(data.get("epsilon_min", self.epsilon_min))
        self.num_actions = int(data.get("num_actions", self.num_actions))
        self.q_table = data.get("q_table", {})
