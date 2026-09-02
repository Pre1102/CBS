# Decentralized Campus Resource Booking System - Final Summary

## Overview
A **Distributed Systems project** implementing a decentralized, fault-tolerant campus resource booking system across 5 phases. Each academic department operates as an independent node in a distributed network with automatic fault detection and recovery.

---

## System Architecture

```
                    React Frontend
                   localhost:5173
                         |
                         v
                  +---------------+
                  |  API Gateway  |
                  |    :8000      |
                  +-------+-------+
                          |
        ┌─────────────────┼─────────────────┐
        |                 |                 |
        v                 v                 v
    ┌────────┐        ┌────────┐        ┌────────┐
    | CSE    |        | IT     |        | E&TC   |
    | Node   |        | Node   |        | Node   |
    |:50151  |        |:50152  |        |:50153  |
    |:50051  |        |:50052  |        |:50053  |
    |gRPC    |        |gRPC    |        |gRPC    |
    +────────+        +────────+        +────────+
        |                 |                 |
    cse.db            it.db            entc.db
        |                 |                 |
        └─────────────────┼─────────────────┘
          gRPC Communication
                 |
        Fault Monitoring Loop
```

---

## Project Phases (All Complete ✅)

| Phase | Title | Key Features | Status |
|-------|-------|--------------|--------|
| **Phase 1** | Architecture Foundation & API Gateway | REST API, Department Nodes, HTTP Health Checks | ✅ |
| **Phase 2** | Distributed Data Layer & Resources | SQLite Databases, Resource Management, REST CRUD Operations | ✅ |
| **Phase 3** | gRPC Inter-Node Communication | Protocol Buffers, gRPC Services, Node-to-Node Coordination | ✅ |
| **Phase 4** | Distributed Synchronization & Mutual Exclusion | Ricart–Agrawala Algorithm, Shared Resource Locking, Lamport Clocks | ✅ |
| **Phase 5** | Fault Detection, Failure Handling & Recovery | Health Monitoring, Node Status Tracking, Automatic Recovery | ✅ |

---

## Technology Stack

### Backend
- **Language**: Python 3.x
- **Framework**: FastAPI + Uvicorn
- **RPC**: gRPC + Protocol Buffers
- **Database**: SQLite (local per-node)
- **Distributed Algorithms**: Ricart–Agrawala, Lamport Clocks

### Frontend
- **Framework**: React 18.2
- **Build Tool**: Vite 5.0
- **HTTP Client**: Fetch API

### Supported Platforms
- Windows (PowerShell scripts)
- Linux/macOS (with bash adaptation)

---

## Running Services

All services are **currently running and operational**:

| Service | Protocol | URL | Status |
|---------|----------|-----|--------|
| **Frontend** | HTTP | http://localhost:5173 | ✅ Running |
| **API Gateway** | HTTP/REST | http://127.0.0.1:8000 | ✅ Running |
| **CSE Node** (HTTP) | HTTP/REST | http://127.0.0.1:50151 | ✅ Running |
| **CSE Node** (gRPC) | gRPC | 127.0.0.1:50051 | ✅ Running |
| **IT Node** (HTTP) | HTTP/REST | http://127.0.0.1:50152 | ✅ Running |
| **IT Node** (gRPC) | gRPC | 127.0.0.1:50052 | ✅ Running |
| **E&TC Node** (HTTP) | HTTP/REST | http://127.0.0.1:50153 | ✅ Running |
| **E&TC Node** (gRPC) | gRPC | 127.0.0.1:50053 | ✅ Running |

---

## Key Features Implemented

### ✅ Distributed Resource Management
- Each department node independently manages its own resource inventory
- Resources include seminar halls, labs, projectors, conference rooms
- Per-node SQLite database ensures data persistence

### ✅ Cross-Department Booking
- Nodes communicate via gRPC to query availability across departments
- Support for shared resources (e.g., SHARED-SEMINAR-HALL)
- Booking requests propagate through API Gateway to appropriate nodes

### ✅ Mutual Exclusion (Ricart–Agrawala Protocol)
- Prevents double-booking of shared resources
- Distributed voting mechanism ensures consistency
- Lamport Clocks for ordering of critical section requests
- Safety guarantee: Only one node can access shared resource at a time

