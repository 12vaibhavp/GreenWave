"""
Experiment Management and Benchmark Service.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
from backend.app.models.database import fetch_all_experiments
from backend.app.config.settings import settings


class ExperimentService:
    """Provides querying and report generation for logged experiments."""

    @staticmethod
    def get_experiments() -> List[Dict[str, Any]]:
        """Fetch all logged experiment records from SQLite."""
        return fetch_all_experiments()

    @staticmethod
    def get_benchmark_summary() -> List[Dict[str, Any]]:
        """Read pre-computed benchmark summary CSV or generate on-the-fly."""
        summary_csv = Path(settings.RESULTS_DIR) / "benchmark_summary.csv"
        if summary_csv.exists():
            df = pd.read_csv(summary_csv)
            return df.to_dict(orient="records")
        return []

    @staticmethod
    def export_csv() -> str:
        """Export experiments data as CSV string."""
        records = fetch_all_experiments()
        if not records:
            return "No experiment records found."
        df = pd.DataFrame(records)
        return df.to_csv(index=False)

experiment_service = ExperimentService()
