## Let's write our own faas

### Background

This is part of the cloud services series I've been woring on recently. Here are a few other related blogs
- [Liteginx proxy](https://ashupednekar.github.io/posts/write-your-own-reverse-proxy/)
- [Lite Web Services]()
- [Lite Containers]()

### Intro

The idea here is to build something similar to `aws lambda` or gcp's `cloud functions`, or if I were to use buzz words, "Serverless" :)

#### What it is
lets developers write http handlers without worrying about the underlying server

#### What it's not
not a wrapper over existing faas projects like openfaas, or cloud services


### The challenge

It's more of a developer experience thing, which lets users just worry about the business logic of the api, with pre configured access to pubsub, KV, DB, and object store

### Approach


