"""Fleet tracker for monitoring connected AI agents and devices."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


class AgentSession:
    def __init__(
        self,
        session_id: str,
        client_ip: str,
        user_agent: Optional[str] = None,
        device_name: Optional[str] = None,
    ):
        self.session_id = session_id
        self.client_ip = client_ip
        self.user_agent = user_agent or "Unknown Agent"
        self.device_name = device_name or "Remote Device"
        self.connected_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.requests_count = 0
        self.last_tool_called: Optional[str] = None

    def record_activity(self, tool_name: Optional[str] = None):
        self.last_activity = datetime.now(timezone.utc)
        self.requests_count += 1
        if tool_name:
            self.last_tool_called = tool_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "device_name": self.device_name,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "requests_count": self.requests_count,
            "last_tool_called": self.last_tool_called,
        }


class FleetTracker:
    def __init__(self):
        self._sessions: Dict[str, AgentSession] = {}

    def register(
        self,
        session_id: str,
        client_ip: str,
        user_agent: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> AgentSession:
        session = AgentSession(
            session_id=session_id,
            client_ip=client_ip,
            user_agent=user_agent,
            device_name=device_name,
        )
        self._sessions[session_id] = session
        return session

    def record_activity(self, session_id: str, tool_name: Optional[str] = None):
        if session_id in self._sessions:
            self._sessions[session_id].record_activity(tool_name)

    def unregister(self, session_id: str):
        self._sessions.pop(session_id, None)

    def list_active(self) -> List[Dict[str, Any]]:
        # Sort by most recently active
        sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.last_activity,
            reverse=True,
        )
        return [s.to_dict() for s in sessions]


fleet_tracker = FleetTracker()