### ✅ Fault Tolerance & Monitoring
- Decentralized health monitoring (no single point of failure)
- Each node runs background health checks every 5 seconds
- Node status: `ONLINE`, `OFFLINE`, `UNKNOWN`
- Failure threshold: 3 consecutive failed checks before marking `OFFLINE`
- Automatic recovery detection when node comes back online

### ✅ Data Persistence
- SQLite databases (`cse.db`, `it.db`, `entc.db`) stored locally
- Databases preserved across node restarts/crashes
- No data loss on node failure

### ✅ Interactive React Dashboard
- View resources across all departments
- Browse existing bookings
- Monitor node health status
- Simulate node failures for testing
- Real-time status updates via API polling

### ✅ Comprehensive Test Suite
- 39 automated tests across 8 test modules
- Tests cover: bookings, coordination, databases, gRPC, fault monitoring, health checks, gateway routing, resources
- Run tests with: `python -m pytest backend/tests -v`

---

## Core Algorithms

### 1. Ricart–Agrawala Mutual Exclusion
**Purpose**: Ensure only one node accesses shared resources at a time
- Request node sends requests to all peers with its Lamport clock value
- Peers vote: grant if not in critical section or have lower clock value
- Request node enters critical section only after receiving all votes
- Release broadcasts to all waiting peers

### 2. Lamport Clocks
**Purpose**: Establish logical ordering of events across distributed nodes
- Each node maintains a monotonically increasing clock
- On sending message: increment clock, attach to message
- On receiving message: update local clock to max(local, received) + 1
- Used for prioritizing mutual exclusion requests

### 3. Decentralized Health Monitoring
**Purpose**: Detect node failures without central coordinator
- Each node pings all peers every 5 seconds
- Tracks consecutive failures per peer
- After 3 failures, marks peer as `OFFLINE`
- On successful response, resets failure count to 0

---

## Project Structure

```
DS_FA_Campus_Booking_System/
├── backend/
│   ├── api_gateway/              # FastAPI Gateway (port 8000)
│   │   ├── main.py
│   │   └── routes/
│   │       ├── departments.py    # Department endpoints
│   │       ├── health.py         # Health check
│   │       └── simulation.py     # Demo endpoints
│   ├── department_nodes/
│   │   ├── common/               # Shared utilities
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── seed_data.py
│   │   ├── cse_node/             # CSE Department (port 50151)
│   │   │   ├── main.py
│   │   │   ├── database/
│   │   │   └── routes/
│   │   ├── it_node/              # IT Department (port 50152)
│   │   │   ├── main.py
│   │   │   ├── database/
│   │   │   └── routes/
│   │   └── entc_node/            # E&TC Department (port 50153)
│   │       ├── main.py
│   │       ├── database/
│   │       └── routes/
│   ├── grpc_communication/       # gRPC services
│   │   ├── server.py
│   │   ├── node_client.py
│   │   ├── lamport_clock.py
│   │   ├── coordination.py
│   │   └── proto/
│   │       └── campus_resource.proto
│   ├── fault_monitoring/         # Fault detection & recovery
│   │   ├── monitor.py
│   │   ├── config.py
│   │   └── routes.py
│   └── tests/                    # 39 automated tests
│       ├── test_bookings.py
│       ├── test_coordination.py
│       ├── test_fault_monitoring.py
│       ├── test_grpc.py
│       └── ...
├── frontend/                     # React + Vite
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   └── ConcurrentConflictDemo.jsx
│   │   └── services/
│   │       └── api.js
│   ├── package.json
│   └── vite.config.js
├── scripts/                      # PowerShell automation
│   ├── run_project.ps1          # Start all services
│   ├── stop_project.ps1         # Stop all services
│   ├── check_project.ps1        # Health check
│   └── reset_demo_data.ps1      # Reset databases
└── docs/
    ├── phase-1.md to phase-5.md (Detailed documentation)
    └── project-overview.md
```

---

## Quick Start Commands

