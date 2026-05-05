import traci
import random

# ===============================
# Q-TABLE
# ===============================
Q = {}

# PARAMETERS
alpha = 0.1
gamma = 0.9

epsilon = 1.0
epsilon_decay = 0.95
min_epsilon = 0.05

MIN_GREEN = 15

# ===============================
# FUNCTIONS
# ===============================

def get_q(state, action):
    return Q.get((state, action), 0.0)


def choose_action(state):
    if random.random() < epsilon:
        return random.choice([0, 1])
    return max([0, 1], key=lambda a: get_q(state, a))


def update_q(state, action, reward, next_state):
    old_q = get_q(state, action)
    next_max = max(get_q(next_state, 0), get_q(next_state, 1))
    Q[(state, action)] = old_q + alpha * (reward + gamma * next_max - old_q)


def get_state():
    q_n = traci.lane.getLastStepHaltingNumber("N2C_0")
    q_s = traci.lane.getLastStepHaltingNumber("S2C_0")
    q_e = traci.lane.getLastStepHaltingNumber("E2C_0")
    q_w = traci.lane.getLastStepHaltingNumber("W2C_0")

    ns = min((q_n + q_s) // 2, 5)
    ew = min((q_e + q_w) // 2, 5)

    return (ns, ew), (q_n + q_s + q_e + q_w)

# ===============================
# TRAINING (NO GUI)
# ===============================

def train():
    global epsilon

    sumo_cmd = ["sumo", "-c", "sim_tls.sumocfg"]

    for episode in range(20):
        print(f"\n🚀 Episode {episode+1}")

        traci.start(sumo_cmd)

        last_switch = 0
        current_action = 0

        for step in range(600):

            state, _ = get_state()

            if step - last_switch >= MIN_GREEN:
                action = choose_action(state)

                if action != current_action:
                    current_action = action
                    last_switch = step
            else:
                action = current_action

            # APPLY ACTION
            if current_action == 0:
                traci.trafficlight.setPhase("C", 0)
            else:
                traci.trafficlight.setPhase("C", 2)

            traci.simulationStep()

            next_state, next_total_queue = get_state()

            waiting = sum(
                traci.vehicle.getWaitingTime(v)
                for v in traci.vehicle.getIDList()
            )

            reward = - (0.7 * next_total_queue + 0.3 * waiting)

            update_q(state, action, reward, next_state)

        traci.close()
        print("✅ Episode completed")

        epsilon = max(min_epsilon, epsilon * epsilon_decay)

    print("\n🎯 Training Finished!")

# ===============================
# TEST (GUI MODE + METRICS)
# ===============================

def test():
    print("\n🧪 Starting GUI Simulation...")

    sumo_cmd = ["sumo-gui", "-c", "sim_tls.sumocfg"]
    traci.start(sumo_cmd)

    last_switch = 0
    current_action = 0

    # ===============================
    # METRICS
    # ===============================
    total_waiting_time = 0.0
    total_queue = 0
    vehicle_count_sum = 0
    completed_vehicles = set()
    steps = 1000

    for step in range(steps):

        state, _ = get_state()

        if step - last_switch >= MIN_GREEN:
            action = max([0, 1], key=lambda a: get_q(state, a))

            if action != current_action:
                current_action = action
                last_switch = step

        # APPLY ACTION
        if current_action == 0:
            traci.trafficlight.setPhase("C", 0)
        else:
            traci.trafficlight.setPhase("C", 2)

        traci.simulationStep()

        vehicles = traci.vehicle.getIDList()
        vehicle_count_sum += len(vehicles)

        # WAITING TIME
        step_wait = 0
        for v in vehicles:
            step_wait += traci.vehicle.getWaitingTime(v)
        total_waiting_time += step_wait

        # QUEUE LENGTH
        step_queue = 0
        for lane in ["N2C_0", "S2C_0", "E2C_0", "W2C_0"]:
            step_queue += traci.lane.getLastStepHaltingNumber(lane)
        total_queue += step_queue

        # THROUGHPUT
        arrived = traci.simulation.getArrivedIDList()
        for v in arrived:
            completed_vehicles.add(v)

    # ===============================
    # FINAL METRICS
    # ===============================
    avg_waiting_time = total_waiting_time / max(vehicle_count_sum, 1)
    avg_queue_length = total_queue / max(steps, 1)
    throughput = len(completed_vehicles)

    print("\n=== Q-LEARNING RESULTS ===")
    print(f"Average Waiting Time: {avg_waiting_time:.2f} sec")
    print(f"Average Queue Length: {avg_queue_length:.2f} vehicles")
    print(f"Throughput: {throughput} vehicles")

    print("🛑 Simulation ended")
    traci.close()

# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    train()
    test()