/**
 * GREENWAVE Dashboard Application Logic
 */

// State variables
let ws = null;
let queueChart = null;
let waitChart = null;
const MAX_CHART_POINTS = 30;

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initCharts();
  initWebSocket();
  loadRLStatus();
  loadBenchmarkSummary();
  loadExperiments();
});

// 1. Navigation handling
function initNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  const pages = document.querySelectorAll(".page-section");

  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      const pageId = item.getAttribute("data-page");

      navItems.forEach((n) => n.classList.remove("active"));
      pages.forEach((p) => p.classList.remove("active"));

      item.classList.add("active");
      const targetPage = document.getElementById(`page-${pageId}`);
      if (targetPage) {
        targetPage.classList.add("active");
      }

      // Trigger re-renders or data fetches if needed
      if (pageId === "experiments") loadExperiments();
      if (pageId === "comparison") loadBenchmarkSummary();
      if (pageId === "rl") loadRLStatus();
    });
  });
}

// 2. Real-Time Charts Setup
function initCharts() {
  const ctxQueue = document.getElementById("chart-queue");
  const ctxWait = document.getElementById("chart-wait");

  if (ctxQueue && typeof Chart !== "undefined") {
    queueChart = new Chart(ctxQueue, {
      type: "line",
      data: {
        labels: [],
        datasets: [{
          label: "Queue Length (veh)",
          data: [],
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          borderWidth: 2,
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        animation: false,
        scales: {
          x: { grid: { color: "#334155" }, ticks: { color: "#94a3b8" } },
          y: { grid: { color: "#334155" }, ticks: { color: "#94a3b8" }, beginAtZero: true }
        }
      }
    });
  }

  if (ctxWait && typeof Chart !== "undefined") {
    waitChart = new Chart(ctxWait, {
      type: "line",
      data: {
        labels: [],
        datasets: [{
          label: "Total Waiting Time (s)",
          data: [],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          borderWidth: 2,
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        animation: false,
        scales: {
          x: { grid: { color: "#334155" }, ticks: { color: "#94a3b8" } },
          y: { grid: { color: "#334155" }, ticks: { color: "#94a3b8" }, beginAtZero: true }
        }
      }
    });
  }
}

// 3. WebSocket Telemetry
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/traffic`;

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      document.getElementById("system-status-dot").style.backgroundColor = "#10b981";
      document.getElementById("system-status-text").innerText = "TraCI Live";
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateDashboardTelemetry(data);
    };

    ws.onclose = () => {
      document.getElementById("system-status-dot").style.backgroundColor = "#ef4444";
      document.getElementById("system-status-text").innerText = "Reconnecting...";
      setTimeout(initWebSocket, 2000);
    };
  } catch (err) {
    console.error("WebSocket error:", err);
  }
}

function updateDashboardTelemetry(data) {
  // Update KPIs
  document.getElementById("kpi-active-controller").innerText = data.active_controller.toUpperCase();
  document.getElementById("kpi-throughput").innerText = data.throughput;
  document.getElementById("kpi-queue").innerText = data.total_queue;
  document.getElementById("kpi-wait").innerText = `${data.total_waiting_time.toFixed(1)}s`;

  // Update Signal Schematic
  const isNS = (data.current_phase === 0 || data.current_phase === 1);
  const isYellow = (data.current_phase === 1 || data.current_phase === 3);

  const nBadge = document.getElementById("sig-north-badge");
  const sBadge = document.getElementById("sig-south-badge");
  const eBadge = document.getElementById("sig-east-badge");
  const wBadge = document.getElementById("sig-west-badge");

  if (nBadge && sBadge && eBadge && wBadge) {
    if (isNS) {
      const cls = isYellow ? "sig-yellow" : "sig-green";
      const txt = isYellow ? "YELLOW" : "GREEN";
      nBadge.className = `signal-badge sig-north ${cls}`;
      sBadge.className = `signal-badge sig-south ${cls}`;
      nBadge.innerText = `North: ${txt} (${data.phase_duration}s)`;
      sBadge.innerText = `South: ${txt} (${data.phase_duration}s)`;

      eBadge.className = "signal-badge sig-east sig-red";
      wBadge.className = "signal-badge sig-west sig-red";
      eBadge.innerText = "East: RED";
      wBadge.innerText = "West: RED";
    } else {
      const cls = isYellow ? "sig-yellow" : "sig-green";
      const txt = isYellow ? "YELLOW" : "GREEN";
      eBadge.className = `signal-badge sig-east ${cls}`;
      wBadge.className = `signal-badge sig-west ${cls}`;
      eBadge.innerText = `East: ${txt} (${data.phase_duration}s)`;
      wBadge.innerText = `West: ${txt} (${data.phase_duration}s)`;

      nBadge.className = "signal-badge sig-north sig-red";
      sBadge.className = "signal-badge sig-south sig-red";
      nBadge.innerText = "North: RED";
      sBadge.innerText = "South: RED";
    }
  }

  // Update Approach breakdown table & Multi-Sensor Array (S1, S2, S3)
  if (data.approaches) {
    const apps = ["North", "South", "East", "West"];
    const prefix = ["n", "s", "e", "w"];
    apps.forEach((app, i) => {
      const info = data.approaches[app];
      if (info) {
        const p = prefix[i];
        const cntEl = document.getElementById(`app-${p}-cnt`);
        if (cntEl) cntEl.innerText = info.active_vehicles;
        const qEl = document.getElementById(`app-${p}-q`);
        if (qEl) qEl.innerText = info.queue_length;
        const wEl = document.getElementById(`app-${p}-w`);
        if (wEl) wEl.innerText = `${info.waiting_time_s.toFixed(1)}s`;
        const dEl = document.getElementById(`app-${p}-d`);
        if (dEl) {
          dEl.innerText = info.density_level;
          dEl.style.color = info.density_level === "HIGH" ? "#ef4444" : info.density_level === "MEDIUM" ? "#f59e0b" : "#10b981";
        }

        // Multi-Sensor Tab updates
        const s1El = document.getElementById(`s-${p}-s1`);
        if (s1El) s1El.innerText = `${info.queue_length} veh`;

        const s3El = document.getElementById(`s-${p}-s3`);
        const radarApproaching = Math.max(0, info.active_vehicles - info.queue_length);
        if (s3El) s3El.innerText = `${radarApproaching} veh`;

        const spdEl = document.getElementById(`s-${p}-spd`);
        const estSpeed = radarApproaching > 0 ? 11.5 : 0.0;
        if (spdEl) spdEl.innerText = `${estSpeed.toFixed(1)} m/s`;

        const etaEl = document.getElementById(`s-${p}-eta`);
        const estEta = estSpeed > 1.0 ? `${(100.0 / estSpeed).toFixed(1)}s` : "--";
        if (etaEl) etaEl.innerText = estEta;

        const s2El = document.getElementById(`s-${p}-s2`);
        if (s2El) {
          const isDilemma = (radarApproaching > 0 && estSpeed >= 8.0);
          s2El.innerText = isDilemma ? "⚠️ DILEMMA RISK" : "CLEAR";
          s2El.style.color = isDilemma ? "#f59e0b" : "#10b981";
        }
      }
    });
  }

  // Update Charts
  if (queueChart && data.step > 0) {
    queueChart.data.labels.push(`t=${data.step}`);
    queueChart.data.datasets[0].data.push(data.total_queue);
    if (queueChart.data.labels.length > MAX_CHART_POINTS) {
      queueChart.data.labels.shift();
      queueChart.data.datasets[0].data.shift();
    }
    queueChart.update();
  }

  if (waitChart && data.step > 0) {
    waitChart.data.labels.push(`t=${data.step}`);
    waitChart.data.datasets[0].data.push(data.total_waiting_time);
    if (waitChart.data.labels.length > MAX_CHART_POINTS) {
      waitChart.data.labels.shift();
      waitChart.data.datasets[0].data.shift();
    }
    waitChart.update();
  }
}

// 4. API Actions
async function startSimulation() {
  const ctrl = document.getElementById("sim-ctrl-select").value;
  const scen = document.getElementById("sim-scen-select").value;
  const seed = parseInt(document.getElementById("sim-seed-input").value) || 42;
  const duration = parseInt(document.getElementById("sim-duration-input").value) || 1800;

  const res = await fetch("/api/v1/simulation/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ controller: ctrl, scenario: scen, seed: seed, duration: duration, step_delay_sec: 0.05 })
  });
  const data = await res.json();
  console.log("Started simulation:", data);
}

async function stopSimulation() {
  await fetch("/api/v1/simulation/stop", { method: "POST" });
}

async function resetSimulation() {
  await fetch("/api/v1/simulation/reset", { method: "POST" });
  if (queueChart) {
    queueChart.data.labels = [];
    queueChart.data.datasets[0].data = [];
    queueChart.update();
  }
  if (waitChart) {
    waitChart.data.labels = [];
    waitChart.data.datasets[0].data = [];
    waitChart.update();
  }
}

async function startVision() {
  await fetch("/api/v1/vision/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: "sample" })
  });
}

async function stopVision() {
  await fetch("/api/v1/vision/stop", { method: "POST" });
}

async function loadRLStatus() {
  const res = await fetch("/api/v1/rl/status");
  const data = await res.json();

  document.getElementById("rl-alpha").innerText = data.alpha.toFixed(2);
  document.getElementById("rl-gamma").innerText = data.gamma.toFixed(2);
  document.getElementById("rl-epsilon").innerText = data.epsilon.toFixed(2);
  document.getElementById("rl-states-cnt").innerText = data.total_states_discovered;

  const tbody = document.getElementById("qtable-sample-tbody");
  if (data.sample_state_actions && Object.keys(data.sample_state_actions).length > 0) {
    tbody.innerHTML = "";
    Object.entries(data.sample_state_actions).forEach(([state, qVals]) => {
      const best = qVals[0] >= qVals[1] ? "KEEP_PHASE" : "SWITCH_PHASE";
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code>${state}</code></td>
        <td>${qVals[0].toFixed(2)}</td>
        <td>${qVals[1].toFixed(2)}</td>
        <td style="color:${best === 'KEEP_PHASE' ? '#10b981' : '#f59e0b'}; font-weight:700;">${best}</td>
      `;
      tbody.appendChild(tr);
    });
  }
}

