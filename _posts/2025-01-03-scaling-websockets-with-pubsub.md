# Scalable websockets powered by pubsub

## Preface

So here's a little refresher on stateless vs stateful systems

As long as you are not worrying about distributed systems, stateless vs stateful doesn't really mean anything, since the requests are going to be served by the same process, and can thus have in memory state without any worries. But as soon as you think about availability, or scale to distributed systems where you have multiple pods running, usually across nodes in different availability zones. Now, if my application has in memory state, it'll break functionality since the requests will be routed to any of the available nodes/replicas which may not have this previous state.

Now certain problems are stateful by definition, and websockets is one of them. The client establishes a TCP connection with the server which stays alive for quite a long time, and messages are exchanged to and fro, which may not work properly on network breaks/ pod downtime, as the next request may be made to an entirely different server. 

## So what to do? 

So there are two main approaches used widely to solve this problem

- The websocket server state, including the client information is stored in a centralized, ideally distributed KV system like redis. Example implementations would be django's `channels` library and some other frameworks. This name is quite apt, you'll know why soon

- The other approach is to have a common proxy server which would then send the requests, say through rpc's to the respective services. PushPin is one such example. This works, but has it's own problems like having a central point of failure and depending on limited tools without widespread support

Pubsub is also generally used to avoid having multiple services in a microservice system have websockets, and limit the "statefulness" to one or two services that can be given special treatment in terms of availability guarantees, through say node affinity. Wouldn't it be great to have this dedicated service be fully distributed, ideally backed by a RAFT based message broker like `NATS`? Another advantage this brings is make it simpler to work with since websockets will be abstracted as simple fire-and-forget pubsub as far as services are concerned.

## Approach 

Here's an excalidraw scrsht illustrating the approach

![websocketstream](https://github.com/user-attachments/assets/9636579c-4598-4514-9ce6-4d3f93327703)

It's a simple idea, which passes websocket messages to and from our services through pubsub streams. There are five main players here

- client: sends and receives messages over ws to our `websocket` service
- recv stream: this goroutine is going to be spawned for each ws connection, which'll start a consumer listening at `ws.recv.<svc>.<user>`. These svc and user values are obtained from the request, say cookies
- send stream: this gorouting, again per request... will listen for client messages and publish them at `ws.send.<svc>.<user>`, that's it
- service consumer: So instead of reading messages from a websocket client, our services will consume them from `ws.send.<svc>.<user>`
- service producer: Whenever service needs to send a message to the client, it'll simply produce to `ws.recv.<svc>.<user>`, this will be picked up by the recv stream and sent to the websocket client

Neat right? And as long as our broker is something like nats/kafka which ensures write consensus, we'll have persistent, distributed websockets that can be scaled independently to any number of replicas, with the added advantage of having dedicated queues for every websocket client. And since these queues are persistent, you can send to them even when the client is not connected, recv stream will pick it up on the next connection :) 

## Let's code it up

Cool, let's start our go project


I'm gonna add the typical `cmd`, `pkg` structure to it, and we're gonna have three packages, for `broker`, `server` and `stream` respectively

```bash
(base) websocketstream git:main ❯ tree                                                                 ✖
.
├── README.md
├── cmd
│   └── main.go
├── go.mod
├── go.sum
└── pkg
    ├── brokers
    ├── server
    └── stream

6 directories, 4 files
```

---

### Server

Let's start with the server. I'm using `gorilla/websocket` here, add it like so

```bash
go get github.com/gorilla/websocket
```

Now go ahead and define the upgrader and the Handler function, in a file called `handler.go`

```go
package server

import (
	"log"
	"net/http"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
  ReadBufferSize: 1024,
  WriteBufferSize: 1024,
}

func HandleWs(w http.ResponseWriter, r *http.Request){
  conn, err := upgrader.Upgrade(w, r, nil)
  if err != nil{
    log.Fatalf("error upgrading websocket connection\n")
  }
  defer conn.Close()
  log.Println("Client connected")
}
```

Here's my main server code, under `serve.go`

```go
package server

import (
	"fmt"
	"log"
	"net/http"
)

type Server struct{
  Port int
}

func NewServer(port int) *Server {
  return &Server{port}
}

func (s *Server) Start(){
  http.HandleFunc("/ws/", HandleWs)
  log.Printf("listening on port: %d", s.Port)
  if err := http.ListenAndServe(fmt.Sprintf(":%d", s.Port), nil); err != nil{
    log.Fatalf("Error starting server at port %d: %s\n", s.Port, err)
  }
}
```

Go ahead and add this to `cmd/main.go`

```go
package main

import "github.com/ashupednekar/websocketstream/pkg/server"

func main(){
  s := server.NewServer(8000)
  s.Start()
}
```

---

### Broker

Now that we have our server, let's set up pubsub. 

I'm gonna create a `base.go` file under `brokers` package with two things. The idea here is to shield the rest of our packages from broker specific stuff, instead they are going to deal with a common `Broker` interface we'll define soon

- A `message` struct, this is the common message type that's gonna be agnostic to which broker we're working with

```go
type Message struct{
  Subject string
  Data []byte
}
```

- We need an interface to define what our brokers should do, namely `pub` and `sub` :)

