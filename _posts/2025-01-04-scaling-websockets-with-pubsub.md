

So.. The OS has threads right? These are lightweight equivalents to processes that share memory and are juggled around by the OS scheduler to allow for concurrent execution. But these are usually used for CPI bound tasks because when we use it for our IO operations like, say API calls, which mostly wait, hence make the scheduler do a lot of work, which can be a huge overhead. Also, OS threads are limited by the number of cores your system has

So there's this elusive concept called green threads, which are managed in the user space, hence the overhead of spinning them up, pausing them and juggling work around 

> P.S. These are just the starter points, will try to finish by next week :)
