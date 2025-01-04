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

## Let's draw it out

Here's an excalidraw scrsht illustrating the approach

![websocketstream](https://github.com/user-attachments/assets/9636579c-4598-4514-9ce6-4d3f93327703)

