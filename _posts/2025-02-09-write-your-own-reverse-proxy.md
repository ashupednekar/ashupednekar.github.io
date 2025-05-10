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

Hope this puts things into perspective :)

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

Here's what we got. We have two upstream servers, one is a `fastapi` server listening at port `3000` with two endpoints `/one` and `/`

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/one")
def get_one():
    return {"message": "one"}

@app.get("/")
def get_root():
    return {"message": "two"}
```

And one TCP echo server listening at 4000

```go
package main

import (
	"bufio"
	"fmt"
	"net"
)

func handleConnection(conn net.Conn) {
	defer conn.Close()
	addr := conn.RemoteAddr().String()
	fmt.Println("Connected to:", addr)

	scanner := bufio.NewScanner(conn)
	for scanner.Scan() {
		text := scanner.Text()
		fmt.Printf("Received from %s: %s\n", addr, text)
		// Echo back
		fmt.Fprintf(conn, "Echo: %s\n", text)
	}
	fmt.Println("Disconnected:", addr)
}

func main() {
	listener, err := net.Listen("tcp", ":4000")
	if err != nil {
		panic(err)
	}
	defer listener.Close()
	fmt.Println("Listening on :4000")

	for {
		conn, err := listener.Accept()
		if err != nil {
			fmt.Println("Failed to accept:", err)
			continue
		}
		go handleConnection(conn) // handle each connection in a new goroutine
	}
}
```

*Don't worry if you miss aspects of this code, just illustrations*

Now, we want our clients to be able to reach the targets like so
- `/one` at port `5000` to reach the fastapi server at `3000`
- `/two` at port `5000` to reach the fastapi server at `3000` with path `/`
- tcp traffic at port `4001` to reach the go echo server running at `4000`

*English does make for a simple config language ;) Maybe we'll get there with AI someday... who knows*

But for now, we need to deal with these, take a look

#### nginx
```nginx
# Listen on 5000 for HTTP routes
server {
    listen 5000;

    location /one {
        proxy_pass http://localhost:3000;
    }

    location /two {
        rewrite ^/two(/.*)$ $1 break;
        proxy_pass http://localhost:3000;
    }
}

# TCP stream block (requires stream module)
# Put this in nginx.conf under the `stream` context
stream {
    server {
        listen 4001;
        proxy_pass localhost:4000;
    }
}
```

#### httpd
```
# HTTP VirtualHost on port 5000
<VirtualHost *:5000>
    ProxyPreserveHost On
    ProxyPass "/one" "http://localhost:3000/one"
    ProxyPassReverse "/one" "http://localhost:3000/one"

    RewriteEngine On
    RewriteRule ^/two(/.*)?$ $1 [PT]
    ProxyPass "/two" "http://localhost:3000/"
    ProxyPassReverse "/two" "http://localhost:3000/"
</VirtualHost>

# TCP proxying (requires mod_proxy_connect or reverse proxy setup outside Apache; usually not done with HTTPD)
# Recommendation: use NGINX or HAProxy for TCP proxying
```

#### kubernetes ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: two-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - http:
      paths:
      - path: /two
        pathType: Prefix
        backend:
          service:
            name: your-service
            port:
              number: 3000
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: one-ingress
spec:
  rules:
  - http:
      paths:
      - path: /one
        pathType: Prefix
        backend:
          service:
            name: your-service
            port:
              number: 3000
# In kubernetes, you would usually expose tcp through loadbalancer service, not ingress
```

Here are a few insights about these
- nginx conf/ httpd groups paths under same virtualhost together
- ingress lets you have individual files for your routes where you specify the hosts instead

The kubernetes way may seem verbose with this simple example, but trust me in real life, it's a lot easier to work with rather than having gigantic host conf files, so we're going with that.

But there are niceties to having your paths grouped together, so we're gonna support that too

This is the configuration I've come up with

