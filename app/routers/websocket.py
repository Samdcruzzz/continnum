"""
WebSocket Routes for Real-Time Alert Streaming

Provides live alert updates via WebSocket for:
- Clinical dashboards
- Mobile push notifications
- Real-time monitoring
- Alert acknowledgment/resolution

Connection URL: ws://localhost:8000/ws/patients/{patient_id}/alerts?requester_id={id}&role={role}
"""

import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocketException, Query, WebSocketDisconnect
from fastapi.websockets import WebSocket

from app.database import SessionLocal
from app.ai_agents.orchestrator import HealthMemoryOrchestrator
from app.ai_agents.alert_engine import RealTimeAlertEngine, Alert

# Initialize router
router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.alert_engine: Optional[RealTimeAlertEngine] = None

    def set_alert_engine(self, engine: RealTimeAlertEngine):
        """Set the alert engine for this connection manager"""
        self.alert_engine = engine

    async def connect(self, websocket: WebSocket, patient_id: int):
        """Register a new WebSocket connection"""
        await websocket.accept()

        if patient_id not in self.active_connections:
            self.active_connections[patient_id] = set()

        self.active_connections[patient_id].add(websocket)

        # Subscribe to alerts
        if self.alert_engine:
            async def alert_callback(alert: Alert):
                """Callback to send alert to this client"""
                await self.send_personal_alert(websocket, alert)

            self.alert_engine.subscribe_patient_alerts(patient_id, alert_callback)

    def disconnect(self, websocket: WebSocket, patient_id: int):
        """Unregister a WebSocket connection"""
        if patient_id in self.active_connections:
            self.active_connections[patient_id].discard(websocket)

            if not self.active_connections[patient_id]:
                del self.active_connections[patient_id]

                # Unsubscribe from alerts
                if self.alert_engine:
                    self.alert_engine.unsubscribe_patient_alerts(patient_id, None)

    async def send_personal_alert(self, websocket: WebSocket, alert: Alert):
        """Send alert to specific client"""
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "alert",
                        "event": "new_alert",
                        "data": {
                            "alert_id": alert.alert_id,
                            "patient_id": alert.patient_id,
                            "severity": alert.severity.value,
                            "category": alert.category.value,
                            "message": alert.message,
                            "action": alert.action,
                            "timestamp": alert.timestamp,
                            "source_agent": alert.source_agent,
                        },
                    }
                )
            )
        except Exception as e:
            print(f"Error sending alert: {e}")

    async def broadcast_to_patient(self, patient_id: int, message: dict):
        """Broadcast message to all clients watching a patient"""
        if patient_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[patient_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)

            # Clean up disconnected clients
            self.active_connections[patient_id] -= disconnected


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/patients/{patient_id}/alerts")
async def websocket_patient_alerts(
    websocket: WebSocket,
    patient_id: int,
    requester_id: int = Query(...),
    requester_role: str = Query(default="clinician"),
):
    """
    WebSocket endpoint for real-time patient alerts.

    Connection Parameters:
    - patient_id: Target patient ID
    - requester_id: ID of connected user
    - requester_role: User role (clinician, guardian, caregiver)

    Example URL:
    ws://localhost:8000/ws/patients/1/alerts?requester_id=5&requester_role=clinician

    Message Types Sent:
    1. connection_established
    2. alert (real-time alerts)
    3. alert_acknowledged
    4. alert_resolved
    5. error

    Message Format:
    {
        "type": "alert",
        "event": "new_alert",
        "data": {
            "alert_id": "POLY-1-0",
            "severity": "HIGH",
            "message": "...",
            "action": "...",
            "timestamp": "2026-09-13T12:30:00Z"
        }
    }
    """

    db = SessionLocal()
    orchestrator = HealthMemoryOrchestrator(db)
    alert_engine = RealTimeAlertEngine(db, orchestrator)
    manager.set_alert_engine(alert_engine)

    try:
        # Verify access via orchestrator consent check
        access_check = orchestrator._check_access_permission(
            patient_id, requester_id, requester_role
        )

        if not access_check:
            await websocket.close(
                code=403, reason="Access denied: consent not verified"
            )
            return

        await manager.connect(websocket, patient_id)

        # Send connection confirmation
        await websocket.send_json(
            {
                "type": "connection",
                "event": "connection_established",
                "data": {
                    "patient_id": patient_id,
                    "requester_id": requester_id,
                    "requester_role": requester_role,
                    "message": "Connected to patient alert stream",
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                },
            }
        )

        # Send existing alert history (last 10)
        alert_history = alert_engine.get_alert_history(patient_id, limit=10)
        await websocket.send_json(
            {
                "type": "alert_history",
                "event": "history_available",
                "data": {
                    "alert_count": len(alert_history),
                    "alerts": alert_history,
                },
            }
        )

        # Listen for incoming messages (acknowledgments, etc.)
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "acknowledge_alert":
                alert_id = message.get("alert_id")
                if alert_engine.acknowledge_alert(alert_id):
                    await manager.broadcast_to_patient(
                        patient_id,
                        {
                            "type": "alert",
                            "event": "alert_acknowledged",
                            "data": {"alert_id": alert_id},
                        },
                    )

            elif message_type == "resolve_alert":
                alert_id = message.get("alert_id")
                if alert_engine.resolve_alert(alert_id):
                    await manager.broadcast_to_patient(
                        patient_id,
                        {
                            "type": "alert",
                            "event": "alert_resolved",
                            "data": {"alert_id": alert_id},
                        },
                    )

            elif message_type == "get_latest_alerts":
                limit = message.get("limit", 20)
                alerts = alert_engine.get_alert_history(patient_id, limit)
                await websocket.send_json(
                    {
                        "type": "alert_list",
                        "event": "latest_alerts",
                        "data": {"alerts": alerts},
                    }
                )

            elif message_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong", "timestamp": __import__("datetime").datetime.utcnow().isoformat()})

    except WebSocketDisconnect:
        manager.disconnect(websocket, patient_id)
        print(f"Client disconnected from patient {patient_id} alerts")

    except WebSocketException as e:
        manager.disconnect(websocket, patient_id)
        print(f"WebSocket exception: {e}")

    except Exception as e:
        manager.disconnect(websocket, patient_id)
        print(f"Unexpected error in WebSocket: {e}")

    finally:
        db.close()


