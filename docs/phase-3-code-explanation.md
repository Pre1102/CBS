# Phase 3 — File-by-File Code Explanation Guide

This guide provides a file-by-file breakdown of key Phase 3 components for your technical viva defense.

---

## 1. `backend/grpc_communication/proto/campus_resource.proto`
- **Purpose**: Central Protocol Buffer Interface Definition Language (IDL) schema defining gRPC services and data messages.
- **Key Elements**:
  - `service DepartmentNodeService`: Declares `GetNodeInfo` and `GetResources` RPC methods.
  - `message NodeInfoRequest / NodeInfoResponse`: Structures for node identity check.
  - `message ResourceRequest / ResourceResponse / ResourceProto`: Structures for inter-node resource querying.
- **Viva Explanation**: *"This `.proto` file defines the explicit contract for remote procedure calls and binary message schemas between department nodes."*

---

## 2. `backend/grpc_communication/server.py`
- **Purpose**: Reusable gRPC server servicer implementation and server runner.
- **Key Functions / Classes**:
  - `DepartmentNodeServicer`: Class inheriting from `DepartmentNodeServiceServicer`. Implements `GetNodeInfo` and `GetResources`. Reads strictly from local SQLite database using `get_all_resources()`.
  - `start_grpc_server(department_code, grpc_port, db_path)`: Starts non-blocking gRPC server listening on assigned gRPC port (`50051`, `50052`, `50053`).
- **Viva Explanation**: *"The gRPC server receives RPC requests from remote nodes and queries only its local SQLite database to construct and return binary Protocol Buffer responses."*

---

## 3. `backend/grpc_communication/node_client.py`
- **Purpose**: Reusable gRPC client helper for making inter-node RPC calls.
- **Key Functions**:
  - `get_remote_node_info(target_dept)`: Connects to target node gRPC port, invokes `GetNodeInfo`, and returns node status.
  - `get_remote_resources(target_dept)`: Connects to target node gRPC port, invokes `GetResources`, converts Protocol Buffer objects to Python dictionaries, and handles `grpc.RpcError` by raising clean HTTP 503 errors.
- **Viva Explanation**: *"This module encapsulates gRPC channel creation, stub instantiation, RPC invocation, and graceful failure handling when a node requests remote resources."*

---

## 4. `backend/department_nodes/cse_node/routes/remote.py`
- **Purpose**: Demonstration HTTP router in CSE node for cross-department resource queries via gRPC.
- **Key Endpoints**:
  - `GET /remote-resources/{target_dept}`: HTTP endpoint in CSE node that calls `get_remote_resources()` over gRPC to fetch resources from IT or E&TC node.
- **Viva Explanation**: *"This endpoint allows web clients or instructors to trigger and observe actual gRPC inter-node communication live in the system."*

---

## 5. `backend/department_nodes/common/config.py`
- **Purpose**: Centralized network host and port definitions.
- **Key Port Definitions**:
  - **Gateway**: `8000`
  - **HTTP Ports**: CSE: `50151`, IT: `50152`, E&TC: `50153`
  - **gRPC Ports**: CSE: `50051`, IT: `50052`, E&TC: `50053`
- **Viva Explanation**: *"Maintains clean port separation between HTTP REST APIs and binary gRPC RPC servers to avoid port binding conflicts."*

---

## 6. `backend/tests/test_grpc.py`
- **Purpose**: Automated Pytest suite verifying Phase 3 gRPC implementation.
- **Key Tests**:
  - Server startup and channel readiness.
  - `GetNodeInfo` RPC execution.
  - CSE -> IT and CSE -> E&TC `GetResources` gRPC execution.
  - Verification of department ownership on returned Protocol Buffer resources.
  - Graceful error handling when target gRPC server is offline.
- **Viva Explanation**: *"Validates end-to-end gRPC communication, server responsiveness, data correctness, and failure isolation across all nodes."*