```yaml
name: one-ingress
spec:
  - kind: http
    path: /one
    listen: 5000
    targets:
    - host: localhost
      port: 3000
tls: 
  enabled: false
```

```yaml
name: two-ingress
spec:
  - kind: http
    path: /two
    rewrite: /
    listen: 5000 
    targets:
    - host: localhost
      port: 3000
tls: 
  enabled: false
```

```yaml
name: tcptest-ingress
spec:
  - kind: tcp
    listen: 4001 
    targets: 
     - host: localhost
       port: 4000 
tls:
  enabled: false
```

Best of both worlds, no? That's what you get to do when you build things from first principles. 

Of course, standards matter too, if you were to use `liteginx` in real life, which you probably shouldn't... I wouldn't expect you to learn yet another markup language ;) pun intended, we'll probably build an ingress controller or something which maps the standard kuberenetes ingresss, or the newer gateway API spec to this config. Again, a topic for another time

### Loader

Let's write the loader for reading these specs into structures our code can work with. I'll have snippets here and there, but if want to look at properly in your editor of choice, go ahead and clone the [repo](https://github.com/ashupednekar/liteginx) 


#### read conf dir to load ingress conf spec
First, we need to look at our conf dir, and load each file into memory

```rust
Ok(fs::read_dir(&settings.liteginx_conf_dir)?
.filter_map(|entry| entry.ok())
.filter(|entry| entry.path().extension().map_or(false, |ext| ext == "yaml"))
.filter_map(|yaml_path| fs::read_to_string(yaml_path.path()).ok())
.filter_map(|yaml| serde_yaml::from_str::<IngressConf>(&yaml).ok())
.collect())
```

Functional code may or may not be your things, here's what this does
- read files in the conf dir, say `~/.config/liteginx`
- iterate through these and ignore any file that's not yaml
- read these to strings
- use the amazing `serde` library to deserialize these into a list of `IngressConf` struct.

This is what each of these will represent
```rust
#[derive(Debug, Deserialize)]
pub enum Kind {
    #[serde(alias = "http")]
    Http,
    #[serde(alias = "tcp")]
    Tcp,
}

#[derive(Debug, Deserialize)]
pub struct IngressSpec {
    pub kind: Kind,
    pub path: Option<String>,
    pub listen: u16,
    pub rewrite: Option<String>,
    pub targets: Vec<UpstreamTarget>,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub struct TlsConf {
    pub enabled: bool,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub struct IngressConf {
    pub name: String,
    pub spec: Vec<IngressSpec>,
    pub tls: TlsConf,
}
```

This is just an expression of the yaml we wrote earlier into rust's beautiful sum types ;)

#### transform into routes/targets/endpoints for use to work with later

This one's a little tricky. I'll paste the function, we'll break it down chunk by chunk

```rust
pub fn new(configs: Vec<IngressConf>) -> Result<Vec<Arc<Route>>> {
    let paths: HashMap<u16, (Option<Router<Endpoint>>, Vec<UpstreamTarget>)> = configs
        .iter()
        .flat_map(|conf| {
            tracing::debug!("loading conf: {:?}", &conf.name);
            conf.spec.iter()
        })
        .fold(HashMap::new(), |mut paths, spec| {
            tracing::debug!("adding listener spec: {:?}", &spec);
            let entry = paths
                .entry(spec.listen)
                .or_insert_with(|| (None, spec.targets.clone()));
            if let Kind::Http = spec.kind {
                let router = entry.0.get_or_insert_with(Router::new);
                let path = spec
                    .path
                    .clone()
                    .expect("http spec missing mandatory field path".into());
                if router.at(&path).is_ok() {
                    tracing::warn!("{} conflicts with existing endpoint", &path);
                    return paths;
                }

                let rewrite = spec.rewrite.clone();
                if let Err(err) = router.insert(path.clone(), Endpoint { path, rewrite }) {
                    tracing::error!("Failed to insert: {}", err);
                    return paths;
                }
            }
            spec.targets.iter().for_each(|target| {
                if !entry.1.contains(target) {
                    entry.1.push(target.clone());
                }
            });
            paths
        });
    let routes = paths
        .into_iter()
        .map(|(listen, (endpoints, targets))| Route {
            listen,
            endpoints,
            targets,
            ..Default::default()
        })
        .map(Arc::new)
        .collect();
    Ok(routes)
}
```

#### Functional primer

Don't let the folds and maps scare you, they are just succinct, or honestly... fancy ways to write a for loop. Will do a deep dive on those in the furure, but here's the gist

- iterators are something that lets us go through, say a list.. while thinking about each element one at a time
- you don't have to worry about the `i` variable
- `map` runs a given closure (anonymous functions) over each element
- `filter_map` runs a given closure and only includes the elements matching the given condition
- `flat_map` say you have two lists, normaly you would have to go through them seperately and do an `append`/`extend` outside the loop.. it just flattens two iterators into one, you can think of it as concatenation
- `fold`
Okay.. so.. say you want to go through a list and create an entirely different list.. kinda like having global variables and pushing elements to it as you go through the elements when certain condition are met
- `collect` returns a `Vec` of a given type from an iterator

Here's what we are doing in this function
- We want a `HashMap` of the port to listen on and a tuple of endpoints and targets for each one. once we have this, we can start a tcp server for each element. A hashmap will also take care of, say if you have two different yamls with the same listen ports.. it'll bring them into the grouped conf like httpd/nginx cuz that's what we need in the end to start serving/routing our requests
- Iterate through a list of configs, remember `IngressConf` ?
- Flatten all the different files we read into a single list 
- If kind is http, we add insert it to a `matchit::Router`, essentially a map of paths to target. Any duplicate paths exist, we return with a warning
- A tcp path is a route where the endpoints list is empty, so we don't need this router business
- Once we have this hashmap, we collect it into a list of routes, which has information of the endpoints and upstream targets


### Epilougue

I don't think there's value in going through the actual code here, the blog's gotten pretty long... but here's the gist

- We defined a conf format
- Wrote a loader to read in the yaml files
```rust
Vec<IngressConf>
```
- Transformed list of yaml conf to a map of port to endpoint/target tuples
```rust
Vec<Routes>
```
- start tcp liseneres for each of these ports
- if the target is of http kind, we route to the right upstream, with path rewrites if needed
- each of these listeners will handle connection streams, and for each new connection, we create client and target channels and pass them around for communication, look [here](https://github.com/ashupednekar/liteginx/tree/main/src/pkg/server/downstream.rs)
- the downstream servers are always running
- when it receives a connection, it's responsble for A. spawn upstream client and B. Send subsequent messages in the TCP stream to said upstream client, look [here](https://github.com/ashupednekar/liteginx/tree/main/src/pkg/server/upstream.rs)
- when client closes connection, it'll close the upstream connection
- if path rewrites are needed, it'll essentially just replace the path in the body per http protocol with the necessary path
- That's the gist

Here's a screenshot of `liteginx` in action

![image](https://github.com/user-attachments/assets/dbd3c029-bffd-4497-9c06-d910709b7ae6)

- We have two tcp clients, with `telnet`, connected at `4001`, routed to the `go` server running at `4000`
- And a have a few `curl` requests to `/one` and `/two` at `5000` being routed to `/one` and `/` at the `fastapi` server running at `3000`


> *If you want to get in the weeds, please go through the [liteginx repo](https://github.com/ashupednekar/liteginx) with your lsp. But this is the general idea*

> *If this interests you, and feel like contributing, or just any doubts, reach me on [threads](https://www.threads.com/@ashupednekar) or just raise an issue [here](https://github.com/ashupednekar/liteginx/issues)* 

> *If there's enough interest, I'd be happy to update this blog to get into the implementation details*

Thanks 😊