@router.get("/api/alerts/patients/{patient_id}/history")
def get_alert_history(
    patient_id: int,
    requester_id: int = Query(...),
    requester_role: str = Query(default="clinician"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """
    Get historical alerts for a patient (HTTP fallback to WebSocket).

    Query Parameters:
    - requester_id: ID of requesting user
    - requester_role: User role
    - limit: Number of alerts to return (max 200)

    Returns:
    ```json
    {
        "patient_id": 1,
        "alert_count": 12,
        "alerts": [
            {
                "alert_id": "POLY-1-0",
                "severity": "HIGH",
                "category": "polypharmacy",
                "message": "...",
                "action": "...",
                "timestamp": "2026-09-13T12:30:00Z",
                "source_agent": "PolypharmacyRiskAgent",
                "acknowledged": false,
                "resolved": false
            }
        ]
    }
    ```
    """
    db = SessionLocal()

    try:
        orchestrator = HealthMemoryOrchestrator(db)

        # Verify access
        access_check = orchestrator._check_access_permission(
            patient_id, requester_id, requester_role
        )

        if not access_check:
            return {"error": "ACCESS_DENIED", "message": "Consent not verified"}

        # Create alert engine to get history
        alert_engine = RealTimeAlertEngine(db, orchestrator)
        alerts = alert_engine.get_alert_history(patient_id, limit)

        return {
            "patient_id": patient_id,
            "alert_count": len(alerts),
            "alerts": alerts,
            "retrieved_at": __import__("datetime").datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {"error": "RETRIEVAL_FAILED", "message": str(e)}

    finally:
        db.close()


@router.post("/api/alerts/patients/{patient_id}/acknowledge/{alert_id}")
def acknowledge_alert(
    patient_id: int,
    alert_id: str,
    requester_id: int = Query(...),
    requester_role: str = Query(default="clinician"),
):
    """
    Mark an alert as acknowledged by clinician.

    Returns:
    ```json
    {
        "alert_id": "POLY-1-0",
        "acknowledged": true,
        "timestamp": "2026-09-13T12:30:00Z"
    }
    ```
    """
    db = SessionLocal()

    try:
        orchestrator = HealthMemoryOrchestrator(db)

        # Verify access
        access_check = orchestrator._check_access_permission(
            patient_id, requester_id, requester_role
        )

        if not access_check:
            return {"error": "ACCESS_DENIED"}

        alert_engine = RealTimeAlertEngine(db, orchestrator)
        success = alert_engine.acknowledge_alert(alert_id)

        if success:
            # Broadcast to all connected clients
            import asyncio
            asyncio.create_task(
                manager.broadcast_to_patient(
                    patient_id,
                    {
                        "type": "alert",
                        "event": "alert_acknowledged",
                        "data": {"alert_id": alert_id},
                    },
                )
            )

        return {
            "alert_id": alert_id,
            "acknowledged": success,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {"error": "ACKNOWLEDGE_FAILED", "message": str(e)}

    finally:
        db.close()


@router.post("/api/alerts/patients/{patient_id}/resolve/{alert_id}")
def resolve_alert(
    patient_id: int,
    alert_id: str,
    requester_id: int = Query(...),
    requester_role: str = Query(default="clinician"),
):
    """
    Mark an alert as resolved.

    Returns:
    ```json
    {
        "alert_id": "POLY-1-0",
        "resolved": true,
        "timestamp": "2026-09-13T12:30:00Z"
    }
    ```
    """
    db = SessionLocal()

    try:
        orchestrator = HealthMemoryOrchestrator(db)

        # Verify access
        access_check = orchestrator._check_access_permission(
            patient_id, requester_id, requester_role
        )

        if not access_check:
            return {"error": "ACCESS_DENIED"}

        alert_engine = RealTimeAlertEngine(db, orchestrator)
        success = alert_engine.resolve_alert(alert_id)

        if success:
            # Broadcast to all connected clients
            import asyncio
            asyncio.create_task(
                manager.broadcast_to_patient(
                    patient_id,
                    {
                        "type": "alert",
                        "event": "alert_resolved",
                        "data": {"alert_id": alert_id},
                    },
                )
            )

        return {
            "alert_id": alert_id,
            "resolved": success,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {"error": "RESOLVE_FAILED", "message": str(e)}

    finally:
        db.close()
