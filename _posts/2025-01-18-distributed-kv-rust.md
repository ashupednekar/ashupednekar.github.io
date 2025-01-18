# Build a distributed KV store from scratch

In this article, we're going to start with a simple rust `HashMap` and build on top of it to include the following:
- persistence
- gRPC API
- RAFT consensus

## Design

Here's a high level design to keep us on track

<img width="670" alt="image" src="https://github.com/user-attachments/assets/e1538d4f-5817-4caa-832b-46c565c8eae9" />

