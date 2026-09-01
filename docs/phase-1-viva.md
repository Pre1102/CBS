# Phase 1 — Viva Preparation Questions & Answers

This document contains short, clear, and conversational responses to potential technical viva questions for Phase 1.

---

## Part 1: Distributed Systems Concepts

### Q1: What is a distributed system?
**Answer:**
A distributed system is a collection of independent computers or processes located on networked nodes that communicate and coordinate their actions by passing messages to appear as a single coherent system to the user.

### Q2: Why is this project a distributed system?
**Answer:**
Instead of storing all campus resources in one database controlled by a single central server, each department (CSE, IT, E&TC) runs its own independent service node. Nodes manage local resources and communicate with each other to coordinate bookings.

### Q3: Why do we have multiple department nodes?
**Answer:**
Multiple department nodes allow individual departments to maintain operational autonomy over their labs and seminar halls. If one department's server goes offline, other departments can continue booking their resources without interruption.

### Q4: What is a node in this architecture?
**Answer:**
A node is an independent software process representing a specific campus department (e.g., CSE Node). It runs on its own dedicated port, manages its own routes, and operates independently of other department nodes.

### Q5: What is decentralization in the context of this system?
**Answer:**
Decentralization means no single department node has absolute control over all campus resources. Decision-making and state management are distributed across equal department nodes rather than controlled by a single master server.

---

## Part 2: Backend & Gateway Concepts

### Q6: Why did you choose Python for the backend?
**Answer:**
Python was chosen for its clean syntax, readability, fast development cycle, and excellent support for modern asynchronous web frameworks like FastAPI.

### Q7: What is FastAPI?
**Answer:**
FastAPI is a modern, high-performance web framework for Python 3.8+ built on standard Python type hints. It provides fast execution, automatic OpenAPI documentation, and easy request validation.

### Q8: What is Uvicorn?
**Answer:**
Uvicorn is an ASGI (Asynchronous Server Gateway Interface) web server implementation for Python. It is used to serve our FastAPI applications asynchronously.

### Q9: What is an API?
**Answer:**
An API (Application Programming Interface) is a set of defined rules and protocols that allow different software applications (like our React frontend and FastAPI backend) to communicate with each other over HTTP.

### Q10: What is an API Gateway?
**Answer:**
An API Gateway is a central entry point that sits between clients (like web frontends) and backend services. It routes incoming requests, handles protocol translation, and centralizes cross-cutting concerns like CORS and authentication.

### Q11: Why do we use an API Gateway in this project?
**Answer:**
The Gateway gives the React frontend a single host and port (`127.0.0.1:8000`) to communicate with. The Gateway abstracts the underlying multi-node architecture so the frontend doesn't need to know the specific network addresses of every individual department node.

---

## Part 3: Frontend & Communication Concepts

### Q12: What is React?
**Answer:**
React is a popular JavaScript UI library for building user interfaces based on reusable components.

### Q13: What is Vite?
**Answer:**
Vite is a lightweight build tool and development server that offers extremely fast hot module replacement (HMR) and optimized build bundling for frontend framework projects like React.

### Q14: How does the React frontend communicate with the Python backend?
**Answer:**
The frontend uses JavaScript's native asynchronous `fetch()` API inside `frontend/src/services/api.js` to send HTTP `GET` requests to the Gateway's `/api/health` endpoint.

### Q15: What is HTTP?
**Answer:**
HTTP (Hypertext Transfer Protocol) is an application-layer protocol used for transmitting hypermedia and structured data (like JSON) over the web using request-response cycles.

### Q16: What is CORS and why is it configured?
**Answer:**
CORS (Cross-Origin Resource Sharing) is a browser security mechanism that restricts web pages from making API requests to a different domain or port than the one that served the web page. We configured CORS on FastAPI to explicitly permit requests from the Vite dev server (`http://localhost:5173`).

---

## Part 4: Project Architecture & Organization

### Q17: What is the role of the CSE node?
**Answer:**
The CSE node (port `50051`) is an independent service responsible for handling resource availability, schedules, and booking requests specific to the Computer Science & Engineering department.

### Q18: What is the role of the IT node?
**Answer:**
The IT node (port `50052`) is an independent service responsible for handling resources, schedules, and bookings for the Information Technology department.

### Q19: What is the role of the E&TC node?
**Answer:**
The E&TC node (port `50053`) is an independent service responsible for handling resources, schedules, and bookings for the Electronics & Telecommunication department.

### Q20: Why are the department nodes separate processes instead of modules inside one server?
**Answer:**
Running nodes as separate processes on different ports simulates true distributed execution. It proves process isolation, fault tolerance, and independent scalability—key learning outcomes of a Distributed Systems course.