```go
type Broker interface{
  Produce(subject string, data []byte);
  Consume(subject string, ch chan Message)
}
```

The `produce` function takes a subject and byte data, I've chosen subject as the terminology because I like nats xP. The same things is going to be routing key and topic respectively when you add amqp and kafka support

Let's have a `NewBroker` function that'll instantiate the right broker based on env, only `nats` for now

```go
func NewBroker() Broker {
  //if os.Getenv("PUBSUB_BROKER") == "nats"{
  return NewNatsBroker("websockets") 
}
```

Note that this is returning the interface, i.e. `Broker`, and not the `NatsBroker` type. This keeps it clean in the rest of the modules and serves as a decent abstraction. 

Let's quickly add the nats implementation

```go
package brokers

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/nats-io/nats.go"
	"github.com/nats-io/nats.go/jetstream"
)

type NatsBroker struct{
  StreamName string
  Stream jetstream.JetStream 
}

func NewNatsBroker(stream string) *NatsBroker{
  nc, err := nats.Connect(os.Getenv("NATS_BROKER_URL"))
  if err != nil{
    log.Fatalf("couldn't connect to nats: %s", err);
  }
  js, _ := jetstream.New(nc)
  ctx := context.Background()
  _, err = js.CreateOrUpdateStream(ctx, jetstream.StreamConfig{Name: stream, Subjects: []string{"ws.>"}, Retention: jetstream.WorkQueuePolicy})
  if err != nil{
    log.Fatalf("error creating/updating stream: %s", err)
  }
  return &NatsBroker{Stream: js, StreamName: stream}
}

func (self *NatsBroker) Produce(subject string, data []byte){
  ctx := context.Background()
  self.Stream.Publish(ctx, subject, data)
  defer ctx.Done()
}

func (self *NatsBroker) Consume(subject string, ch chan Message){
  ctx, _ := context.WithTimeout(context.Background(), time.Second * 300)
  defer ctx.Done()
  c, err := self.Stream.CreateOrUpdateConsumer(ctx, self.StreamName, jetstream.ConsumerConfig{
    Durable: strings.ReplaceAll(fmt.Sprintf("%s-consumer", subject), ".", "-"),
    FilterSubject: subject,
  })
  if err != nil{
    log.Fatalf("error creating consumer: %s", err)
  }
  consumer, err := c.Consume(func(msg jetstream.Msg){
    msg.Ack()
    log.Printf("Received message: %v", msg.Data())
    ch <- Message{
      Subject: subject,
      Data: msg.Data(),
    }
  })
  defer consumer.Stop()
  <-ctx.Done()
}
```

> Just add this and run `go mod tidy`, it'll take care of the dependencies

Here's what's being done here
- Connecting to nats, picking the url from an env
- Creating the `websockets` stream, with the wildcard pattern `ws.>`, refer to nats docs for more
- Defined `Produce` and `Consume` methods conforming to the previously defined interface

Note that the consumer accepts a channel `chan Message` and passes that to the callback. Essentially every message consumed will be passed through this channel in the common `Message` format we talked about earlier, with the subject and the byte data

---

### Stream

Now let's get to the meat, the send and recv stream we mentioned in our diagram...

Since we wrote decent abstractions around the pubsub and server, the main business logic is going to be short and clean


Let's start with the stream responsible for receiving client messages

```go
package stream

import (
	"log"

	"github.com/ashupednekar/websocketstream/pkg/brokers"
	"github.com/gorilla/websocket"
)

func RecvClientMessages (conn *websocket.Conn, broker brokers.Broker){
  go func(){
    for {
      _, message, err := conn.ReadMessage()
      if err != nil{
        log.Printf("error reading client message: %s\n", err)
        break
      }
      log.Printf("received message from client: %s\n", message)
      broker.Produce("ws.send.svc.user", message)
    }
  }()
}
```

The naming here can get tricky, since something that's "sending" messages from one perspective is actually "receiving" from another perspective. That's why I chose to go with what messages they are working with.


**This one receives client messages from the websocket client, and produces it to pubsub**

Note that the whole thing is wrapped in a `go func(){}()` cuz we want this to run concurrently in a seperate goroutine

---

Cool, let's proceed to handing the messages from our services

```go
package stream

import (
	"github.com/ashupednekar/websocketstream/pkg/brokers"
	"github.com/gorilla/websocket"
)

func RecvServiceMessages(conn *websocket.Conn, broker brokers.Broker){
  ch := make(chan brokers.Message)
  go broker.Consume("ws.recv.svc.user", ch)
  for msg := range(ch){
    conn.WriteMessage(websocket.BinaryMessage, msg.Data)
  }
}

```

Here's the bottom line

**This one consumes the messages from pubsub, and writes them to the websocket client**

Note that the consumer here, runs in a seperate goroutine for concurrency, and we're getting the messages it writes to the channel, which are then written to the websocket client

