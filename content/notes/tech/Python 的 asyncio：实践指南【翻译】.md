+++
title = "Python 的 asyncio：实践指南【翻译】"
author = "CC"
date = 2026-03-17T00:00:00
tags = ["python", "asyncio"]
categories = ["article"]
draft = false
toc = true
+++

![Async IO in Python: A Complete Walkthrough](https://files.realpython.com/media/A-Complete-Walkthrough-of-Pythons-Asyncio_Watermarked.5b6b9a01fdc9.jpg)

Python 的 `asyncio` 库使你能够使用 `async` 和 `await` 关键字编写并发代码。Python 中异步 I/O 的核心构建块是可等待对象——最常见的是协程——由事件循环异步调度和执行。这种编程模型让你能够在单个执行线程中高效管理多个 I/O 密集型任务。

在本教程中，你将学习 Python `asyncio` 的工作原理、如何定义和运行协程，以及何时使用异步编程来提高执行 I/O 密集型任务的应用程序性能。

**通过本教程，你将了解：**

- Python 的 `asyncio` 提供了一个框架，用于使用 **协程**、**事件循环** 和 **非阻塞 I/O 操作** 编写单线程 **并发代码**。
- 对于 I/O 密集型任务，异步 I/O **通常可以优于多线程**——尤其是在管理大量并发任务时——因为它避免了线程管理的开销。
- 当你的应用程序花费大量时间等待 **I/O 操作**（如网络请求或文件访问），并且你希望 **并发运行许多此类任务** 而不创建额外线程或进程时，应该使用 `asyncio`。

通过实践示例，你将获得实用技能，使用 `asyncio` 编写高效的 Python 代码，随着 I/O 需求的增加而优雅地扩展。

> **参加测验** 通过我们的交互式 "Python 的 asyncio：实践指南" 测验测试你的知识。完成后你将收到分数，帮助你跟踪学习进度：
>
> [交互式测验](https://realpython.com/quizzes/async-io-python/)：测试你对 `asyncio` 并发的知识，包括协程、事件循环和高效的 I/O 密集型任务管理。

## 异步 I/O 初探

在探索 `asyncio` 之前，值得花点时间将异步 I/O 与其他并发模型进行比较，看看它如何融入 Python 更广泛、有时令人眼花缭乱的生态系统。以下是一些基本概念：

- **并行/Parallelism** 同一时间执行的多个操作。
- **多进程/Multiprocessing** 是实现并行的一种方法，需要将任务分散到计算机的中央处理单元 (CPU) 核心上。多进程非常适合 CPU 密集型任务，例如紧密绑定CPU的 `for` 循环** 和数学计算。
- **并发/Concurrency** 是一个比并行稍宽泛的术语，指多个任务能够以重叠的方式运行。并发不一定意味着并行。
- **线程/Threading** 是一种并发执行模型，其中多个线程轮流执行任务（系统在一段时间内能够处理多个任务）。单个进程可以包含多个线程。由于 **全局解释器锁 (GIL)**，Python 与线程的关系很复杂，但这超出了本教程的范围。

线程适用于 **I/O 密集型任务**。I/O 密集型任务主要由大量等待 **输入/输出 (I/O)** 完成的时间组成，而 **CPU 密集型任务** 的特点是计算机核心从开始到结束持续努力工作。

Python **标准库** 通过其 `multiprocessing`、`concurrent.futures` 和 `threading` 包长期支持这些模型。

现在是时候添加一个新成员了。近年来，一种单独的模型已被更全面地构建到 **CPython** 中：**asynchronous I/O**，通常称为 **async I/O**。此模型通过标准库的 `asyncio` 包以及 `async` 和 `await` 关键字启用。

Python 文档将 `asyncio` 包称为 [编写并发代码的库](https://docs.python.org/3/library/asyncio.html)。然而，异步 I/O 不是线程或多进程。它不是建立在这两者之上的。

异步 I/O 是一种单线程、单进程技术，使用 [协作式多任务处理](https://en.wikipedia.org/wiki/Cooperative_multitasking)。尽管在单个进程中使用单个线程，异步 I/O 仍会给人并发的感觉。**协程**——或简称 **coro**——是异步 I/O 的核心特性，可以并发调度，但它们本身并不是并发的。

重申一下，异步 I/O 是并发编程的模型，但不是并行。它与线程的关系比与多进程更密切，但它与两者都不同，是并发生态系统中的独立成员。

还有一个术语。什么是 **异步**？这不是一个严格的定义，但就本教程而言，你可以考虑两个关键属性：

1. **异步例程/routines** 可以在等待结果时 *暂停* 其执行，并允许其他例程在此期间运行。
2. **异步代码/code** 通过协调异步例程来实现任务的并发执行。

下面的图表将所有内容放在一起。白色术语表示概念，绿色术语表示它们的实现方式：

![Concurrency versus parallelism](https://files.realpython.com/media/Screen_Shot_2018-10-17_at_3.18.44_PM.c02792872031.jpg)

要深入探讨线程与多进程与异步 I/O 的区别，请在此处暂停并查看 [使用并发加速 Python 程序](https://realpython.com/python-concurrency/) 教程。

### 异步 I/O 解释

异步 I/O 一开始可能看起来违反直觉和自相矛盾。如何使用单个线程和单个 CPU 核心实现并发代码？Miguel Grinberg 的 [PyCon](https://realpython.com/pycon-guide/) 演讲非常漂亮地解释了一切：

> 国际象棋大师朱迪特·波尔加 (Judit Polgár) 举办国际象棋表演赛，与多位业余选手对弈。她有两种方式进行表演：*同步* 和 *异步*。
>
> 假设：
>
> - 24 位棋手
> - 朱迪特每步棋需要 5 秒
> - 每位棋手每步棋需要 55 秒
> - 平均每场比赛 30 对棋步（共 60 步）
>
> **同步版本**：朱迪特一次下一场比赛，从不同时下两场，直到比赛完成。每场比赛需要 *(55 + 5) \* 30 == 1800* 秒，即 30 分钟。整个表演需要 *24 \* 30 == 720* 分钟，即 **12 小时**。
>
> **异步版本**：朱迪特从一张桌子移动到另一张桌子，在每张桌子上走一步。她离开桌子，让对手在等待时间内走下一步。在所有 24 场比赛中走一步需要朱迪特 *24 \* 5 == 120* 秒，即 2 分钟。整个表演现在减少到 *120 \* 30 == 3600* 秒，即只有 **1 小时**。（[来源](https://youtu.be/iG6fr81xHKA?t=4m29s)）

只有一个朱迪特·波尔加，一次只走一步棋。异步下棋将表演时间从 12 小时缩短到 1 小时。异步 I/O 将这一原理应用于编程。在异步 I/O 中，程序的事件循环——稍后会详细介绍——运行多个任务，允许每个任务在最佳时间轮流运行。

异步 I/O 处理长时间运行的 **函数**——比如上面例子中的一整场象棋比赛 —— 会阻塞程序的执行（朱迪特·波尔加的时间）。异步 I/O 以这样的方式进行管理，当一个程序被阻塞时，安排其他程序运行。在象棋示例中，当前一个棋手正在走棋时，朱迪特与另一位棋手对弈。

### 异步 I/O 并不简单

构建耐用的多线程代码可能具有挑战性且容易出错。异步 I/O 避免了在多线程设计中可能遇到的一些潜在障碍。然而，这并不是说 **异步编程** 在 Python 中是一项简单的任务。

请注意，当稍微深入表面时，异步编程可能会变得棘手。Python 的异步模型围绕回调、协程、事件、传输、协议和 [futures](https://docs.python.org/3/library/asyncio-future.html#asyncio.Future) 等概念构建——甚至只是术语本身就可能令人生畏。

话虽如此，Python 中异步编程的生态系统已经显著改善。`asyncio` 包已经成熟，现在提供了稳定的 **API**。此外，其文档已经进行了相当大的改革，并且关于该主题的一些高质量资源也已经出现。

## 使用 asyncio 在 Python 中实现异步 I/O

现在你已经了解了异步 I/O 作为并发模型的一些背景，是时候探索 Python 的实现了。Python 的 `asyncio` 包及其两个相关关键字 `async` 和 `await` 服务于不同的目的，但一起帮助声明、构建、执行和管理异步代码。

### 协程和协程函数

异步 I/O 的核心是 **协程** 的概念，它是一个可以暂停执行并稍后恢复的对象。同时，它可以将控制权传递给事件循环，事件循环可以执行另一个协程。协程对象是调用 **协程函数**（也称为 **异步函数**）的结果。使用 `async def` 语法来定义一个。

在编写第一个异步代码之前，考虑以下同步运行的示例：

```python
import time

def count():
    print("One")
    time.sleep(1)
    print("Two")
    time.sleep(1)

def main():
    for _ in range(3):
        count()

if __name__ == "__main__":
    start = time.perf_counter()
    main()
    elapsed = time.perf_counter() - start
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")
```

`count()` 函数 **打印** `One` 并等待一秒钟，然后打印 `Two` 并等待另一秒钟。 `main()` 函数中的循环执行 `count()` 三次。在 `if __name__ == "__main__"` 条件下，在执行开始时记录当前时间，调用 `main()`，计算总时间，并在屏幕上显示它。

当 **运行此脚本** 时，将获得以下输出：

```bash
$ python countsync.py
One
Two
One
Two
One
Two
countsync.py executed in 6.03 seconds.
```

该脚本交替打印 `One` 和 `Two`，每次打印操作之间需要一秒钟。总共需要超过六秒钟才能运行。

如果你更新此脚本以使用 Python 的异步 I/O 模型，那么它会看起来像以下内容：

```python
import asyncio

async def count():
    print("One")
    await asyncio.sleep(1)
    print("Two")
    await asyncio.sleep(1)

async def main():
    await asyncio.gather(count(), count(), count())

if __name__ == "__main__":
    import time

    start = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - start
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")
```

现在，使用 `async` 关键字将 `count()` 转换为协程函数，该函数打印 `One`，等待一秒钟，然后打印 `Two`，再等待一秒钟。使用 `await` 关键字来 *等待* `asyncio.sleep()` 的执行。这将控制权交还给程序的事件循环，说：*我将睡眠一秒钟。在此期间继续运行其他东西。*

`main()` 函数是另一个协程函数，它使用 `asyncio.gather()` 并发运行三个 `count()` 实例。使用 `asyncio.run()` 函数启动 [事件循环](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio-event-loop) 并执行 `main()`。

比较此版本与同步版本的性能：

```bash
$ python countasync.py
One
One
One
Two
Two
Two
countasync.py executed in 2.00 seconds.
```

由于异步 I/O 方法，总执行时间仅为两秒多一点，而不是六秒，展示了 `asyncio` 对 I/O 密集型任务的效率。

虽然使用 `time.sleep()` 和 `asyncio.sleep()` 可能看起来很平常，但它们可以作为涉及等待时间的耗时过程的替代品。对 `time.sleep()` 的调用可以表示耗时的阻塞函数调用，而 `asyncio.sleep()` 用于代表也需要一些时间完成的 **非阻塞调用**。

正如在下一节中将看到的，等待包括 `asyncio.sleep()` 在内的任何内容的好处是，周围的函数可以暂时将控制权让给另一个更能立即做某事的函数。相比之下，`time.sleep()` 或任何其他阻塞调用与异步 Python 代码不兼容，因为它会在整个睡眠期间停止所有内容。

### async 和 await 关键字

在这一点上，需要对 `async`、`await` 以及它们帮助创建的协程函数进行更正式的定义：

- `async def` 语法结构引入了 **协程函数** 或 **异步生成器**。
- `async with` 和 `async for` 语法结构分别引入了异步 `with` 语句 和 `for` 循环。
- `await` 关键字暂停协程的执行，并将控制权交还给事件循环。

为了稍微澄清最后一点，当 Python 在协程函数 `g()` 的内部中遇到 `await f()` 表达式时，`await` 告诉事件循环：*暂停 `g()` 的执行，直到 `f()` 的结果返回。在此期间，让其他东西运行。*

在代码中，最后一个要点大致如下：

```python
async def g():
    result = await f()  # 暂停并在 f() 返回时返回 g()
    return result
```

关于何时以及如何使用 `async` 和 `await`，也有一套严格的规则。无论你是仍在学习语法还是已经接触过使用 `async` 和 `await`，这些规则都很有帮助：

- 使用 `async def` 语法结构，可以定义一个协程函数。它可以使用 `await`、`return` 或 `yield`，但所有这些都是可选的：
  - `await`、`return` 或两者都可以在常规协程函数中使用。要调用协程函数，必须通过 `await` 获取其结果，或直接在事件循环中运行它。
  - 在 `async def` 函数中使用 `yield` 会创建一个异步生成器。要迭代此生成器，可以使用 `async for` 循环或推导式。
  - `async def` 不可以使用 `yield from`，这会引发 `SyntaxError`。
- 在 `async def` 函数外部使用 `await` 也会引发 `SyntaxError`。只能在协程体中使用 `await`。

以下是总结这些规则的一些简洁示例：

```python
async def f(x):
    y = await z(x)  # OK - `await` 和 `return` 在协程中允许
    return y

async def g(x):
    yield x  # OK - 这是一个异步生成器

async def m(x):
    yield from gen(x)  # NO - SyntaxError

def n(x):
    y = await z(x)  # NO - SyntaxError（这里没有 `async def`）
    return y
```

最后，当使用 `await f()` 时，`f()` 必须是 **可等待** 的对象，它要么是另一个协程，要么是定义了 `.__await__()` **特殊方法** 并返回迭代器的对象。对于大多数目的，只需要关心协程即可。

下面是一个更详细的例子，说明异步 I/O 如何减少等待时间。假设有一个名为 `make_random()` 的协程函数，它不断生成范围 [0, 10] 内的随机整数，并在其中一个超过阈值时返回。在以下示例中，异步运行此函数三次。为了区分每个调用，使用颜色区分：

```python
import asyncio
import random

COLORS = (
    "\033[0m",  # End of color
    "\033[36m",  # Cyan
    "\033[91m",  # Red
    "\033[35m",  # Magenta
)

async def main():
    return await asyncio.gather(
        makerandom(1, 9),
        makerandom(2, 8),
        makerandom(3, 8),
    )

async def makerandom(delay, threshold=6):
    color = COLORS[delay]
    print(f"{color}Initiated makerandom({delay}).")
    while (number := random.randint(0, 10)) <= threshold:
        print(f"{color}makerandom({delay}) == {number} too low; retrying.")
        await asyncio.sleep(delay)
    print(f"{color}---> Finished: makerandom({delay}) == {number}" + COLORS[0])
    return number

if __name__ == "__main__":
    random.seed(444)
    r1, r2, r3 = asyncio.run(main())
    print()
    print(f"r1: {r1}, r2: {r2}, r3: {r3}")
```

该程序定义了 `makerandom()` 协程并使用三个不同的输入并发运行它。大多数程序将由小的模块化的协程和一个包装函数组成，该包装函数用于 **链接/chain** 每个较小的协程。我们在 `main()` 中收集三个任务，对 `makerandom()` 的三次调用就是我们的 **任务池**。

此示例中的随机数生成是 CPU 密集型任务，不过它的影响可以忽略不计。`asyncio.sleep()` 模拟了 I/O 密集型任务，这证明了只有 I/O 密集型或非阻塞任务才能从异步 I/O 模型中受益。

### 异步 I/O 事件循环

在异步编程中，事件循环类似一个**无限循环**，它监视协程，收集那些处于闲置状态的反馈，同事四处寻找可以执行的事情。在闲置状态协程所等待的任务完成时，事件循环会唤醒空闲的协程。

在现代 Python 中启动事件循环的推荐方法是使用 [`asyncio.run()`](https://docs.python.org/3/library/asyncio-runner.html#asyncio.run)。此函数负责获取事件循环，运行任务直到它们完成，并关闭循环。当同一代码中运行另一个异步事件循环时，不能调用此函数。

我们还可以使用 [`get_running_loop()`](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.get_running_loop) 函数获取运行中循环的实例：

```python
loop = asyncio.get_running_loop()
```

如果需要在 Python 程序中与事件循环交互，上述模式是一种很好的方法。`loop` 对象支持使用 `.is_running()` 和 `.is_closed()` 进行内省。例如，当你想通过将循环作为参数传递来 [调度一个回调](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio-example-lowlevel-helloworld) 时，它会很有用。请注意，如果没有运行中的事件循环，`get_running_loop()` 会引发 `RuntimeError` 异常。

更重要的是理解事件循环表面之下发生的事情。以下是值得强调的几点：

- 协程在与事件循环绑定之前本身不会做太多事情。
- 默认情况下，异步事件循环在单个线程和单个 CPU 核心上运行。在大多数 `asyncio` 应用程序中，只会有一个事件循环，通常在主线程中。在不同线程中运行多个事件循环在技术上是可能的，但通常不需要或不推荐。
- 事件循环是可插拔的。你可以编写自己的实现并让它运行任务，就像 `asyncio` 中提供的事件循环一样。

关于第一点，如果有一个等待其他协程的协程，那么孤立地调用它几乎没有效果：

```python
>>> import asyncio

>>> async def main():
...     print("Hello...")
...     await asyncio.sleep(1)
...     print("World!")
...

>>> routine = main()
>>> routine
<coroutine object main at 0x1027a6150>
```

在此示例中，直接调用 `main()` 会返回一个协程对象，无法孤立使用。需要使用 `asyncio.run()` 来安排 `main()` 协程在事件循环上执行：

```python
>>> asyncio.run(routine)
Hello...
World!
```

通常将 `main()` 协程包装在 `asyncio.run()` 调用中。可以使用 `await` 执行更低级别的协程。

最后，事件循环是 *可插拔的* 这一事实意味着我们可以使用任何一个可以实际运行的事件循环实现，并且这与你的协程结构无关。`asyncio` 包附带两种不同的 [事件循环实现](https://docs.python.org/3/library/asyncio-eventloop.html#event-loop-implementations)。

默认的事件循环实现取决于你的平台和 Python 版本。例如，在 Unix 上，默认通常是 [`SelectorEventLoop`](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.SelectorEventLoop)，而 Windows 使用 [`ProactorEventLoop`](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.ProactorEventLoop) 以获得更好的子进程和 I/O 支持。

第三方事件循环也可用。例如，[uvloop](https://github.com/MagicStack/uvloop) 包提供了一个替代实现，承诺比 `asyncio` 循环更快。

### asyncio REPL

从 **Python 3.8** 开始，`asyncio` 模块包含一个专门的交互式 shell，称为 [asyncio REPL](https://docs.python.org/3/library/asyncio.html#asyncio-cli)。此环境允许你直接在顶层使用 `await`，而无需将代码包装在 `asyncio.run()` 调用中。此工具有助于实验、调试和学习 Python 中的 `asyncio`。

要启动 **REPL**，你可以运行以下命令：

```bash
$ python -m asyncio
asyncio REPL 3.13.3 (main, Jun 25 2025, 17:27:59) ... on darwin
Use "await" directly instead of "asyncio.run()".
Type "help", "copyright", "credits" or "license" for more information.
>>> import asyncio
>>>
```

获得 `>>>` 提示符后，你可以在那里开始运行异步代码。下面的示例用的是上一节中的代码：

```python
>>> import asyncio

>>> async def main():
...     print("Hello...")
...     await asyncio.sleep(1)
...     print("World!")
...

>>> await main()
Hello...
World!
```

此示例的工作方式与上一节中的示例相同。然而，不是使用 `asyncio.run()` 运行 `main()`，而是直接使用 `await`。

## 常见的异步 I/O 编程模式

异步 I/O 有自己的一套可能的编程模式，允许你编写更好的异步代码。在实践中，你可以 *链式协程/chain coroutines* 或使用一个协程的队列。你将在以下部分中学习如何使用这两种模式。

### 协程的链接

协程的一个关键特性是你可以把它们 *链接/chain* 起来。请记住，协程是可等待的，因此另一个协程可以使用 `await` 关键字等待它。这使得将程序分解为更小、可管理和可重用的协程变得更加容易。

下面的示例模拟了一个获取用户信息的两步过程。第一步获取用户信息，第二步获取他们发布的帖子：

```python
import asyncio
import random
import time

async def main():
    user_ids = [1, 2, 3]
    start = time.perf_counter()
    await asyncio.gather(
        *(get_user_with_posts(user_id) for user_id in user_ids)
    )
    end = time.perf_counter()
    print(f"\n==> Total time: {end - start:.2f} seconds")

async def get_user_with_posts(user_id):
    user = await fetch_user(user_id)
    await fetch_posts(user)

async def fetch_user(user_id):
    delay = random.uniform(0.5, 2.0)
    print(f"User coro: fetching user by {user_id=}...")
    await asyncio.sleep(delay)
    user = {"id": user_id, "name": f"User{user_id}"}
    print(f"User coro: fetched user with {user_id=} (done in {delay:.1f}s).")
    return user

async def fetch_posts(user):
    delay = random.uniform(0.5, 2.0)
    print(f"Post coro: retrieving posts for {user['name']}...")
    await asyncio.sleep(delay)
    posts = [f"Post {i} by {user['name']}" for i in range(1, 3)]
    print(
        f"Post coro: got {len(posts)} posts by {user['name']}"
        f" (done in {delay:.1f}s):"
    )
    for post in posts:
        print(f" - {post}")

if __name__ == "__main__":
    random.seed(444)
    asyncio.run(main())
```

在此示例中，你定义了两个主要协程：`fetch_user()` 和 `fetch_posts()`。两者都使用 `asyncio.sleep()` 模拟具有随机延迟的网络调用。

在 `fetch_user()` 协程中，你返回一个模拟用户 **字典**。在 `fetch_posts()` 中，你使用这个字典返回对应用户的模拟帖子列表。随机延迟模拟了现实世界的异步行为，如网络延迟。

协程的链接发生在 `get_user_with_posts()` 中。这个协程等待 `fetch_user()` 并将结果存储在 `user` **变量** 中。一旦用户信息可用，它就会传递给 `fetch_posts()` 以异步检索帖子。

在 `main()` 中，你使用 `asyncio.gather()` 通过执行 `get_user_with_posts()` 来运行上述的链式协程，执行次数为用户 ID 的数量。

以下是执行脚本的结果：

```bash
$ python chained.py
User coro: fetching user by user_id=1...
User coro: fetching user by user_id=2...
User coro: fetching user by user_id=3...
User coro: fetched user with user_id=2 (done in 0.5s).
Post coro: retrieving posts for User2...
User coro: fetched user with user_id=1 (done in 1.0s).
Post coro: retrieving posts for User1...
User coro: fetched user with user_id=3 (done in 1.2s).
Post coro: retrieving posts for User3...
Post coro: got 2 posts by User2 (done in 1.8s):
 - Post 1 by User2
 - Post 2 by User2
Post coro: got 2 posts by User1 (done in 1.6s):
 - Post 1 by User1
 - Post 2 by User1
Post coro: got 2 posts by User3 (done in 1.5s):
 - Post 1 by User3
 - Post 2 by User3

==> Total time: 2.68 seconds
```

如果汇总所有操作的耗时，那么该示例采用同步实现时，总耗时约为 7.6 秒；而采用异步实现时，仅需 2.68 秒即可完成。

这种 “等待一个协程执行完成后，将其结果传递给下一个协程” 的模式，构成了一条**协程链** —— 链中的每个步骤都依赖于前一个步骤的执行结果。该示例模拟了一种常见的异步工作流：先获取某一条信息，再利用该信息获取相关联的数据

### 协程和队列的集成

`asyncio` 包提供了一些 **拟队列的类**，这些类设计为类似于 [`queue`](https://docs.python.org/3/library/queue.html#module-queue) 模块中的类。之前的示例都不需要队列结构。在 `chained.py` 中，每个任务都由一个协程执行，你将其与其他链式协程以将数据从一个传递到下一个。

另一种方法是使用 **生产者** 向 **队列** 中添加元素。每个生产者可能会向队列添加多个元素，添加的时间点是错开的、随机的、且未事先通知的。然后，一组 **消费者** 会从队列中提取元素，只要队列中有元素就取出，不等待任何其他信号。

在这种设计中，生产者和消费者之间没有链接。消费者不知道生产者的数量，反之亦然。

单个生产者或消费者向队列添加和删除元素所需的时间是可变的。队列作为消息流转的载体，实现生产者与消费者之间的通信，二者无需直接交互。

基于队列的版本的 `chained.py` 如下所示：

```python
import asyncio
import random
import time

async def main():
    queue = asyncio.Queue()
    user_ids = [1, 2, 3]

    start = time.perf_counter()
    await asyncio.gather(
        producer(queue, user_ids),
        *(consumer(queue) for _ in user_ids),
    )
    end = time.perf_counter()
    print(f"\n==> Total time: {end - start:.2f} seconds")

async def producer(queue, user_ids):
    async def fetch_user(user_id):
        delay = random.uniform(0.5, 2.0)
        print(f"Producer: fetching user by {user_id=}...")
        await asyncio.sleep(delay)
        user = {"id": user_id, "name": f"User{user_id}"}
        print(f"Producer: fetched user with {user_id=} (done in {delay:.1f}s)")
        await queue.put(user)

    await asyncio.gather(*(fetch_user(uid) for uid in user_ids))
    for _ in range(len(user_ids)):
        await queue.put(None)  # Sentinels for consumers to terminate

async def consumer(queue):
    while True:
        user = await queue.get()
        if user is None:
            break
        delay = random.uniform(0.5, 2.0)
        print(f"Consumer: retrieving posts for {user['name']}...")
        await asyncio.sleep(delay)
        posts = [f"Post {i} by {user['name']}" for i in range(1, 3)]
        print(
            f"Consumer: got {len(posts)} posts by {user['name']}"
            f" (done in {delay:.1f}s):"
        )
        for post in posts:
            print(f"  - {post}")

if __name__ == "__main__":
    random.seed(444)
    asyncio.run(main())
```

在这个示例中，`producer()` 函数以异步方式获取模拟用户数据。每获取到一个用户字典，都会将其放入 `asyncio.Queue` 队列对象中，由该队列实现与消费者之间的数据共享。生产者生成完所有用户对象后，会为每个消费者插入一个[哨兵值](https://en.wikipedia.org/wiki/Sentinel_value)（在此场景下也被称为 “**毒丸**”）—— 这个值用于告知消费者 “不会再发送更多数据”，从而让消费者能够优雅地退出。

`consumer()` 函数会持续从队列中读取数据：如果读取到的是用户字典，它会模拟获取该用户的帖子数据，等待一段随机时长的延迟后打印结果；如果读取到的是哨兵值，则会终止循环并退出。

这种解耦设计使得多个消费者可以并发处理用户数据（即便生产者仍在生成用户数据），而队列则保证了生产者与消费者之间通信的安全性和有序性。

队列是生产者与消费者之间的核心通信枢纽，依托这一设计可构建出可扩展、响应迅速的系统。

以下是这段代码的实际运行逻辑：

```bash
$ python queued.py
Producer: fetching user by user_id=1...
Producer: fetching user by user_id=2...
Producer: fetching user by user_id=3...
Producer: fetched user with user_id=2 (done in 0.5s)
Consumer: retrieving posts for User2...
Producer: fetched user with user_id=1 (done in 1.0s)
Consumer: retrieving posts for User1...
Producer: fetched user with user_id=3 (done in 1.2s)
Consumer: retrieving posts for User3...
Consumer: got 2 posts by User2 (done in 1.8s):
  - Post 1 by User2
  - Post 2 by User2
Consumer: got 2 posts by User1 (done in 1.6s):
  - Post 1 by User1
  - Post 2 by User1
Consumer: got 2 posts by User3 (done in 1.5s):
  - Post 1 by User3
  - Post 2 by User3

==> Total time: 2.68 seconds
```

同样地，这段代码仅耗时 2.68 秒即可运行完成，相比同步解决方案效率更高。这一结果与你在上一小节中使用链式协程时得到的结果几乎完全一致。

## Python 中的其他异步 I/O 特性

Python 的异步 I/O 特性并非仅包含 `async def` 和 `await` 语法结构，还涵盖了其他高级工具 —— 这些工具能让异步编程的表达力更强，且与常规 Python 语法结构的使用逻辑保持一致。

在接下来的章节中，你将探索各类强大的异步特性，包括异步循环与推导式、`async with` 语句以及异常组。掌握这些特性后，你能编写出更简洁、可读性更高的异步代码。

### 异步迭代器、异步循环与异步推导式

除了使用 `async` 和 `await` 定义协程外，Python 还提供了 `async for` 语法结构，用于遍历 **异步迭代器**。异步迭代器支持遍历以异步方式生成的数据：在循环执行过程中，它会将控制权交还给事件循环，从而让其他异步任务得以运行。

这个概念的自然延伸是 **异步生成器**。以下示例展示了如何生成 2 的幂次，并在异步循环和异步推导式中使用它们：

```python
>>> import asyncio

>>> async def powers_of_two(stop=10):
...     exponent = 0
...     while exponent < stop:
...         yield 2**exponent
...         exponent += 1
...         await asyncio.sleep(0.2)  # Simulate some asynchronous work
...

>>> async def main():
...     g = []
...     async for i in powers_of_two(5):
...         g.append(i)
...     print(g)
...     f = [j async for j in powers_of_two(5) if not (j // 3 % 5)]
...     print(f)
...

>>> asyncio.run(main())
[1, 2, 4, 8, 16]
[1, 2, 16]
```

同步与异步的生成器、循环、推导式之间存在一个关键区别：异步版本的这些结构并不会天生让迭代变得并发。相反，只有当你通过 `await` 显式让出控制权时，它们才会允许事件循环在迭代间隙运行其他任务。除非你使用 `asyncio.gather()` 引入并发机制，否则迭代过程本身仍然是顺序执行的。

仅当你操作异步迭代器或异步上下文管理器时，才需要使用 `async for` 和 `async with`，如果在这些场景下使用常规的 for 或 with，会直接抛出错误。

### Async with 语句

`with` 语句 也有一个 **异步** 的版本 `async with`。这种语法结构在异步代码中很常见，因为许多 **I/O 密集型任务** 都会涉及初始化（setup）和清理（teardown）阶段。

例如，假设你需要编写一个协程来检查某些网站是否在线。为此，你可以使用 [`aiohttp`](https://docs.aiohttp.org/en/stable/index.html)，这是一个第三方库，你需要通过在命令行上运行 `python -m pip install aiohttp` 来安装。

以下是一个快速实现该需求的示例代码：

```python
>>> import asyncio
>>> import aiohttp

>>> async def check(url):
...     async with aiohttp.ClientSession() as session:
...         async with session.get(url) as response:
...             print(f"{url}: status -> {response.status}")
...

>>> async def main():
...     websites = [
...         "https://realpython.com",
...         "https://pycoders.com",
...         "https://www.python.org",
...     ]
...     await asyncio.gather(*(check(url) for url in websites))
...

>>> asyncio.run(main())
https://www.python.org: status -> 200
https://pycoders.com: status -> 200
https://realpython.com: status -> 200
```

本示例中，通过 `aiohttp` 和 `asyncio` 向一组网站发起并发的 `HTTP GET` 请求。`check()` 协程负责获取并打印网站的状态信息。`async with` 语句能够确保 `ClientSession` 会话对象和每个 HTTP 响应都被妥善且异步地管理 —— 它会在不阻塞事件循环的前提下，完成这些对象的创建（打开）与销毁（关闭）操作。

在本示例中，使用 `async with` 还能保证：即便发生错误，底层的网络资源（包括连接和套接字）也会被正确释放。

最后，`main()` 函数会并发运行多个 `check()` 协程，让你可以并行获取这些 URL 对应的内容，无需等待前一个请求完成后再启动下一个。

### 其他 asyncio 工具

除了 `asyncio.run()` 之外，你还用到了其他一些包级函数，例如 `asyncio.gather()` 和 `asyncio.get_event_loop()`。你可以使用 [`asyncio.create_task()`](https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task) 来调度协程对象的执行，然后像往常一样调用 `asyncio.run()` 函数：

```python
>>> import asyncio

>>> async def coro(numbers):
...     await asyncio.sleep(min(numbers))
...     return list(reversed(numbers))
...

>>> async def main():
...     task = asyncio.create_task(coro([3, 2, 1]))
...     print(f"{type(task) = }")
...     print(f"{task.done() = }")
...     return await task
...

>>> result = asyncio.run(main())
type(task) = <class '_asyncio.Task'>
task.done() = False
>>> print(f"result: {result}")
result: [1, 2, 3]
```

这种模式包含一个你需要注意的细微细节：如果你使用 `create_task()` 创建了任务，但既没有等待（await）这些任务，也没有将它们包装在 `gather()` 中，那么当你的 `main()` 协程执行完毕时，事件循环结束后这些手动创建的任务会被取消。你必须等待所有你希望完成的任务执行结束。

`create_task()` 函数会将可等待对象（awaitable object）包装成更高级的 [`Task`](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task) 对象，该对象在事件循环中是在后台被调度然后并发运行。相比之下，直接等待（await）一个协程会立即执行该协程，并暂停调用方的执行，直到被等待的协程执行完毕。

`gather()` 函数的作用是将一组协程整齐地整合为一个单独的未来对象（`future object`）。这个对象代表一个结果占位符 —— 其初始值未知，但会在某个时刻变为可用（通常是异步计算完成后的结果）。

如果你等待（await）`gather()` 并传入多个任务或协程，事件循环会等待所有任务全部完成。`gather()` 的返回结果将是一个列表，包含所有输入任务 / 协程的执行结果：

```python
>>> import time

>>> async def main():
...     task1 = asyncio.create_task(coro([10, 5, 2]))
...     task2 = asyncio.create_task(coro([3, 2, 1]))
...     print("Start:", time.strftime("%X"))
...     result = await asyncio.gather(task1, task2)
...     print("End:", time.strftime("%X"))
...     print(f"Both tasks done: {all((task1.done(), task2.done()))}")
...     return result
...

>>> result = asyncio.run(main())
Start: 14:38:49
End: 14:38:51
Both tasks done: True

>>> print(f"result: {result}")
result: [[2, 5, 10], [1, 2, 3]]
```

你可能有注意到， `gather()` 会等待传入的所有协程全部执行完毕，才会返回完整结果。 `gather()` 返回结果的顺序是确定的，与最初传入的可等待对象顺序完全一致。

此外，你也可以通过遍历 `asyncio.as_completed()` 在任务完成时逐个获取结果。该函数返回一个同步迭代器，当一个任务完成就立刻产出结果。下面的示例中，`coro([3, 2, 1])` 的结果会比 `coro([10, 5, 2])` 先返回，这与 `gather()` 函数的行为不同：

```python
>>> async def main():
...     task1 = asyncio.create_task(coro([10, 5, 2]))
...     task2 = asyncio.create_task(coro([3, 2, 1]))
...     print("Start:", time.strftime("%X"))
...     for task in asyncio.as_completed([task1, task2]):
...         result = await task
...         print(f'result: {result} completed at {time.strftime("%X")}')
...     print("End:", time.strftime("%X"))
...     print(f"Both tasks done: {all((task1.done(), task2.done()))}")
...

>>> asyncio.run(main())
Start: 14:36:36
result: [1, 2, 3] completed at 14:36:37
result: [2, 5, 10] completed at 14:36:38
End: 14:36:38
Both tasks done: True
```

在此示例中，`main()` 函数了使用 `asyncio.as_completed()`，它按照任务完成的顺序逐一返回，而不是按照它们开始的顺序。当程序遍历任务时会等待它们，从而能在任务一完成就立即获取结果。

因此，执行速度更快的任务（`task1`）会先完成，其结果也会更早打印出来；而耗时更长的任务（`task2`）则会后完成并打印结果。当你需要在任务完成时动态处理结果时，`as_completed()` 函数非常实用，这能提升并发工作流的响应性。

### 异步异常处理

从 **Python 3.11** 开始，你可以使用 `ExceptionGroup` 类来处理可能并发发生的多个不相关异常。这在运行多个可能引发不同异常的协程时特别有用。此外，新的 `except*` 语法能帮助你优雅地一次处理多个错误。

以下是如何在异步代码中使用此类的快速演示：

```python
>>> import asyncio

>>> async def coro_a():
...     await asyncio.sleep(1)
...     raise ValueError("Error in coro A")
...

>>> async def coro_b():
...     await asyncio.sleep(2)
...     raise TypeError("Error in coro B")
...

>>> async def coro_c():
...     await asyncio.sleep(0.5)
...     raise IndexError("Error in coro C")
...

>>> async def main():
...     results = await asyncio.gather(
...         coro_a(),
...         coro_b(),
...         coro_c(),
...         return_exceptions=True
...     )
...     exceptions = [e for e in results if isinstance(e, Exception)]
...     if exceptions:
...         raise ExceptionGroup("Errors", exceptions)
...
```

此示例中有三个协程，它们会引发三种不同类型的 **异常**。在 `main()` 函数中调用 `gather()` 函数，协程作为参数传入，同时将 `return_exceptions` 参数设置为 `True`，以便在发生异常时可以捕获它们。

然后使用列表推导式将异常存储在新的列表中。如果列表包含至少一个异常，那么创建一个 `ExceptionGroup` 异常组。

可以使用以下代码处理这个异常组：

```python
>>> try:
...     asyncio.run(main())
... except* ValueError as ve_group:
...     print(f"[ValueError handled] {ve_group.exceptions}")
... except* TypeError as te_group:
...     print(f"[TypeError handled] {te_group.exceptions}")
... except* IndexError as ie_group:
...     print(f"[IndexError handled] {ie_group.exceptions}")
...
[ValueError handled] (ValueError('Error in coro A'),)
[TypeError handled] (TypeError('Error in coro B'),)
[IndexError handled] (IndexError('Error in coro C'),)
```

在上述代码中，你在 `try` 块中调用 `asyncio.run()` 。然后，使用 `except*` 语法分别捕获预期的异常。在屏幕上打印每种异常的错误消息。

## 异步 I/O 的上下文

现在你已经见识了相当多的异步代码，不妨花点时间回过头思考：异步 I/O 何时是理想选择，以及如何判断它是否适合当前场景，还是另一种并发模型会更优。

### 何时使用异步 I/O

如果为执行**阻塞操作**（如普通文件 I/O 或同步网络请求）的函数使用 `async def`，会阻塞整个事件循环，抵消异步 I/O 的优势，甚至可能降低程序效率。`async def` 函数只应用于**非阻塞操作**。

异步 I/O 与多进程之间并非 “二选一” 的对抗关系。你完全可以结合使用这两种模型。在实际开发中，如果存在大量CPU 密集型任务，多进程通常是更合适的选择。

异步 I/O 与多线程的对比则更为直接。多线程并不简单，即便看似容易实现，也仍可能因为**竞态条件**、**内存占用**等问题，引发难以排查的 Bug。

同时，多线程的扩展性通常不如异步 I/O，因为线程是一种有限的系统资源。在很多机器上创建数千个线程会失败，或导致代码运行变慢。与之相反，创建数千个异步 I/O 任务是完全可行的。

异步 I/O 在以下I/O 密集型场景中表现尤为出色，这些场景原本会被大量阻塞等待时间占据：

- **网络 I/O**，无论程序是作为服务端还是客户端
- **无服务器架构**，如点对点、多用户网络（例如群聊）
- **读写操作**，希望采用 “发后即忘/[fire-and-forget](https://en.wikipedia.org/wiki/Fire-and-forget)” 模式，无需担心资源锁占用

不使用异步 I/O 的最主要原因是：`await` 只支持实现了特定方法的特定对象。例如，如果你想对某个数据库管理系统（DBMS）执行异步读取，就必须找到该 DBMS 支持 `async/await` 语法的 Python 封装库。

### 支持异步 I/O 的库

你会发现 Python 中有许多高质量的第三方库和框架都支持 `asyncio` 或是基于它构建，涵盖 Web 服务器、数据库、网络、测试等诸多领域。以下是其中最知名的一些：

- **Web 框架：**
  - [FastAPI](https://fastapi.tiangolo.com/)：用于构建 **Web API** 的现代异步 Web 框架。
    - [Starlette](https://www.starlette.io/)：轻量级 [异步服务器网关接口 (ASGI)](https://en.wikipedia.org/wiki/Asynchronous_Server_Gateway_Interface) 框架，用于构建高性能异步 Web 应用程序。
    - [Sanic](https://sanic.dev/)：使用 `asyncio` 构建的速度快的异步 Web 框架。
    - [Quart](https://github.com/pallets/quart)：与 **Flask** 具有相同 API 的异步 Web 微框架。
    - [Tornado](https://github.com/tornadoweb/tornado)：高性能 Web 框架和异步网络库。
- **ASGI 服务器：**
  - [uvicorn](https://www.uvicorn.org/)：快速的 ASGI Web 服务器。
    - [Hypercorn](https://pypi.org/project/Hypercorn/)：支持多种协议和配置选项的 ASGI 服务器。
- **网络工具：**
  - [aiohttp](https://docs.aiohttp.org/)：使用 `asyncio` 的 HTTP 客户端和服务器实现。
    - [HTTPX](https://www.python-httpx.org/)：功能齐全的异步和同步 HTTP 客户端。
    - [websockets](https://websockets.readthedocs.io/)：使用 `asyncio` 构建 WebSocket 服务器和客户端的库。
    - [aiosmtplib](https://aiosmtplib.readthedocs.io/)：用于 **发送电子邮件** 的异步 SMTP 客户端。
- **数据库工具：**
  - [Databases](https://www.encode.io/databases/)：与 **SQLAlchemy** 核心兼容的异步数据库访问层。
    - [Tortoise ORM](https://tortoise.github.io/)：轻量级异步对象关系映射器 (ORM)。
    - [Gino](https://python-gino.org/)：为 **PostgreSQL** 构建在 SQLAlchemy 核心上的异步 ORM。
    - [Motor](https://motor.readthedocs.io/)：构建在 `asyncio` 上的异步 **MongoDB** 驱动程序。
- **实用库：**
  - [aiofiles](https://github.com/Tinche/aiofiles)：包装 Python 的文件 API 以用于 `async` 和 `await`。
    - [aiocache](https://github.com/aio-libs/aiocache)：支持 **Redis** 和 Memcached 的异步缓存库。
    - [APScheduler](https://github.com/agronholm/apscheduler)：支持异步作业的任务调度器。
    - [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)：使用 **pytest** 添加对测试异步函数的支持。

这些库和框架能帮助你编写高性能的异步 Python 应用程序。无论你是构建 Web 服务器、通过网络获取数据，还是访问数据库，这些 `asyncio` 工具都让你能够以最小的开销并发处理许多任务。

## 结论

你已经扎实掌握了 Python 的 `asyncio` 库以及 `async/await` 语法，了解了异步编程如何在单线程内高效管理大量 I/O 密集型任务。

在此过程中，你厘清了并发、并行、多线程、多进程与异步 I/O 之间的区别。你还通过实际示例学习了协程、事件循环、链式调用和基于队列的并发。除此之外，你还掌握了 `asyncio` 的高级特性，包括异步上下文管理器、异步迭代器、异步推导式，以及如何使用第三方异步库。

在构建可扩展的网络服务器、`Web API`，或是需要同时执行大量 I/O 操作的应用时，熟练掌握 `asyncio` 至关重要。

**在本教程中，你学习了如何：**

- 区分不同的并发模型，并确定何时将 `asyncio` 用于 I/O 密集型任务
- 使用 `async def` 和 `await` 编写、运行 并 链式调用协程
- 使用 `asyncio.run()`、`gather()` 和 `create_task()` 管理事件循环并调度多个任务
- 实现异步模式，如协程的**链式调用**、用于生产者-消费者工作流的**异步队列**
- 使用 `async for` 和 `async with`，并与第三方异步库集成

掌握这些技能后，你就可以开发高性能、现代化的 Python 应用，能够异步处理大量并发操作。

## 常见问题

既然你已经积累了一些 Python 中 `asyncio` 的使用经验，不妨通过以下问答来检验自己的理解程度，并回顾所学内容。

这些常见问题（FAQs）均围绕本教程涵盖的核心概念展开。点击每个问题旁的 “显示 / 隐藏” 开关，即可查看对应的答案。

{{< collapse title="什么是 `asyncio`？为什么使用它？" >}}
使用 asyncio 结合 async 和 await 关键字可以编写并发代码，从而在单线程内高效管理多个 I/O 密集型任务，且不会阻塞程序运行。
{{< /collapse >}}

{{< collapse title="在 I/O 密集型任务中，asyncio 是否优于多线程？" >}}
对于 I/O 密集型任务而言，使用 asyncio 通常能获得更优的性能 —— 因为它规避了线程带来的开销与复杂度。这使得数千个任务可以并发运行，且不受 Python 全局解释器锁（GIL）的限制。
{{< /collapse >}}

{{< collapse title="在 Python 项目中什么情况下应该使用 `asyncio`？" >}}
当你的程序需要花费大量时间等待 I/O 密集型操作（例如网络请求、文件访问），且你希望高效地并发运行大量此类任务时，就可以使用 `asyncio`。
{{< /collapse >}}

{{< collapse title="如何使用 `asyncio` 定义和运行一个协程？" >}}
可以通过 `async def` 语法定义协程。要运行协程，既可将其传入 `asyncio.run()` 执行，也可通过 `asyncio.create_task()` 将其调度为一个任务。
{{< /collapse >}}

{{< collapse title="事件循环（Event Loop）在 `asyncio` 中扮演什么角色？" >}}
依靠事件循环可以对协程的调度与执行进行管理：每当某个协程执行 `await` 操作（等待）或完成一项 I/O 密集型操作时，事件循环会为其他协程提供运行的机会。
{{< /collapse >}}

---

[原文链接](https://realpython.com/async-io-python/)
