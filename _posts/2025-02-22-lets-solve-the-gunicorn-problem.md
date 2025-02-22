### Preface

This blog post is targeted at backend developers who are already doing backend in python. If you're new to backend development, and are looking at python, first of all, `DON'T`. Please walk away to literally anything else. 

Python is an amazing language for dynamic linking `C` libraries to make it easy for science folks to work with data, ML and all that. But it doesn't really have any concurrency considerations to even be called an afterthought. If you don't want to do static languages, just go with javascript.

I've personally done python backend for half a decade, so this is coming from personal experience. 

But it's not all bad. As I said, python is great at abstracting over dll libraries. This solves things, especially recently thanks to amazing tooling to help build python abstractions with rust or zig

### Intro

Cool. So what's gunicorn? If your background is anything non python, be it node js or go, the idea of having to run a seperate server just to run your code on the server, apart from the actual reverse proxy web server may be alien to you, and that makes sense. Here's the problem servers like `gunicorn` or `uvicorn` solve

Web traffic, usually involves calling handler functions, or API business logic for each user request. These are independent processing or queries, so we need to be able to concurrently handle these requests.

Before containers and kubernetes, the way things usually worked is you would have a server, and you would run monolithic applications as linux services. These are processes running on the server. Since python doesn't have good threading model, the only way to actually achive concurrency was to have multiple worker processes. Think of it as having multiple pods in today's terms. Gunicorn does that. 

It supports various worker models, and spins up proceses and threads as per configuration, and route requests to these workers to achieve concurrency. In a way, `gunicorn/uvicorn` was way ahead of it's time. It's like having pod autoscaler, as a vague kubernetes analogy.

### What happens today (in python)

What we talked about so far was a totally valid approach, but thanks to microservices, most folks now have scaled to hundreds of microservice containers, which can be great. But then if you use the same process mangers that were designed for running on bare metal servers, things go crazy. 

If you have a uvicorn pod with 4 workers, that's just not right. Imagine your autoscaler in kubernetes detects that there's not enough resources, and scales by adding a replica.. Now you just blocked a gigabyte of memory for no reason. 

Here are a [blog post](https://dev.to/check/from-chaos-to-control-the-importance-of-tailored-autoscaling-in-kubernetes-2kpn?utm_source=chatgpt.com) going into more details on this one.

### What happens today (generally)

If you look at most modern languages that come with green threads built in, either in the standard library (`go`) or through defacto default liraries (`rust`), they provide robust concurrency models

