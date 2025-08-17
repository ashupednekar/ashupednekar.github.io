### Preface
Alright, let's do this. In this article, I'm gonna walk through what's packaging, how it was done in the past, and eventually land at the mess we've created for ourselves recently 🙃 

What tools like helm does is help us sort out this mess/ or mesh, if you will... and give users or fellow devs a decent experience

### Traditional packaging

So software was traditionally shipped as executable binaries, be it `exe`s on windows you installed as a kid, or the elf binaries you `chmod +x` and move to `'/usr/local/bin` once you got cool 😎, they are all the same, with certain exceptions. 

#### Wasn't all sunshines and roses though..
<div style="display: flex; align-items: center;">
  <div style="flex: 1; padding-right: 1rem;">
    <p>
      There are two kinds of binaries, generally... statically linked and dynamically linked.  
      We'll do another article digging through these, here's a meme to give you the general idea.
      And trust me, the difference shows up the moment you try running them on someone else’s machine, or containers
    </p>
    <blockquote>
      You'll see a lot of these repeating in our modern <code>cloud native</code> applications as well ;)
    </blockquote>
  </div>

  <div>
    <img 
      src="/assets/imgs/helmblog/one.png"
      alt="image" 
      width="200" 
      height="300"
    />
  </div>
</div>

Anyway, there's one more thing we need to address before we proceed

#### Dynamic Languages 🥲
Of course, this is not the only reason docker exists, as server applications/ microservices have a bunch of configuration/ networking complexity too, we'll get to that soon, just addressing a gripe on modern web dev here

A big reason containers even had to exist was the pain of distributing dynamic-language apps. With Python, Ruby, Node, etc., shipping an app meant shipping the right interpreter, the right version of pip/npm/gem packages, and matching system libraries. Suddenly, “works on my machine” became a universal curse. Tell me you haven't encountered this...

Here's how you would package typical services as docker images

<div style="display: flex; gap: 1rem;">
  <div style="flex: 1;">
    <h4>Go HTTP (scratch)</h4>
    <pre><code class="dockerfile">
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN go build -o server main.go

FROM scratch
COPY --from=builder /app/server /
EXPOSE 8080
ENTRYPOINT ["/server"]
    </code></pre>
  </div>
  <div style="flex: 1;">
    <h4>FastAPI (distroless)</h4>
    <pre><code class="dockerfile">
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM gcr.io/distroless/python3
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
EXPOSE 8000
CMD ["main:app"]
    </code></pre>
  </div>
</div>
> You'd usually use distroless for dynamically linked binaries as well, e.g. rust

If most things were self-contained static binaries, a simple scp would’ve been enough — no container runtime, no dependency wrangling, just drop the binary and run. Docker filled that gap by wrapping dynamic runtimes, dependencies, and system packages into a portable unit. 
Things like distroless or `slim` do help tone down the image sizes and security surface area, to make it feasible to run these services in the cloud

#### Deployment 

<div style="display: flex; align-items: center;">
  <div style="flex: 1; padding-right: 1rem;">
    <p>
      Based on the deployment targets, you would start off by creating a <code>deploy repo</code>, which will either house a bunch of <code>docker-compose.yaml</code>'s or if you are not trapped in a lefacy environment, a bunch of kubernetes resources that will then be hooked up to a <code>CD</code> tool that pulls in the desired state when you make changes
    </p>
  </div>

  <div>
    <img 
      src="/assets/imgs/helmblog/helmimg2.png"
      alt="image" 
      width="200" 
      height="300"
    />
  </div>
</div>

This is good enough, if you have a single deployment target, or if your applications don't need much in terms of external dependencies, e.g. if you are using cloud services like SQS, S3 etc

---

#### So why helm then?

As their site says... it's a package manager for microservices, similar to what `brew`, `yay` or `apt` are on the desktop. Let's build a scenario and do it without helm first, in order to appreciate what we're getting here

#### Scenario
### scenario set up
- db, kv, pubsub
- go services needing envs, each other and essentials



### superpowers - lib charts

### parent charts/ dependencies

### operator nuances

### conclusion

`
