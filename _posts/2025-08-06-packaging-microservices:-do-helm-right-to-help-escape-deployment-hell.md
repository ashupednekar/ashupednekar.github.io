> **Note: NOT PUBLISHED**


## Preface
Alright, let's do this. In this article, I'm gonna walk through what's packaging, how it was done in the past, and eventually land at the mess we've created for ourselves recently 🙃 

What tools like helm does is help us sort out this mess/ or mesh, if you will... and give users or fellow devs a decent experience


## Traditional packaging

So software was traditionally shipped as executable binaries, be it `exe`s on windows you installed as a kid, or the elf binaries you `chmod +x` and move to `'/usr/local/bin` once you got cool 😎, they are all the same, with certain exceptions. 

### Wasn't all sunshines and roses though..
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

### Dynamic Languages 🥲
Of course, this is not the only reason docker exists, as server applications/ microservices have a bunch of configuration/ networking complexity too, we'll get to that soon, just addressing a gripe on modern web dev here

A big reason containers even had to exist was the pain of distributing dynamic-language apps. With Python, Ruby, Node, etc., shipping an app meant shipping the right interpreter, the right version of pip/npm/gem packages, and matching system libraries. Suddenly, “works on my machine” became a universal curse. Tell me you haven't encountered this...

Here's how you would package typical services as docker images

<div style="display: flex; align-items: center;">
  <div style="flex: 1; padding-right: 1rem;">
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
RUN pip install --prefix=/install \ 
  -r requirements.txt

FROM gcr.io/distroless/python3
WORKDIR /app
COPY --from=builder /install \
   /usr/local
COPY . .
EXPOSE 8000
CMD ["main:app"]
    </code></pre>
  </div>
</div>
> You'd usually use distroless for dynamically linked binaries as well, e.g. rust

If most things were self-contained static binaries, a simple scp would’ve been enough — no container runtime, no dependency wrangling, just drop the binary and run. Docker filled that gap by wrapping dynamic runtimes, dependencies, and system packages into a portable unit. 
Things like distroless or `slim` do help tone down the image sizes and security surface area, to make it feasible to run these services in the cloud

### Deployment 

<div style="display: flex; align-items: center;">
  <div style="flex: 1; padding-right: 1rem;">
    <p>
      Based on the deployment targets, you would start off by creating a <code>deploy repo</code>, which will either house a bunch of <code>docker-compose.yaml</code>'s or if you are not trapped in a lefacy environment, a bunch of kubernetes resources that will then be hooked up to a <code>CD</code> tool that pulls in the desired state when you make changes
    </p>
  </div>

  <div>
    <img 
      src="/assets/imgs/helmblog/two.png"
      alt="image" 
      width="200" 
      height="300"
    />
  </div>
</div>

This is good enough, if you have a single deployment target, or if your applications don't need much in terms of external dependencies, e.g. if you are using cloud services like SQS, S3 etc

---

### So why helm then?

As their site says... it's a package manager for microservices, similar to what `brew`, `yay` or `apt` are on the desktop. Let's build a scenario and do it without helm first, in order to appreciate what we're getting here

### Scenario

=======
<p>Cool, so let's take a typical SaaS situation where you'd need the following:</p>

<div style="display: flex; align-items: flex-start; gap: 2rem;">
  <!-- Functional Reqs -->
  <div style="flex: 1;">
    <h4>Functional reqs</h4>
    <ul>
      <li>email verification</li>
      <li>jwt authentication</li>
      <li>proxy level authentication</li>
      <li>profile pic update</li>
      <li>authorized users to manage products</li>
      <li>simple product catalogue</li>
      <li>user cart / orders</li>
      <li>scheduled notifications</li>
    </ul>
  </div>

  <!-- Non-Functional Reqs -->
  <div style="flex: 1;">
    <h4>Non functional reqs</h4>
    <ul>
      <li>cloud agnostic</li>
      <li>distributed DB shipped</li>
      <li>pub/sub broker shipped</li>
      <li>stateless applications</li>
      <li>proxy level auth / authz</li>
      <li>scalability</li>
      <li>encrypted secrets</li>
      <li>easy install</li>
    </ul>
  </div>

  <!-- Meme -->
  <div style="flex-shrink: 0;">
    <img 
      src="/assets/imgs/helmblog/three.png"
      alt="meme: let's overengineer this shit" 
      width="220"
    />
  </div>
