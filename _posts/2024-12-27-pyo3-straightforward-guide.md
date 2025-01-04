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

Extra things you'll wanna do at some point
- using classes, and limitations of `pymethods`
- passing `PyObject`'s around tokio threads
- accept `*args` and `**kwargs`
- asyncio 😧?

First off, we're gonna stick to pyo3 version 0.20.0 in this article, things change slightly in subsequent versions

> first off, install maturin with `pip install maturin`  

## Simple rust function called from python

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

Here's the starter lib.rs it'll generate

```rust
use pyo3::prelude::*;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn sum_up_to(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
```

If you think this is complicated, take a look at this C code, that we had to do before, not to mention the amazing tooling by folks at pyo3

```c
#include <Python.h>

// Function to compute the sum of two numbers and return it as a string.
static PyObject* sum_as_string(PyObject* self, PyObject* args) {
    unsigned long a, b;

    // Parse the Python arguments (two unsigned long integers).
    if (!PyArg_ParseTuple(args, "kk", &a, &b)) {
        return NULL;
    }

    // Compute the sum and convert to string.
    unsigned long sum = a + b;
    char result[32]; // Buffer to hold the resulting string.
    snprintf(result, sizeof(result), "%lu", sum);

    // Return the result as a Python string.
    return PyUnicode_FromString(result);
}

// Define the method table for the module.
static PyMethodDef SumUpToMethods[] = {
    {"sum_as_string", sum_as_string, METH_VARARGS, "Returns the sum of two numbers as a string."},
    {NULL, NULL, 0, NULL} // Sentinel value indicating the end of the table.
};

// Define the module definition structure.
static struct PyModuleDef sumuptomodule = {
    PyModuleDef_HEAD_INIT,
    "sum_up_to", // Module name.
    "A module that sums two numbers and returns the result as a string.", // Module documentation.
    -1,          // Size of per-interpreter state of the module or -1 if the module keeps state in global variables.
    SumUpToMethods
};

// Module initialization function.
PyMODINIT_FUNC PyInit_sum_up_to(void) {
    return PyModule_Create(&sumuptomodule);
}
```

### Cool.. Here's a bottom line of what's happening here
`pymodule`, `pyfunction`, `pyclass`, `pymethods` are rust macros provided by pyo3

- `pyfunction` automagically make your rust function `extern`, or in other words, "can be called from python"
- `pymodule` is a representation of your library as python would see it, you need to add your functions and classes here explicitly


### Let's make our code changes

```rust
use pyo3::prelude::*;

#[pyfunction]
fn add_up_to(n: i32) -> PyResult<i32> {
    Ok((1..=n).sum())
}

#[pymodule]
fn sum_up_to(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(add_up_to, m)?)?;
    Ok(())
}
```

> We couldv'e written a prcedural for loop with a mutable variable, but we're not writing `go` here xD

### Now we compile...

Maturin’s `develop` command is like that one friend who insists on doing *everything* for you:

- Compiles your Rust code.  
- Builds the `.so` file for Python.  
- Packs it into a `.whl`.  
- Installs it straight into your Python venv.  

```bash
(base) sum_up_to ❯ maturin develop --release
🔗 Found pyo3 bindings
🐍 Found CPython 3.12 at /Users/ashutoshpednekar/.virtualenvs/base/bin/python
📡 Using build options features from pyproject.toml
   Compiling target-lexicon v0.12.16
   Compiling once_cell v1.20.2
   Compiling proc-macro2 v1.0.92
   Compiling unicode-ident v1.0.14
   Compiling autocfg v1.4.0
   Compiling libc v0.2.169
   Compiling heck v0.5.0
   Compiling cfg-if v1.0.0
   Compiling unindent v0.2.3
   Compiling indoc v2.0.5
   Compiling memoffset v0.9.1
   Compiling quote v1.0.38
   Compiling syn v2.0.92
   Compiling pyo3-build-config v0.22.6
   Compiling pyo3-macros-backend v0.22.6
   Compiling pyo3-ffi v0.22.6
   Compiling pyo3 v0.22.6
   Compiling pyo3-macros v0.22.6
   Compiling sum_up_to v0.1.0 (/Users/ashutoshpednekar/Desktop/sum_up_to)
    Finished `release` profile [optimized] target(s) in 5.54s
📦 Built wheel for CPython 3.12 to /var/folders/dy/y5vs5b593mj87r518n0164rw0000gn/T/.tmpbQGGTM/sum_up_to-0.1.0-cp312-cp312-macosx_11_0_arm64.whl
✏️  Setting installed package as editable
🛠 Installed sum_up_to-0.1.0
```

