# os-aio-pod

[![Build Status](https://www.travis-ci.org/cfhamlet/os-aio-pod.svg?branch=master)](https://www.travis-ci.org/cfhamlet/os-aio-pod)
[![codecov](https://codecov.io/gh/cfhamlet/os-aio-pod/branch/master/graph/badge.svg)](https://codecov.io/gh/cfhamlet/os-aio-pod)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/os-aio-pod.svg)](https://pypi.python.org/pypi/os-aio-pod)
[![PyPI](https://img.shields.io/pypi/v/os-aio-pod.svg)](https://pypi.python.org/pypi/os-aio-pod)


A container of AIO components.

This project is a framework for combining multiple AIO components into one. For example, you can easily extend your TCP server with a HTTP server to offer HTTP API. Usage is simple, write regular coroutine and config file, start with the command line tool, the framework will take care of the work loop.

Each of the coroutine is a magic bean, this framework is a magic pod.



## Conception

Custom coroutine is packed as a ``asyncio.Task``, we call it: *bean*. Thanks to the Python asyncio, all beans can work together. A runner named *pod* maintains the beans and the whole work loop life cycle.

Each bean has a unique id. label can also be used for identifying one or more beans.

You can access other beans by using a context object with id or label.

Signals can be  dispatched to each beans which registered callback function.

## Install

```
pip install os-aio-pod
```

There are some extra packages can be installed for more  features.

| subpackage | install command                        | enables                                                      |
| ---------- | -------------------------------------- | ------------------------------------------------------------ |
| uvloop     | ``pip install os-aio-pod[uvloop]``     | enable [uvloop](https://github.com/MagicStack/uvloop)        |
| uvicorn    | ``pip install os-aio-pod[uvicorn]``    | enable [uvicorn](https://github.com/encode/uvicorn) http server adapter |
| aiohttp | ``pip install os-aio-pod[aiohttp]`` | enable [aiohttp](https://github.com/aio-libs/aiohttp) http server adapter |
| aiomonitor | ``pip install os-aio-pod[aiomonitor]`` | enable [aiomonitor](https://github.com/aio-libs/aiomonitor) adapter |



## Usage

### Quick start

1. Write your coroutine function

    ```
    # example.py
    import asyncio

    async def helloworld(**kwargs):
        await asyncio.sleep(1)
        print("hello world!", kwargs)
    ```

2. run with ``os-aio-pod``
 
    ```
    os-aio-pod run example.helloworld:hi="Ozzy"
    ```

### APIs

#### Custom coroutine

Actually, there are three types of coroutine code for your choice:

1. Regular coroutine, the ``hello`` object of the following example.

    ```
    import asyncio
    
    async def hello_world(**kwargs):
        print('hello world!')
        await asyncio.sleep(1)
    
    hello = hello_world()
    ```

2. Regular coroutine fucntion, the ``hello_world`` function of the above example. Keyword arguments can be set in the config file.
3. A class with ``async def __call__(self)`` method and have context as init arguments:

    ```
    class HelloWorld(object):
    
        def __init__(self, context):
            self.context = context
            
        async def __call__(self, **kwargs):
            print('hello world!')
            await asyncio.sleep(1)
    ```

#### Context

When you use class type coroutine, you can use the context to communicate with the framework and other beans.

Since v0.1.27, ``pass_context`` decorator can be used for passing context to function as the first argument if it is invoked by the framework. ``lable`` can also be specified as argument ``@pass_context(label="app")``

```
from os_aio_pod.decorators import pass_context

@pass_context
async def hello_world(context, **kwargs):
    print(context, kwargs)
```

#### Signals

Thanks to [asyncio_dispatch](https://github.com/lenzenmi/asyncio_dispatch), we easily can register and deliver signals.

Typically, you should only use context APIs to process signals.

The system ``SIGINT``,``SIGTERM`` are caught by the framework to handler shutdown stuff after dispatch to each registered callback.

Other system signals are not supported yet.

### Configure

Config file is a regular Python file, all upper case variables will pass to the frame work which can be accessed later. The reserved key words:

* ``BEANS``: a list of bean config dict, the reserved key words of each bean config are:  ``core``, ``label``, other keyword arguments will pass to your function

    ``core``:  string path of your coroutine

    ``label``: optional, can be used to trace your bean

* ``LOG_LEVEL``: logger level, default  ``INFO``
* ``LOOP_TYPE``: default is ``asyncio``, can be ``uvloop`` when you install uvloop
* ``DEBUG``: enable debug mode, default ``False``
* ``STOP_WAIT_TIME``: the wait time when recieve signal(``SIGINT``, ``SIGTERM``). Once timeout, all unfinished bean will be cancelled. Default is ``None``, indicate wait until all beans done



Example:

``config.py``

```
BEANS = [
    {
        'core' : 'hello_world.HelloWorld',
        'label': 'first-bean',
        'key1' : 'value1',
    }
]

LOG_LEVEL      = 'debug'
LOOP_TYPE      = 'asyncio'
DEBUG          = False
STOP_WAIT_TIME = 10
```



### Command line

``os-aio-pod`` command can be used to start the whole framework, the typical usage:

```
$ os-aio-pod run -c config.py
```

or quick start

```
$ os-aio-pod run [awaitable-func1:k1=v1,k2=v2] [awaitable-func2:k3=v3,k4=v4]
```

The reserved config key words(exclude ``BEANS``) can be set by passing command line options.

```
$ os-aio-pod run --help
```



### Built-In Components

There are some built-in adapters can be used for convenient:


* built-in simple server class ``os_aio_pod.contrib.simple.Server``

    It is a scaffold base class for simple server

    ```
    from os_aio_pod.contrib.simple import Server

    class YourServer(Server):

        # can be async/sync 
        async def startup(self, **kwargs):
            pass

        # can be async/sync 
        async def cleanup(self, **kwargs):
            pass

        async def run(self, **kwargs):
            print(self.config)

        # on kill(Ctrl+C)
        def on_stop(self, **kwargs):
            pass
    ```

* [ptpython](https://github.com/prompt-toolkit/ptpython), python REPL


    ```
    pip install ptpython contextvars
    ```

    ```
    BEANS = [
        {
            'core': 'os_aio_pod.contrib.pypython.TelnetServerAdapter',
        }
    ]
    ```
    you can connect this server with telnet

* [uvicorn](https://github.com/encode/uvicorn), a lightning-fast ASGI server

    ```
    pip install uvicorn
    ```

    ```
    BEANS = [
        {
            'core': 'os_aio_pod.contrib.uvicorn.UvicornAdapter',
            'app' : 'your.app.object.path'
        }
    ]
    ```

    a context object named ``aio_pod_context`` will attached to the app object

* [aiohttp](https://github.com/aio-libs/aiohttp), a well known aio http server

    ```
    pip install aiohttp
    ```

    ```
    BEANS = [
        {
            'core': 'os_aio_pod.contrib.aiohttp.WebAdapter',
            'app' : 'your.app.object.path'
        }
    ]
    ```

    a context object named ``aio_pod_context`` will attached to the app object

* [aiomonitor](https://github.com/aio-libs/aiomonitor), adds monitor and python REPL capabilities for asyncio application
    ```
    pip install aiomonitor
    ```

    ```
    BEANS = [
        {
            'core': 'os_aio_pod.contrib.aiomonitor.AioMonitorAdapter',
        }
    ]
    ```

* built-in tcp server

    An event driven server can be inherited from ``os_aio_pod.contrib.tcp_server.Server``(default server).
    
    If protocol is configured, low-level networking protocol interface will be used instead of the server's on_connect method. The server instance can be accessed with ``your_protocol.server``

    ```
    BEANS = [
        {
            'core': 'os_aio_pod.contrib.tcp_server.TCPServerAdapter',
            # 'protocol': 'your.asyncio.Protocol.path'
            # 'server': 'your.event.driven.server'
        }
    ]
    ```

* built-in producer-consumer model

    One producer and multi-consumers is a common model. You can inherit from ``os_aio_pod.contrib.pcflow.Server``(which is inherit from built-in simple server) and implement ``produce`` and ``consume`` methods to run as this model.

    ```
    import asyncio

    from os_aio_pod.contrib.pcflow import Server


    class YourProducerConsumerServer(Server):
        def startup(self, **kwargs):
            self.stopping = False

        def on_stop(self, **kwargs):
            self.stopping = True

        async def produce(self, **kwargs):
            while not self.stopping:
                await asyncio.sleep(1)
                yield 1

        async def consume(self, obj, **kwargs):
            print(obj) 
    ```


    ```
    BEANS = [
        {
            'core': 'YourProducerConsumerServer',
            'consumer_num': 10,
        }
    ]
    ```

## Unit Tests

```
tox
```

## License

MIT licensed.
