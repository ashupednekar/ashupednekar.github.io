# Build a distributed KV store from scratch

In this article, we're going to start with a simple rust `HashMap` and build on top of it to include the following:
- persistence
- gRPC API
- RAFT consensus

## Design

Here's a high level design to keep us on track


