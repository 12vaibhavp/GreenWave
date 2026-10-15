"""
Phase 8 Automated Tests: FastAPI Backend Endpoints & Data Contracts
"""
import pytest
from starlette.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    """Create test client instance."""
    return TestClient(app)


def test_health_endpoint(client):
    """Ensure /health returns 200 and accurate system metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "GREENWAVE" in data["project"]
    assert "yolo_loaded" in data


def test_traffic_current_endpoint(client):
    """Ensure /api/v1/traffic/current returns approach breakdowns."""
    response = client.get("/api/v1/traffic/current")
    assert response.status_code == 200
    data = response.json()
    assert "approaches" in data
    assert "North" in data["approaches"]
    assert "total_queue" in data


def test_signals_endpoint(client):
    """Ensure /api/v1/signals returns phase info."""
    response = client.get("/api/v1/signals")
    assert response.status_code == 200
    data = response.json()
    assert "current_phase" in data
    assert "phase_name" in data


def test_experiments_endpoint(client):
    """Ensure /api/v1/experiments returns list of logged experiments."""
    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "experiment_id" in first
        assert "avg_waiting_time" in first


def test_rl_status_endpoint(client):
    """Ensure /api/v1/rl/status returns Q-table information."""
    response = client.get("/api/v1/rl/status")
    assert response.status_code == 200
    data = response.json()
    assert "q_table_loaded" in data
    assert "total_states_discovered" in data


def test_simulation_controls(client):
    """Ensure start and stop simulation endpoints respond with 200."""
    start_payload = {
        "controller": "fixed_time",
        "scenario": "low",
        "seed": 42,
        "duration": 50,
        "step_delay_sec": 0.01
    }
    res_start = client.post("/api/v1/simulation/start", json=start_payload)
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "started"

    res_stop = client.post("/api/v1/simulation/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "stopped"

def test_dashboard_index_and_static_files(client):
    """Ensure dashboard index and static JS/CSS are served."""
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "GREENWAVE" in res_index.text

    res_css = client.get("/static/css/style.css")
    assert res_css.status_code == 200
    assert "--bg-primary" in res_css.text

    res_js = client.get("/static/js/app.js")
    assert res_js.status_code == 200
    assert "updateDashboardTelemetry" in res_js.text
