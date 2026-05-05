import traci

sumo_cmd = ["sumo-gui", "-c", "sim_tls.sumocfg"]
traci.start(sumo_cmd)

# ===============================
# METRIC VARIABLES
# ===============================
total_waiting_time = 0.0
total_queue = 0
vehicle_count_sum = 0
completed_vehicles = set()
steps = 600

try:
    tls_ids = traci.trafficlight.getIDList()
    print("Traffic Lights:", tls_ids)

    for step in range(steps):
        traci.simulationStep()

        vehicles = traci.vehicle.getIDList()
        vehicle_count_sum += len(vehicles)

        # waiting time (sum for this step)
        step_wait = 0
        for v in vehicles:
            step_wait += traci.vehicle.getWaitingTime(v)
        total_waiting_time += step_wait

        # queue length (all lanes)
        step_queue = 0
        for lane in ["N2C_0", "S2C_0", "E2C_0", "W2C_0"]:
            step_queue += traci.lane.getLastStepHaltingNumber(lane)
        total_queue += step_queue

        # throughput (arrived vehicles)
        arrived = traci.simulation.getArrivedIDList()
        for v in arrived:
            completed_vehicles.add(v)

        if step % 50 == 0:
            print(f"Step {step}")

    # ===============================
    # FINAL METRICS
    # ===============================

    avg_waiting_time = total_waiting_time / max(vehicle_count_sum, 1)
    avg_queue_length = total_queue / max(steps, 1)
    throughput = len(completed_vehicles)

    print("\n=== FIXED SIGNAL RESULTS ===")
    print(f"Average Waiting Time: {avg_waiting_time:.2f} sec")
    print(f"Average Queue Length: {avg_queue_length:.2f} vehicles")
    print(f"Throughput: {throughput} vehicles")

finally:
    traci.close()