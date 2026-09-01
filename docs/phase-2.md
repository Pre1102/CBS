# Phase 2 — Distributed Data Layer and Department Resource Nodes

## 1. Objective
Phase 2 introduces a **decentralized data layer** to the Campus Resource Booking System. Each department node (`CSE`, `IT`, `E&TC`) is equipped with its own independent SQLite database (`cse.db`, `it.db`, `entc.db`) and localized REST APIs for resource inventory management and booking processing.

Key Phase 2 features:
1. Independent SQLite local database per department node.
2. `resources` table for local inventory management.
3. `bookings` table for local schedule reservations.
4. Department node resource CRUD endpoints (`/resources`).
5. Department node booking CRUD endpoints (`/bookings`).
6. Local booking conflict validation (`has_booking_conflict`).
7. Booking cancellation workflow (`status = CANCELLED`).
8. Department-level data isolation.
9. Gateway forwarding to department node ports (`/api/departments/{dept}/...`).
10. Department status monitoring endpoint (`/api/departments/status`).

---

## 2. Distributed Database Architecture

```text
                               FRONTEND
                                  |
                                  | HTTP GET/POST
                                  v
                          +---------------+
                          | FastAPI       |
                          | API Gateway   |
                          | :8000         |
                          +-------+-------+
                                  |
                      HTTP Forwarding (Phase 2)
                                  |
        +-------------------------+-------------------------+
        |                         |                         |
        v                         v                         v
  +-----------+             +-----------+             +-----------+
  | CSE Node  |             | IT Node   |             | E&TC Node |
  | :50051    |             | :50052    |             | :50053    |
  +-----+-----+             +-----+-----+             +-----+-----+
        |                         |                         |
        v                         v                         v
     cse.db                    it.db                     entc.db
```

### Why Independent Databases?
In a truly distributed system, individual department nodes must maintain operational autonomy. If a central database were used, the database would become a single point of failure and single point of congestion. Giving each department node its own SQLite file simulates real-world distributed node persistence.

---

## 3. Database Schema

### RESOURCES TABLE (`resources`)
Stores equipment, rooms, labs, and halls owned by a specific department.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique resource ID within node |
| `name` | TEXT | NOT NULL | Resource title (e.g. CSE Computer Lab 1) |
| `resource_type` | TEXT | NOT NULL | Category (Laboratory, Classroom, Seminar Hall, Equipment) |
| `location` | TEXT | NOT NULL | Building block and floor location |
| `department` | TEXT | NOT NULL | Owning department code (CSE, IT, E&TC) |
| `capacity` | INTEGER | NOT NULL | Seating or items capacity |
| `is_available` | INTEGER | DEFAULT 1 | Availability status (1 = Available, 0 = Unavailable) |

### BOOKINGS TABLE (`bookings`)
Stores local reservation records for resources.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique booking ID within node |
| `resource_id` | INTEGER | NOT NULL, FOREIGN KEY | Target resource ID in local DB |
| `booked_by` | INTEGER / TEXT | NOT NULL | Name or ID of person/group booking |
| `department` | TEXT | NOT NULL | Department making the booking |
| `booking_date` | TEXT | NOT NULL | Reservation date (`YYYY-MM-DD`) |
| `start_time` | TEXT | NOT NULL | Start time (`HH:MM`, e.g. `10:00`) |
| `end_time` | TEXT | NOT NULL | End time (`HH:MM`, e.g. `12:00`) |
| `purpose` | TEXT | NOT NULL | Description or course title |
| `status` | TEXT | DEFAULT 'CONFIRMED' | `CONFIRMED` or `CANCELLED` |
| `created_at` | TEXT | NOT NULL | ISO timestamp of booking creation |

---

## 4. Local Conflict Detection Logic

Before creating a booking, the target department node executes local validation inside `backend/department_nodes/common/handlers.py`:

### Validation Steps:
1. **Time Range Check**: Ensures `start_time < end_time`.
2. **Resource Existence Check**: Ensures `resource_id` exists in the node's local `resources` table.
3. **Department Ownership Check**: Ensures the resource belongs to the target department node.
4. **Overlap Conflict Check (`has_booking_conflict`)**:
   Query active bookings for the same resource on the requested date:
   ```sql
   SELECT start_time, end_time FROM bookings
   WHERE resource_id = ? AND booking_date = ? AND status != 'CANCELLED';
   ```
   An overlap occurs if:
   ```text
   new_start < existing_end AND new_end > existing_start
   ```
   If an overlap is detected, the request is rejected with **HTTP 400 Bad Request**.

> [!IMPORTANT]
> **Local Conflict Check vs. Distributed Mutual Exclusion**:
> Phase 2 performs **local validation** within a single node's SQLite database. It prevents double-booking resources managed by that specific node.
> It is **NOT** a distributed mutual exclusion protocol (such as Lamport's algorithm or Ricart-Agrawala). Inter-node synchronization across department nodes will be implemented in later phases using gRPC and message queues.

---

## 5. Gateway Forwarding Responsibilities

The API Gateway (`backend/api_gateway/main.py`):
- Receives frontend requests at `/api/departments/{department}/...`
- Maps `{department}` to target node base URL:
  - `cse` -> `http://127.0.0.1:50051`
  - `it` -> `http://127.0.0.1:50052`
  - `entc` -> `http://127.0.0.1:50053`
- Forwards HTTP request asynchronously using `httpx`.
- Returns the department node's JSON response or **HTTP 503 Service Unavailable** if the node is offline.

---

## 6. What is Intentionally NOT Implemented in Phase 2
- **gRPC / Protocol Buffers**: Reserved for Phase 3.
- **RabbitMQ Event Messaging**: Reserved for Phase 4.
- **WebSocket Push Updates**: Reserved for Phase 4.
- **Distributed Locking / Consensus**: Reserved for Phase 5.
- **Automated Failure Detection / Heartbeats**: Reserved for Phase 5.
