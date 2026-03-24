+++
title = "Python 异步编程 02：asyncio 事件循环"
author = "CC"
date = 2026-03-24T00:00:00
tags = ["asyncio", "python"]
categories = ["note"]
draft = false
toc = true
+++

事件循环是 `asyncio` 的核心组件，负责调度和执行协程、管理I/O操作、处理回调等。本部分将深入探讨事件循环的内部机制、工作原理以及如何自定义管理事件循环。

事件循环是一个无限循环，它不断地从队列中取出任务并执行，直到所有任务都完成。在 `asyncio` 中，事件循环由`asyncio.AbstractEventLoop`抽象类定义，不同平台有不同的实现：

- **Unix/Linux**：`SelectorEventLoop` - 使用 `selectors` 模块
- **Windows**：`ProactorEventLoop` - 使用 Windows `IOCP`

<!--more-->
事件循环是相对低层的组件，通常更推荐使用高级接口来管理事件循环。

## 获取事件循环

- `asyncio.get_running_loop()` 获取当前系统的线程中正在运行的事件循环（3.7 引入）
- `asyncio.get_event_loop()` 获取当前的事件循环。
  - 在协程/coroutine或回调/callbacks中调用时，返回正在运行的事件循环。
  - 如果没有 running event loop，返回 `get_event_loop_policy().get_event_loop()` 的结果。
  - 这个函数行为，在自定义事件循环策略时，会非常复杂。因此在协程和回调函数内部，建议使用 `asyncio.get_running_loop()` 来获取当前运行的事件循环。
- `asyncio.set_event_loop(loop)` 将 loop 设置为当前的事件循环。
- `asyncio.new_event_loop()` 创建一个新的事件循环。

`get_event_loop()`, `set_event_loop()`, `new_event_loop()` 这些函数的行为会因为自定义事件循环策略而改变。

示例代码

```python
import asyncio

# 获取当前线程的事件循环
loop = asyncio.get_event_loop()

# 在Python 3.7+中，推荐使用
async def main():
    loop = asyncio.get_running_loop()
    print(f"Current event loop: {loop}")

asyncio.run(main())
```

## 事件循环的方法

### 执行和停止事件循环

- `loop.run_until_complete(future)` 运行直到完成指定的 Future 实例。
- `loop.run_forever()` 运行事件循环，直到 `stop()` 方法停止事件循环。
- `loop.stop()` 停止事件循环。
- `loop.is_running()` 返回事件循环是否正在运行。
- `loop.is_closed()` 如果事件循环已关闭，返回 True。
- `loop.close()` 关闭事件循环。
  - 调用 `close()` 方法后，事件循环将无法再运行。
  - 所有待处理的 callbacks 将被丢弃。
  - 清理所有队列/queue，关闭处理器/executor，不会等待处理器执行完成。
  - 幂等且不可逆。执行 close() 后，不应该再调用其他方法。
- `loop.shutdown_asyncgens()` 关闭所有异步生成器（async generators）的资源。
- `loop.shutdown_default_executor(timeout=None)` 关闭默认的 executor（线程池）。
  - 【注】：在使用 `asyncio.run()` 启动事件循环时，不需要调用 `shutdown_asyncgens()` 或 `shutdown_default_executor()` 方法，因为 `asyncio.run()` 会在事件循环关闭时自动处理这些资源。

### 回调函数的调度

- `loop.call_soon(callback, *args, context=None)` 在事件循环的下一次迭代中执行回调函数，`*args` 是回调函数的参数，`context` 是回调函数的上下文。
  - 返回 `asyncio.Handle` 实例，可用于取消回调函数的执行。
  - 回调函数按注册顺序执行。每个回调函数只会执行一次。
  - 非线程安全。
- `loop.call_soon_threadsafe(callback, *args, context=None)` 线程安全版本的 `call_soon()` 方法。

### 延迟回调函数的调度

- `loop.call_later(delay, callback, *args, context=None)` 在指定延迟时间后执行回调函数。
  - 返回 `asyncio.TimerHandle` 实例，可用于取消延迟函数的执行。
- `loop.call_at(when, callback, *args, context=None)` 在指定时间点执行回调函数。
  - 行为与 `call_later()` 方法相同。
  - `when` 时间戳，int 或 float 类型，使用 `loop.time()` 的参考时间。
- `loop.time()` 方法根据事件循环内部的单调时钟返回当前时间。

### 创建 Future 和 Task

- `loop.create_future()` 创建一个 `asyncio.Future` 实例。
- `loop.create_task(coro, *, name=None, context=None, eager_start=None, **kwargs)` 调度一个协程对象的执行，返回一个 `Task` 实例。
  - name 参数 3.8 引入
  - context 参数 3.11 引入
  - kwargs 参数 3.13.3 引入，3.13.4 部分回滚
  - 3.14 传递所有 kwargs
- `loop.set_task_factory(factory)` 设置任务工厂，用于创建 `Task` 实例。
- `loop.get_task_factory()` 获取当前的任务工厂，或 None 如果没有任务工厂。

### 创建网络连接

- `async loop.create_connection(...)` 开启一个流式传输连接，连接到由主机和端口指定的指定地址。
- `async loop.create_datagram_endpoint(...)` 创建一个数据报连接。
- `async loop.create_unix_connection(...)` 创建一个 Unix 连接。

