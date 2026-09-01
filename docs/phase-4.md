# Phase 4 — Distributed Synchronization and Mutual Exclusion

## 1. Objective
Phase 4 implements **distributed synchronization and mutual exclusion** for shared campus resources (`SHARED-SEMINAR-HALL`) across the decentralized department nodes (`CSE`, `IT`, `E&TC`) using **Lamport Logical Clocks** and a simplified **Ricart–Agrawala algorithm** operating over the existing gRPC communication layer.

Key Phase 4 features:
1. Thread-safe **Lamport Logical Clock** implementation (`backend/grpc_communication/lamport_clock.py`).
2. Deterministic request priority ordering: `(timestamp, requester_node)` tuple.
3. Peer-to-peer distributed mutual exclusion coordinator (`backend/grpc_communication/coordination.py`).
4. Extended Protocol Buffer schema (`campus_resource.proto`) with `RequestResourceAccess` and `ReleaseResourceAccess` RPCs.
5. gRPC server and client integration for peer permission requests and deferred queues.
6. HTTP coordination routes (`/coordination/request`, `/coordination/release`, `/coordination/status`) on all department nodes and forwarded by API Gateway.
7. Interactive React dashboard synchronization controls and live status cards.
8. Comprehensive automated test suite (`backend/tests/test_coordination.py`).

---

## 2. Peer-to-Peer Coordination Architecture

```text
                           FRONTEND (React)
                                 |
                                 | HTTP GET/POST (:8000)
                                 v
                         +---------------+
                         | FastAPI       |
                         | API Gateway   |
                         | :8000         |
                         +-------+-------+
                                 |
           ┌─────────────────────┼─────────────────────┐
           | HTTP                | HTTP                | HTTP
           v                     v                     v
    +--------------+      +--------------+      +--------------+
    | CSE Node     |      | IT Node      |      | E&TC Node    |
    | HTTP :50151  |      | HTTP :50152  |      | HTTP :50153  |
    | gRPC :50051  |      | gRPC :50052  |      | gRPC :50053  |
    +-------+------+      +-------+------+      +-------+------+
            |                     |                     |
            |<====== gRPC =======>|<====== gRPC =======>|
            |                     |                     |
            +<====================+====================>+
                        Ricart–Agrawala RPCs
```

> [!IMPORTANT]
> **No Central Lock Manager**:
> The API Gateway acts solely as an HTTP request proxy. Department nodes coordinate directly with each other via gRPC to acquire mutual exclusion for shared resources.

---

## 3. Lamport Logical Clock Rules

The Lamport Logical Clock ensures event ordering across independent distributed nodes without relying on physical system clocks:

1. **Local Event / Pre-Send Rule**:
   Before initiating a request, the node increments its logical clock:
   $$\text{clock} = \text{clock} + 1$$
2. **Receive Rule**:
   Upon receiving an RPC request with remote timestamp $T_{\text{remote}}$, the node updates its logical clock:
   $$\text{clock} = \max(\text{clock}, T_{\text{remote}}) + 1$$

---

## 4. Ricart–Agrawala Algorithm & Priority Ordering

### Request Priority Tuple
When a node requests access to `SHARED-SEMINAR-HALL`, it broadcasts its request timestamp $T$ along with its node name $N$:
$$\text{Priority} = (T, N)$$

For example: `(10, "CSE")` has higher priority than `(10, "IT")` because `"CSE" < "IT"` lexicographically.

### State Machine & Transitions

```text
       +------------------------------------+
       |                IDLE                |
       +-----------------+------------------+
                         |
           request_access() broadcast
                         v
       +------------------------------------+
       |             REQUESTING             |
       +-----------------+------------------+
                         |
           all peer permissions granted
                         v
       +------------------------------------+
       |        IN_CRITICAL_SECTION         |
       +-----------------+------------------+
                         |
           release_access() & notify deferred
                         v
       +------------------------------------+
       |                IDLE                |
       +------------------------------------+
```

### Protocol Steps:
1. **Requesting Access**:
   - Node sets state to `REQUESTING`, increments clock to $T$, and broadcasts `RequestResourceAccess` gRPC RPC to all peer department nodes.
2. **Handling Incoming Peer Request**:
   - Node updates its Lamport clock using incoming $T_{\text{remote}}$.
   - If local node is `REQUESTING` or `IN_CRITICAL_SECTION` for the same resource AND local request has higher priority $(T_{\text{local}}, N_{\text{local}}) < (T_{\text{remote}}, N_{\text{remote}})$, the incoming request is **deferred**.
   - Otherwise, the node returns `granted = true`.
3. **Critical Section Entry**:
   - Node transitions to `IN_CRITICAL_SECTION` only after receiving permission from **all** online peer nodes.
4. **Releasing Access**:
   - Node transitions to `IDLE` and sends permission responses to all queued deferred requests.

---

## 5. Network & Coordination API Endpoints

| Node / Service | Method | Route | Description |
| :--- | :--- | :--- | :--- |
| **Department Node** | `POST` | `/coordination/request` | Triggers Ricart-Agrawala request broadcast for `SHARED-SEMINAR-HALL` |
| **Department Node** | `POST` | `/coordination/release` | Releases critical section and notifies deferred peer requests |
| **Department Node** | `GET` | `/coordination/status` | Returns node state, Lamport clock, and deferred queue status |
| **API Gateway** | `POST` | `/api/departments/{dept}/coordination/request` | Gateway proxy forwarding request to target department node |
| **API Gateway** | `POST` | `/api/departments/{dept}/coordination/release` | Gateway proxy forwarding release to target department node |
| **API Gateway** | `GET` | `/api/departments/{dept}/coordination/status` | Gateway proxy forwarding status check to target department node |

---

## 6. Manual Demonstration Procedure

1. **Start System Nodes**:
   - Start Gateway (`:8000`), CSE (`HTTP :50151 / gRPC :50051`), IT (`HTTP :50152 / gRPC :50052`), and E&TC (`HTTP :50153 / gRPC :50053`).
2. **Trigger Concurrent Requests**:
   - In React dashboard (or via cURL), click **Request Access** on CSE Node -> state changes to `REQUESTING`, collects peer permissions, transitions to `IN_CRITICAL_SECTION`.
   - While CSE is `IN_CRITICAL_SECTION`, click **Request Access** on IT Node -> IT enters `REQUESTING`, broadcasts gRPC request, CSE defers IT's request (`IT` appears in CSE's deferred queue).
3. **Trigger Release**:
   - Click **Release Access** on CSE Node -> CSE transitions to `IDLE`, notifies IT, IT receives permission and transitions to `IN_CRITICAL_SECTION`.

---

## 7. Current System Limitations
1. **Basic Timeout & Failure Isolation**:
   - If a peer node is offline during `RequestResourceAccess`, the calling node catches gRPC connection timeout, records the failure, and prevents unsafe critical section entry.
2. **Scope Boundaries**:
   - Phase 4 does **not** implement automated consensus algorithms (Raft/Paxos), leader election, dynamic peer discovery, or message queues (RabbitMQ). These will be addressed in subsequent phases.
