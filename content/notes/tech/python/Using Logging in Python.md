+++
title = "Using Logging in Python"
author = "CC"
date = 2026-01-17T00:00:00
tags = ["python"]
categories = ["note"]
draft = false
toc = true
+++

logging 是项目开发中非常基础但重要的模块。它用于记录程序运行时的事件、错误、警告等信息。方便我们进行代码调试、bug 定位、服务监控，还可以支持流量监控、统计分析等。

对于一次性执行的脚本，直接用 `print()` 打印想要关注的信息是可行的。当时对于长期运行的服务，就有必要对日志信息做规范性的记录，落盘到文件中。

Python 的 [logging](https://docs.python.org/3/library/logging.html) 模块提供了一套完善的日志记录机制。它支持不同的日志级别（DEBUG、INFO、WARNING、ERROR、CRITICAL），可以将日志输出到控制台、文件、网络等。它还提供了格式化日志的功能，志的输出格式。
<!--more-->

## 基础用法

使用 `logging` 记录日志，最简单的方式是直接调用 `logging.info()` 等方法。

```python
import logging
logging.warning('Watch out!')  # will print a message to the console
logging.info('I told you so')  # will not print anything
```

这里调用的是根日志器（root logger），它的默认级别是 `WARNING` 。所以输出会是这样:

```plaintext
WARNING:root:Watch out!
```

### `getLogger()` 创建日志器

根日志器也可以进行配置，设置日志级别、日志格式、输出目录等。但通常不推荐直接使用根日志器，更常见的做法是通过 `logging.getLogger()` 创建自定义日志器。下面是一个示例：

```python
# config_logger.py
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


_loggers = {}


def get_logger(
    name: str,
    level: str = "INFO",
    file_level: str = "INFO",
    console_level: str = "DEBUG",
    file_path: str = "logs",
    file_name: str = "main.log",
    propagate: bool = False,
) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # if the logger will propagate the log to the parent logger or not
    logger.propagate = propagate

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建日志目录
    log_dir = Path(file_path)
    log_dir.mkdir(exist_ok=True)

    # 文件处理器 - 所有级别都写入文件
    file_handler = RotatingFileHandler(
        log_dir / file_name,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger
```

这里定义了一个获取日志器的函数 `get_logger`。配置了一个 `FileHandler` 和 `StreamHandler`，分别用于将日志写入文件和控制台。用它输出几条日志看：

```python
my_logger = get_logger(
    "my_logger", level="DEBUG", file_level="INFO", console_level="DEBUG"
)
my_logger.debug("Debug, world!")
my_logger.info("Hello, world!")
my_logger.warning("Warning, world!")
my_logger.error("Error, world!")

"""
# output
# console:
DEBUG - Debug, world!
INFO - Hello, world!
WARNING - Warning, world!
ERROR - Error, world!

# file:
2026-03-27 13:52:36 - my_logger - INFO - Hello, world!
2026-03-27 13:52:36 - my_logger - WARNING - Warning, world!
2026-03-27 13:52:36 - my_logger - ERROR - Error, world!
"""
```

注意，这里 `logger` 的日志级别会影响后续 `handler` 的级别。如果 `logger` 的级别是 `INFO`，`handler` 们的级别必须高于 `INFO` 才会生效。假如 logger.level == INFO，而 console_handler.level == DEBUG，那么 console_handler 依然只输出 INFO 级别以上的日志，而不会输出 DEBUG 日志。

`propagate` 参数的作用是控制日志是否传播到父日志器。默认是 True，即日志会传播到父日志器。这里可以通过调用一下根日志器来看到传递到父日志器的后果。

```python
my_logger = get_logger(
    "my_logger",
    propagate=True,
)
logging.warning("Warning from root looger, world!")
my_logger.info("Hello, world!")
```

结果如下， `console` 输出了两遍。第一个 `INFO` 日志是 `my_logger` 输出的，第二个 `INFO` 日志是根日志器的输出。因为根日志器没有配置 `FileHandler` 所以日志文件中是没有重复的。这里重复日志的根源，这条日志传递给了多个 `StreamHandler` 。

```plaintext
WARNING:root:Warning from root looger, world!
INFO - Hello, world!
INFO:my_logger:Hello, world!
```

将 `propagate` 参数设置为 `False` 可以修复上面的问题。

另外还需要注意，不要给 `logger` 重复添加处理器，这也可能导致日志输出混乱。方法可以有多种，上面的示例代码通过

1. `_loggers` 字典记录已存在的日志器，不重复创建。
2. 通过判断 `logger.handlers` 是否为空来避免是否重复添加处理器。
3. 总之，日志器的初始化应该仅执行一次。

### 日志器的层级关系

日志器的层级关系与 Python 的模块层级关系类似，通过点号分隔的命名空间来表示。

```plaintext
root
  ├── app
  │     ├── user
  │     └── order
  └── utils
```

1. **命名空间层级**：日志器名称中的点号（`.`）表示层级关系。例如，user 的日志器 `app.user` ，是 `app` 的子日志器。
2. **继承特性**：
   - 子日志器会继承父日志器的配置（级别、处理器等）
   - 如果子日志器没有显式设置级别，会使用父日志器的级别
   - 子日志器的日志默认会传播到父日志器（可通过 `propagate` 参数控制）
3. **根日志器**：所有日志器的最终父级是根日志器（`root`），它是默认创建的。

子模块获取日志器的方法：在实际项目中，推荐使用 `__name__` 作为日志器名称，这样可以自动创建与模块结构一致的日志器层级。

```python
# app/user.py
from config_logger import get_logger

# 记录日志
logger = get_logger(__name__)
logger.info("This is a message from %s", __name__)
```

当然也可以显示的创建日志器，例如 `get_logger("app")` 。这样写的好处是可以在代码中直接看到日志器的名称，如果项目比较简单，整体使用一个日志器，这样写也可以接受。但大多数情况下还是建议使用 `__name__` 来创建。

那么同理，对于三方库/框架的日志器，也可以使用同样的逻辑来进行配置。例如，对于 `requests` 库，可以使用 `get_logger("requests")` 来获取日志器，然后对日志器进行配置。

日志器层级关系的优势：

1. **集中配置**：可以在父日志器中配置处理器和格式，子日志器自动继承
2. **模块隔离**：每个模块可以有自己的日志器，便于区分日志来源
3. **灵活控制**：可以针对不同模块设置不同的日志级别和处理器
4. **清晰的日志结构**：通过日志器名称可以清晰地看出日志来源的模块层级

通过这种层级关系，可以构建一个清晰、可维护的日志系统，便于在大型项目中管理和分析日志。

### 最佳实践

- 在项目入口处配置根日志器或顶层日志器
- 使用 `__name__` 作为日志器名称，自动创建与模块结构一致的层级
- 合理使用 `propagate` 参数控制日志传播

---

TODOs

- [ ] 进阶用法
  - [ ] 通过配置文件配置。
  - [ ] Filter, LogRecord。
  - [ ] 高度定制化的日志系统。
  - [ ] 其他：logstash，kafka...
