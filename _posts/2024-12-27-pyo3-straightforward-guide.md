## So you wanna speed up Python?

Alright, buckle up, Pythonistas, because shared libraries are here to save the day! But forget C (because we’re not touched by the arcane), and say hello to Rust—our favorite mix of performance and sanity.


## Why Rust?

1. 🦀 Fast: Rust zips through code like your Wi-Fi when your neighbors aren’t stealing it.

2. Safe: Unlike your average Python dev at 3 AM, Rust won’t let you shoot yourself in the foot.

3. Shared Libs: Because why rewrite everything when you can just wrap the spicy Rust bits and call them from Python?


## The Game Plan


We’re gonna:

1. Write some 🔥 Rust code.
2. Turn it into a shared library (.so for Linux folks, .dll for Windows weirdos).
3. Slap some Python bindings on it (thanks, PyO3!).
4. Watch your Python code finally graduate from crawling like a toddler to sprinting like Usain Bolt :)

Jokes aside, we're gonna cover the following three scenarios
- simple rust function called from python
- accept python objects and run them from rust
- import python code direcrty and run

First off, we're gonna stick to pyo3 version 0.20.0 in this article, things change slightly in subsequent versions

> first off, install maturin with `pip install maturin`  

### Simple rust function called from python

Let's go, start a fresh pyo3 project. We're just gonna sum numbers up to a given n, just to mock python for loop 😄

```bash
(base) Desktop ❯ mkdir sum_up_to                                                                       ⏎
(base) Desktop ❯ cd sum_up_to
(base) sum_up_to ❯ maturin init
✔ 🤷 Which kind of bindings to use?
  📖 Documentation: https://maturin.rs/bindings.html · pyo3
  ✨ Done! Initialized project /Users/ashutoshpednekar/Desktop/sum_up_to
```

This will create a simple library crate with lib.rs, and a pyproject toml for the python stuff

```bash
(base) sum_up_to ❯ tree
.
├── Cargo.toml
├── pyproject.toml
└── src
    └── lib.rs

2 directories, 3 files
```


