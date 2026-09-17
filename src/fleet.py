"""Fleet tracker for monitoring connected AI agents and devices."""

from dataclasses import dataclass, field
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
        self.status: str = "online"

    def record_activity(self, tool_name: Optional[str] = None):
        self.last_activity = datetime.now(timezone.utc)
        self.requests_count += 1
        self.status = "online"
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
            "status": self.status,
        }


@dataclass
class FleetNode:
    node_id: str
    hostname: str
    ip: str
    os_name: str
    username: str = ""
    agents: List[Dict[str, Any]] = field(default_factory=list)
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "online"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "hostname": self.hostname,
            "ip": self.ip,
            "os_name": self.os_name,
            "username": self.username,
            "agents": self.agents,
            "registered_at": self.registered_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "status": self.status,
            "detected_count": sum(1 for a in self.agents if a.get("detected")),
            "configured_count": sum(1 for a in self.agents if a.get("configured")),
        }


class FleetTracker:
    def __init__(self):
        self._sessions: Dict[str, AgentSession] = {}
        self._nodes: Dict[str, FleetNode] = {}

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

        # If a known workstation node exists for this IP, update its last_seen
        matched_node = next((n for n in self._nodes.values() if n.ip == client_ip), None)
        if matched_node:
            matched_node.last_seen = datetime.now(timezone.utc)
            matched_node.status = "online"
        elif client_ip and client_ip not in ("unknown", "127.0.0.1", "::1"):
            self.register_node(
                hostname=f"Workstation ({client_ip})",
                ip=client_ip,
                os_name="Remote Agent",
                username=user_agent or "",
            )
        return session

    def register_node(
        self,
        hostname: str,
        ip: str,
        os_name: str,
        username: str = "",
        agents: Optional[List[Dict[str, Any]]] = None,
    ) -> FleetNode:
        node_id = hostname
        matched = self._nodes.get(node_id)
        if not matched:
            # Check if there was an unnamed placeholder for this IP
            for k, n in list(self._nodes.items()):
                if n.ip == ip and (not n.agents or n.hostname.startswith("Workstation (")):
                    self._nodes.pop(k, None)
                    matched = n
                    break

        if matched:
            matched.node_id = node_id
            matched.hostname = hostname
            matched.ip = ip
            matched.os_name = os_name
            if username:
                matched.username = username
            if agents:
                matched.agents = agents
            matched.last_seen = datetime.now(timezone.utc)
            matched.status = "online"
            self._nodes[node_id] = matched
            return matched
        else:
            node = FleetNode(
                node_id=node_id,
                hostname=hostname,
                ip=ip,
                os_name=os_name,
                username=username,
                agents=agents or [],
            )
            self._nodes[node_id] = node
            return node

    def record_activity(self, session_id: str, tool_name: Optional[str] = None):
        if session_id in self._sessions:
            self._sessions[session_id].record_activity(tool_name)

    def unregister(self, session_id: str):
        # Instead of immediately deleting, mark session as idle
        if session_id in self._sessions:
            self._sessions[session_id].status = "idle"
            # Limit historical session count
            if len(self._sessions) > 20:
                oldest = min(self._sessions.keys(), key=lambda k: self._sessions[k].last_activity)
                self._sessions.pop(oldest, None)

    def list_active(self, max_idle_seconds: int = 1800) -> List[Dict[str, Any]]:
        # Sort by most recently active, excluding stale sessions older than 30 mins
        now = datetime.now(timezone.utc)
        active = [
            s for s in self._sessions.values()
            if (now - s.last_activity).total_seconds() <= max_idle_seconds
        ]
        return [s.to_dict() for s in sorted(active, key=lambda s: s.last_activity, reverse=True)]

    def list_nodes(self) -> List[Dict[str, Any]]:
        nodes = [
            n for n in self._nodes.values()
            if n.agents or not n.hostname.startswith("Workstation (")
        ]
        nodes.sort(key=lambda n: n.last_seen, reverse=True)
        return [n.to_dict() for n in nodes]


fleet_tracker = FleetTracker()
