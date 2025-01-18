## Write a simple gRPC server in rust in less than 5 minutes

If you've seen my article on writing gRPC servers in go, this article will be very similar, but a lot more magical, thanks to the amaaaazing `tonic` crate in the `tokio` stack.

### Let's get started

Create a crate, and add the dependencies

```bash
(base) Documents ❯ cargo new calculator
(base) Documents ❯ cd calculator
(base) calculator git:master ❯ cargo add tokio -F full                                              (base) calculator git:master ❯ cargo add tonic
(base) calculator git:master ❯ cargo add tonic-build
```

Go ahead and install the protobuf compiler with your package manager of choice

```bash
(base) calculator git:master ❯ brew install protobuf 
```

Create a `proto` directory in your project root, next to your `src` directory, and define your protobuf messages and rpc's

```bash
(base) calculator git:master ❯ mkdir proto
(base) calculator git:master ❯ touch proto/calc.proto
```

```proto
syntax = "proto3";

package calc;

service CalcService {
  rpc Add(Input) returns (Result);
  rpc Subtract(Input) returns (Result);
  rpc Multiply(Input) returns (Result);
  rpc Divide(Input) returns (Result);
}

message Input {
  int32 a = 1;
  int32 b = 2;
}

message Result {
  int32 c = 1;
}
```

The four rpc's here accept the `Input` message and returns it's result in the `Result` crate

### The magic part

Usually at this stage, you'd have to jump to the gRPC docs to hunt for the `protoc` command to generate the proto code, and worry about placing it somewhere in your package, which can become a hassle unless you are in go and have first class support from gRPC itself.

Take a look at [quickgrpc](https://pypi.org/project/quickgrpc/) if you need to do this in python

---

Anyway...

in rust, we have amazing tooling from tonic, thanks to macro magic which completely hides all this from the developer, so you can focus on implementing your logic the rusty way 😄

So this works by telling the compiler to invoke a macro provided by tonic at compile time, so the generated code is available for use as just another crate, as you'll see soon

Start by adding a `build.rs` in your project root

```rust
use std::error::Error;

fn main() -> Result<(), Box<dyn Error>> {
    tonic_build::compile_protos("proto/calc.proto")?;
    Ok(())
}
```

Cool, now let's import these and implement the rpc methods, in your `main.rs`

```rust
use std::error::Error;

use proto::calculator_server::{Calculator, CalculatorServer};
use tonic::transport::Server;

mod proto{
    tonic::include_proto!("calc");
}

#[derive(Debug, Default)]
struct CalcService{}

#[tonic::async_trait]
impl Calculator for CalcService{

    async fn add(
        &self, 
        req: tonic::Request<proto::Input>
    ) -> Result<tonic::Response<proto::Result>, tonic::Status>{
        let input = req.get_ref();
        let result = proto::Result{c: input.a+input.b};
        Ok(tonic::Response::new(result))
    }

    async fn subtract(
        &self, 
        req: tonic::Request<proto::Input>
    ) -> Result<tonic::Response<proto::Result>, tonic::Status>{
        let input = req.get_ref();
        let result = proto::Result{c: input.a-input.b};
        Ok(tonic::Response::new(result))
    }

    async fn multiply(
        &self, 
        req: tonic::Request<proto::Input>
    ) -> Result<tonic::Response<proto::Result>, tonic::Status>{
        let input = req.get_ref();
        let result = proto::Result{c: input.a*input.b};
        Ok(tonic::Response::new(result))
    }

    async fn divide(
        &self, 
        req: tonic::Request<proto::Input>
    ) -> Result<tonic::Response<proto::Result>, tonic::Status>{
        let input = req.get_ref();
        let result = proto::Result{c: input.a/input.b};
        Ok(tonic::Response::new(result))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>>{
    let calc = CalcService::default();
    Server::builder()
        .add_service(CalculatorServer::new(calc))
        .serve("[::1]:3000".parse()?)
        .await?;
    Ok(())
}
```

> note: since tonic needs the trait to implement async methods, you need to add an macro to enable that. 

- The handler receives a `tonic::Request` containing a struct that corresponds to your proto message- Your can get a reference to your message struct using the `get_ref` method
- Once you perform your logic, you can intantiate the struct corresponding to your result message and wrap it in `tonic::Response` and return

Finally, let's set up the server

```rust
use proto::calculator_server::CalculatorServer;
use tonic::transport::Server;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>>{
    let calc = CalcService::default();
    Server::builder()
        .add_service(CalculatorServer::new(calc))
        .serve("[::1]:3000".parse()?)
        .await?;
    Ok(())
}
```
