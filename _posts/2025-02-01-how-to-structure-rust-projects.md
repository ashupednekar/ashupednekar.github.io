# How to structure a rust project?

If you are coming from other languages like say, python or java which means you are mostly working with certain frameworks and would be used to having a defined way of structuring your projects, or even automated tools that do that for you. Whereas modern languages like rust, go, zig don't impose any such structure on you and we instead follow common conventions.

## Preface

Here's a popular blueprint for go by the streamer Melkey: [go-blueprint](https://github.com/Melkeydev/go-blueprint/). This includes a cli that lets you select things you need and build out the scaffolding for you, kind of like springboot. 

![meme](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRMO5UYCDNwknNTGLmJTk92cCKZbIUq30ZlUs09m74gxCwrynh106jlBSBwFAkEilaT-YE&usqp=CAU)

Rust is mainly a systems language and has varied applications, the web being just one of these. This is probably the reason why there's no such convention available right now, maybe that's something we can look at in the future.

This blog will cover my go-to standard, which is completely based on my personal preference/ inclinations, and heavily inspired by go's `pkg`/`'cmd` convention, which I think makes a lot of sense in general. This is not a hard and fast boilerplate, just a starter kit that can help push your rust projects to be in good enough shape that you can stop worrying about the structure and just build what you want, and fight the borrow checker of course ;)

> note: This is suitable for small to medium sized projects that mainly belong to the following categories
> - web services
> - cli tools 

## Dependencies

Let's start with a `cargo new` to create a bin crate. Once that's done, proceed to add two modules, `cmd` and `pkg`. The pkg module is gonna house all our abstractions and utilities while the cmd takes care of the thing s that run these utilities like accepting cli args or starting a server

Let's start by adding the following dependencies to `Cargo.toml`


- Instead of sprinking `env::var("MY_ENV")` everywhere, it's better to have a lazy loaded settings struct.
```toml
lazy_static = "1.5.0"
config = "0.15.6"
```

The serde wizards will parse our envs for us with customizations like custom aliases, or even custom deserializers... more on that later
```toml
serde = { version = "1.0.217", features = ["derive"] }
serde_json = "1.0.136"
```

Now, if you've worked with something like `django` before, you must be familiar with management commands right? Things like db migrations, server startup, cli client, seperate gRPC server, etc can be invoked through cli arguments with the best Cli library ever made, i.e. `clap`.
```toml
clap = { version = "4.5.26", features = ["derive"] }
```

This one is optional, but definitely recommended. Let's add the dependencies for tracing and telemetry
```toml
tracing = "0.1.40"
tracing-opentelemetry = "0.27.0"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
opentelemetry = "0.26.0"
opentelemetry-otlp = { version = "0.26.0", features = ["default", "tracing"] }
opentelemetry_sdk = { version = "0.26.0", features = ["rt-tokio"] }
tracing-test = "0.2.5"
```

Then ofcourse, proceed to add your other dependencies, say `axum` for apis, `sqlx`/`diesel` for databases, `reqwest`, `chrono` etc, and don't forget the main one, `tokio` :)


## Sample use case

I'll go with rolling our own simple `auth` service so that we can have a relatable example and cover all bases

```bash
cargo new auth-svc
    Creating binary (application) `auth-svc` package
note: see more `Cargo.toml` keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html
(base) Desktop ❯ cd auth-svc
(base) src git:master ❯ mkdir pkg                                                             ✭
(base) src git:master ❯ touch pkg/mod.rs                                                      ✭
(base) src git:master ❯ mkdir cmd                                                             ✭
(base) src git:master ❯ touch cmd/mod.rs                                                      ✭
(base) auth-svc git:master ❯ tree                                                             ✭
.
├── Cargo.lock
├── Cargo.toml
└── src
    ├── cmd
    │   └── mod.rs
    ├── main.rs
    └── pkg
        └── mod.rs

4 directories, 5 files
```


