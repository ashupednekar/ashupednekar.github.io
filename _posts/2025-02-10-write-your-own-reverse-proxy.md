## Not nginx, but all the nginx we need 😁

By the end of this blog post, we'll have ourselves a working reverse proxy that does the following
- TLS termination
- HTTP/TCP routing
- Rewrite rules

### Intro

A reverse proxy server is a server that sits in front of our applications, usually micro-services, and takes in external traffic, terminates SSL, and routes to the appropriate service. 

### Why "reverse"?

Again with the overly gatekeeping terminology... As far as using nginx/envoy goes, there's nothing reverse about reverse proxies. It's called reverse because a "proxy" is usually at the outgoing end, taking care of say, IP anonymization, etc, and web servers being at the incoming end does reverse of that.

While we're at it, let's get all the other terms out of the way
- Ingress: Simply means incoming
- Egress: Means outgoing

![image](https://github.com/user-attachments/assets/eb340c72-db6b-4c52-bca2-0ce38a7bf925)

That's it. There are other nuances with gateways, services and ingress resources/ controllers when it comes to something like kubernetes, but generally, an ingress or a "web server", if you're working with legacy folks... just takes web traffic in before hitting our application services.

