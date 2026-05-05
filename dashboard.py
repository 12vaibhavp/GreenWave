import streamlit as st
import matplotlib.pyplot as plt
import subprocess
import time

st.set_page_config(page_title="GreenWave Traffic AI", layout="wide")

# =========================
# HEADER
# =========================
st.title("🚦 GreenWave: AI Traffic Signal Control")
st.markdown("### Smart Traffic Optimization using Reinforcement Learning")

st.sidebar.title("⚙️ Controls")

mode = st.sidebar.selectbox(
    "Select Mode",
    ["Fixed Signal", "Adaptive Signal", "AI (Q-Learning)"]
)

run_btn = st.sidebar.button("▶ Run Simulation")

# =========================
# PLACEHOLDERS
# =========================
col1, col2, col3 = st.columns(3)

metric_wait = col1.empty()
metric_queue = col2.empty()
metric_throughput = col3.empty()

graph_placeholder = st.empty()

# =========================
# SIMULATION RUN
# =========================
def run_simulation(script_name):
    result = subprocess.run(
        ["python", script_name],
        capture_output=True,
        text=True
    )
    return result.stdout

# =========================
# PARSE OUTPUT
# =========================
def extract_metrics(output):
    lines = output.split("\n")

    wait = 0
    queue = 0
    throughput = 0

    for line in lines:
        if "Average Waiting Time" in line:
            wait = float(line.split(":")[-1])
        if "Average Queue Length" in line:
            queue = float(line.split(":")[-1])
        if "Throughput" in line:
            throughput = float(line.split(":")[-1])

    return wait, queue, throughput

# =========================
# RUN BUTTON LOGIC
# =========================
if run_btn:

    st.info("Running simulation... Please wait ⏳")

    if mode == "Fixed Signal":
        output = run_simulation("fixed_control.py")

    elif mode == "Adaptive Signal":
        output = run_simulation("adaptive_control.py")

    else:
        output = run_simulation("qlearning_control.py")

    wait, queue, throughput = extract_metrics(output)

    # =========================
    # SHOW METRICS
    # =========================
    metric_wait.metric("⏳ Avg Waiting Time", f"{wait:.2f} sec")
    metric_queue.metric("🚗 Avg Queue Length", f"{queue:.2f}")
    metric_throughput.metric("📈 Throughput", f"{throughput:.0f}")

    # =========================
    # GRAPH
    # =========================
    fig, ax = plt.subplots()

    labels = ["Waiting Time", "Queue Length", "Throughput"]
    values = [wait, queue, throughput]

    ax.bar(labels, values)
    ax.set_title("Performance Comparison")

    graph_placeholder.pyplot(fig)

    st.success("Simulation Completed ✅")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown("👨‍💻 Developed by Vaibhav Prakash | AI Traffic Optimization Project")
