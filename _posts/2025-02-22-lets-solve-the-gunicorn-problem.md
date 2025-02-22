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

It took quite a bit of prompts to get gpt to simplify it, that's how convoluted the various implementation and documentation are, but at it's core, its a very nice interface.

A wsgi application is basically a `Callable` with two arguments

```python
def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b"Hello, WSGI!"]
```

- The `environ` dictionary contains various metadata information like request path, headers, etc. 
- `start_response` is a function takes in a shared reference to status and headers, that the frameworks are then going to write to. 

It's a little tricky, but you'll get the hang of it once you see the code

### Let's start coding then

We need a python library with a serve command, let's start by creating a new `pyo3` project with `maturin`

Refer to my [pyo3 blog](https://ashupednekar.github.io/posts/lets-solve-the-gunicorn-problem/) for more details

#### Depencencies

I'll start by adding our dependencies, `hyper`, `tokio` and `pyo3`, along with a few tracing crates

```toml
hyper = { version = "0.14.28", features = ["full", "server"] }
pyo3 = { version = "0.23.4", features = ["extension-module"] }
tokio = { version = "1.43.0", features = ["full"] }
tracing = "0.1.40"
tracing-opentelemetry = "0.27.0"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
opentelemetry = "0.26.0"
opentelemetry-otlp = { version = "0.26.0", features = ["default", "tracing"] }
opentelemetry_sdk = { version = "0.26.0", features = ["rt-tokio"] }
tracing-test = "0.2.5"
```

#### Cli command

Let's start by defining a star function in `lib.rs`. The actual function will be async, so we need to start the tokio runtime to be able to call async functions

```rust
#[pyfunction]
fn start(py: Python, path: &str, port: u16) -> PyResult<()> {
    py.allow_threads(||{
        tokio::task::block_in_place(move || {
            let rt = Runtime::new().expect("failed");
            rt.block_on(async {
                serve(&path, port).await.unwrap();     
            });
        });
        Ok(())
    })
}

#[pymodule]
fn servers(m: &Bound<'_, PyModule>) -> PyResult<()> {
    tracing_subscriber::fmt::init();
    m.add_function(wrap_pyfunction!(start, m)?)?;
    Ok(())
}
```

The way pyo3 works, is it includes the compiled `.so` shared library in the wheel file, along with a package with the same name.

We also need a command the users can run once they install the library. We can do that by overriding the `__init__.py` to include a `serve` function, and include it as an entrypoint in `pyproject.toml`

```python
from .servers import start
from pathlib import Path
import argparse
import sys


def serve():
    sys.path.insert(0, str(Path.cwd()))
    parser = argparse.ArgumentParser(description="Start the server.")
    parser.add_argument("path", type=str, help="Path to the server directory")
    parser.add_argument("port", type=int, help="Path to the server directory")
    args = parser.parse_args()
    sys.exit(start(args.path, args.port))
```

We need to import the wsgi application, but the thing is our script is going to be placed in the `bin/` directory within the python virtual environment, that's what the `sys.path` insert is for. 

> You could ofcourse add more arguments. Keep it simple though, or we'd end up with the same thing we're trying to replace xD

Then we add it to `pyproject.toml` for including it in our wheel

```toml
[project.scripts]
serve-rs = "servers:serve"
```

#### Server

We'll soon define a wsgi application, for handing the requests. Before that, let's define our `hyper` server

```rust
use crate::pkg::wsgi::WSGIApp;

pub async fn serve(path: &str, port: u16) -> PyResult<()>{
    let (wsgi_module, wsgi_app) = if let Some((module, app)) = path.split_once(':') {
        (module, app)    
    } else {
        return Err(PyValueError::new_err("Invalid path format"));
    };
    
    let app = Arc::new(Python::with_gil(|py|{
        WSGIApp::new(py, wsgi_module, wsgi_app)
    })?);
    
    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    let make_svc = make_service_fn(move |_| {
        let app = app.clone();
        async { 
            Ok::<_, Infallible>(service_fn(move |req| {
                let app = app.clone();
                async move {
                    app.handle_request(req).await 
                }
            }))
        }
    });

    println!("WSGI Server running at http://{}", addr);
    let server = Server::bind(&addr).serve(make_svc);
    tokio::select! {
        _ = server => {},
        _ = signal::ctrl_c() => {}
    }
    Ok(())
}

```

Here's the TLDR 
- take our wsgi path as input
- load the wsgi module in an Arc, cuz it has to be shared across threads
- create a hypr server listening at the configured port, using `make_service_fn`
- spawn the server in a new `tokio` thread, while also handling the `ctrl+c` signal

#### Let's now start the wsgi module

```rust
pub struct WSGIApp {
    app: Arc<Py<PyAny>>,
    port: u16
}
```

The wsgiapp stuct stores the wsgi `application` callable, i.e. `Py<PyAny>`

```rust
impl WSGIApp {
    pub fn new(py: Python, module: &str, app: &str, port: u16) -> PyResult<Self> {
        let module = py.import(module)?;
        let app = Arc::new(module.getattr(app)?.into_pyobject(py)?.into());
        Ok(Self { app, port })
    }
}
```

the `new` function loads the app and store it as an `Arc`

#### Request handling

We need to build the `environ` dictionary for the input

##### headers

```rust
let headers: HashMap<String, String> = req.headers()
    .iter()
    .map(|(k, v)| {
        let key = format!("HTTP_{}", k.as_str().replace("-", "_").to_uppercase());
        let value = v.to_str().unwrap_or("").to_string();
        (key, value)
    })
    .collect();
```

Reads the hyper request headers, which is an iterator to create a hashmap with underscored keys in upper case

##### body

```rust
let body_bytes = hyper::body::to_bytes(req.into_body())
    .await
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{}", e)))?
    .to_vec();
```

Using the `to_bytes` utility from hyper to create bytes, and convert to a `Vec<u8>`

##### Building the environ

We now need to start a python gil to build the environ `PyDict`, and call the app callable with the environ and the `start_response` function, more on that later

Also, we need to spawn a new thread for handing each request to gain fearless concurrency, as they say it

```rust
let (status, response_headers, body) = tokio::task::spawn_blocking(move || {
    Python::with_gil(|py| -> PyResult<(u16, Vec<(String, String)>, Vec<u8>)> {
        let environ = PyDict::new(py);
        for (k, v) in headers.into_iter(){
            environ.set_item(k.as_str().replace("-", "_").to_uppercase(), v.to_string())?;
        }
        environ.set_item("SERVER_NAME", "")?;
        environ.set_item("SERVER_PORT", port)?;
        environ.set_item("HTTP_HOST", "localhost")?;
        environ.set_item("PATH_INFO", path)?;
        environ.set_item("REQUEST_METHOD", method)?;

        let py_body = PyBytes::new(py, &body_bytes);

        let io = py.import("io")?;
        let wsgi_input = io.getattr("BytesIO")?.call1((py_body,))?;
        environ.set_item("wsgi.input", wsgi_input)?;

        environ.set_item("wsgi.version", (1, 0))?;
        environ.set_item("wsgi.errors", py.None())?;

        tracing::debug!("prepared environ: {:?}", environ);

        let wsgi_response = Py::new(py, WsgiResponse::new())?;
        let start_response = wsgi_response.getattr(py, "start_response")?;
        let res = app.call1(py, (environ, start_response, ))?;
        tracing::info!("called Python WSGI function");

        let status_code = wsgi_response
            .getattr(py, "get_status")?
            .call0(py)?
            .extract::<String>(py)?
            .split_whitespace()
            .next()
            .and_then(|s| s.parse::<u16>().ok())
            .unwrap_or_default();
        tracing::info!("status code: {}", &status_code);

        tracing::info!("res: {:?}", &res);
        let response_bytes: Vec<u8> = res
            .getattr(py, "content")?
            .extract::<Vec<u8>>(py)?;
        Ok((status_code, vec![], response_bytes))   
    })
}).await.map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))??;
```

Here's a quick description for each keys in our environ dictionary=

SERVER_NAME → Server hostname
SERVER_PORT → Server port
HTTP_HOST → Request host
PATH_INFO → Requested URL path.
REQUEST_METHOD → HTTP method
wsgi.input → Request body as a BytesIO stream.
wsgi.version → WSGI version ((1, 0)).
wsgi.errors → Error stream (set to None).

We then proceed to extract the reponse body and status code from result of the python invocation

Finally, we build the hyper response and send it back to the client

```rust
    tracing::info!("{:?}| {:?} | {:?}", status, response_headers, body);
    let mut builder = Response::builder().status(status);
    Ok(builder.body(Body::from(body)).unwrap())
}
```

#### Response

We create a response object with shared mutices for status and headers

```rust
#[pyclass]
pub struct WsgiResponse {
    status: Mutex<Option<String>>,
    headers: Mutex<Vec<(String, String)>>,
}

#[pymethods]
impl WsgiResponse {
    #[new]
    pub fn new() -> Self {
        WsgiResponse {
            status: Mutex::new(None),
            headers: Mutex::new(Vec::new()),
        }
    }
}
```

Thanks to the `pyclass`/`pymethods` macro, this behaves like just another python function when invoked by our wsgi application, i.e. the framework like django when we pass it in the handle request function

```rust
let wsgi_response = Py::new(py, WsgiResponse::new())?;
let start_response = wsgi_response.getattr(py, "start_response")?;
```

### Conclusion

That's it, now we compile and run it. Or you can download the library from [pip](https://pypi.org/project/serve-rs/). Here are the [docs](https://ashupednekar.github.io/serve-rs/)

Gunicorn does its job well, but like any abstraction, it’s easy to use without truly understanding what’s happening under the hood. Digging into its internals made me realize that a lot of its complexity comes from solving problems I don’t always need. So I built serve-rs—a simple, transparent alternative that does just enough without the extra baggage. The real takeaway? Whether you use Gunicorn, serve-rs, or something else entirely, understanding how things work makes you a better engineer—and sometimes, building your own tool is the best way to do that. 🚀

