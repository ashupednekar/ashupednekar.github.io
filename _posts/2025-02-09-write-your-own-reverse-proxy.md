## Not nginx, but all the nginx we need 😁

By the end of this blog post, we'll have ourselves a working reverse proxy that does the following
- TLS termination
- HTTP/TCP routing
- Rewrite rules

Thing we'll look at, maybe
- mTLS
- security

### Intro

A reverse proxy server is a server that sits in front of our applications, usually micro-services, and takes in external traffic, terminates SSL, and routes to the appropriate service. 

### Why "reverse"?

Again with the overly gatekeeping terminology(no pun intended)... As far as using nginx/envoy goes, there's nothing reverse about reverse proxies. It's called reverse because a "proxy" is usually at the outgoing end, taking care of say, IP anonymization, etc, and web servers being at the incoming end does reverse of that.

While we're at it, let's get all the other terms out of the way
- Ingress: Simply means incoming
- Egress: Means outgoing

![image](https://github.com/user-attachments/assets/eb340c72-db6b-4c52-bca2-0ce38a7bf925)

That's it. There are other nuances with gateways, services and ingress resources/ controllers when it comes to something like kubernetes, but generally, an ingress or a "web server", if you're working with legacy folks... just takes web traffic in before hitting our application services.

A really nice analogy, (thought of it when `chatgpt` generated this image xD) you can think of it as a gatekeeper or a security guard who'll give you a visitor tag and redirect you to the right floor


Let's start to code it up, by our typical pkg/cmd structure


```bash
├── Cargo.lock
├── Cargo.toml
└── src
    ├── cmd
    │   └── mod.rs
    ├── main.rs
    └── pkg
        └── mod.rs

5 directories, 7 files
```


### Configuration

Here's what we need to cover
- http and tcp routing
- path rewrites for http
- multiple virtualhosts or listen addreses

Let's keep the configuration simple. We can go about it two ways:
- Like nginx.conf, where keep all the locations blocks within a virtualhost together
- Or like ingresss resourses, where each route gets its own file

> This is very much like choosing between seperation of concern and locality of behaviour in code structuring. I'll go with the latter

We'll have a conf directory with individual conf file for hypothetical services covering each scenario

##### normal http proxy 

```yaml
name: one-ingress
spec:
  kind: http
  path: /one
  listen_port: 80
  routes:
  - target_host: localhost
    target_port: 3000
tls: 
  enabled: false
```
This is something off the top of my head, keed eyed among you must've noticed the obvious traits borrowed from the kubernetes ingress spec.

> Let's get back to the tls aspect at a later point, leaving that disabled for now

##### http proxy with rewrite

```yaml
name: two-ingress
spec:
  kind: http
  path: /two
  listen_port: 80
  routes:
  - target_host: localhost
    target_port: 3001
    rewrite: /
tls: 
  enabled: false
```

> Rewrite rules are meant to tweak the path to help with scenarious where you have clashing base paths, usually `/`. 

For example, say I want to host argo-cd at `/argo` but the appplication itself is accepting connections at `/`. You still need to take care of redirections at to make sure it includes the prefix.

##### tcp proxy

```yaml
name: redis-ingress
spec:
  kind: tcp
  listen_port: 6379
  routes: 
   - target_host: localhost
     target_port: 6379
tls:
  enabled: false
```

This is when you want to route raw `TCP` connections at a different port, e.g. Say if you're providing redis as a service, for example

Let's now go about representing this more concretely, starting with a `conf/spec.rs` under pkg

```bash
└── pkg
    ├── conf
    │   ├── mod.rs
    │   └── spec.rs
```

Let's start with our main `Config` struct

```rust
#[derive(Deserialize, Clone)]
pub struct Config{
    pub name: String,
    pub spec: Spec,
    pub tls: Tls
}
```
I'll defer the tls stuff for later, here's a simple struct for now

```rust
#[derive(Deserialize, Clone)]
pub struct Tls{
    pub enabled: bool
}

```

The spec could vary based on whether it's an http or a raw tcp route. Here's the enum

```rust
#[derive(Deserialize, Clone)]
pub enum Spec{
    Http(Http),
    Tcp(Tcp)
}
```

Let's start with the TCP route, cuz it's simple with just a port, along with kind

```rust
#[derive(Deserialize, Clone)]
pub struct Tcp{
    #[serde(default = "default_tcp_kind")]
    pub kind: String,
    pub port: i32
}
```

The kind for a Tcp spec variant should have kind being "tcp"

```rust
fn default_tcp_kind() -> String {
    "tcp".to_string()
}
```

Now let's go with Http

Apart from the http route, we need two things, the destingation route host/port and the host/port our server should listen at to accept ingress traffic

```rust
#[derive(Deserialize, Clone)]
pub struct HttpRoute{
    pub host: String,
    pub port: i32,
    pub rewrite: Option<String>
}

#[derive(Deserialize, Clone)]
pub struct VirtualHost{
    pub host: String,
    pub port: i32
}

#[derive(Deserialize, Clone)]
pub struct Http{
    #[serde(default = "default_http_kind")]
    pub kind: String,
    pub path: String,
    pub listen: VirtualHost,
    pub route: HttpRoute
}
```

Again, we have a default function for the kind attribute

```rust
fn default_tcp_kind() -> String {
    "tcp".to_string()
}
```

When deserializing from yaml, we want to get the `Http` or the `Tcp` variants based on the kind value, and check the rest of the validations subsequently

We'll need to add a custom deserializer for the spec attribute

```rust
#[derive(Deserialize, Clone)]
pub struct Config{
    pub name: String,
    #[serde(deserialize_with = "deserialize_spec")]
    pub spec: Spec,
    pub tls: Tls
}


fn deserialize_spec<'de, D>(deserializer: D) -> Result<Spec, D::Error>
where
    D: Deserializer<'de>,
{
    let v: Value = Deserialize::deserialize(deserializer)?;
    if let Some(kind) = v.get("kind").and_then(|k| k.as_str()) {
        match kind {
            "http" => Ok(Spec::Http(serde_yaml::from_value(v).map_err(D::Error::custom)?)),
            "tcp" => Ok(Spec::Tcp(serde_yaml::from_value(v).map_err(D::Error::custom)?)),
            _ => Err(D::Error::custom("Unknown kind")),
        }
    } else {
        Err(D::Error::custom("Missing `kind` field"))
    }
}
```

Apart from the generic decor, this function's pretty straightforward. We return the appropriate variants baseed of the `kind` value and triggering `serde_yaml` deserialization for the serde `Value` subset of your yaml

> If you think this was a lot, don't worry... it was. representing data with proper types can be tricky

#### Server

Before we proceed to roll out our tcp server, let's first plan our application state

##### Loader

We're going to walk through a conf directory, and load yaml manifests into a data structure that we can refer throughout, once we're done with this, we should have our server struct equipped with all the configuration it'll need to do the reverse proxying

Cool, so we're gonna mainly need two things, our http routes and tcp routes. The former being a simple port to port mapping to route traffic. 

For Http routes we're going to use the `Router` map from the `matchit` crate, like we did in our http implementation. It's an optimized map designed to store generic types against hashed strings. It's used by popular frameworks like axum/actix for their routing as well

```rust
struct Server{
  tcp_routes: HashMap<i32, Vec<TcpRoute>>,
  http_routes: HashMap<i32, Router<Vec<HttpRoute>>>,
}
```

Let's go through why I chose this data structure here

So, for tcp routes, what the proxy is going to essentially do is listen at ports, and route raw TCP traffic to the list specified `TcpRoute`, which is essentially just the host and the port of the target service. The reason this is a Vector is for load balancing, we'll come to that right after this. 

Similarly, for http routes, similar to nginx or httpd virtualhosts, we'll have multiple server threads listening at each listen ports, and then route all the http requests forward. Time to implement the loader. Again, the `Vec` is for load balancing. 

> The examples above have a single entry for routes, we're gonna look at load balancing later


Let's now start implementing our `new` function to instantiate our `Server`, and load the routing configuration by walking our manifests directory


```rust
impl Server {
    fn new() -> State {
        State {
            tcp_routes: HashMap::new(),
            http_routes: Router::new(),
        }
    }

  fn new() -> Result<Server> {
      let config_path =
          env::var("LITEGINX_CONF_DIR").unwrap_or(format!("{}/.config/liteginx", env!("HOME")));
      let configs: Vec<Config> = fs::read_dir(&config_path)?
          .filter_map(|entry| entry.ok())
          .filter(|entry| entry.path().extension().map_or(false, |ext| ext == "yaml"))
          .filter_map(|yaml_path| fs::read_to_string(yaml_path.path()).ok())
          .filter_map(|yaml| serde_yaml::from_str::<Config>(&yaml).ok())
          .collect();

      let mut state = Server{
          tcp_routes: HashMap::new(),
          http_routes: HashMap::new(),
      }
;
      for config in configs{
          match config.spec{
              Spec::Http(spec) => {
                  state
                      .http_routes
                      .entry(spec.listen.port)
                      .or_insert_with(Router::new)
                      .insert(spec.path, spec.routes)?;
              },
              Spec::Tcp(spec) => {
                  state
                      .tcp_routes
                      .entry(spec.listen_port)
                      .or_insert(spec.routes);
              }
          }
      }
      Ok(state)
  }
```

I was planning on going crazy with the iterator functions with folds and everything, but it honestly got too hard to look at, but I can't go full procedural either 🙃. So this is what I wrote 

Let's go through it.. Here's what's heppening, in order
- get config path from env, or default to unix path
- get the `Vec<Config>` from the `Readdir` iterator like so:
  - setup our config path. We're gonna look for an env, or default to the `unix` style `$HOME/.config/liteginx`
  - make sure we only look at `yaml` files, ignore others
  - read each file and deserialize them to our `Config` struct
  - Populate them in our `Server` struct based whether on the `config.spec` variants, be http or tcp. Creates a map of port to vec of tcproutes and a map of port to matchit router respectively


### Routing

We'll need multiple servers, listening at each `listen_port` in our loaded route config. How do we go about doing that? 

Let's first create the scaffolding for starting and managing tcp servers, let's start by creating a `tcp.rs` module under `/server`