async function loadBenchmarkSummary() {
  const res = await fetch("/api/v1/experiments/benchmark/summary");
  const data = await res.json();
  const tbody = document.getElementById("benchmark-full-tbody");

  if (Array.isArray(data) && data.length > 0) {
    tbody.innerHTML = "";
    data.forEach((row) => {
      const tr = document.createElement("tr");
      const isPositiveWait = row.waiting_time_reduction_pct > 0;
      const isPositiveQueue = row.queue_reduction_pct > 0;

      tr.innerHTML = `
        <td style="font-weight:600; text-transform:capitalize;">${row.scenario}</td>
        <td>${row.controller_label}</td>
        <td>${row.avg_waiting_time_s}s &plusmn; ${row.waiting_time_std}</td>
        <td style="color:${isPositiveWait ? '#10b981' : '#ef4444'}; font-weight:700;">
          ${row.waiting_time_reduction_pct > 0 ? '-' : ''}${Math.abs(row.waiting_time_reduction_pct)}%
        </td>
        <td>${row.avg_queue_length_veh} &plusmn; ${row.queue_length_std}</td>
        <td style="color:${isPositiveQueue ? '#10b981' : '#ef4444'}; font-weight:700;">
          ${row.queue_reduction_pct > 0 ? '-' : ''}${Math.abs(row.queue_reduction_pct)}%
        </td>
        <td>${row.throughput_veh}</td>
      `;
      tbody.appendChild(tr);
    });
  }
}

async function loadExperiments() {
  const res = await fetch("/api/v1/experiments");
  const data = await res.json();
  const tbody = document.getElementById("experiments-db-tbody");

  if (Array.isArray(data) && data.length > 0) {
    tbody.innerHTML = "";
    data.slice(0, 30).forEach((exp) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>#${exp.id}</td>
        <td>${exp.timestamp.substring(0, 19).replace("T", " ")}</td>
        <td><strong>${exp.controller}</strong></td>
        <td>${exp.scenario}</td>
        <td>${exp.seed}</td>
        <td>${exp.avg_waiting_time}s</td>
        <td>${exp.avg_queue_length}</td>
        <td>${exp.throughput}</td>
        <td>${exp.avg_travel_time}s</td>
      `;
      tbody.appendChild(tr);
    });
  }
}
