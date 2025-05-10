## Not nginx, but all the nginx we need 😁

By the end of this blog post, we'll have ourselves a working reverse proxy that does the following
- HTTP/TCP routing
- Rewrite rules

Things we'll look at, in subsequent blogs
- tls termination
- service discovery
- rate limiting
- lua/wasm snippets
- metrics

### Intro

A reverse proxy server is a server that sits in front of our applications, usually micro-services, and takes in external traffic, terminates SSL, and routes to the appropriate service. 

Hmm, now that the textbook definition is out of the way, let's take a step back and talk.

> So why are we doing this?

There are a gajillion proxies available out there, from nginx, envoy, traefik, haproxy etc. Here's a quick disclaimer on what this blog is not
- This is not a nginx replacement, not meant for production use
- This is not an imitation of nginx or any other implementations

If you've seen my previous blogs, you'd know. We're here to address interesting problems from first principles and get the required functionality working, while trying to be good citizens and build things properly 

### Let's get all the terms out of the way - so why "reverse"?

Again with the overly gatekeeping terminology(no pun intended)... As far as using nginx/envoy goes, there's nothing reverse about reverse proxies. It's called reverse because a "proxy" is usually at the outgoing end, taking care of say, IP anonymization, etc, and web servers being at the incoming end does reverse of that.

While we're at it, let's get all the other terms out of the way

<div style="display: flex; align-items: center; gap: 20px;">

<div style="flex: 1;">
  <ul>
    <li><strong>Ingress:</strong> Simply means incoming</li>
    <li><strong>Egress:</strong> Means outgoing</li>
  </ul>
</div>

<div style="flex: 1;">
  <img src="https://github.com/user-attachments/assets/eb340c72-db6b-4c52-bca2-0ce38a7bf925" alt="Image" width="100%">
</div>

</div>


That's it. There are other nuances with gateways, services and ingress resources/ controllers when it comes to something like kubernetes, but generally, an ingress or a "web server", if you're working with legacy folks... just takes web traffic in before hitting our application services.

A really nice analogy, (thought of it when `chatgpt` generated this image xD) you can think of it as a gatekeeper or a security guard who'll give you a visitor tag and redirect you to the right floor

### So what does it take?
You must have worked with web servers in the past, whether it's using http based frameworks like axum, gin or fastapi, or raw dogging the protocol yourself. Under the hood, we're working with TCP connections. 

