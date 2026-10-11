# Decentralized Campus Resource Booking System

A decentralized, fault-tolerant campus resource booking system designed for Distributed Systems.

## Project Phases
- [x] **Phase 1**: Architecture Foundation & API Gateway (`docs/phase-1.md`)
- [x] **Phase 2**: Distributed Data Layer & Department Resource Nodes (`docs/phase-2.md`)
- [x] **Phase 3**: gRPC / RPC Inter-Node Communication (`docs/phase-3.md`)
- [x] **Phase 4**: Distributed Synchronization & Mutual Exclusion (`docs/phase-4.md`)
- [x] **Phase 5**: Fault Detection, Failure Handling & Node Recovery (`docs/phase-5.md`)

---

## Final System Architecture

```text
                         React Frontend
                         localhost:5173
                               |
                               v
                    +----------------------+
                    |    API Gateway       |
                    |      :8000           |
                    +----------+-----------+
                               |
             +-----------------+-----------------+
             |                 |                 |
             v                 v                 v
       +-----------+     +-----------+     +-----------+
       | CSE Node  |     | IT Node   |     | E&TC Node |
       | HTTP 50151|     | HTTP 50152|     | HTTP 50153|
       | gRPC 50051|     | gRPC 50052|     | gRPC 50053|
       | cse.db    |     | it.db     |     | entc.db   |
       +-----------+     +-----------+     +-----------+
             \                 |                 /
              \________________|________________/
                       gRPC Communication
                               |
                     Fault Monitoring Loop
```

---

## FINAL PROJECT RUN

### 1. First-time Setup
```powershell
# Create & Activate Virtual Environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Backend Dependencies
pip install -r backend/requirements.txt

# Install Frontend Dependencies
cd frontend
npm install
cd ..
```

### 2. Start Complete System
Run the PowerShell project launcher script:
```powershell
.\scripts\run_project.ps1
```

### 3. Check System Health
Run the health check script to verify all services:
```powershell
.\scripts\check_project.ps1
```

### 4. Stop All System Services
Run the stop script to terminate all project processes cleanly:
```powershell
.\scripts\stop_project.ps1
```

---

## Configured Ports & Services
- **API Gateway**: `http://127.0.0.1:8000`
- **CSE Department Node**: HTTP `http://127.0.0.1:50151` / gRPC `50051`
- **IT Department Node**: HTTP `http://127.0.0.1:50152` / gRPC `50052`
- **E&TC Department Node**: HTTP `http://127.0.0.1:50153` / gRPC `50053`
- **React Frontend**: `http://localhost:5173`

## Accessing the Web Application from Another Device

The frontend and API Gateway can be reached from another device on the same
network. Start the system from PowerShell with the gateway listening on all
interfaces and add the browser's origin to the gateway's CORS allowlist:

```powershell
$env:GATEWAY_HOST = "0.0.0.0"
$env:FRONTEND_ORIGINS = "http://<HOST-LAN-IP>:5173"
.\scripts\run_project.ps1
```

Replace `<HOST-LAN-IP>` with the IP address of the computer running the project
(for example, `192.168.1.20`). Open `http://<HOST-LAN-IP>:5173` on the other
device. The frontend sends API requests to port `8000` on the same host. The
department services and their synchronization logic remain unchanged.

---

## Automated Testing

Run full automated test suite (39 tests across 8 test modules):
```powershell
python -m pytest backend/tests -v
```

---

## Documentation Links
- [Phase 1 Technical Architecture](docs/phase-1.md)
- [Phase 2 Technical Architecture](docs/phase-2.md)
- [Phase 3 Technical Architecture](docs/phase-3.md)
- [Phase 4 Technical Architecture](docs/phase-4.md)
- [Phase 5 Technical Architecture](docs/phase-5.md)
