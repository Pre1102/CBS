# Phase 2 — Code Explanation Guide for Viva Defense

This guide provides line-by-line explanations for key files created or modified in Phase 2. Use this guide to prepare for technical viva questions from course faculty.

---

## 1. `backend/department_nodes/common/database.py`

### What it does:
Provides SQLite connection management and database schema initialization routines.

### Why it exists:
Centralizes SQLite database connection settings (`sqlite3.Row`) and table creation SQL logic so each department node can initialize its local `.db` file on startup without duplicate code.

### Important Functions:
- `get_connection(db_path: str)`: Opens a SQLite connection, ensures directory exists, and sets `row_factory = sqlite3.Row` for dictionary-style field access.
- `initialize_database(db_path: str, department_code: str)`: Executes SQL statements `CREATE TABLE IF NOT EXISTS` for `resources` and `bookings`. If `resources` is empty, inserts seed sample data.

### Viva Question & Answer:
**Q:** *Why is `row_factory = sqlite3.Row` used?*  
**A:** "It allows accessing database query results by column names (e.g. `row['name']`) instead of numeric tuple indices (e.g. `row[1]`), making the code more readable."

---

## 2. `backend/department_nodes/common/models.py`

### What it does:
Defines Pydantic data schemas for request bodies and API response serializations.

### Why it exists:
FastAPI relies on Pydantic models to parse incoming JSON request payloads, validate data types, enforce restrictions (like positive capacity), and generate OpenAPI documentation.

### Key Classes:
- `ResourceCreate` & `ResourceResponse`: Validate resource creation attributes (`name`, `resource_type`, `location`, `capacity`).
- `BookingCreate` & `BookingResponse`: Validate booking request attributes (`resource_id`, `booked_by`, `booking_date`, `start_time`, `end_time`).

### Viva Question & Answer:
**Q:** *What is the role of Pydantic models in FastAPI?*  
**A:** "Pydantic performs automatic data validation and type coercion. If a client sends invalid types, FastAPI automatically returns a structured 422 Unprocessable Entity error."

---

## 3. `backend/department_nodes/common/handlers.py`

### What it does:
Contains core database query logic and local business validation functions for resources and bookings.

### Why it exists:
Decouples raw SQL queries and validation rules from API route endpoints, keeping HTTP route handlers clean and concise.

### Key Functions:
- `has_booking_conflict(db_path, resource_id, booking_date, start_time, end_time)`: Checks if any non-cancelled booking overlaps with the requested time slot using `new_start < existing_end AND new_end > existing_start`.
- `create_booking(db_path, booking, node_dept)`: Validates start time < end time, verifies resource existence and department ownership, executes conflict check, and inserts the new booking.
- `cancel_booking(db_path, booking_id)`: Updates `status = 'CANCELLED'` for a booking record without physically deleting it from SQLite.

### Viva Question & Answer:
**Q:** *Explain the overlap detection logic.*  
**A:** "For two time intervals on the same day to overlap, the new start time must be earlier than the existing end time, and the new end time must be later than the existing start time."

---

## 4. `backend/department_nodes/cse_node/main.py` (and `it_node`, `entc_node`)

### What it does:
Main application entry point for the CSE Department Node process (port 50051).

### Why it exists:
Initializes the node's local SQLite database (`cse.db`), registers resource and booking routes, and exposes HTTP health endpoints.

### Key Code:
```python
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "database", "cse.db"))
initialize_database(DB_PATH, "CSE")
app.include_router(resources_router)
app.include_router(bookings_router)
```

### Viva Question & Answer:
**Q:** *What happens when `main.py` of CSE node starts?*  
**A:** "It bootstraps the `cse.db` database, creates tables if missing, seeds initial CSE resources, registers the REST routers, and starts Uvicorn on port 50051."

---

## 5. `backend/api_gateway/routes/departments.py`

### What it does:
Handles client requests sent to `/api/departments/{department}/...` and forwards them to target department nodes.

### Why it exists:
The API Gateway acts as a reverse proxy. It resolves the department code (e.g. `cse` -> `http://127.0.0.1:50051`) and forwards HTTP GET/POST/PUT requests asynchronously using `httpx`.

### Key Functions:
- `resolve_node_url(department: str)`: Looks up target department base URL from `DEPARTMENT_MAP`.
- `get_departments_status()`: Asynchronously checks health of all 3 department nodes and returns `ONLINE` / `OFFLINE` status dict for the React dashboard.

### Viva Question & Answer:
**Q:** *Why does the Gateway use `httpx.AsyncClient`?*  
**A:** "`httpx.AsyncClient` enables non-blocking asynchronous HTTP requests, allowing FastAPI to handle multiple incoming client requests concurrently."
