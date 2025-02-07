## HTTP - intro

Buckle up, we're gonna dive into HTTP, the protocol that powers the internet. I'm not going to start with "HTTP stands for hyper tex..", we all learnt that as kids. As developers, we can understand it in a much simpler and relatable way.

## What's a protocol anyway?

Certain terms tend to intimidate folks, especially as junior engineers, and protocol is definitely one of them. Once you realize that all software is written by developers like you and me, things do get easier. So what is a protocol then?

Like the english word, a protocol is nothing but a set of rules that are agreed upon and followed by everyone. And network protocols can be simply be thought of as `PAYLOAD FORMATS`, that's it. Seriously, your openapi spec could be called a protocol if enough people use it! 😄 (S3, openai are a few examples...)

So what's so special about HTTP then? It's an application layer text based protocol that's designed for exchanging text and bytes over TCP. Let's get a quick refresher on the OSI model

## OSI model

If you come from CS, you've seen this diagram a thousand times already. But here we go again... If you're new to OSI, don't worry, we'll cover all you need to know right here

![OSI](https://www.indusface.com/wp-content/uploads/2023/09/OSI-Model-7-layers.png)

Found this really nice diagram that actually has really nice one liners with simple examples.

Here's what we need to know..

#### Layer 4

The transport layer keeps track of the end to end connections and does things like handshakes, acknowledgements and package redeliveries. Bottom line, it makes sure a packet that's sent reaches the other side. 

TCP and UDP are the two main protocols here, `HTTP/1.1` the one we're buildig here is built on top of TCP. The UDP protocol is meant for cases where a few packet drops wouldn't affect the user experience, say video streaming for example. Though nowadays our network infrastructure and error correction techniques have gotten so good, the web is eventually said to phase out TCP in favour of UDP(quic)... that's `HTTP/3`.

Anyway, as far as we are concerned, TCP lets us create servers that listen on a port, that clients can connect and send data over. Here's a quick demo using `nc` and `telnet`

```bash
(base) ~ ❯ nc -l -k 3000                                                                               ⏎
client sent message
server sent message
```

We started a server at port 3000


```bash
base) ~ ❯ telnet localhost 3000                                                                       ⏎
Trying ::1...
telnet: connect to address ::1: Connection refused
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
client sent message
server sent message
```

Telnet lets us connect to this server and send some bytes. Then, we sent some data from the server back to the client

That's TCP. It's pretty straightforward to implement this in most languages


#### Layer 7

The application layer is basically the end user logic that deals with the data to serve business logic, essentially.

Imagine a person sitting in front of a server looking at messages clients sent over TCP and replying, here's a `chatgpt` illustration

![image](https://github.com/user-attachments/assets/253d1802-cced-43ef-b4fb-689d3184dcdd)

What this guy is doing is the application layer. But it's not realistic to code this way, if clients were sending whatever they want. That's where HTTP comes in.

It defines a simple text format that's agreed upon, here's the [RFC for HTTP/1.1](https://datatracker.ietf.org/doc/html/rfc2616), so that we can have abstractions built on top of this that we can work with across languages. Libraries and frameworks to further abstract commonly used features, to make us more productive and less error prone to build apis or web services. The level of abstraction you want to have is a discussion for another day 😄

Let's take a look at HTTP in action like we did for TCP

## HTTP at it's simplest

Here, I'm starting a TCP server at port 3000

![server](https://github.com/user-attachments/assets/d861ead1-84fe-4624-9850-ba37b695f7b8)

Now, let's send a simple `POST` request with `cURL` that just sends an 8 byte string "hey jane", of type `text/plain`

![client](https://github.com/user-attachments/assets/f0b4ff2c-ee91-4491-b75b-b887ef047cbf)

On the server side I'm literally typing out the text format HTTP protocol, which curl then understands this and parses our headers and body accordingly.


## Let's look at the RFC


## Time to code it up


### Structure


### TCP Server


### Request Parser


### Response Builder


### Bring it together


### cURL it up


## Future work


## Conclusion





