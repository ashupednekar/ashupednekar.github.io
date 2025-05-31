## Let's build our own lambda faas

### Why?

As usual, as engineers, we build things out from scratch, in order to test our own understanding of something, and discover what we don't know.

As they say,
> "We did it not cuz it's easy, but cuz we thought it was"

### Background

This is part of the cloud services series I've been woring on recently. Here are a few other related blogs
- [Liteginx proxy](https://ashupednekar.github.io/posts/write-your-own-reverse-proxy/)
- [Lite Web Services](https://ashupednekar.github.io/)
- [Lite Containers](https://ashupednekar.github.io/)

### Intro

The idea here is to build something similar to `aws lambda` or gcp's `cloud functions`, or if I were to use buzz words, "Serverless" :)


#### So what is it?

`Serverless` functions are a way to give developers a way to build out microservices as individual functions, where all the infrastructure and setup is abstracted away in a nice interface where you can write functions in your language of choice, which would then magically become HTTP endpoints or pub/sub consumers. 

**Benefits**
- Approachable
- Can support everything u need as standard interfaces
- Pay as you go
- microservices without thinking much about it
- Easy/ automated deployment

**Downsides**
- Yet another abstraction
- You're tied to the provider's assumptions
- Hard to structure complex codebase scenarios
- Cold start problem

### What's out there... 

Most cloud providers provide function as a service solutions, and there are a few open source ones as well

Let's take a look at the most popular one, aws's "lambda"
![image](https://github.com/user-attachments/assets/b1c566cb-7ccb-4592-86da-6cbb35016e1e)

Here's the gist of what we it offers
- Uses cloudformation to provision resources
- Your endpoints sit behind an api gateway that takes care of things like rate limiting, authentication, etc
- each funciton is sort of a basket microservice which gets its own dynamo db 
- You can have your function be triggerered in response to an event coming to SQS through something called AES eventbridge/bus.. 

### Here's what we'll offer

here's what we typically need access to to build a modern web service
- A database, to store our user data and persistent state. A KV makes the most sense for faas, but we'll attempt to support relational as well
- Access to a pubsub system, we'll use nats. We do need to figure out how to abstract it away from the function code though
- API gateway, we'll use [liteginx](https://github.com/ashupednekar/liteginx) cuz that can spin up additional blogs for features we'd need like rate limiting, authentication, etc


