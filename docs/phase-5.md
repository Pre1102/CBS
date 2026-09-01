# Phase 5 — Fault Detection, Failure Handling, and Node Recovery

## 1. Objective
Phase 5 introduces **basic fault detection, failure handling, and node recovery** for the decentralized department nodes (`CSE`, `IT`, `E&TC`). 

Key Phase 5 features:
1. Decentralized `NodeHealthMonitor` (`backend/fault_monitoring/monitor.py`) running background health checks.
2. Clear Node Status Model: `ONLINE`, `OFFLINE`, `UNKNOWN`.
3. Consecutive failure threshold rule (`FAILURE_THRESHOLD = 3`) to prevent false-positive status flips.
4. Automatic recovery detection restoring recovered nodes to `ONLINE`.
5. Fault status endpoint (`GET /fault-status`) on nodes and proxied by API Gateway (`/api/departments/{dept}/fault-status`).
6. Mutual Exclusion Safety Guarantee: Safety over availability — nodes block critical section entry if a required peer is `OFFLINE` or unreachable.
7. Local Database Preservation: Node crashes/restarts preserve SQLite databases (`cse.db`, `it.db`, `entc.db`) without data loss.
8. Interactive React Dashboard for fault monitoring and failure demonstration.
9. Comprehensive automated test suite (`backend/tests/test_fault_monitoring.py`).

---

## 2. Fault Monitoring Architecture

```text
                         React Frontend
                              |
                              v
                       API Gateway :8000
                              |
          ┌───────────────────┼───────────────────┐
          |                   |                   |
          v                   v                   v
      CSE Node             IT Node             E&TC Node
      :50151               :50152               :50153
      :50051               :50052               :50053
          |                   |                   |
       cse.db               it.db               entc.db
          |                   |                   |
          └──────────── gRPC Coordination ───────┘
                              |
                    Fault Monitoring Loop
                              |
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
             CSE              IT              E&TC
              |               |               |
          ONLINE/OFFLINE  ONLINE/OFFLINE  ONLINE/OFFLINE
```

> [!NOTE]
> **Decentralized Peer Monitoring**:
> Each node runs its own instance of `NodeHealthMonitor` in a background thread. There is no central monitoring daemon or single point of failure.

---

## 3. Node Status Model & State Transitions

```text
                  +-------------------------+
                  |         UNKNOWN         |
                  +------------+------------+
                               |
               first successful check / response
                               v
                  +-------------------------+
                  |         ONLINE          |
                  +------------+------------+
                               |
                   3 consecutive failures
                               v
                  +-------------------------+
                  |         OFFLINE         |
                  +------------+------------+
                               |
                   successful health check
                               v
                  +-------------------------+
                  |         ONLINE          |
                  +-------------------------+
```

### State Definitions:
- **`UNKNOWN`**: Initial state before the local health monitor has checked the target peer node.
- **`ONLINE`**: The target node responded with HTTP `200 OK` to `/health` or handled gRPC requests successfully.
- **`OFFLINE`**: The target node failed `FAILURE_THRESHOLD` (3) consecutive health checks or gRPC RPCs.

---

## 4. Configuration Parameters

| Setting | Default Value | Description |
| :--- | :--- | :--- |
| `HEALTH_CHECK_INTERVAL` | `5.0` seconds | Interval between background peer ping loops |
| `HEALTH_CHECK_TIMEOUT` | `2.0` seconds | Maximum timeout allowed for HTTP `/health` response |
| `FAILURE_THRESHOLD` | `3` | Consecutive failures required before marking peer `OFFLINE` |

---

## 5. Interaction with Phase 4 Mutual Exclusion

> [!IMPORTANT]
> **Safety Over Availability**:
> During Ricart–Agrawala mutual exclusion requests (`SHARED-SEMINAR-HALL`), if a peer is marked `OFFLINE` or fails gRPC communication, the requesting node:
> 1. Records the peer as unreachable.
> 2. Does **NOT** assume permission was granted.
> 3. Does **NOT** enter `IN_CRITICAL_SECTION`.
> 4. Remains in `REQUESTING` state and informs the user.

This prevents race conditions and corrupted shared resource state during network partitions or node outages.

---

## 6. Manual Failure & Recovery Demonstration

### Step 1: Normal System Operation
- Start Gateway (`:8000`), CSE (`:50151`), IT (`:50152`), E&TC (`:50153`), and Frontend (`:5173`).
- All nodes display `ONLINE` status in the Fault Dashboard.

### Step 2: Simulate Node Failure
- Terminate IT node process in terminal (`Ctrl+C`).
- Observe remaining CSE and E&TC nodes count consecutive failures (1/3 -> 2/3 -> 3/3).
- After ~15 seconds, IT transitions to **`OFFLINE`** on CSE and E&TC monitors.

### Step 3: Verify Coordination Safety
- Click **Request Access** on CSE Node for `SHARED-SEMINAR-HALL`.
- CSE detects IT is `OFFLINE` -> safely blocks entering `IN_CRITICAL_SECTION` and alerts user.

### Step 4: Simulate Node Recovery
- Restart IT node process (`python -m backend.department_nodes.it_node.main`).
- On next health check cycle, CSE and E&TC monitors receive `200 OK`, reset failure count to `0`, and restore IT to **`ONLINE`**.

### Step 5: Data Preservation
- Verify local database `it.db` remains intact; all previously created resources and bookings are present.
- Re-run distributed synchronization request -> normal coordination resumes.

---

## 7. Known Limitations
1. Periodic polling introduces a small detection delay ($\sim \text{interval} \times \text{threshold}$).
2. Peers are statically configured in `config.py` (no dynamic broadcast discovery).
3. System prioritizes safety over availability (offline peer blocks shared resource entry).
4. No Raft/Paxos consensus or distributed database replication (by design per scope).