---

### Wrapping up

Let's update our websocket handler

```go
func HandleWs(w http.ResponseWriter, r *http.Request){
  conn, err := upgrader.Upgrade(w, r, nil)
  if err != nil{
    log.Fatalf("error upgrading websocket connection\n")
  }
  defer conn.Close()

  log.Println("Client connected")

  broker := brokers.NewBroker()
  stream.RecvClientMessages(conn, broker)
  stream.RecvServiceMessages(conn, broker)
}
```

I've just created the broker and started both streams, note that even the goroutine creation is abstracted from here, that's a personal preference, you could go either way

### One last thing

We need to identify the target service and user from the request, say through cookies
I'm gonna update my route and handler to accept these two path params

```go
http.HandleFunc("/ws/{svc}/{user}/", HandleWs)
```

```go
service, _ := r.Cookie("service")
user, _ := r.Cookie("user")
log.Printf("service: %s, user: %s", service.Value, user.Value)
...
stream.RecvClientMessages(conn, broker, service.Value, user.Value)
stream.RecvServiceMessages(conn, broker, service.Value, user.Value)
```

Now let's update our stream functions to accept these, and use them in their corresponding pubsub subjects

```go
func RecvServiceMessages(conn *websocket.Conn, broker brokers.Broker, service string, user string){
  ...
  go broker.Consume(fmt.Sprintf("ws.recv.%s.%s", service, user), ch)
  ...
}
```

```go
func RecvClientMessages (conn *websocket.Conn, broker brokers.Broker, service string, user string){
  ...
  broker.Produce(fmt.Sprintf("ws.send.%s.%s", service, user), message)
}
```

```go
stream.RecvClientMessages(conn, broker, service, user)
stream.RecvServiceMessages(conn, broker, service, user)
```

---

### Let's see it in action

Server logs

```bash
(base) websocketstream git:main ❯ go run cmd/main.go                                                 ⏎ ✹
2025/01/06 01:58:02 listening on port: 8000
2025/01/06 01:58:14 Client connected
2025/01/06 01:58:14 service: service1, user: user001
2025/01/06 01:58:17 received message from client: clientsendingmessage1

2025/01/06 01:58:17 producing to: ws.send.service1.user001
2025/01/06 01:58:24 received message from client: clientsendingmessage2

2025/01/06 01:58:24 producing to: ws.send.service1.user001
2025/01/06 01:58:42 Received message: [115 101 114 118 101 114 115 101 110 100 105 110 103 109 101 115 115 97 103 101 49]
2025/01/06 01:58:44 Received message: [115 101 114 118 101 114 115 101 110 100 105 110 103 109 101 115 115 97 103 101 50]
2025/01/06 01:58:53 Received message: [121 97 121]
2025/01/06 01:59:01 received message from client: yay

2025/01/06 01:59:01 producing to: ws.send.service1.user001
```

Websocket client

```bash
(base) ~ ❯ websocat ws://localhost:8000/ws/notification/user001/ -H 'Cookie: user=user001;service=service1'
clientsendingmessage1
clientsendingmessage2
serversendingmessage1
serversendingmessage2
yay
yay
```

Service sending messages

```bash
(base) ~ ❯ nats pub ws.recv.service1.user001 serversendingmessage1
01:58:42 Published 21 bytes to "ws.recv.service1.user001"
(base) ~ ❯ nats pub ws.recv.service1.user001 serversendingmessage2
01:58:44 Published 21 bytes to "ws.recv.service1.user001"
(base) ~ ❯ nats pub ws.recv.service1.user001 yay
01:58:53 Published 3 bytes to "ws.recv.service1.user001"
```

Service receiving messages

```bash
(base) ~ ❯ nats sub "ws.send.service1.>"                                                               ⏎
01:58:10 Subscribing on ws.send.service1.>
[#1] Received on "ws.send.service1.user001" with reply "_INBOX.K35i42q5yDFnMzZcaoO6aO.X9GVnakO"
clientsendingmessage1

[#2] Received on "ws.send.service1.user001" with reply "_INBOX.K35i42q5yDFnMzZcaoO6aO.oV4fBGgX"
clientsendingmessage2

[#3] Received on "ws.send.service1.user001" with reply "_INBOX.K35i42q5yDFnMzZcaoO6aO.io2js6cd"
yay
```

---

That's it! 

You now have a scalable websocket broker, you can always try it out by installing it like so...

```bash
(base) ~ ❯ go install github.com/ashupednekar/websocketstream/cmd@latest                               ⏎
(base) ~ ❯ which cmd
/Users/ashutoshpednekar/go/bin/cmd
(base) ~ ❯ mv /Users/ashutoshpednekar/go/bin/cmd /Users/ashutoshpednekar/go/bin/websocketstream
(base) ~ ❯ websocketstream
2025/01/06 02:06:26 listening on port: 8000
```

Thank you :) Any broker support PR's are welcome. Please star the repo on [github](https://github.com/ashupednekar/websocketstream) 

😄
