# Reinforcement Learning Design & MDP Formulation

GREENWAVE formulates traffic signal control as a discrete **Markov Decision Process (MDP)**:
$$\mathcal{M} = \langle \mathcal{S}, \mathcal{A}, \mathcal{P}, \mathcal{R}, \gamma \rangle$$

---

## 1. Discrete State Space ($\mathcal{S}$)
To avoid state sparsity and ensure tabular convergence, continuous simulation telemetry is discretized into a 4-tuple:
$$s = (q_{\text{NS}}, q_{\text{EW}}, p, d)$$

1. $q_{\text{NS}} \in \{0, 1, 2, 3\}$: North-South Queue Level (0: None, 1: 1-3 veh, 2: 4-8 veh, 3: 9+ veh).
2. $q_{\text{EW}} \in \{0, 1, 2, 3\}$: East-West Queue Level (0: None, 1: 1-3 veh, 2: 4-8 veh, 3: 9+ veh).
3. $p \in \{0, 1\}$: Current Signal Phase (0: North-South Green, 1: East-West Green).
4. $d \in \{0, 1, 2, 3\}$: Phase Duration Bucket (0: $<10$s, 1: $10-29$s, 2: $30-59$s, 3: $\ge 60$s).

$$\text{Total State Space Size} = 4 \times 4 \times 2 \times 4 = 128 \text{ discrete states}$$

---

## 2. Action Space ($\mathcal{A}$)
* $\mathcal{A} = \{0, 1\}$:
  * $a = 0$: **KEEP_PHASE** (Maintain current green phase).
  * $a = 1$: **SWITCH_PHASE** (Initiate transition to the competing green phase).

### Civil Engineering Safety Constraints
1. **Minimum Green Time ($T_{\min} = 10$s)**: Action `SWITCH_PHASE` is illegal if $d < T_{\min}$.
2. **Maximum Green Time ($T_{\max} = 60$s)**: Action `KEEP_PHASE` is penalized and converted to switch if $d \ge T_{\max}$.
3. **Yellow Change Interval ($T_{\text{yellow}} = 4$s)**: Phase transitions automatically route through intermediate yellow clearance intervals (`yyyyrrrryyyyrrrr` or `rrrryyyyrrrryyyy`).

---

## 3. Reward Function ($\mathcal{R}$)
$$R(s, a, s') = - (w_q \cdot Q + w_w \cdot W + w_s \cdot \mathbb{I}_{\text{switch}}) + w_{\text{tp}} \cdot \text{VehiclesArrived}$$

Where:
* $Q$: Total halting vehicles across all approaches.
* $W$: Accumulated waiting time in seconds.
* $\mathbb{I}_{\text{switch}}$: Binary indicator equal to 1 if a signal change was initiated.
* $w_q = 0.25, w_w = 0.05, w_s = 5.0, w_{\text{tp}} = 10.0$.

---

## 4. Bellman Optimality Update Equation
$$Q(s, a) \leftarrow Q(s, a) + \alpha \left[ R + \gamma \max_{a' \in \mathcal{A}_{\text{legal}}(s')} Q(s', a') - Q(s, a) \right]$$

Hyperparameters:
* Learning rate $\alpha = 0.10$
* Discount factor $\gamma = 0.95$
* Exploration rate $\epsilon_0 = 1.0$, decayed at $\epsilon \leftarrow \max(0.01, \epsilon \times 0.90)$ per episode.