</div>

> Okay, I'm getting ahead of myself 😅, let's not worry about the actual code, just the services and the setups

Here's what the architecture will look like
<img width="839" height="434" alt="image" src="/assets/imgs/helmblog/four.png" />

---

## Essentials

Let's get the essentials out of the way. Essentials are off the shelf services you would pick of `artifacthub` or `docker.io`, to run the core infrastructure of a cloud agnostic microservices system. You can skip this if you have the luxury to stick to a single cloud provider, as those would be served on a silver platter. But then again, if you are shipping something as an "installable", or as an open source project that others could run locally, you'd usually ship these as well

We'll get to how to include this in out shipped "package", in the next part. Right now, I'll show you what it's like on the other side,... to just install stuff :)

Here are the essentials we're going to pull

### Pubsub broker (nats) 

This is what the install section on [artifacthub](https://artifacthub.io/packages/helm/bitnami/nats?modal=install) says
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install nats bitnami/nats 
```
Cool right? but we do need to tweak a few things, like so

```
helm install nats bitnami/nats \
    --set jetstream.enabled=true \
    --set cluster.enabled=true \
    --set auth.enabled=false \
    --set replicaCount=3 \
    --set persistence.enabled=false
```

If this seems like a lot, try doing this with docker compose. It's well and good until it's a single container with some volume mounts and envs, trust me... gets a lot harder on real systems, unless you got something like this

> note: helm does accept a values.yaml, for those ready to jump to comments, didn't want to bring that up just yet


### Distribued database (Cruncy Postgres Operator)

```
helm install pgo oci://registry.developers.crunchydata.com/crunchydata/pgo
```

This ones a little weird, could be daunting, cuz there's both a helm install and a kubectl apply, out of the box. We'll see why and simplify this in our chart subsequently

```
kubectl apply -f -- <<EOF
apiVersion: postgres-operator.crunchydata.com/v1beta1
kind: PostgresCluster
metadata:
  name: db
spec:
  service:
    type: NodePort 
  instances:
  - dataVolumeClaimSpec:
      accessModes:
      - ReadWriteOnce
      resources:
        requests:
          storage: 5Gi
    name: postgres
    replicas: 3
  port: 5432
  postgresVersion: 16
  patroni:
    dynamicConfiguration:
      postgresql:
        parameters:
          max_connections: "500"
  proxy:
    pgBouncer:
      service:
        type: NodePort 
      port: 5432
      replicas: 2
EOF
```

> If you feel like it, go ahead and use a standalone postgres instead
> ```
> helm install postgresql bitnami/postgresql --version 16.7.26
> ```
> Refer [artifacthub](https://artifacthub.io/packages/helm/bitnami/postgresql?modal=install) for configuration options

### Object store

We need to upload our profile pictures, remember? Relational databases are not designed to store arbitrary files like this. That's where an object store comes in. Usually you'd just use AWS S3 or Google's GCS, but we're being cloud agnostic here, so I'm going with MinIO

```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install minio bitnami/minio --version
```

That's it, we're ready to code... We could always add more stuff like key value stores, vector databases, etc... but we don't need those for our use case

---

## Services

Each of out service will be a simple go service with minimal logic, only payload deserialization where needed

> If you are one of the I'm devops, I don't look at code folks, skip to the next section :)

Let's look at them one by one. We'll keep it simple yet reasonably structured, instead of cramming everything into a single `main.go`, keeping track of the external dependencies and config envs as we go

Here's the standard structure, with the conf, handlers, state and spec under `pkg`, and our binary's main under `cmd`

```bash
├── cmd
│   └── main.go
├── config.env
├── go.mod
├── go.sum
└── pkg
    ├── conf.go
    ├── handlers.go
    ├── spec.go
    └── state.go
```
#### Environment variables
> Don't worry, these are my local credentials and are rotated frequently

```env
LISTEN_PORT=3000
CONN_TIMEOUT=10
DATABASE_URL=postgresql://db:bjw9GPJ%5D2%5EM2Ynw;myNiny%7B%7C@localhost:31562/db
NATS_BROKER_URL=nats://localhost:30042
```

```go
type Settings struct{
	ListenPort int `env:"LISTEN_PORT"`
	ConnTimeout int `env:"CONN_TIMEOUT"`
	DatabaseUrl string `env:"DATABASE_URL"`
	NatsBrokerUrl string `env:"NATS_BROKER_URL"`
}
```

#### Dependencies
- Database, i.e. postgres
- Broker, i.e. nats - so that we can communicate with our notification service to send emails

```go
func NewState() (*AppState, error){
	ctx, done := context.WithTimeout(context.Background(), time.Millisecond*time.Duration(settings.ConnTimeout)) 
	defer done()
	dbPool, err := pgxpool.New(ctx, settings.DatabaseUrl)
	if err != nil{
		return nil, fmt.Errorf("DB connection failed: %v", err)
	}
	nc, err := nats.Connect(settings.NatsBrokerUrl)
	if err != nil{
		return nil, fmt.Errorf("Nats connection failed: %v", err)
	}
	js, err := jetstream.New(nc)
	if err != nil{
		return nil, fmt.Errorf("ERR-NATS-JS: %v", err)
	}
	streamConfig := jetstream.StreamConfig{
		Name: "messages",
		Subjects: []string{"msg.>"},
	}
	stream, err := js.CreateOrUpdateStream(ctx, streamConfig)
	return &AppState{DBPool: dbPool, Nc: nc, Stream: stream}, nil
}
```

#### Endpoints
The auth service will expose three endpoints, one lets our users create new session, and two internal endpoints we'd be using in our proxy auth for verifying said session

```go
	http.HandleFunc("POST /auth/login", NewSession)
	http.HandleFunc("POST /authn", Authenticate)
	http.HandleFunc("POST /authz", Authorize)
```

Similarly, our other services would host the necessary endpoint like so

**Products**
Simple CRUD on products

```go
  http.HandleFunc("POST /product", CreateProduct)
  http.HandleFunc("GET /product", ListProducts)
  http.HandleFunc("GET /product/{id}", GetProduct)
  http.HandleFunc("PUT /product/{id}", UpdateProduct)
  http.HandleFunc("DELETE /product/{id}", DeleteProduct)
```
> The list endpoint would be for anyone to use, whereas only authorized users can perform the rest

**Orders**

```go
  http.HandleFunc("POST /order", CreateOrder)
  http.HandleFunc("GET /order", ListOrders)
  http.HandleFunc("GET /order/{id}", GetOrder)
```
> These are authenticated endpoints, and performs these actions for the currently logged in user

**Notifications**

This service won't have any http endpoints, instead, will consumer messages producted at `msg.>` and send notifications accordingly, refer [nats docs](https://docs.nats.io/nats-concepts/jetstream/consumers)

> **Again, if you are only interested in the packaging aspects, you can skip over this bit and proceed to the next section**
> For the rest, I've tried to cover at a high level here, you can always look at the examples [here](https://github.com/ashupednekar/ashupednekar.github.io/tree/main/examples/helmblog/services)

Alright then, let's proceed

---
## Ingress



## Setting up our charts

## superpowers - lib charts

## parent charts/ dependencies

## operator nuances

## conclusion

`
