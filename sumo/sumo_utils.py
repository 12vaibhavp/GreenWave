"""
SUMO Binary and Environment Utility
"""
import os
import sys
import shutil
from pathlib import Path
from typing import Optional
import sumolib

# Auto-configure SUMO_HOME
if "SUMO_HOME" not in os.environ or not os.path.exists(os.environ["SUMO_HOME"]):
    try:
        import sumo_data
        sumo_data_path = list(sumo_data.__path__)[0]
        if os.path.exists(sumo_data_path):
            os.environ["SUMO_HOME"] = sumo_data_path
    except Exception:
        pass


def get_sumo_binary(gui: bool = False) -> str:
    """Resolve correct path to sumo or sumo-gui binary."""
    binary_name = "sumo-gui" if gui else "sumo"
    
    # 1. Check virtualenv bin
    venv_bin = Path(sys.executable).parent / binary_name
    if venv_bin.exists() and os.access(venv_bin, os.X_OK):
        return str(venv_bin)
        
    # 2. Check sumolib checkBinary
    try:
        bin_path = sumolib.checkBinary(binary_name)
        if bin_path and os.path.exists(bin_path) and os.access(bin_path, os.X_OK):
            return bin_path
    except Exception:
        pass

    # 3. Check system PATH
    sys_bin = shutil.which(binary_name)
    if sys_bin:
        return sys_bin

    raise FileNotFoundError(f"Could not locate executable '{binary_name}' binary.")


def get_netconvert_binary() -> str:
    """Resolve correct path to netconvert binary."""
    # 1. Check virtualenv bin
    venv_bin = Path(sys.executable).parent / "netconvert"
    if venv_bin.exists() and os.access(venv_bin, os.X_OK):
        return str(venv_bin)

    try:
        bin_path = sumolib.checkBinary("netconvert")
        if bin_path and os.path.exists(bin_path) and os.access(bin_path, os.X_OK):
            return bin_path
    except Exception:
        pass

    sys_bin = shutil.which("netconvert")
    if sys_bin:
        return sys_bin

    raise FileNotFoundError("Could not locate executable 'netconvert' binary.")