Voila, now you can use it in python

```python
>>> from sum_up_to import add_up_to
>>> import timeit
>>>
>>> def foo(n):
...     start_time = timeit.default_timer()  # High-resolution timer
...     result = add_up_to(n)
...     elapsed_time = (timeit.default_timer() - start_time) * 1e6  
...     print(result)
...     print(f"Time taken: {elapsed_time:.0f} microseconds")  
...
>>> foo(1000000)
1784293664
Time taken: 6 microseconds
>>>
```

You don't even want to try adding a million numbers in python, see how simple it is?


If you’d rather just get the wheel and upload it to PyPI with say, twine... the `build` command has you covered.

```bash
(base) sum_up_to ❯ maturin build --release -f --out dist
🔗 Found pyo3 bindings
🐍 Found CPython 3.9 at /opt/homebrew/opt/python@3.9/bin/python3.9, CPython 3.11 at /opt/homebrew/opt/python@3.11/bin/python3.11, CPython 3.12 at /Users/ashutoshpednekar/.virtualenvs/base/bin/python3.12
📡 Using build options features from pyproject.toml
💻 Using `MACOSX_DEPLOYMENT_TARGET=11.0` for aarch64-apple-darwin by default
   Compiling pyo3-build-config v0.22.6
   Compiling pyo3-macros-backend v0.22.6
   Compiling pyo3-ffi v0.22.6
   Compiling pyo3 v0.22.6
   Compiling pyo3-macros v0.22.6
   Compiling sum_up_to v0.1.0 (/Users/ashutoshpednekar/Desktop/sum_up_to)
    Finished `release` profile [optimized] target(s) in 3.84s
📦 Built wheel for CPython 3.9 to dist/sum_up_to-0.1.0-cp39-cp39-macosx_11_0_arm64.whl
💻 Using `MACOSX_DEPLOYMENT_TARGET=11.0` for aarch64-apple-darwin by default
   Compiling pyo3-build-config v0.22.6
   Compiling pyo3-ffi v0.22.6
   Compiling pyo3-macros-backend v0.22.6
   Compiling pyo3 v0.22.6
   Compiling pyo3-macros v0.22.6
   Compiling sum_up_to v0.1.0 (/Users/ashutoshpednekar/Desktop/sum_up_to)
    Finished `release` profile [optimized] target(s) in 3.35s
📦 Built wheel for CPython 3.11 to dist/sum_up_to-0.1.0-cp311-cp311-macosx_11_0_arm64.whl
💻 Using `MACOSX_DEPLOYMENT_TARGET=11.0` for aarch64-apple-darwin by default
   Compiling pyo3-build-config v0.22.6
   Compiling pyo3-ffi v0.22.6
   Compiling pyo3-macros-backend v0.22.6
   Compiling pyo3 v0.22.6
   Compiling pyo3-macros v0.22.6
   Compiling sum_up_to v0.1.0 (/Users/ashutoshpednekar/Desktop/sum_up_to)
    Finished `release` profile [optimized] target(s) in 3.37s
📦 Built wheel for CPython 3.12 to dist/sum_up_to-0.1.0-cp312-cp312-macosx_11_0_arm64.whl
(base) sum_up_to ❯ ls dist
sum_up_to-0.1.0-cp311-cp311-macosx_11_0_arm64.whl sum_up_to-0.1.0-cp39-cp39-macosx_11_0_arm64.whl
sum_up_to-0.1.0-cp312-cp312-macosx_11_0_arm64.whl
```

It’s doing all the heavy lifting—compiling, packaging, integrating—so you can sit back and take the credit. Trust me, as your project gets bigger... you'll have to sit back a lot 😉

## Let's use classes

A class in python is complemented by structs in rust, with the `pyclass` and `pymethods` macros, here's how

