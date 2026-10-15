"""
SQLite Database Engine and Experiment Storage Tables.
"""
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from backend.app.config.settings import settings


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get or initialize SQLite database connection."""
    target_path = Path(db_path or settings.DATABASE_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables for experiments and real-time telemetry."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_id TEXT UNIQUE NOT NULL,
        timestamp TEXT NOT NULL,
        controller TEXT NOT NULL,
        scenario TEXT NOT NULL,
        seed INTEGER NOT NULL,
        duration_sec INTEGER NOT NULL,
        avg_waiting_time REAL NOT NULL,
        total_waiting_time REAL NOT NULL,
        avg_queue_length REAL NOT NULL,
        max_queue_length INTEGER NOT NULL,
        throughput INTEGER NOT NULL,
        total_departed INTEGER NOT NULL,
        avg_travel_time REAL NOT NULL,
        avg_speed_mps REAL NOT NULL,
        config_json TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_id TEXT NOT NULL,
        step INTEGER NOT NULL,
        phase INTEGER NOT NULL,
        ns_queue INTEGER NOT NULL,
        ew_queue INTEGER NOT NULL,
        total_queue INTEGER NOT NULL,
        total_waiting REAL NOT NULL,
        throughput INTEGER NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()


def save_experiment_result(result: Dict[str, Any], db_path: Optional[str] = None) -> None:
    """Insert a completed simulation experiment record into the database."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO experiments (
        experiment_id, timestamp, controller, scenario, seed, duration_sec,
        avg_waiting_time, total_waiting_time, avg_queue_length, max_queue_length,
        throughput, total_departed, avg_travel_time, avg_speed_mps, config_json
    ) VALUES (
        :experiment_id, :timestamp, :controller, :scenario, :seed, :duration_sec,
        :avg_waiting_time, :total_waiting_time, :avg_queue_length, :max_queue_length,
        :throughput, :total_departed, :avg_travel_time, :avg_speed_mps, :config_json
    );
    """, result)

    conn.commit()
    conn.close()


def fetch_all_experiments(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all logged experiment results."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments ORDER BY id DESC")
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
