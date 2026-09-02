import os
import sys
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    from backend.grpc_communication.simulation import (
        SimulationRequest,
        PRESET_RESOURCES,
        run_concurrent_conflict_simulation
    )
except ImportError:
    from grpc_communication.simulation import (
        SimulationRequest,
        PRESET_RESOURCES,
        run_concurrent_conflict_simulation
    )

router = APIRouter(prefix="/api/coordination", tags=["Distributed Coordination Simulation"])

@router.get("/preset-resources")
def get_preset_resources():
    """
    Returns list of curated campus-wide shared resources available for concurrent simulation.
    """
    return PRESET_RESOURCES

@router.post("/simulate-conflict")
def simulate_concurrent_conflict(config: SimulationRequest):
    """
    Executes a real-time concurrent conflict simulation between two department nodes:
    - Independent Lamport logical clock progression.
    - Ricart-Agrawala mutual exclusion ordering using (timestamp, node_name).
    - True SQLite database booking for the winner and conflict prevention for the loser.
    - Full chronological event trace for UI visualization.
    """
    try:
        result = run_concurrent_conflict_simulation(config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")
