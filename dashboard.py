import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import time

st.set_page_config(page_title="GreenWave AI", layout="wide")

# =========================
# CUSTOM CSS (ULTRA UI)
# =========================
st.markdown("""
<style>
.main {
    background-color: #0e1117;
}
.title {
    font-size: 50px;
    font-weight: 800;
    color: #00FFA3;
}
.subtitle {
    font-size: 18px;
    color: #9aa0a6;
}
.card {
    background: linear-gradient(145deg, #1c1f26, #222733);
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 0 15px rgba(0,255,163,0.3);
    transition: 0.3s;
}
.card:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# =========================
# HERO SECTION
# =========================
st.markdown('<div class="title">🚦 GreenWave AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Next-Gen Traffic Intelligence Platform</div>', unsafe_allow_html=True)

st.markdown("---")

# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ Control Panel")

mode = st.sidebar.selectbox(
    "Choose Algorithm",
    ["Fixed Signal", "Adaptive Signal", "AI (Q-Learning)"]
)

run = st.sidebar.button("🚀 Run AI Engine")

# =========================
# DATA (REALISTIC DEMO)
# =========================
data = {
    "Fixed Signal": {"wait": 25.4, "queue": 18.2, "throughput": 210},
    "Adaptive Signal": {"wait": 17.8, "queue": 12.5, "throughput": 260},
    "AI (Q-Learning)": {"wait": 10.6, "queue": 8.3, "throughput": 310}
}

# =========================
# ANIMATION FUNCTION
# =========================
def animate_metric(target):
    val = 0
    step = target / 30
    for _ in range(30):
        val += step
        time.sleep(0.01)
    return round(target, 2)

# =========================
# KPI SECTION
# =========================
col1, col2, col3 = st.columns(3)

if run:
    with st.spinner("⚡ AI Optimizing Traffic..."):
        time.sleep(2)

    result = data[mode]

    wait = animate_metric(result["wait"])
    queue = animate_metric(result["queue"])
    throughput = animate_metric(result["throughput"])

    col1.markdown(f'<div class="card">⏳<h1>{wait}</h1><p>Waiting Time (sec)</p></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="card">🚗<h1>{queue}</h1><p>Queue Length</p></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="card">📈<h1>{throughput}</h1><p>Throughput</p></div>', unsafe_allow_html=True)

    st.success("AI Optimization Complete ✅")

else:
    st.info("Click 'Run AI Engine' to start simulation")

st.markdown("---")

# =========================
# LIVE GRAPH (FAKE REAL-TIME)
# =========================
st.markdown("## 📊 Live Traffic Trend")

chart_data = pd.DataFrame({
    "time": list(range(30)),
    "traffic": [20 + i + (i % 5)*3 for i in range(30)]
})

st.line_chart(chart_data.set_index("time"))

# =========================
# COMPARISON GRAPH
# =========================
st.markdown("## 📈 Algorithm Comparison")

df = pd.DataFrame({
    "Method": ["Fixed", "Adaptive", "Q-Learning"],
    "Waiting Time": [25.4, 17.8, 10.6],
    "Queue Length": [18.2, 12.5, 8.3],
    "Throughput": [210, 260, 310]
})

fig, ax = plt.subplots()
df.set_index("Method").plot(kind="bar", ax=ax)
ax.set_title("Performance Comparison")

st.pyplot(fig)

# =========================
# FEATURES GRID
# =========================
st.markdown("## ⚡ Features")

c1, c2, c3 = st.columns(3)

c1.markdown("🚦 **Smart Signal Control**")
c2.markdown("🧠 **AI Learning Engine**")
c3.markdown("📊 **Real-Time Analytics**")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown("🌐 GreenWave AI | Smart City Traffic Solution Prototype")