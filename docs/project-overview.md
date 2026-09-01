# Project Overview

## Project Title
**A Decentralized Campus Resource Booking System Using Distributed Synchronization and Fault-Tolerant Coordination**

---

## 1. Problem Statement
In educational institutions, campus resources such as seminar halls, computing laboratories, projectors, and conference rooms are shared across multiple academic departments (e.g., Computer Science, Information Technology, Electronics & Telecommunications).

Traditional resource management relies on a single centralized database or server. This model presents several operational challenges:
- **Single Point of Failure**: If the central server fails or undergoes maintenance, all department bookings across campus become unavailable.
- **Bottlenecks and Scalability Issues**: High concurrent booking requests during peak academic hours can congest a central server.
- **Lack of Autonomy**: Individual departments cannot manage their local resources independently when isolated from a central network.

---

## 2. Proposed Solution
This project proposes a **decentralized, distributed campus resource booking system**. Each major academic department operates as an independent node in a distributed network.

Key aspects of the system:
- **Department Autonomy**: Each department node manages its own local resource inventory and schedule.
- **Inter-Node Coordination**: Department nodes communicate directly with each other to query availability and reserve cross-department resources.
- **Fault Tolerance**: If one department node goes offline, the remaining nodes continue to function normally for their respective departments.

---

## 3. Why Distributed Systems?
A distributed system architecture is specifically chosen for this problem because:
1. **High Availability**: Department nodes continue processing requests independently even if network partitions occur.
2. **Concurrency & Synchronization**: Distributed synchronization protocols ensure that cross-department resource reservations remain consistent without double-booking.
3. **Scalability**: New department nodes can be added to the institution without modifying or disrupting existing department infrastructure.

---

## 4. Main System Components

### Frontend (Secondary Component)
- **React + Vite**: Web-based user interface enabling students and faculty to view campus resources and submit booking requests.

### Backend (Primary Component)
- **FastAPI Gateway**: Acts as the central client entry point, forwarding incoming frontend requests to appropriate department nodes.
- **CSE Department Node**: Independent service managing Computer Science & Engineering resources.
- **IT Department Node**: Independent service managing Information Technology resources.
- **E&TC Department Node**: Independent service managing Electronics & Telecommunication resources.

---

## 5. Implementation Roadmap Across Project Phases

| Component / Technology | Phase 1 (Current) | Future Phases |
| :--- | :--- | :--- |
| **FastAPI Backend Gateway** | Implemented (`/api/health`) | Request routing & payload validation |
| **Department Service Nodes** | Implemented (`CSE`, `IT`, `E&TC` HTTP health) | gRPC services & local persistence |
| **React UI** | Implemented (Basic status indicator) | Full booking dashboard & interactive forms |
| **Database (SQLite)** | Not Implemented | Local per-node SQLite databases |
| **gRPC Communication** | Not Implemented | Phase 3: Inter-node gRPC calls & Proto files |
| **RabbitMQ Messaging** | Not Implemented | Phase 4: Event-driven broadcast messaging |
| **WebSocket Realtime Updates** | Not Implemented | Phase 4: Real-time UI status push |
| **Heartbeat & Fault Recovery** | Not Implemented | Phase 5: Automatic dead-node detection |
