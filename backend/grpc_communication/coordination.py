import threading
import logging
from typing import Dict, Any, List, Set, Tuple, Optional

try:
    from backend.grpc_communication.lamport_clock import LamportClock
    from backend.grpc_communication.node_client import send_resource_access_request
except ImportError:
    from grpc_communication.lamport_clock import LamportClock
    from grpc_communication.node_client import send_resource_access_request

logger = logging.getLogger(__name__)

ALL_DEPARTMENTS = ["CSE", "IT", "E&TC"]

class DistributedResourceCoordinator:
    """
    Implements a simplified Ricart-Agrawala Distributed Mutual Exclusion Algorithm
    using Lamport Logical Clocks for conflict-free access to shared campus resources.

    States:
      - IDLE: Node is not requesting or holding any shared resource.
      - REQUESTING: Node has broadcast access requests and is waiting for peer permissions.
      - IN_CRITICAL_SECTION: Node has received all peer permissions and holds access.
    """
    def __init__(self, node_name: str, initial_clock: int = 0, health_monitor=None):
        self.node_name = node_name.strip().upper()
        self.clock = LamportClock(initial_clock)
        self.health_monitor = health_monitor
        
        self.state = "IDLE"
        self.current_resource: Optional[str] = None
        self.request_timestamp: Optional[int] = None
        
        # Track peers that granted permission for current request
        self.received_replies: Set[str] = set()
        
        # Queue of incoming requests deferred because this node had higher priority
        # List of tuples: (requester_node, resource_id, timestamp)
        self.deferred_requests: List[Tuple[str, str, int]] = []
        
        self._lock = threading.Lock()

    def get_peer_nodes(self) -> List[str]:
        """Returns list of peer node names excluding self."""
        return [dept for dept in ALL_DEPARTMENTS if dept != self.node_name]

    def request_access(self, resource_id: str, timeout: float = 3.0) -> Tuple[bool, str]:
        """
        Initiates distributed mutual exclusion request for resource_id using Ricart-Agrawala protocol.
        1. Increments Lamport clock.
        2. Sets state to REQUESTING and records (timestamp, node_name).
        3. Sends gRPC RequestResourceAccess to all peer department nodes.
        4. Evaluates responses and enters IN_CRITICAL_SECTION if all permissions granted.
        """
        with self._lock:
            if self.state != "IDLE":
                return False, f"Node {self.node_name} is already in state '{self.state}' for resource '{self.current_resource}'"
            
            # Step 1: Increment Lamport clock
            req_ts = self.clock.increment()
            self.state = "REQUESTING"
            self.current_resource = resource_id
            self.request_timestamp = req_ts
            self.received_replies = set()

        peers = self.get_peer_nodes()
        granted_peers = []
        failed_peers = []

        # Step 2: Broadcast RequestResourceAccess to all peers
        for peer in peers:
            if self.health_monitor and not self.health_monitor.is_peer_online(peer):
                failed_peers.append((peer, f"Node {peer} is marked OFFLINE by local fault monitor"))
                continue

            res = send_resource_access_request(
                target_dept=peer,
                requester_node=self.node_name,
                resource_id=resource_id,
                timestamp=req_ts,
                timeout=timeout
            )
            if res.get("granted"):
                granted_peers.append(peer)
            else:
                if self.health_monitor and ("unreachable" in res.get("message", "").lower() or "error" in res.get("message", "").lower()):
                    self.health_monitor.record_failure(peer)
                failed_peers.append((peer, res.get("message", "Permission denied or deferred")))

        with self._lock:
            for p in granted_peers:
                self.received_replies.add(p)

            # Step 3: Check if all peers granted permission
            if len(self.received_replies) == len(peers):
                self.state = "IN_CRITICAL_SECTION"
                return True, f"Access granted for resource '{resource_id}'. State: IN_CRITICAL_SECTION"
            else:
                # If some peers deferred or failed, node remains in REQUESTING or reverts
                msg = f"Waiting for peer permissions. Granted: {list(self.received_replies)}, Failed/Deferred: {failed_peers}"
                return False, msg

    def handle_incoming_request(self, requester_node: str, resource_id: str, timestamp: int) -> Tuple[bool, str]:
        """
        Evaluates an incoming RequestResourceAccess RPC from a remote peer according to Ricart-Agrawala rules:
        - Updates local Lamport clock using incoming timestamp.
        - Defer request if local node is REQUESTING or IN_CRITICAL_SECTION for same resource AND local request has higher priority: (local_ts, local_node) < (remote_ts, remote_node).
        - Otherwise, grant permission immediately.
        """
        # Step 1: Update Lamport clock on receiving remote message
        self.clock.update(timestamp)

        with self._lock:
            has_priority = False
            if self.state in ["REQUESTING", "IN_CRITICAL_SECTION"] and self.current_resource == resource_id:
                local_priority = (self.request_timestamp, self.node_name)
                remote_priority = (timestamp, requester_node)
                if local_priority < remote_priority:
                    has_priority = True

            if has_priority:
                # Defer response until local node exits critical section
                self.deferred_requests.append((requester_node, resource_id, timestamp))
                return False, f"Request deferred by {self.node_name} (Local priority higher: {self.request_timestamp} < {timestamp})"
            else:
                return True, f"Permission granted by {self.node_name}"

    def release_access(self, resource_id: str) -> Tuple[bool, str]:
        """
        Releases critical section for resource_id:
        1. Sets state to IDLE.
        2. Clears current resource.
        3. Returns list of deferred requests that were pending permission.
        """
        with self._lock:
            if self.state != "IN_CRITICAL_SECTION" or self.current_resource != resource_id:
                return False, f"Node {self.node_name} is not in CRITICAL_SECTION for resource '{resource_id}' (Current state: {self.state})"

            self.state = "IDLE"
            self.current_resource = None
            self.request_timestamp = None
            self.received_replies = set()
            
            pending_deferred = list(self.deferred_requests)
            self.deferred_requests = []

        return True, f"Resource '{resource_id}' released by {self.node_name}. {len(pending_deferred)} deferred requests notified."

    def get_status(self) -> Dict[str, Any]:
        """Returns current coordination status and Lamport clock value."""
        with self._lock:
            return {
                "node": self.node_name,
                "state": self.state,
                "lamport_clock": self.clock.get_time(),
                "current_resource": self.current_resource,
                "request_timestamp": self.request_timestamp,
                "received_replies": list(self.received_replies),
                "deferred_requests": [
                    {"requester_node": req, "resource_id": r_id, "timestamp": ts}
                    for (req, r_id, ts) in self.deferred_requests
                ]
            }
