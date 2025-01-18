# Build a distributed KV store from scratch

In this article, we're going to start with a simple rust `HashMap` and build on top of it to include the following:
- persistence
- gRPC API
- RAFT consensus

## Design

Here's a high level design to keep us on track

<img width="670" alt="image" src="https://github.com/user-attachments/assets/e1538d4f-5817-4caa-832b-46c565c8eae9" />


### Get started

Let's get started with our crate and define some structure, I'll go with the `cmd` and `pkg` convention commonly used in go projects, cuz it keeps things nice and clean

```bash
(base) kv git:chore_initial_structure ❯ tree                                                                                ✭
.
├── Cargo.lock
├── Cargo.toml
└── src
    ├── cmd
    │   ├── cli.rs
    │   ├── mod.rs
    │   └── server.rs
    ├── main.rs
    └── pkg
        ├── handler.rs
        ├── map.rs
        └── mod.rs

4 directories, 9 files
```


### The Map

We're going to stick to the standard Hashmap from `std::collections` for the map, let's do that and add our `get`, `set`, `del` and `ttl` methods 

```rust
pub struct KV<T>{
    map: HashMap<String, T>
}

impl<T: Clone> KV<T>{

    async fn new() -> Self{
        Self{
            map: HashMap::new()
        }
    }

    async fn set(&mut self, key: &str, val: T){
        self.map.insert(key.to_string(), val);
    }

    async fn get(&self, key: &str) -> Result<T> {
        match self.map.get(key).cloned(){
            Some(v) => Ok(v),
            None => Err("key not found".into()) 
        }
    }
   
    async fn del(&mut self, key: &str) {
        self.map.remove(key);
    }

    async fn ttl(&self, _key: &str) -> Duration{
        unimplemented!()
    }
}
```

Let's quickly add basic tests...

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_set_key(){
        let mut kv = KV::new().await;
        kv.set("name", "ashu").await;
    }

    #[tokio::test]
    async fn test_get_key() -> Result<()>{
        let mut kv = KV::new().await;
        kv.set("name", "ashu").await;
        assert_eq!(kv.get("name").await?, "ashu");
        Ok(())
    }

    #[tokio::test]
    async fn test_del_key(){
        let mut kv: KV<String> = KV::new().await;
        kv.del("name").await;
    }
    
}
```

### gRPC

Cool, now that we have our basic map, let's add our gRPC wrapper
