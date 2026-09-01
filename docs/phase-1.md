# Phase 1 — Backend-First Project Foundation

## 1. Objective
The primary objective of Phase 1 is to establish a solid, clean, and easily explainable **Python backend foundation** for the Decentralized Campus Resource Booking System (FA-1 evaluation).

Phase 1 delivers:
1. A FastAPI API Gateway operating on port `8000`.
2. Three independent department service nodes (`CSE`, `IT`, `E&TC`) operating on ports `50051`, `50052`, and `50053`.
3. Centralized environment configuration.
4. Automated unit tests with `pytest`.
5. A minimal React + Vite frontend that validates backend connectivity.

---

## 2. High-Level Architecture (Phase 1 Foundation)

```text
+---------------------------------------+
|            React Frontend             |
|         (http://localhost:5173)       |
+---------------------------------------+
                    |
                    | HTTP GET /api/health
                    v
+---------------------------------------+
|         Python FastAPI Gateway        |
|         (http://127.0.0.1:8000)       |
+---------------------------------------+
        |               |               |
        | HTTP          | HTTP          | HTTP
        v               v               v
+---------------+---------------+---------------+
|   CSE Node    |    IT Node    |   E&TC Node   |
| (Port 50051)  | (Port 50052)  | (Port 50053)  |
+---------------+---------------+---------------+
```

*Note: In Phase 1, basic HTTP endpoints prove process independence. Advanced inter-node communication (gRPC) will be added in Phase 3.*

---

## 3. Folder Structure Explanation

```text
campus-resource-booking/
│
├── backend/                             # Core Python Backend
│   ├── api_gateway/                     # Gateway entry point & routes
│   │   ├── main.py                      # FastAPI Gateway app definition & CORS
│   │   ├── routes/
│   │   │   └── health.py                # Gateway GET /api/health route
│   │   └── __init__.py
│   │
│   ├── department_nodes/                # Independent Department Nodes
│   │   ├── common/                      # Shared configurations
│   │   │   ├── config.py                # Host & Port environment variables
│   │   │   └── __init__.py
│   │   ├── cse_node/                    # Computer Science Node (Port 50051)
│   │   │   ├── main.py
│   │   │   └── __init__.py
│   │   ├── it_node/                     # Information Technology Node (Port 50052)
│   │   │   ├── main.py
│   │   │   └── __init__.py
│   │   └── entc_node/                   # Electronics & Telecom Node (Port 50053)
│   │       ├── main.py
│   │       └── __init__.py
│   │
│   ├── grpc_communication/              # Reserved for Phase 3 gRPC proto files
│   │   └── README.md
│   ├── message_communication/           # Reserved for Phase 4 RabbitMQ modules
│   │   └── README.md
│   ├── realtime_communication/          # Reserved for Phase 4 WebSocket handlers
│   │   └── README.md
│   ├── fault_monitoring/                # Reserved for Phase 5 Heartbeat services
│   │   └── README.md
│   ├── tests/                           # Pytest automated test suite
│   │   ├── test_health.py
│   │   └── __init__.py
│   ├── requirements.txt                 # Phase 1 Python package requirements
│   └── __init__.py
│
├── frontend/                            # React + Vite Minimal Frontend
│   ├── src/
│   │   ├── components/                  # UI components
│   │   ├── pages/                       # Page layouts
│   │   ├── services/
│   │   │   └── api.js                   # Fetch call to Gateway health endpoint
│   │   ├── styles/
│   │   │   └── global.css               # Clean minimal CSS stylesheet
│   │   ├── App.jsx                      # Main application UI & status card
│   │   └── main.jsx                     # React DOM entry point
│   ├── public/
│   ├── package.json                     # Frontend dependencies
│   ├── vite.config.js                   # Vite dev server configuration
│   └── .env.example                     # Frontend environment template
│
├── docs/                                # Technical & Viva Documentation
│   ├── project-overview.md              # System problem statement & roadmap
│   ├── phase-1.md                       # Phase 1 technical details & guide
│   └── phase-1-viva.md                  # Viva Q&A preparation guide
│
├── scripts/                             # Reserved for operational automation
│   └── README.md
│
├── .env.example                         # Root environment template
├── .gitignore                           # Git ignore rules
└── README.md                            # Comprehensive project README
```

---

## 4. Backend Implementation Details

### FastAPI & Uvicorn
- **FastAPI**: Used for its speed, automatic OpenAPI documentation, and minimal boilerplate.
- **Uvicorn**: An ASGI web server used to run the FastAPI application instances.

### CORS Configuration
Cross-Origin Resource Sharing (CORS) is enabled on the Gateway (`backend/api_gateway/main.py`) to allow browser requests originating from the Vite frontend server (`http://localhost:5173`). Wildcard `*` origins are avoided for security best practice.

---

## 5. Frontend Implementation Details

### React + Vite
- Vite provides fast local development and lightweight builds.
- The UI is designed to be minimal, clean, and restrained (no neon, no glowing effects, no complex animations).

### Status Checking
- `src/services/api.js` executes an asynchronous `fetch()` request to `http://127.0.0.1:8000/api/health`.
- The `App.jsx` component displays standard status indicators (`Checking...`, `ONLINE`, or `OFFLINE`).

---

## 6. Execution & Running Instructions

### Step 1: Install Backend Dependencies
```bash
cd campus-resource-booking/backend
pip install -r requirements.txt
```

### Step 2: Run API Gateway (Terminal 1)
```bash
python -m backend.api_gateway.main
# Or: uvicorn backend.api_gateway.main:app --host 127.0.0.1 --port 8000
```

### Step 3: Run Department Nodes (Terminals 2, 3, 4)
```bash
# Terminal 2 - CSE Node
python -m backend.department_nodes.cse_node.main

# Terminal 3 - IT Node
python -m backend.department_nodes.it_node.main

# Terminal 4 - E&TC Node
python -m backend.department_nodes.entc_node.main
```

### Step 4: Run Frontend Development Server (Terminal 5)
```bash
cd campus-resource-booking/frontend
npm install
npm run dev
```

---

## 7. Testing Instructions

Run backend unit tests from the `campus-resource-booking` root folder:
```bash
pytest backend/tests
```
Expected output: 2 passed tests (`test_get_root` and `test_get_health`).
