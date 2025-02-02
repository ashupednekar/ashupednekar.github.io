# How to structure a rust project?

If you are coming from other languages like say, python or java... you are most likeky working with certain frameworks and would be used to having a defined way of structuring your projects, or even automated tools that do that for you. Whereas modern languages like rust, go, zig don't impose any such structure on you and we instead follow common conventions.

## Preface

Here's a popular blueprint for go by the streamer Melkey: [go-blueprint](https://github.com/Melkeydev/go-blueprint/). This includes a cli that lets you select things you need and build out the scaffolding for you, kind of like springboot. 

![meme](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRMO5UYCDNwknNTGLmJTk92cCKZbIUq30ZlUs09m74gxCwrynh106jlBSBwFAkEilaT-YE&usqp=CAU)

Rust is mainly a systems language and has varied applications, the web being just one of them. This is probably the reason why there's no such convention available right now, maybe that's something we can look at in the future.

This blog will cover my go-to standard, which is completely based on my personal preference/ inclinations, and heavily inspired by go's `pkg`/`cmd` convention, which I think makes a lot of sense in general. This is not a hard and fast boilerplate, just a starter kit that can help push your rust projects to be in good enough shape that you can stop worrying about the structure and just build what you want, and fight the borrow checker of course ;)

> note: This is suitable for small to medium sized projects that mainly belong to the following categories
> - web services
> - cli tools 

## Dependencies

Let's start with a `cargo new` to create a bin crate. Once that's done, proceed to add two modules, `cmd` and `pkg`. The pkg module is gonna house all our abstractions and utilities while the cmd takes care of the thing s that run these utilities like accepting cli args or starting a server

Let's start by adding the following dependencies to `Cargo.toml`


Instead of sprinking `env::var("MY_ENV")` everywhere, it's better to have a lazy loaded settings struct.
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


Then ofcourse, proceed to add your other dependencies, say `axum` for apis, `sqlx`/`diesel` for databases, `reqwest`, `thiserror`, `chrono` etc, and don't forget the main one, `tokio` :)


## Sample Use Case

In this article, we'll be using the process of rolling out our own simple `auth` service as an example. While this service is the specific use case, the real focus here is on structuring Rust web/API projects in a way that can be applied across various types of services. The auth service is just a relatable, practical example to guide us through building a well-structured Rust project.

We’ll be walking through this example from start to finish, covering everything from basic project setup to advanced considerations. This will allow us to cover all bases, ensuring that you have a solid blueprint for structuring your own Rust APIs in a maintainable and scalable way.

Let's start by setting up a new Rust project:

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
    │   └── mod.rs
    ├── main.rs
    └── pkg
        └── mod.rs
```

**Note**

It's important to note that the `auth` service is merely an example used to demonstrate the project structure. The techniques and patterns we cover here can be applied to any web/API project, not just authentication services. The goal is to establish a solid foundation for building and structuring Rust APIs that can scale and be easily maintained, regardless of the specific functionality they provide. 

If you're primarily interested in the structuring of Rust projects, feel free to skip ahead where needed. The rest of the guide will walk through a full implementation of the auth service, but the structure we've outlined will remain applicable to other use cases as well.

---

I've added the dependencies like so...
```rust
[dependencies]
lazy_static = "1.5.0"
config = "0.15.6"
serde = { version = "1.0.217", features = ["derive"] }
serde_json = "1.0.136"
clap = { version = "4.5.26", features = ["derive"] }
tracing = "0.1.40"
tracing-opentelemetry = "0.27.0"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
opentelemetry = "0.26.0"
opentelemetry-otlp = { version = "0.26.0", features = ["default", "tracing"] }
opentelemetry_sdk = { version = "0.26.0", features = ["rt-tokio"] }
tracing-test = "0.2.5"
tokio = { version = "1.43.0", features = ["full"] }
axum = "0.8.1"
sqlx = { version = "0.8.3", features = ["postgres", "runtime-tokio"] }
async-trait = "0.1.86"
axum-macros = "0.5.0"
standard-error = { version = "0.1.7", features = ["sqlx"] }
chrono = { version = "0.4.39", features = ["serde"] }
mail-send = "0.5.0"
```


## Prelude

The prelude module contains something we'll end up using throughout, our `Error` and `Result` types, let's go ahead and add these

Define the module in `main.rs` with `mod prelude;` and add a `prelude.rs` file, alongside `main.rs`

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum CustomError{
    #[error("some variant")]
    SomeVariant
}

pub type Result<T> = core::result::Result<T, CustomError>;
```

