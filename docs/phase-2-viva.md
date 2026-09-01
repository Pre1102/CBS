# Phase 2 — Viva Preparation Questions & Answers

This document contains concise, conversational responses to viva questions focused on SQLite, data layer architecture, local conflict detection, and distributed systems principles for Phase 2.

---

## Part 1: SQLite & Database Layer

### Q1: What is SQLite?
**Answer:**
SQLite is a C-language library that provides a lightweight, disk-based database. It does not require a separate database server process, allowing Python applications to interact directly with structured database files using SQL.

### Q2: Why did you choose Python's built-in `sqlite3` module without an ORM like SQLAlchemy?
**Answer:**
Using raw `sqlite3` keeps the project simple, transparent, and easy to explain during a technical viva. It avoids extra framework overhead and allows faculty to see exact SQL table definitions and queries.

### Q3: Why does every department node have its own separate `.db` file?
**Answer:**
In a distributed system, individual department nodes must own their data stores (`cse.db`, `it.db`, `entc.db`). If all nodes shared a single database file, it would create a single point of failure and bottleneck, defeating the purpose of decentralization.

### Q4: How are databases initialized when a department node starts?
**Answer:**
When a node starts, its entry point calls `initialize_database()`. It executes SQL `CREATE TABLE IF NOT EXISTS` for `resources` and `bookings`. If the `resources` table is empty, it automatically populates initial sample data from `seed_data.py`.

---

## Part 2: Architecture & Gateway Routing

### Q5: Why doesn't the API Gateway directly access the SQLite database files?
**Answer:**
Direct database access by the Gateway would break process isolation and departmental autonomy. The Gateway's sole responsibility is routing frontend client requests to the correct department node. The department node is responsible for managing its own database.

### Q6: How does the Gateway route requests to specific department nodes?
**Answer:**
The Gateway extracts the `{department}` path parameter from URLs like `/api/departments/cse/resources` and looks up the corresponding node base URL (`http://127.0.0.1:50051`). It forwards the request using an asynchronous HTTP client (`httpx`).

### Q7: What happens if a requested department node is offline?
**Answer:**
If a department node cannot be reached, the API Gateway catches the connection error and returns a clean `HTTP 503 Service Unavailable` response to the client without crashing.

---

## Part 3: Booking & Conflict Detection

### Q8: How does local booking conflict detection work?
**Answer:**
Before creating a booking, the node checks existing `CONFIRMED` bookings for the same resource on that date. It checks if the requested time interval overlaps with any existing booking using the formula: `new_start < existing_end AND new_end > existing_start`.

### Q9: What happens when a booking is cancelled?
**Answer:**
When cancelled, the booking record is not deleted from SQLite. Its `status` column is updated to `CANCELLED`. This preserves booking history while excluding the cancelled slot from future overlap conflict checks.

### Q10: What happens if a client submits a booking for a non-existent resource?
**Answer:**
The department node queries `SELECT * FROM resources WHERE id = ?`. If no record is found, it returns `HTTP 404 Not Found` with a clear message: `"Resource ID not found in node"`.

---

## Part 4: Distributed Systems & Future Phases

### Q11: Is the Phase 2 booking conflict check a distributed synchronization algorithm?
**Answer:**
No. Phase 2 provides **local conflict validation** within a single department node's SQLite database. It prevents double-booking resources belonging to that node. Distributed synchronization across nodes will be added in later phases.

### Q12: What limitation does the Phase 2 implementation have?
**Answer:**
Currently, nodes communicate with the Gateway over HTTP REST, and nodes do not directly coordinate with each other. If a cross-department booking transaction requires atomic execution across multiple nodes, HTTP alone is insufficient.

### Q13: Why do we need gRPC in Phase 3?
**Answer:**
gRPC provides high-performance, low-latency binary Remote Procedure Calls (RPC) using Protocol Buffers. It enables direct, strongly typed node-to-node communication required for cross-department resource queries and distributed synchronization.