If not, refer [this blog](https://ashupednekar.github.io/posts/understand-and-implement-http/) for an intuitive understanding. Most proxies nowadays also support UDP, and with quic, most of the internet is moving on from TCP, but that's a topic for another day

First, let's get past the term - "proxy".  What does it mean, in real life? Here are a few examples,

- If your school had an attendance requirement, you must've had your friends be a "proxy" once or twice to log your attendance for you a few times ;)
- Or when a kid acts as a proxy between fighting parents

Here's a loose definition: 

**A proxy is something that acts as in interface/messenger between two parties that cannot directly reach each other** 

That's what our ingress controller in kubernetes, or a web server for legacy folks... is doing. External clients cannot access the services running on the node, cuz opening ports outside would be stupid security wise, so the reverse proxy takes in all this traffic and passes it along as needed 

Now an added benefit of having this entrypoint, is we can implement a lot of stuff, especially security related here, in one place so that our appliations are unburdened from the implementation details and discrepencies. Rate limiting, external auth, TLS termination are among the many things these proxies do for us, you can even add lua snippets to do custom stuff. 

*This blog will target getting a working proxy for TCP streams and HTTP endpoints, with support for path rewrites and basic load balancing. I'll get to the other features in subsequent blogs*

## Channels primer

Cool, so what's making this possible are `channels`. Here's a quick primer on what these are

Modern programming languages/ eco-systems come built in with some primitives for dealing with concurrency. When you have a bunch of, let's call them threads doing various things, we need them to be aware of each other for control, and message passing. I'll post a blog post detailing the various approaches across programming languages (at some point 🤞), I'll have chatgpt illustrate it for now

![image](https://github.com/user-attachments/assets/3c8f98a9-9b53-4479-b318-736075284ac6)

You can of course look at the plethora of resources out there on go channels and tokio. Here's a one liner

**A channel is like a message queue that lets coroutines communicate. You pass these around, and coroutines can either write or read from them, sorta like pubsub with something like nats or kafka, but in memory**


### Approach

This is one of those things that fit the meme, *"I didn't do this because it's easy, but cuz I thought it was xD"* 

Trust me, I spent a lot more time on this than I should've. We'll first cover the actual approach I ended up following, I'll try to address a few mistakes I did as well, cuz that's an important part of learning

Cool, let's begin

So we need something that will listen for connections from clients who want to talk to services running on our server, and pass them along and vice versa.

#### Few terms

*These terms may seem obvious, cuz they are. Just need these to be clear*

**Downstream**

Our proxy lies in between the two parties we talked about. A downstream client is something that wants to establish a TCP/HTTP connection with our upstream services

**Upstream**

Services running upstream that our proxy needs to route traffic to, the ones actually running the application code 

#### Spec

Before we can start serving, we need to define few routing specs, Here we go

```rust
use matchit::Router;
use serde::Deserialize;
use tokio::sync::mpsc::{Receiver, Sender};

#[allow(dead_code)]
#[derive(Debug, Clone, Deserialize)]
pub struct Endpoint {
    pub path: String,
    pub rewrite: Option<String>,
}

#[derive(Debug, Deserialize, Default, Clone)]
pub struct UpstreamTarget {
    pub host: String,
    pub port: u16,
}

impl PartialEq for UpstreamTarget {
    fn eq(&self, other: &Self) -> bool {
        self.host == other.host && self.port == other.port
    }
}

#[derive(Debug, Default)]
pub struct Route {
    pub listen: u16,
    pub endpoints: Option<Router<Endpoint>>,
    pub targets: Vec<UpstreamTarget>,
}

pub type SenderCh = Sender<Vec<u8>>;
pub type ReceiverCh = Receiver<Vec<u8>>;
```

Let's break it down

**Route**
This is what our proxy server will iterat through and start TCP servers for. Each of these are keeping track of the following
- Downstream port to listen on, this is what our tcp listener will bind to
- Upstream targets, List of destination servers, i.e. targets
- Endpoints, this is what will tell us whether it's a raw TCP connections, or are there HTTP paths we need to work with

**UpstreamTarget**
- Keeps track of the host/port address of the upstream target

**Endpoint**
- Keeps track of the Http details like path rewrites

*Ignore the Router for now, we'll get to it. Sender/Receiver are just aliases for the two ends of our channels that carry byte data*

#### Bird's eye view

Here's a diagram illustrating the responsibilities of each component

![image](https://github.com/user-attachments/assets/b3b532e8-1cdb-4141-bcc0-08125f328ab4)

> *Traits in rust are interface specs that dictate certain functionality on structs that implement them*

Our downstream servers are responsible to
- Maintain servers listening at downstream ports
- When a new client connects, match it with a random(for now), upstream target and maintain TCP connection with it
- listen to it's channel's receiver and send received messages downstream. We'll call this channel `route` or `client` going forward
- send messages received from downstream clients to target channels, for upstream servers to pick up

And Upstream listeners
- Maintain TCP connections with upstream targets
- listen to target channel receiver and send received messages upstream
- send messages received from upstream to client channels, for downstream servers to pick up

### Configuration

There's quite a few things we need to know about our target servers and clients before we can serve as a proxy. This is one of the most daunting aspects of operations as a tiny key value in some ingress annotation or modsec config can make or break production. 

Let's take a look at a few example configurations out there before we come up with our own. You can skip this if you've already dealt with those at work. If not, this is crucial to appreciate the subsequent sections

#### nginx

#### httpd

#### ingress


- Config
- Loader
- Tests
- Demo
- Improvements - minor features
- Benchmarks ? xD
- Future works


