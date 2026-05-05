import traci

sumo_cmd = ["sumo-gui", "-c", "sim_tls.sumocfg"]
traci.start(sumo_cmd)

tls_ids = traci.trafficlight.getIDList()
print("Traffic Lights:", tls_ids)

steps = 600
for step in range(steps):

    traci.simulationStep()

    for tls in tls_ids:

        lanes = traci.trafficlight.getControlledLanes(tls)

        ns_queue = 0
        ew_queue = 0

        for lane in lanes:

            q = traci.lane.getLastStepHaltingNumber(lane)

            if "N2C" in lane or "S2C" in lane:
                ns_queue += q
            else:
                ew_queue += q

        # choose direction with more traffic
        if ns_queue > ew_queue:
            traci.trafficlight.setPhase(tls, 0)
        else:
            traci.trafficlight.setPhase(tls, 2)

    if step % 50 == 0:
        print(f"Step {step}")


traci.close()