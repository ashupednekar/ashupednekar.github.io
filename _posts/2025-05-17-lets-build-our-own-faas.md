## Let's write our own faas

### Background

This is part of the cloud services series I've been woring on recently. Here are a few other related blogs
- [Liteginx proxy](https://ashupednekar.github.io/posts/write-your-own-reverse-proxy/)
- [Lite Web Services](https://ashupednekar.github.io/)
- [Lite Containers](https://ashupednekar.github.io/)

### Intro

The idea here is to build something similar to `aws lambda` or gcp's `cloud functions`, or if I were to use buzz words, "Serverless" :)

#### What it is
lets developers write http handlers without worrying about the underlying server

#### What it's not
not a wrapper over existing faas projects like openfaas, or cloud services


### The challenge

It's more of a developer experience thing, which lets users just worry about the business logic of the api, with pre configured access to pubsub, KV, DB, and object store

### Approach

The thing about building frameworks or "magic" tools is the freedom to make certain decisions about how we'd do things

#### What we need
- Support for popular programing languages, both static and dynamic
- Users can create functions under projects
- Dependency management per project for dynamic languages
- Support for fixtures and tests per function
- Endpoints with basic load balancing and rate limiting


**Here's what we're gonna do**

![image](https://github.com/user-attachments/assets/0288ca95-83cd-42d0-afa5-e9a1eeb70fa9)

A simple way to put what we're trying to build is a cross language API framework

#### Why NATS?

We could've just started HTTP servers for each of these, sounds simple right? Well... it should be, but some of these languages, especially python would be much harder to work with that way.

Taka a look at [this blog](https://ashupednekar.github.io/posts/lets-solve-the-gunicorn-problem/)

These dynamic languages maybe slow when it comes to handling http requests, especially in a single process, but they do come with the ability to be embeddable. 

Since we are using nats to take care of request reply for us, we don't need http servers for the function runtimes, we could have a rust consumer listening at `reply.>` and start the relevant subscribers. We're gonna embed a python interpretor to call the actual function handlers, same for javascript and lua.

For static langs, we'll just start these processes individually instead of pre-heating a shared runtime








