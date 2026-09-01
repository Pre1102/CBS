import time
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List
import httpx

try:
    from backend.fault_monitoring.config import (
        HEALTH_CHECK_INTERVAL,
        HEALTH_CHECK_TIMEOUT,
        FAILURE_THRESHOLD
    )
    from backend.department_nodes.common.config import (
        CSE_HTTP_HOST, CSE_HTTP_PORT,
        IT_HTTP_HOST, IT_HTTP_PORT,
        ENTC_HTTP_HOST, ENTC_HTTP_PORT
    )
except ImportError:
    from fault_monitoring.config import (
        HEALTH_CHECK_INTERVAL,
        HEALTH_CHECK_TIMEOUT,
        FAILURE_THRESHOLD
    )
    from department_nodes.common.config import (
        CSE_HTTP_HOST, CSE_HTTP_PORT,
        IT_HTTP_HOST, IT_HTTP_PORT,
        ENTC_HTTP_HOST, ENTC_HTTP_PORT
    )

logger = logging.getLogger(__name__)

ALL_NODES = ["CSE", "IT", "E&TC"]

PEER_HTTP_MAP = {
    "CSE": f"http://{CSE_HTTP_HOST}:{CSE_HTTP_PORT}",
    "IT": f"http://{IT_HTTP_HOST}:{IT_HTTP_PORT}",
    "E&TC": f"http://{ENTC_HTTP_HOST}:{ENTC_HTTP_PORT}",
    "ETC": f"http://{ENTC_HTTP_HOST}:{ENTC_HTTP_PORT}",
    "ENTC": f"http://{ENTC_HTTP_HOST}:{ENTC_HTTP_PORT}",
}

class NodeHealthMonitor:
    """
    Background health monitor that periodically pings peer department nodes
    to detect node availability, node failures, and node recoveries.
    """
    def __init__(self, node_name: str, check_interval: float = HEALTH_CHECK_INTERVAL, failure_threshold: int = FAILURE_THRESHOLD):
        self.node_name = node_name.strip().upper()
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread = None

        # Initialize peer status dictionary
        self.peers_status: Dict[str, Dict[str, Any]] = {}
        for peer in ALL_NODES:
            if peer != self.node_name:
                self.peers_status[peer] = {
                    "status": "UNKNOWN",
                    "failure_count": 0,
                    "last_success": None,
                    "last_failure": None
                }

    def get_peer_nodes(self) -> List[str]:
        """Returns list of peer node names excluding self."""
        return [node for node in ALL_NODES if node != self.node_name]

    def record_success(self, peer_name: str):
        """Records a successful heartbeat response for peer_name."""
        key = peer_name.strip().upper()
        if key in self.peers_status:
            with self._lock:
                peer_info = self.peers_status[key]
                peer_info["status"] = "ONLINE"
                peer_info["failure_count"] = 0
                peer_info["last_success"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def record_failure(self, peer_name: str):
        """Records a failed heartbeat for peer_name and updates OFFLINE status if threshold reached."""
        key = peer_name.strip().upper()
        if key in self.peers_status:
            with self._lock:
                peer_info = self.peers_status[key]
                peer_info["failure_count"] += 1
                peer_info["last_failure"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if peer_info["failure_count"] >= self.failure_threshold:
                    peer_info["status"] = "OFFLINE"

    def is_peer_online(self, peer_name: str) -> bool:
        """Returns True unless peer is explicitly marked OFFLINE."""
        key = peer_name.strip().upper()
        with self._lock:
            info = self.peers_status.get(key)
            if not info:
                return True
            return info["status"] != "OFFLINE"

    def check_single_peer(self, peer_name: str, timeout: float = HEALTH_CHECK_TIMEOUT) -> bool:
        """Performs a single HTTP GET /health check against target peer."""
        base_url = PEER_HTTP_MAP.get(peer_name.strip().upper())
        if not base_url:
            return False
        
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(f"{base_url}/health")
                if resp.status_code == 200:
                    self.record_success(peer_name)
                    return True
                else:
                    self.record_failure(peer_name)
                    return False
        except Exception:
            self.record_failure(peer_name)
            return False

    def _monitoring_loop(self):
        """Background thread loop that pings peer nodes periodically."""
        while not self._stop_event.is_set():
            for peer in self.get_peer_nodes():
                if self._stop_event.is_set():
                    break
                self.check_single_peer(peer)
            self._stop_event.wait(self.check_interval)

    def start(self):
        """Starts background monitoring thread."""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Stops background monitoring thread cleanly."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def get_status(self) -> Dict[str, Any]:
        """Returns current node fault-monitoring state."""
        with self._lock:
            # Deep copy status dict
            copied_peers = {
                peer: dict(info)
                for peer, info in self.peers_status.items()
            }
            return {
                "node": self.node_name,
                "status": "ONLINE",
                "peers": copied_peers
            }
