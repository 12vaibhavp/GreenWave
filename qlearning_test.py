import traci
import json

with open("q_table.json", "r") as f:
    Q = {eval(k): v for k, v in json.load(f).items()}

def get_q(state, action):
    return Q.get((state, action), 0.0)

def choose_best_action(state):
    q0 = get_q(state, 0)
    q1 = get_q(state, 1)
    return 0 if q0 >= q1 else 1

def get_state():
    q_n = traci.lane.getLastStepHaltingNumber("N2C_0")
    q_s = traci.lane.getLastStepHaltingNumber("S2C_0")
    q_e = traci.lane.getLastStepHaltingNumber("E2C_0")
    q_w = traci.lane.getLastStepHaltingNumber("W2C_0")

    ns = min((q_n + q_s)//3, 5)
    ew = min((q_e + q_w)//3, 5)

    return (ns, ew)

sumo_cmd = ["sumo-gui", "-c", "sim_tls.sumocfg"]
traci.start(sumo_cmd)

tls_id = "C"

try:
    for step in range(600):

        state = get_state()

        action = choose_best_action(state)

        if action == 0:
            traci.trafficlight.setPhase(tls_id, 0)
        else:
            traci.trafficlight.setPhase(tls_id, 2)

        traci.simulationStep()

finally:
    traci.close()