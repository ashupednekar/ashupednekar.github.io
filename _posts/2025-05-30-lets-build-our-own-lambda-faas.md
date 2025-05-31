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

#### What's out there... 

Most cloud providers provide function as a service solutions, and there are a few open source ones as well

Let's take a look at the most popular one, aws's "lambda"