We'll import this result type with `use crate::prelude::Result` going forward

As and when we come across more cases, we'll come back and add variants to the `CustomError` enum

## Config

Next, go ahead and add a `conf` module like we just did with `prelude` and add the following contents

```rust
use config::{Config, ConfigError, Environment};
use lazy_static::lazy_static;
use serde::Deserialize;

#[derive(Deserialize)]
pub struct Settings {
}

impl Settings {
    pub fn new() -> Result<Self, ConfigError> {
        let conf = Config::builder()
            .add_source(Environment::default())
            .build()?;
        conf.try_deserialize()
    }
}

lazy_static! {
    pub static ref settings: Settings = Settings::new().expect("improperly configured");
}
```

Here's what happening here...
- The config crate with it's `Config::builder()` reads environment variables and uses `serde` to parse them into a given struct
- The `lazy_static` macro lets us define a constant called settings that'd be evaluated in a lazy fashion

Now add a config.env at the project root, and let's add one env for illustration, say `LISTEN_PORT`, which also needs a corresponding property in our `Settings` struct

```rust
#[derive(Deserialize)]
pub struct Settings {
    pub listen_port: String
}
```

Note that the case doesn't have to be capitalized here, config and serde takes care of that for us. You can also have certain envs as optional, by simply using wrapping it with an `Option`, like so

```rust
#[derive(Deserialize)]
pub struct Settings {
    pub listen_port: String,
    pub otlp_host: Option<String>,
    pub otlp_port: Option<String>
}
```

Here, I've added two more settings, the host/port of our traces server, more on that later which are optional envs

You can ofcouse have other types as well

```rust
#[derive(Deserialize)]
pub struct Settings {
    pub listen_port: String,
    pub otlp_host: Option<String>,
    pub otlp_port: Option<String>,
    pub use_telemetry: bool
}
```

## The entrypoint 👏

So far, we've not added anything to our main

