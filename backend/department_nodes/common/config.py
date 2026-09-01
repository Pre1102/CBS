import os

# Centralized Network & Port Configuration for Distributed Nodes

# API Gateway Configuration
GATEWAY_HOST = os.getenv("GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8000"))

# Department Nodes — HTTP Services Ports (Phase 2 & 3)
CSE_HTTP_HOST = os.getenv("CSE_HTTP_HOST", "127.0.0.1")
CSE_HTTP_PORT = int(os.getenv("CSE_HTTP_PORT", "50151"))

IT_HTTP_HOST = os.getenv("IT_HTTP_HOST", "127.0.0.1")
IT_HTTP_PORT = int(os.getenv("IT_HTTP_PORT", "50152"))

ENTC_HTTP_HOST = os.getenv("ENTC_HTTP_HOST", "127.0.0.1")
ENTC_HTTP_PORT = int(os.getenv("ENTC_HTTP_PORT", "50153"))

# Department Nodes — gRPC Inter-Node RPC Ports (Phase 3)
CSE_GRPC_HOST = os.getenv("CSE_GRPC_HOST", "127.0.0.1")
CSE_GRPC_PORT = int(os.getenv("CSE_GRPC_PORT", "50051"))

IT_GRPC_HOST = os.getenv("IT_GRPC_HOST", "127.0.0.1")
IT_GRPC_PORT = int(os.getenv("IT_GRPC_PORT", "50052"))

ENTC_GRPC_HOST = os.getenv("ENTC_GRPC_HOST", "127.0.0.1")
ENTC_GRPC_PORT = int(os.getenv("ENTC_GRPC_PORT", "50053"))

# Legacy Alias Compatibility
CSE_NODE_HOST = CSE_HTTP_HOST
CSE_NODE_PORT = CSE_HTTP_PORT

IT_NODE_HOST = IT_HTTP_HOST
IT_NODE_PORT = IT_HTTP_PORT

ENTC_NODE_HOST = ENTC_HTTP_HOST
ENTC_NODE_PORT = ENTC_HTTP_PORT
