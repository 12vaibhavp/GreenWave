"""
WebSocket Live Telemetry Streaming Endpoint.
"""
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services.simulation_service import simulation_service

router = APIRouter()


@router.websocket("/ws/traffic")
async def traffic_telemetry_websocket(websocket: WebSocket):
    """
    Stream live simulation metrics, current signal phase, queues, and throughput at 5Hz.
    """
    await websocket.accept()
    try:
        while True:
            state = simulation_service.get_current_state()
            await websocket.send_json(state)
            await asyncio.sleep(0.2)  # 5 updates/second
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