```rust
#[pyclass]
struct Add{
    pub n: i32
}

#[pymethods]
impl Add{
    #[new]
    fn new(n: i32) -> Self{
        Self{n}
    }

    fn up_to(&self) -> PyResult<i32>{
        Ok((1..=self.n).sum())
    }
}
```

There's no such thing as a constructor in the language as far as rust is concerned, you can have any function that returns `Self` act like one. Pyo3's `new` macro leverages the `new` convention and makes it the constructor when invoked from python

Now update the module definition to include this class instead of a function

```rust
#[pymodule]
fn sum_up_to(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<crate::Add>()?;
    Ok(())
}
```

### Compile and run :)

Now compile with `maturin develop`, and it's ready to be used from python

```python
Python 3.12.7 (main, Oct  1 2024, 02:05:46) [Clang 16.0.0 (clang-1600.0.26.3)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from sum_up_to import Add
>>> a = Add(1000000)
>>> a.up_to()
1784293664
>>>
```

That’s all you need to dive in, here are a few juicy tidbits to keep in mind.

### Accept Variadic Arguments  

Ah, `*args`, the Swiss Army knife of Python argument handling. In Python, we embrace the chaos of variadic arguments, but in Rust? Not so much. Static languages tend to roll their eyes and say, "Why not just use a `Vec` like civilized folks?"  

Still, if you must channel your inner Pythonista in Rust, PyO3 has your back with `PyTuple`. This nifty type lets you handle variadic arguments the Python way. You grab the `PyTuple` and iterate through it like any other iterator, feeling both rebellious and sophisticated.  

And because PyO3 believes in doing things with flair, you can even specify the function signature in a Pythonic way using annotations. Here's an example:  

```rust
use pyo3::prelude::*;
use pyo3::types::PyTuple;

#[pyfunction]
#[pyo3(signature = (name, *args))]
fn accept_args(name, args: &PyTuple) -> PyResult<()> {
    println!("Hey {}", &name);
    for arg in args {
        println!("Got: {:?}", arg);
    }
    Ok(())
}

#[pymodule]
fn example_module(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(accept_args, m)?)?;
    Ok(())
}
```

### What's Happening Here?  
1. **`&PyTuple` Magic**: This is PyO3's way of saying, "I see your variadic arguments and raise you proper type handling."  
2. **Iteration**: Loop over the tuple like any iterator. No fancy ceremony required.  
3. **Annotation Swagger**: With `#[pyfunction]`, you tell Python this function plays nice with its `*args` syntax.  

See? Python-like chaos, Rust-level safety. A beautiful mess.

### Pass Python Objects Around Threads

Rust achieves its safety magic ⚙️ by tracking variable scope and ensuring objects are dropped from the stack when their lifetimes end—unless you're dealing with heap-allocated data or bending the rules with the `'static` lifetime. While this works well for synchronous code, it gets tricky when you need to use `tokio::spawn` or send objects across threads. For that, objects must implement the `Send` trait—which most types don't. 😅

The accepted way to deal with this is to wrap your object in an `Arc<Mutex<T>>`. However, Python objects are even trickier to manage because of their complex lifetimes and ownership rules. Thankfully, PyO3 provides a handy abstraction: `Py<T>`.

Here's what you need to know about using `Py<T>`:

- You need a `py: Python` object to create or convert Rust or PyO3 types into `Py<T>`.
- Functions annotated with `#[pyfunction]` or methods under `#[pymethods]` automatically receive `py: Python` as a parameter.
- In other cases, you can obtain the Python GIL and create a `Py<PyAny>` object like this:

```rust
use pyo3::prelude::*;

fn create_python_object() -> PyResult<String> {
    Python::with_gil(|py| {
        let py_obj = py.eval("'Hello from Python!'", None, None)?; // Example Python eval
        Ok(py_obj.extract::<String>()?) // Convert the Python object to a Rust String
    })
}
```
Once you have a `Py<T>`, you can safely pass it around threads! Use an `Arc` if needed, allowing you to achieve "fearless concurrency" 🚀 even with Python objects. 🎉

### Working with the tokio reactor and async

Async python, like rust have what's called colored functions, defined as `async def` and `async fn` respectively, which you can then await when needed. Before we proceed, here's a crude explanation of how async rust/ tokio works, I've posted another post diving deep into this, it's a work in progress but should help understand the gist of it





