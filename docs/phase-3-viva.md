# Phase 3 — Viva Preparation Questions & Answers

This document provides concise, technically accurate answers to 20 viva questions on gRPC, Protocol Buffers, RPC communication, stubs, channels, and port separation for Phase 3.

---

## Part 1: RPC & gRPC Concepts

### Q1: What is Remote Procedure Call (RPC)?
**Answer:**
RPC is an inter-process communication protocol that allows a program on one process or machine to call a subroutine/function in another process as if it were a local function call.

### Q2: Why is RPC useful in a distributed system?
**Answer:**
RPC abstracts away low-level network socket handling, data serialization, and transport protocols. It allows distributed nodes to interact through strongly typed function signatures instead of constructing manual HTTP request URLs.

### Q3: What is the difference between local function calls and RPC calls?
**Answer:**
A local function call executes within the same process memory space with negligible latency and guaranteed execution. An RPC call traverses network boundaries, involves binary serialization, experiences network latency, and can fail due to network disconnection or remote node downtime.

### Q4: What is gRPC?
**Answer:**
gRPC is a high-performance, open-source universal RPC framework developed by Google. It relies on HTTP/2 for efficient multiplexed transport and Protocol Buffers for structured binary serialization.

### Q5: Why did you choose gRPC over REST HTTP for inter-node communication?
**Answer:**
gRPC offers higher throughput, lower latency, binary serialization (smaller payload sizes), HTTP/2 multiplexing, and strict interface definition language (IDL) contracts compared to text-based JSON over HTTP REST.

---

## Part 2: Protocol Buffers & Code Generation

### Q6: What is a `.proto` file?
**Answer:**
A `.proto` file is an Interface Definition Language (IDL) file where service RPC methods and structured request/response message schemas are defined in a language-neutral format.

### Q7: Why do we use Protocol Buffers?
**Answer:**
Protocol Buffers serialize data into a compact binary format that is significantly smaller and faster to parse than JSON or XML. It also provides automatic code generation for multiple programming languages.

### Q8: What does `campus_resource_pb2.py` contain?
**Answer:**
It contains the generated Python data classes for Protocol Buffer request and response messages (`NodeInfoRequest`, `NodeInfoResponse`, `ResourceRequest`, `ResourceResponse`, `ResourceProto`).

### Q9: What does `campus_resource_pb2_grpc.py` contain?
**Answer:**
It contains generated client stub classes (`DepartmentNodeServiceStub`) and server base classes (`DepartmentNodeServiceServicer`) used to invoke and serve RPC methods.

### Q10: Why should students not manually edit generated `pb2` files?
**Answer:**
`pb2` files are automatically compiled by `grpc_tools.protoc`. Any manual edits will be overwritten whenever the `.proto` schema file is recompiled.

---

## Part 3: Channels, Stubs, & Servers

### Q11: What is a gRPC Channel?
**Answer:**
A gRPC channel represents a persistent HTTP/2 connection between a gRPC client and a remote gRPC server endpoint (e.g. `127.0.0.1:50052`).

### Q12: What is a gRPC Stub?
**Answer:**
A stub is the client-side proxy object instantiated from `campus_resource_pb2_grpc.DepartmentNodeServiceStub(channel)`. Calling a method on the stub serializes arguments and sends the RPC over the channel.

### Q13: What is a gRPC Servicer?
**Answer:**
A servicer is the server-side class (`DepartmentNodeServicer`) that inherits from `DepartmentNodeServiceServicer` and implements the actual logic for RPC methods like `GetNodeInfo` and `GetResources`.

---

## Part 4: Project Architecture & Execution

### Q14: How does CSE Node get IT Node's resources in Phase 3?
**Answer:**
CSE Node creates an insecure gRPC channel to IT Node (`127.0.0.1:50052`), uses the generated stub to call `GetResources()`, and IT Node's gRPC server queries `it.db` and returns the resources in a binary `ResourceResponse`.

### Q15: Can CSE Node directly open `it.db`?
**Answer:**
No. Each department node strictly owns its local SQLite database. CSE Node obtains IT's resources exclusively through IT's gRPC service.

### Q16: Why are HTTP and gRPC using separate ports?
**Answer:**
To avoid port binding conflicts. HTTP endpoints use ports `50151` (CSE), `50152` (IT), `50153` (E&TC), while gRPC servers listen on ports `50051` (CSE), `50052` (IT), `50053` (E&TC).

### Q17: What happens if IT Node is offline when CSE calls `GetResources`?
**Answer:**
The gRPC channel raises `grpc.RpcError` (`StatusCode.UNAVAILABLE`). The CSE node catches the error and returns a clean `HTTP 503 Service Unavailable` response to the client without crashing.

### Q18: Why does the React frontend not directly use gRPC?
**Answer:**
Browsers do not natively support standard HTTP/2 gRPC framing without a gRPC-Web proxy. The frontend communicates with Gateway over standard HTTP REST, and nodes communicate internally using gRPC.

### Q19: Is distributed mutual exclusion implemented in Phase 3?
**Answer:**
No. Phase 3 focuses exclusively on gRPC inter-node RPC communication. Distributed mutual exclusion and synchronization algorithms will be implemented in subsequent phases.

### Q20: What will be implemented in Phase 4?
**Answer:**
Phase 4 will introduce asynchronous message queues using RabbitMQ and real-time event broadcasting using WebSockets.
