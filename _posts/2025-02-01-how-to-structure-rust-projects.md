# How to structure a rust project?

If you are coming from other languages like say, python or java which means you are mostly working with certain frameworks and would be used to having a defined way of structuring your projects, or even automated tools that do that for you. Whereas modern languages like rust, go, zig don't impose any such structure on you and we instead follow common conventions.

## Preface

Here's a popular blueprint for go by the streamer Melkey: [go-blueprint](https://github.com/Melkeydev/go-blueprint/). This includes a cli that lets you select things you need and build out the scaffolding for you, kind of like springboot. 

![meme](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRMO5UYCDNwknNTGLmJTk92cCKZbIUq30ZlUs09m74gxCwrynh106jlBSBwFAkEilaT-YE&usqp=CAU)

Rust is mainly a systems language and has varied applications, the web being just one of these. This is probably the reason why there's no such convention available right now, maybe that's something we can look at in the future.

This blog will cover my go-to standard, which is completely based on my personal preference/ inclinations, and heavily inspired by go's `pkg`/`'cmd` convention, which I think makes a lot of sense in general. This is not a hard and fast boilerplate, just a starter kit that can help push your rust projects to be in good enough shape that you can stop worrying about the structure and just build what you want, and fight the borrow checker of course ;)

> note: This is suitable for small to medium sized projects that mainly belong to the following categories
> - web services
> - cli 
> - libraries

## Crate structure



