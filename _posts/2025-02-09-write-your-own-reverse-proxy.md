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

Pointers..

- Tcp
- channels
- Proxy
- Attemps xD
- Config
- Loader
- Downstream/Upstream
- Tests
- Demo
- Improvements - minor features
- Benchmarks ? xD
- Future works