### 创建网络服务器

- `async loop.create_server(...)` 创建一个 TCP 服务器（套接字类型: SOCK_STREAM），监听主机地址的端口 。
- `async loop.create_unix_server(...)` 与 `create_server()` 类似，但适用于 AF_UNIX 套接字家族。
- `async loop.connect_accepted_socket(protocol_factory, sock,...)` 将已接受的连接包装成传输/协议对。
  - 当服务器需要接收 asyncio 外部的连接是，可以使用它包装外部连接，然后使用 asyncio 处理。

### 传输文件

- `async loop.sendfile(transport, file, offset=0, count=None, *, fallback=True)` 通过 `transport` 发送文件 。返回发送的总字节数。

### 查看文件描述符

- `loop.add_reader(fd, callback, *args)` 开始监控 fd 文件描述符的读取可用性，一旦 fd 可用，就用指定的参数调用回调函数。
- `loop.remove_reader(fd)` 停止监控 fd 文件描述符的读取可用性。如果之前有监控，返回 `True` 。
- `loop.add_writer(fd, callback, *args)` 开始监控 fd 文件描述符的写入可用性，一旦 fd 可用，就用指定的参数调用回调函数。
- `loop.remove_writer(fd)` 停止监控 fd 文件描述符的写入可用性。

### 错误处理 API

- `loop.set_exception_handler(handler)` 设置异常处理器。
- `loop.get_exception_handler()` 获取当前的异常处理器。如果没有设置，返回 `None` 。
- `loop.default_exception_handler(context)` 默认异常处理器。
- `loop.call_exception_handler(context)` 调用异常处理器。

### 启用调试模式

- `loop.set_debug(enable: bool)` 设置调试模式。
- `loop.get_debug()` 获取调试模式是否启用。
  - 如果环境变量 `PYTHONASYNCIODEBUG` 为非空字符串，其默认值为 `True`。否则，默认值为 `False`。
- `loop.slow_callback_duration` 改属性用于设定慢回调的阈值，默认值为 `0.1` 秒（100ms）。如果回调函数执行时间超过该阈值，就会被标记为慢回调。

### 其他方法

- TLS upgrade
- Working with socket objects directly
- DNS
- Working with pipes
- Unix signals
- Executing code in thread or process pools
- Running subprocesses

## callback handles

- `class asyncio.Handle` 由 `call_soon()/call_soon_threadsafe()` 方法返回的回调包装对象。它有以下方法：
  - `get_context()` 获取回调函数的上下文。
  - `cancel()` 取消回调函数的执行。
  - `cancelled()` 返回回调函数是否已被取消。
- `class asyncio.TimerHandle` 由 `call_later()/call_at()` 方法返回的延迟回调包装对象。
  - `when()` 返回回调函数执行时间的时间戳，`float` 类型。

## Server 对象

- `class asyncio.Server` server 对象是异步的上下文管理器。

```python
srv = await loop.create_server(...)

async with srv:
    # some code

# At this point, srv is closed and no longer accepts new connections.
```

## 事件循环的两种实现

Asyncio 提供两种不同的事件环实现： `SelectorEventLoop` 和 `ProactorEventLoop。`

- `class asyncio.SelectorEventLoop` 使用给定平台最高效的 `selector` 。适用于 Unix 和 Windows。
- `class asyncio.ProactorEventLoop` 使用 “I/O Completion Ports” (IOCP)，适用于 Windows 平台。

## 事件循环策略

事件循环策略（Event loop policy）是一个全局对象，用于获取和设置当前事件循环，以及创建新事件循环。可以修改默认策略，使用 built-in 的不同的事件循环实现， 或由自定义策略，来改变事件循环的行为。

> 警告: 策略已被弃用，并将在 Python 3.16 中被移除。鼓励用户使用 `asyncio.run()` 函数，或使用 `asyncio.Runner` 和 `loop_factory` 以实现所需的事件循环。

**使用uvloop**：uvloop是一个高性能的事件循环实现，基于libuv

```python
# 安装uvloop
# pip install uvloop

import asyncio
import uvloop

# 设置uvloop为默认事件循环
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

async def main():
    print("Using uvloop event loop")
    # 你的代码

asyncio.run(main())
```

## 示例

使用 `call_later()` 方法打印时间。

```python
import asyncio
import datetime as dt


def display_date(end_time, loop):
    print(dt.datetime.now())
    if (loop.time() + 1.0) < end_time:
        loop.call_later(1, display_date, end_time, loop)
    else:
        loop.stop()


loop = asyncio.new_event_loop()

# Schedule the first call to display_date()
end_time = loop.time() + 5.0
loop.call_soon(display_date, end_time, loop)

# Blocking call interrupted by loop.stop()
try:
    loop.run_forever()
finally:
    loop.close()
```

`asyncio.run()` 版本

```python
import asyncio
import datetime as dt


async def display_date2():
    loop = asyncio.get_running_loop()
    end_time = loop.time() + 5.0
    while True:
        print(dt.datetime.now())
        if (loop.time() + 1.0) >= end_time:
            break
        await asyncio.sleep(1)


asyncio.run(display_date2())
```
