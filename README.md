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

Three steps:

1.  write your coroutine
2. write a config file(Python file)
3. run with ``os-aio-pod``

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



The reserved config key words(exclude ``BEANS``) can be set by passing command line options.

```
$ os-aio-pod run --help
```



### Built-In Components

There are some built-in adapters can be used for convenient.

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

    ```
    BEANS = [
        {
            'core': 'os_aio_pod.contrib.tcp_server.TCPServerAdapter',
            'protocol': 'your.asyncio.Protocol.path'
            # 'server': 'your.event.driven.server'
        }
    ]
    ```

    a event driven server can be inherited(from ``os_aio_pod.contrib.tcp_server.Server``) and configure attach to your protocol object for more fuctional purpose


## Unit Tests

```
tox
```

## License

MIT licensed.