### 1. First-Time Setup
```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

### 2. Start Complete System
```powershell
.\scripts\run_project.ps1
```

### 3. Run Tests
```powershell
python -m pytest backend/tests -v
```

### 4. Health Check
```powershell
.\scripts\check_project.ps1
```

### 5. Stop All Services
```powershell
.\scripts\stop_project.ps1
```

### 6. Reset Demo Data
```powershell
.\scripts\reset_demo_data.ps1
```

---

## Fault Testing Scenario

### Step 1: Verify Normal Operation
- All 3 nodes display `ONLINE` status
- Can view resources from all departments
- Cross-department bookings work normally

### Step 2: Simulate Node Failure
- Terminate IT node: Press `Ctrl+C` in IT node terminal
- Other nodes detect failure (3 failed health checks = ~15 seconds)
- IT node transitions to `OFFLINE` on CSE and E&TC monitors

### Step 3: Verify Safety Mechanism
- Try booking shared resource while IT is `OFFLINE`
- CSE node safely blocks critical section entry
- User sees: "Cannot access shared resource - IT Node is OFFLINE"

### Step 4: Simulate Recovery
- Restart IT node: `python -m backend.department_nodes.it_node.main`
- Next health check succeeds
- IT transitions back to `ONLINE`
- Normal coordination resumes

### Step 5: Verify Data Preservation
- All bookings and resources remain intact in `it.db`
- No data loss after node restart

---

## API Endpoints

### Gateway Endpoints (Port 8000)
```
GET  /health                                    - System health
GET  /api/departments/{dept}/resources          - Get department resources
GET  /api/departments/{dept}/bookings           - Get department bookings
POST /api/departments/{dept}/bookings           - Create booking
GET  /api/departments/{dept}/fault-status       - Get node fault status
GET  /api/coordination/preset-resources         - Get shared resources
```

### Department Node Endpoints (Ports 50151, 50152, 50153)
```
GET  /health                                    - Node health
GET  /resources                                 - Local resources
GET  /bookings                                  - Local bookings
POST /bookings                                  - Create booking
POST /release-semaphore                         - Release mutual exclusion
GET  /coordination-status                       - Coordination state
```

---

## Problem Solved

### Traditional Centralized System Problems:
- ❌ Single point of failure
- ❌ Scalability bottlenecks
- ❌ Central server maintenance downtime
- ❌ No department autonomy

### Distributed System Solution:
- ✅ Fault tolerance — other nodes continue operating
- ✅ Scalability — new nodes can be added independently
- ✅ Autonomy — each department manages its resources
- ✅ Reliability — no single point of failure
- ✅ Consistency — mutual exclusion prevents data corruption

---

## Dependencies

### Backend (Python)
```
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
httpx>=0.24.0
requests>=2.31.0
pytest>=7.4.0
grpcio>=1.60.0
grpcio-tools>=1.60.0
```

### Frontend (Node.js)
```
react>=18.2.0
react-dom>=18.2.0
vite>=5.0.0
```

---

## Known Limitations & Future Improvements

### Current Limitations:
1. Peers are statically configured (no dynamic discovery)
2. Periodic polling introduces ~15 second detection delay
3. No distributed database replication (by design)
4. No Raft/Paxos consensus (beyond project scope)

### Future Improvements:
1. Implement dynamic peer discovery
2. Reduce detection latency with event-based notifications
3. Add distributed database replication
4. Implement Raft for improved fault tolerance
5. Add authentication and authorization
6. Implement message queuing for async operations

---

## Documentation

Detailed phase-by-phase documentation available in `docs/` folder:
- `phase-1.md` - Architecture & API Gateway
- `phase-2.md` - Data Layer & Resources
- `phase-3.md` - gRPC Communication
- `phase-4.md` - Mutual Exclusion & Synchronization
- `phase-5.md` - Fault Detection & Recovery
- `project-overview.md` - Complete system overview

---

## Status Summary

✅ **All 5 Phases Complete**
✅ **All Services Running**
✅ **All Tests Passing (39/39)**
✅ **Database Persistence Working**
✅ **Fault Tolerance Operational**
✅ **Frontend UI Functional**

**System is production-ready for demonstration and evaluation.**