![meme](https://i.redd.it/a2n75ff2gvk41.jpg)

Before we do that, let's set up our `cmd` module. This will essentially be a `clap` cli, with sub commands for various things out application can do, like we talked about earlier

Add the `cmd` as a module to `main.rs` with `mod cmd;` and head over to `src/cmd/mod.rs`

First, let's import our `settings` and `Result` we just definedm and the `Parser`/`Subcommand` macros from the `clap` crate

```rust
use crate::{prelude::Result, conf::settings};
use clap::{Parser, Subcommand};
```

Now we need to define a `Cmd` struct and a `SubCommandType` enum like so

```rust
#[derive(Parser)]
#[command(about="lets you run auth-svc commands")]
struct Cmd{
    #[command(subcommand)]
    command: Option<SubCommandType>
}

#[derive(Subcommand)]
enum SubCommandType{
    Listen,
    Migrate,
}
```

Let's start with two commands here, `Listen`, which is gonna start our server and `Migrate`, which will set up our db tables, akin to django's `runserver` and `migrate`

Then define a `run` function which will invoke clap's argument parsing and later invoke the respective utilities

```rust
pub async fn run() -> Result<()>{
    let args = Cmd::parse();
    match args.command{
        Some(SubCommandType::Listen) => {
            //start server
        },
        Some(SubCommandType::Migrate) => {
            //run diesel/sqlx migrations
        },
        None => {
            tracing::error!("no subcommand passed")
        }
    }
    Ok(())
}
```

Now go ahead and call this from your `main.rs`

```rust
mod prelude;
mod conf;
mod cmd;

use crate::prelude::Result;

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    cmd::run().await?;
    Ok(())
}
```

Few things to note:
- we've used the `tokio::main` macro to make our main function run within a tokio runtime
- we've used the `Result` from `prelude` so that we can use the `?` operator on our `run` call
- note that run is awaited since it's an async function
- the `tracing_subscriber::fmt::init()` line initiates the tracing module to work with `stdout` to print our logs


Now, if we run `cargo run help`, clap will kindly print out a useful help it generated for our cli

```bash
(base) auth-svc git:main ❯ cargo run help
Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.17s
  Running `target/debug/auth-svc help`
lets you run auth-svc commands

Usage: auth-svc [COMMAND]

Commands:
  listen
  migrate
  help     Print this message or the help of the given subcommand(s)

Options:
  -h, --help  Print help
```

If I call without passing any subcommands, our error log will show up, like so

```bash
cargo run
  Running `target/debug/auth-svc`
2025-02-01T06:53:30.148276Z ERROR auth_svc::cmd: no subcommand passed
```

Once we add and invoke out utilities, we could run our server with `cargo run listen`, or `./auth listen` once compiled into a static binary

## Server

A quick plug here, I'll replace the error enum in our prelude with one from a crate I've published last year, called [standard-error](https://crates.io/crates/standard-error)

```bash
(base) auth-svc git:main ❯ cargo add standard-error                                                  ✹ ✭
    Updating crates.io index
      Adding standard-error v0.1.5 to dependencies
             Features:
             - diesel
             - git
             - reqwest
             - validator
             - sqlx
```

This'll make it easier to work with various libraries as it takes care of mapping the errors and returns a user friendly error message from a yaml file and implements the `IntoResponse` trait. It can also do internationalization for error messages, look at the crate details for more details

Add a `errors.yaml` file at the project root
```yaml
errors:
  - code: ER-0001
    detail_en_US: "error starting server"
```

Update the prelude to use `StandardError` instead

```rust
pub type Result<T> = core::result::Result<T, standard_error::StandardError>;
```

Let's quickly setup the server module with a dedicated directory for handlers

```bash
(base) auth-svc git:main ❯ tree src                                                                ⏎ ✹ ✭
src
├── cmd
│   └── mod.rs
├── conf.rs
├── main.rs
├── pkg
│   ├── mod.rs
│   └── server
│       ├── handlers
│       │   ├── mod.rs
│       │   └── probes.rs
│       └── mod.rs
└── prelude.rs

5 directories, 8 files
```

Make sure to add the corresponding module definitions in `main.rs` and `mod.rs`

Let's add a `listen` function in `server/mod.rs`

```rust
pub mod handlers;

use axum::{routing::get, Router};
use tokio::net::TcpListener;
use crate::{prelude::Result, conf::settings};

use self::handlers::probes::livez;


pub async fn listen() -> Result<()>{
    let listener = TcpListener::bind(
        &format!("0.0.0.0:{}", &settings.listen_port)
    ).await.unwrap();
    let router = Router::new()
        .route("/livez/", get(livez));
    tracing::info!("listening at: {}", &settings.listen_port);
    axum::serve(listener, router)
        .await?;
    Ok(())
}
```

I've added a `livex` handler under `probes.rs`

```rust
use axum::response::IntoResponse;

pub async fn livez() -> impl IntoResponse{
    "OK"
}
```

Go ahead and call this in the `cmd` run function

```rust
 Some(SubCommandType::Listen) => {
     server::listen().await?; 
 }
```

Now you should be able to start the server

```bash
(base) auth-svc git:main ❯ cargo run listen                                                          ✹ ✭
   Compiling auth-svc v0.1.0 (/Users/ashutoshpednekar/Desktop/auth-svc)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 1.73s
     Running `target/debug/auth-svc listen`
2025-02-01T10:55:52.326115Z  INFO auth_svc::pkg::server: listening at: 3000
```

```bash
curl http://localhost:3000/livez/ -v
> GET /livez/ HTTP/1.1
> Host: localhost:3000
< HTTP/1.1 200 OK
< content-type: text/plain; charset=utf-8
< content-length: 2
< date: Sat, 01 Feb 2025 10:56:56 GMT
```

## State

Usually api services need some application state, that's shared across requests, be it a mutex bound map, database connection pool, etc.

Let's go with an empty state for now

Add a `state.rs` alongside `main.rs`

```rust
#[derive(Clone, Debug)]
pub struct AppState {
}

impl AppState {
    pub fn new() -> AppState {
        AppState {}
    }
}
```

Update your router to include the state

```rust
pub async fn listen() -> Result<()>{
    let state = AppState::new();
    ...
    let router = Router::new()
        .route("/livez/", get(livez))
        .with_state(state);
    ...
}
```

> note: If you have too many routes, it's good practive to move the router to a seperate module, say `router.rs`, like so

```rust
pub fn build_routes() -> Router{
    let state = AppState::new();
    Router::new()
        .layer(from_fn_with_state(state.clone(), auth_middleware))
        .route("/livez/", get(livez))
        .with_state(state)
}
```
Then invoke this from the `listen` function with `axum::serve(listener, build_routes()).await?`

## Packages

The `pkg` module is supposed to contain any abstractions or utility modules with seperation of concern. Let's go with our examlpe, of auth.

The following structure is something off the top of my mind, and may not be the ideal one ofcouse, that's what refactoring is for. I'm trying to put out the though process that could do into deciding the structure.

Our use case is auth, which mainly comprises of the following business logic/ domains
- user management
- authentication 

### user managements

User management are basically a set of actions, apart from `CRUD` that can be performed on a user type, which can go about somewhat like this...

```bash
mkdir src/pkg/users                                                       ✹ ✭
touch src/pkg/users/mod.rs                                                ✹ ✭
touch src/pkg/users/models.rs                                             ✹ ✭
touch src/pkg/users/mutators.rs  
```

Let's include these modules with module definitions, and start by defining the `User` struct in `models.rs`

Add the `sqlx` dependency and it's `FromRow` macro for future use, along with `Debug` and serde's `Deserialize` with the derive (`#[derive(Debug, Deserialize, FromRow)]`) macro

```rust
#[derive(Debug, Deserialize, FromRow)]
pub struct User{
    pub email: String,
    pub username: String,
    pub password: String,
    pub display_pic: String
}
```

Before we proceed with the database setup, let's think about the actions.. we can broadly list them as follows
registration
- initiate 
- verify
profile
- update_dp
recovery
- initate
- verify
- change_password

Let's replace our actions.rs with a module corresponding to these.

```bash
❯ tree src/pkg/users                                                       ⏎ ✹ ✭
src/pkg/users
├── adaptors 
│   ├── mod.rs
│   ├── profile.rs
│   ├── recovery.rs
│   └── register.rs
├── mod.rs
└── models.rs

2 directories, 6 files
```

In rust, we usually define traits for essentially "things an object can do", so that later on, in our api handlers, we can do something like `user.update_dp()`. Keeps things clean and readable.

Let's go ahead and define these traits for our actions. Do add the `async_trait` dependency cuz we'll need async functions in our traits

Also, we need to implement these functions for our `User` struct, can be empty for now

**register.rs**

```rust
#[async_trait]
trait RegisterActions{
    async fn initiate_registration(&self) -> Result<()>;
    async fn verify_registration(&self, code: &str) -> Result<()>;
}


#[async_trait]
impl RegisterActions for User{
    async fn initiate_registration(&self) -> Result<()>{
        Ok(())
    }
    async fn verify_registration(&self, code: &str) -> Result<()>{
        Ok(())
    }
}
```

**profile.rs**

```rust
#[async_trait]
trait ProfileMutator{
    async fn update_dp(&mut self, display_pic: &str) -> Result<()>;
}

#[async_trait]
impl ProfileMutator for User{
    async fn update_dp(&mut self, display_pic: &str) -> Result<()>{
        Ok(())
    }
}
```

**recovery.rs**

```rust
#[async_trait]
pub trait RecoveryActions{
    async fn initiate(&self) -> Result<()>;
    async fn verify(&self, code: &str) -> Result<()>;
}

#[async_trait]
impl RecoveryActions for User{
    async fn initiate(&self) -> Result<()>{
        Ok(())
    }
    async fn verify(&self, code: &str) -> Result<()>{
        Ok(())
    }
}
```

The beauty of doing things this way, and rust traits in general is proper seperation of concerns. Note that we haven't done any actual integrations yet, e.g. SMTP, Cache, DB, etc but we can already use these in our api handlers and test them independently

### auth middleware

The authn check could be a middleware that's invoked on every api call, so let's go with that

```bash
mkdir src/pkg/middlewares                                                 ✹ ✭
touch src/pkg/middlewares/mod.rs                                          ✹ ✭
touch src/pkg/middlewares/auth.rs
```

Here's our dummy middleware

**auth.rs**

```rust
use axum::{
    extract::Request,
    middleware::Next,
    response::Response,
};

use crate::prelude::Result;

pub async fn auth_middleware(
    State(state): State<AppState>,
    request: Request,
    next: Next,
) -> Response {
    tracing::debug!("state: {:?}", &state);
    tracing::debug!("req: {:?}", &request);
    next.run(request).await
}
```

Add it to your router like so

```rust
pub fn build_routes() -> Router{
    let state = AppState::new();
    Router::new()
        .layer(from_fn_with_state(state.clone(), auth_middleware))
        .route("/livez/", get(livez))
        .with_state(state)
}
```

## Database

Let's now set up the database, I'll go with `sqlx` cuz of the async support. Let's go...

Make sure you have a running postgres server
```bash
docker run --network host --name postgres -d -e POSTGRES_USER=user -e POSTGRES_PASSWORD=pass123  postgres
```

Now add the dependency and set up the dsn env

```bash
cargo add sqlx -F postgres,runtime-tokio
```
**config.env**
```dotenv
LISTEN_PORT=3000
USE_TELEMETRY=false
RUST_LOG=debug
DATABASE_URL=postgres://user:pass123@localhost:5432/auth
```
> note: make sure to add this to the settings struct in `conf.rs`

Let's go ahead and create this db in our postgres container

```bash
docker exec -it postgres psql -U user -d postgres -c 'create database auth'
CREATE DATABASE
```

Now we need an init `.sql` script to setup migrations

```sql
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    secret_question TEXT NOT NULL,
    secret_answer TEXT NOT NULL,
    display_pic TEXT NOT NULL
);

CREATE INDEX idx_users_email ON users(email);
```

Here, `username` is the primary key and `email` has a unique constraint and a btree index for faster lookups

Create a directory called migrations in `src/` and place this in there. This is an arbitrary choice, could be anywhere. Usually, if there are too many db adaptors, I usually club them in a db module and place migrations within that. Take a call, these are not hard and fast rules.

Now, let's add the migration logic in cmd, under the migrate subcommand type

```rust
Some(SubCommandType::Migrate) => {
    let pool = PgPool::connect(&settings.database_url).await?;
    pool.execute(include_str!("../migrations/init.sql")).await?;
    tracing::info!("init migrations applied successfully")
}
```

> note: make sure to enable the `sqlx` feature in standard-error for auto handling of sqlx errors

Now we can run our migrations, and the tables should be setup :)

```bash
(base) auth-svc git:main ❯ cargo run migrate                                                       
     Running `target/debug/auth-svc migrate`
2025-02-01T19:45:42.696946Z DEBUG sqlx::query: summary="CREATE TABLE users ( …" db.statement="\n\nCREATE TABLE users (\n    username TEXT PRIMARY KEY,\n    email TEXT UNIQUE NOT NULL,\n    password TEXT NOT NULL,\n    secret_question TEXT NOT NULL,\n    secret_answer TEXT NOT NULL,\n    display_pic TEXT NOT NULL\n);\n\nCREATE INDEX idx_users_email ON users(email);\n\n" rows_affected=0 rows_returned=0 elapsed=16.270792ms elapsed_secs=0.016270792
2025-02-01T19:45:42.697160Z  INFO auth_svc::cmd: init migrations applied successfully
```

```sql
auth=# \dt
       List of relations
 Schema | Name  | Type  | Owner
--------+-------+-------+-------
 public | users | table | user

auth=# \d+ users;
                                             Table "public.users"
     Column      | Type | Collation | Nullable | Default | Storage  | Compression | Stats target | Description
-----------------+------+-----------+----------+---------+----------+-------------+--------------+-------------
 username        | text |           | not null |         | extended |             |              |
 email           | text |           | not null |         | extended |             |              |
 password        | text |           | not null |         | extended |             |              |
 secret_question | text |           | not null |         | extended |             |              |
 secret_answer   | text |           | not null |         | extended |             |              |
 display_pic     | text |           | not null |         | extended |             |              |
Indexes:
    "users_pkey" PRIMARY KEY, btree (username)
    "idx_users_email" btree (email)
    "users_email_key" UNIQUE CONSTRAINT, btree (email)
Access method: heap
```

We need to add the DB pool to our state, so that it's available to our handlers

```rust
use std::sync::Arc;

use sqlx::PgPool;

use crate::{prelude::Result, conf::settings};

#[derive(Clone, Debug)]
pub struct AppState {
    pub db_pool: Arc<PgPool>
}

impl AppState {
    pub async fn new() -> Result<AppState> {
        let db_pool = Arc::new(PgPool::connect(&settings.database_url).await?);
        Ok(AppState {
            db_pool
        })
    }
}
```

We need to use an `Arc` because this needs to be shared across threads, since our requests handlers will be executed as `tokio` threads

Make the corresponding change in router, now that the new is async, and returns a result type

```rust
//router
pub async fn build_routes() -> Result<Router>{
    let state = AppState::new().await?;
    Ok(Router::new()
        .layer(from_fn_with_state(state.clone(), auth_middleware))
        .route("/livez/", get(livez))
        .with_state(state))
}

//server
axum::serve(listener, build_routes().await?)
        .await?;
```

Let's implement the requirede CRUD functions on our `User` struct, along with a `new` method for initialization

```rust
impl User{

    pub fn new(payload: RegistrationInput) -> Self{
        Self {
            username: payload.username,
            email: payload.email,
            password: payload.password,
            display_pic: None,
            verified: false,
        }
    }

    pub async fn save(&self, pool: &PgPool) -> Result<()>{
        sqlx::query!(
            r#"
            INSERT INTO users (username, email, password, display_pic, verified) 
            VALUES ($1, $2, $3, $4, $5)
            "#,
            self.username,
            self.email,
            self.password,
            self.display_pic,
            self.verified
        )
        .execute(pool)
        .await?;
        Ok(())
    }

    pub async fn mark_as_verified(&self, pool: &PgPool) -> Result<()> {
        sqlx::query!(
            r#"
            UPDATE users 
            SET verified = true 
            WHERE username = $1
            "#,
            self.username
        )
        .execute(pool)
        .await?;
        Ok(())
    }

    pub async fn update_display_pic(&self, pool: &PgPool, new_dp: &str) -> Result<()> {
        sqlx::query!(
            r#"
            UPDATE users 
            SET display_pic = $1 
            WHERE username = $2
            "#,
            new_dp,
            self.username
        )
        .execute(pool)
        .await?;
        Ok(())
    }

    pub async fn find_by_username(pool: &PgPool, username: &str) -> Result<Option<User>> {
        let user = sqlx::query_as!(
            User,
            r#"
            SELECT username, email, password, display_pic, verified 
            FROM users 
            WHERE username = $1
            "#,
            username
        )
        .fetch_optional(pool)
        .await?;

        Ok(user)
    }

}

```


### Email

Let's add an email module to our package, and corresponding settings. 


```rust
use mail_send::{mail_builder::MessageBuilder, SmtpClientBuilder};
use standard_error::{Interpolate, StandardError};

use crate::conf::settings;

pub async fn send_email(
    to: &str,
    subject: &str,
    body: &str,
) -> Result<(), StandardError> {
    let message = MessageBuilder::new()
        .from(settings.from_email.clone())
        .to(vec![to.to_string()])
        .subject(subject.to_string())
        //.html_body("<h1>Hello, world!</h1>")
        .text_body(body.to_string());

    tracing::debug!("{:?}", (settings.from_email.clone(), settings.smtp_pass.clone()));

    SmtpClientBuilder::new(settings.smtp_server.clone(), settings.smtp_port)
        .implicit_tls(false)
        .credentials((settings.from_email.clone(), settings.smtp_pass.clone()))
        .connect()
        .await.unwrap()//map_err(|e| StandardError::new("ER-SMTP").interpolate_err(e.to_string()))?
        .send(message)
        .await.map_err(|e| StandardError::new("ER-SMTP").interpolate_err(e.to_string()))?;
    Ok(())
}


#[cfg(test)]
mod tests {
    use super::*;
    use standard_error::StandardError;

    #[tracing_test::traced_test]
    #[tokio::test]
    async fn test_send_email() -> Result<(), StandardError> {
        let to = "ashupednekar49@gmail.com";
        let subject = "Test Email from Rust";
        let body = "Hello! This is a test email sent from a Rust application.";
        send_email(to, subject, body).await?;
        Ok(())
    }
}
```

### Handlers

Now that all the dependent packages are set up, we can proceed to implement the business logic and add the api handlers and routes

Since we're gonna deal with user management, I created a module called `user_mgmt` under handlers

Let's start with the first handler: **initiate_registration**

Before we proceed to writing the handler itself, we need to implement the business logic in our trait implementation

We need to set the email codes in redis with an expiry... let's add the redis client to the state

```rust
#[derive(Clone, Debug)]
pub struct AppState {
    pub db_pool: Arc<PgPool>,
    pub redis_client: Arc<Client>,
}

impl AppState {
    pub async fn new() -> Result<AppState> {
        let db_pool = Arc::new(PgPool::connect(&settings.database_url).await?);
        let redis_client = Arc::new(Client::open(settings.redis_url.as_str()).map_err(|_|StandardError::new("ERR-REDIS-CONN"))?);
        Ok(AppState { 
            db_pool,
            redis_client
        })
    }
}
```
Ideally we should be using a connection pool instead of a single connection, like we did for DB, didn't want to complicate for the sake of this blog post, do refer to the [docs](https://docs.rs/redis/latest/redis/) to use `r2d2` to pool your redis connections

> Make sure to run redis with `docker run --network host -d --name redis redis`
> Add `REDIS_URL` env and conf attribute: `REDIS_URL=redis://localhost:6379`

```rust
    async fn initiate_registration(&self, state: AppState) -> Result<()> {
        let code = Uuid::new_v4().to_string();
        let mut conn = state.redis_client.get_connection().unwrap();
        let timeout = parse_duration(&settings.registration_timeout).expect("invalid time format").as_secs(); 
        let _: () = redis::cmd("SET")
            .arg(&code)
            .arg(&self.username)
            .arg("EX")
            .arg(timeout)
            .query(&mut conn)
            .map_err(|_|StandardError::new("ERR-REG-001"))?;
        send_email(&self.email, "registration", &format!("here's your code: {}", &code)).await?;
        Ok(())
    }

    async fn verify_registration(state: AppState, code: &str) -> Result<()> {
        let mut conn = state.redis_client.get_connection().unwrap();
        let username: Option<String> = redis::cmd("GET")
            .arg(code)
            .query(&mut conn)
            .map_err(|_| StandardError::new("ERR-REG-002"))?; // expired code
        if let Some(username) = username{
            let user = User::find_by_username(&state.db_pool, &username).await?;
            if let Some(user) = user{
                user.mark_as_verified(&state.db_pool).await?; 
            }else{
                return Err(StandardError::new("ERR-REG-003")); //invalid code
            }
        }
        Ok(())
    }
```
The initiate registration implementation is setting a redis key with a random code as key and username as value, with expiry and sending the code over email

The verify registration tries to fetch this code from redis, if it finds it, the email link is valid, or else it has expired which would be `ERR-REG-002`. Then we set this user as verified, thereby completing the registration process. If there is no user entry, it'll return so through `ERR-REG-003`


Now let's bring it all together in the handlers

```rust
#[derive(Deserialize)]
pub struct RegistrationInput {
    pub username: String,
    pub email: String,
    pub password: String,
    pub confirm_password: String,
}

pub async fn initiate_user_registration(
    State(state): State<AppState>,
    Json(payload): Json<RegistrationInput>,
) -> Result<String> {
    if payload.password != payload.confirm_password {
        return Err(StandardError::new("ERR-AUTH-001").code(StatusCode::BAD_REQUEST));
    }
    let user = User::new(payload);
    user.save(&state.db_pool).await?;
    user.initiate_registration(state).await?;
    Ok(serde_json::to_string(&json!({ "msg": "registration initiated successfully" }))?)
}

pub async fn verify_user_registration(
    State(state): State<AppState>,
    Query(params): Query<RegVerifyInput>
) -> Result<String>{
    User::verify_registration(state, &params.code).await?;
    Ok(serde_json::to_string(&json!({ "msg": "user verified successfully" }))?)
}
```

I prefer to define the input structs right next to the handlers for clarity, since my handlers are divided into smaller modules. You could also choose to go the serializers route and keep these together under a `serializers` module as well

Don't forget to add the route to this handler

```rust
 .route("/register/initiate/", post(initiate_registration))
```

Note how clean our handlers end up being are thanks to the work we did earlier. That's what rust coding is all about, "optimize your code for reading, not writing" :)

```yaml
  - code: ERR-REG-000
    detail_en_US: "password and confirm password should match"
  - code: ERR-REG-001
    detail_en_US: "error generating validation code"
  - code: ERR-REG-002
    detail_en_US: "this code has expired"
  - code: ERR-REG-003
    detail_en_US: "this code is invalid"
```

As for the validation error, I simply added the error messages in the `errors.yaml` and raised it from here with a custom status code (another shameless plug 😉)

---
 
Now we should be able to perform user registration with `curl` 😄

```bash
curl -X POST http://localhost:3000/register/initiate/ -H 'Content-type: application/json' -d '{"username": "ashupednekar", "email": "ashupednekar@gmail.com", "password": "pass123", "confirm_password": "pass123"}'
{"msg":"registration initiated successfully"}%   
```

```bash
curl -X GET 'http://localhost:3000/register/verify/?code=52da603d-db84-4d48-8f2c-3d2a6aa47b8a'     
{"msg":"user verified successfully"}
```

```sql
auth=# select * from users ;
   username   |          email           | password | display_pic | verified
--------------+--------------------------+----------+-------------+----------
 ashu         | ashupednekar49@gmail.com | pass123  |             | f
 ashupednekar | ashupednekar@gmail.com   | pass123  |             | t
```

Let's leave the rest of the implementation as an exercise, go ahead and add real stuff like CSRF validation, oauth provider support, multi-tenancy, etc. This topic is endless, trust me xD... 


## Conclusion

Let's be clear - this whole auth service was just a practical vehicle to explore Rust project structuring patterns. While we did end up with a sorta working authentication (rather registration xD) system, the real focus was on creating a maintainable and scalable project structure. The pkg/cmd pattern borrowed from Go gives us a clean separation of concerns, with our core business logic living in pkg and our entry points in cmd.

Speaking of cmd, there's an interesting thought for future iterations - since our handlers are essentially just orchestrating calls to our business logic, maybe they belong in cmd rather than pkg? After all, they're more about coordinating how things run rather than implementing core functionality. It's the kind of architectural decision that teams could debate over coffee (or something stronger xD).

And let's be honest - while this structure has worked well for a few projects of mine, it's not a silver bullet at all. Your codebase can and will still get messy if you're not careful. The key is to stay flexible and adapt the structure as your project grows. Using traits for our business logic helps here, making it easier to modify implementations without touching the interfaces. You might be rightly thinking if they were overkill in this example, since we only had a single implementation. It's more meaningful in cases where you have a single interface, but multiple implementations, say pubsub brokers for example. I used them because I like traits and especially the `user.do_this()` invokation 🤣

Remember - project structure is like a good recipe: there are some basic principles to follow, but there's always room for adaptation based on your specific needs. Just try not to let it turn into a spaghetti monster. Nobody likes debugging spaghetti code on a Monday morning. But when it does, just take a deep breath and ponder about refactoring
