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


![current](https://assets.grok.com/users/56e197c1-b0e7-49e3-ae35-52eaf2b5def3/66ACNA8iFRpVVmul-generated_image.jpg)


### What should happen

If you look at most modern languages that come with green threads built in, either in the standard library (`go`) or through defacto default liraries (`rust`), they provide robust concurrency models

Each of these containers are single processes, that do take advantage of the available compute through a combination of os threads and green threads.

### So what are we building here?

I've posted recently digging through HTTP and building a basic web framework on top of it. Here's the [link](https://ashupednekar.github.io/posts/understand-and-implement-http/). At the end of this, we had a small web framework, that used tokio for concurrency to spin up green threads for each request. There's pyo3.. so why not put two and two together to bring that to python?

#### Previous attempts

One way would be to start a rust server that laods a shared mutex of route map to python functions, that can be invoked when the route is triggered. 

Here's a simple codebase I wrote some time back, called [axumapi](https://github.com/ashupednekar/axumapi). Yes, the end result is a fast, liteweight http framework, but it would take a lot of effort and time to make things like this feature complete.

There are projects like [robyn](https://robyn.tech/), which have gotten pretty far. 

But the problem with python developers in general is they are shielded from what's actually happening to such an extent, that they end up becoming very dependent on their framework of choice, and cannot even image using something else.

#### gunicorn alternatives

> Gunicorn is great, until it isn't. Why? cuz you don't know how it works

I can't emphasize enough how many times I've faced production outages due to weird edge cases due to some black box case happening in gunicorn, or uvicorn. 

There are other alternatives, here are a few one liner descriptions of the various worker models gunicorn provides 

**Faiw warning, these are very opinionated, if you don't agree with these, that's okay**

- gunicorn sync: runs prefork processes
> not useful in containers

- gunicorn gthread: uses python thread pool 
> good for syncronous wsgi frameworks like django ✅
> If you're in this camp, you are good until your rps requirements are low enough, or can scale compute vertically

- gunicorn gevent: uses gevent, the library that implements green threads to python
> the right apprach for containers, but needs code changes and monkey patching

- gunicorn uvicorn: uses uvicorn workers, which uses uvloop as the asyncio eventloop
> great for async frameworks like fastapi ✅
> If you are in this camp, you're good. Async starlette plus uvicorn is pretty good for most cloud native use cases

What we're gonna build is a simplified form of something called [granian](https://github.com/emmett-framework/granian), which provides a wsgi/asgi interface built in rust.

What makes this possible is something called the "web server gateway interface"

### So what's WSGI?

There was a need for a standard interfact so that different implementations of process managers and servers could work properly with all python web frameworks, say django, flask, fastapi, etc

![image](https://github.com/user-attachments/assets/939cd4ca-53ad-4ee7-858d-bf2a06be2457)


