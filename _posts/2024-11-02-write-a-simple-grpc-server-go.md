## Write a simple gRPC server in go in 5 minutes

This article explains how to create a simple gRPC server in Go. It covers defining a service in a .proto file, generating Go code using protoc, implementing the server, and running it. Ideal for beginners, the guide provides clear, step-by-step instructions to quickly set up a basic gRPC server in Go.

--

## Here are the steps..

Create your directory

```bash
mkdir myserver
```

Initialize your module

```bash
cd myservergo mod init github.com/user/myserver. 
```

Create basic structure

```bash
mkdir internalmkdir cmdtouch cmd/main.go
```

Add main boilerlplate

```protofile
package mainfunc main(){}
```

Cool, now let’s get to the fun part…

Say I’m making a calculator gRPC server with only ints…

```bash
cd internalmkdir calctouch calc.proto
```

Write your `calc.proto`\` file like so

```proto
syntax = "proto3";

option go_package = "github.com/user/myserver/internal/calc";

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

Now let’s install protoc compiler

Visit [https://github.com/protocolbuffers/protobuf/releases](https://github.com/protocolbuffers/protobuf/releases) in your browser and download the zip file that corresponds to your OS and computer architecture.

Next, unzip the file under `$HOME/.local` by running the following command, where `protoc-24.3-osx-universal_binary.zip` is the zip file that corresponds to your OS and computer architecture:

```bash
unzip protoc-24.3-osx-universal_binary.zip -d $HOME/.local
```

Now update your environment’s `PATH` variable to include the path to the `protoc` executable by adding the following code to your `.bash_profile` or `.zshrc` file:

```bash
export PATH="$PATH:$HOME/.local/bin"
```

Note: If your `.bash_profile` or `.zshrc` file already contains an `export path`, you can simply append `:$HOME/.local/bin`.

Now we’re ready for protoc to do it’s magic.

Run the following command from the `internal` directory

```bash
protoc --go_out=calc --go_opt=paths=source_relative \    --go-grpc_out=calc --go-grpc_opt=paths=source_relative \    calc.proto
```

This will generate the pb serializer and stub code under `intenal/calc`

```bash
├── calc
│   ├── calc.pb.go
│   └── calc_grpc.pb.go
└── calc.proto
```

Run `go mod tidy for necessary packages to be downloaded`

``bash
internal ❯ go mod tidy
go: finding module for package google.golang.org/grpc
go: finding module for package google.golang.org/protobuf/reflect/protoreflect
go: finding module for package google.golang.org/grpc/codes
go: finding module for package google.golang.org/grpc/status
go: finding module for package google.golang.org/protobuf/runtime/protoimpl
go: found google.golang.org/grpc in google.golang.org/grpc v1.67.1
go: found google.golang.org/grpc/codes in google.golang.org/grpc v1.67.1
go: found google.golang.org/grpc/status in google.golang.org/grpc v1.67.1
go: found google.golang.org/protobuf/reflect/protoreflect in google.golang.org/protobuf v1.35.1
go: found google.golang.org/protobuf/runtime/protoimpl in google.golang.org/protobuf v1.35.1
```

Now let’s add the `server.go`\`, under `internal`

Import pb

```go
import ( pb "github.com/user/myserver/internal/calc")
```

Define server type

```go
type server struct{  pb.UnimplementedCalcServiceServer}
```

Implement rpc methods

```go
func (s *server) Add(ctx context.Context, inp *pb.Input) (*pb.Result, error) {
    return &pb.Result{C: inp.A + inp.B}, nil
}

func (s *server) Subtract(ctx context.Context, inp *pb.Input) (*pb.Result, error) {
    return &pb.Result{C: inp.A - inp.B}, nil
}

func (s *server) Multiply(ctx context.Context, inp *pb.Input) (*pb.Result, error) {
    return &pb.Result{C: inp.A * inp.B}, nil
}

func (s *server) Divide(ctx context.Context, inp *pb.Input) (*pb.Result, error) {
    return &pb.Result{C: inp.A / inp.B}, nil
}
```

Add server code

```go
func StartServer() {
    ln, err := net.Listen("tcp", ":3000")
    if err != nil {
        log.Fatalf("error listening at port 3000: %v", err)
    }

    s := grpc.NewServer()
    pb.RegisterCalcServiceServer(s, &server{})

    log.Printf("gRPC server listening at %v", ln.Addr())

    if err := s.Serve(ln); err != nil {
        log.Fatalf("failed to start gRPC server: %v", err)
    }
}
```

Here’s it all together: `server.go`

```go
package internal

import (
    "context"
    "log"
    "net"
    pb "github.com/user/myserver/internal/calc"
    "google.golang.org/grpc"
)

type server struct {
    pb.UnimplementedCalcServiceServer
}

func (s *server) Add(ctx context.Context, inp *pb.Input) (*pb.Result, error) {
    return &pb.Result{C: inp.A + inp.B}, nil
}

func (s *server) Subtract(ctx context.Context, inp *pb.Input) (*pb.Result, error) {
    return &pb.Result{C: inp.A - inp.B}, nil
}

func (s *server) Multiply(ctx context.Context, inp *pb.Input) (*pb.Result, error) {
    return &pb.Result{C: inp.A * inp.B}, nil
}

func (s *server) Divide(ctx context.Context, inp *pb.Input) (*pb.Result, error) {
    return &pb.Result{C: inp.A / inp.B}, nil
}

func StartServer() {
    ln, err := net.Listen("tcp", ":3000")
    if err != nil {
        log.Fatalf("error listening at port 3000: %v", err)
    }

    s := grpc.NewServer()
    pb.RegisterCalcServiceServer(s, &server{})

    log.Printf("gRPC server listening at %v", ln.Addr())

    if err := s.Serve(ln); err != nil {
        log.Fatalf("failed to start gRPC server: %v", err)
    }
}
```

Now add this to `cmd/main.go`

```
package main

import "github.com/user/myserver/internal"

func main() {
    internal.StartServer()
}
```

That’s it, server is ready

```bash
myserver ❯ go run cmd/main.go
2024/11/02 10:23:36 gRPC server listening at [::]:3000
```

Now let’s add the client code, `internal/client.go like so...`

```go
package internal

import (
    "context"
    "time"
    pb "github.com/user/myserver/internal/calc"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
)

func Connect() (pb.CalcServiceClient, error) {
    conn, err := grpc.Dial("localhost:3000", grpc.WithTransportCredentials(insecure.NewCredentials()))
    if err != nil {
        return nil, err
    }
    return pb.NewCalcServiceClient(conn), nil
}

func Add(client pb.CalcServiceClient, a int32, b int32) (int32, error) {
    ctx, cancel := context.WithTimeout(context.Background(), time.Millisecond*100)
    defer cancel()
    r, err := client.Add(ctx, &pb.Input{A: a, B: b})
    if err != nil {
        return 0, err
    }
    return r.C, nil
}

func Subtract(client pb.CalcServiceClient, a int32, b int32) (int32, error) {
    ctx, cancel := context.WithTimeout(context.Background(), time.Millisecond*100)
    defer cancel()
    r, err := client.Subtract(ctx, &pb.Input{A: a, B: b})
    if err != nil {
        return 0, err
    }
    return r.C, nil
}

func Multiply(client pb.CalcServiceClient, a int32, b int32) (int32, error) {
    ctx, cancel := context.WithTimeout(context.Background(), time.Millisecond*100)
    defer cancel()
    r, err := client.Multiply(ctx, &pb.Input{A: a, B: b})
    if err != nil {
        return 0, err
    }
    return r.C, nil
}

func Divide(client pb.CalcServiceClient, a int32, b int32) (int32, error) {
    ctx, cancel := context.WithTimeout(context.Background(), time.Millisecond*100)
    defer cancel()
    r, err := client.Divide(ctx, &pb.Input{A: a, B: b})
    if err != nil {
        return 0, err
    }
    return r.C, nil
}
```

There’s a `Connect function and wrappers for each rpc method`

Let’s now modify main to use the client functions as well

First, move the server to a seperate goroutine

```go
func main() {
    go internal.StartServer()
    select {}
}
```

Now call the client wrappers

```go
package main

import (
    "fmt"
    "log"
    "github.com/user/myserver/internal"
)

func main() {
    go internal.StartServer()

    client, err := internal.Connect()
    if err != nil {
        log.Fatalf("error connecting to server: %v", err)
    }

    fmt.Println(internal.Add(client, 2, 2))
    fmt.Println(internal.Subtract(client, 2, 2))
    fmt.Println(internal.Multiply(client, 2, 2))
    fmt.Println(internal.Divide(client, 2, 2))

    select {}
}
```

Let’s run it :)

```bash
go run cmd/main.go
2024/11/02 10:35:24 gRPC server listening at [::]:3000
4 <nil>
0 <nil>
4 <nil>
1 <nil>
```

That’s it 😄  
You know how to write gRPC servers/clients in go now.

_note: this was only unary… you can look at the docs for insights on client/server side streaming… It’s pretty simple with channels._
