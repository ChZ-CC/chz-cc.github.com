+++
title = "uv -- Python Package and Project Manager"
author = "CC"
date = 2025-10-26T00:00:00
tags = ["Python", "uv"]
categories = ["note"]
draft = false
toc = true
+++

Python 管理工具，all in one。用 `rust` 写的。包含了集成环境管理、依赖解析、构建发布功能，支持多版本Python，通过硬链接优化性能，可替代pip、venv、poetry等工具，提供极速安装和一致环境。
<!--more-->

## Install

安装文档: [Installing uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods), 可以使用 `curl` 或 `pip/pipx` 安装。

- curl 命令安装在 `$HOME/.local/bin` 目录下，需要重启 shell 生效。

## 常用命令

管理 Python 版本

- `uv self update` -- 升级自己
- `uv python list` -- 列出uv支持的python版本
- `uv python install cpython3.12` -- 安装某个python版本 (3.12)

从本地安装：

- 配置环境变量，将安装包放入对应目录，然后安装。
  - `env:UV_PYTHON_INSTALL_MIRROR='file://D:\uv\mirror'`
  - `export UV_PYTHON_INSTALL_MIRROR='file:///home/user/uv/mirror'`(Linux)
- 命令行参数: `uv python install cpython3.12 -mirror file:///home/user/uv/mirror`

执行脚本

- `uv run -p 3.12 xxx.py` -- 使用特定版本python运行xxx.py
- `uv run -p 3.12 python` -- 运行指定版本的python交互界面。如果版本不存在，则自动安装对应版本的 Python 解释器。
- `uv run xxx.py` -- 使用系统python或当前工程的虚拟环境运行xxx.py
-

管理系统级/全局工具

- `uv tool install ruff` -- 系统级的安装。
- `uv tool list` -- 打印当前系统中已安装的工具。
- `uv tool upgrade --all` -- 升级所有系统级的工具。

管理依赖

- `uv init` -- 创建工程，创建 `uv` 相关的文件。`-p 3.12` 可以指定Python版本。
  - git & .gitignore
  - .python-version - 记录Python版本号。
  - pyproject.toml
- `uv add pydantic_ai` -- 添加依赖 (pydantic_ai)。
  - 如果当前项目没有虚拟环境，会自动创建 venv。
- `uv add pytest --dev` 作为开发依赖，打包时不会打包进去。适合用于安装项目的测试模块等。
- `uv tree` -- 打印依赖树
- `uv remove pydantic_ai` -- 删除依赖

编译、发布

- `uv build` -- 编译工程。生成一个 `dist` 目录，其中有可以 install 的 `whl` 文件，用于发布一个Python 库。

虚拟环境 `venv`

- 创建虚拟环境 `uv venv -p/--python python3.14t {path}` 【无pip，uv 的特性】
- 虚拟环境安装三方库 `uv pip install`, 虚拟环境激活状态下安装到当前环境。
- 如果是项目，可指定目录/配置文件等。

>[!notice] 注意
>`uv` 安装的 Python 解释器不会加到 path 中，无法直接使用。可以使用 `uv run -p {your-python-version}` 来执行，或者手动添加软连接或环境变量。

## 开发环境依赖隔离

最佳实践：

- Use `pyproject.toml` with `[tool.uv.dependencies] dev` section (recommended)
- `uv sync --dev` to install
- `uv run` to use tools.

| Task                                 | Command                                                         |
| ------------------------------------ | --------------------------------------------------------------- |
| Install dev dependencies             | `uv sync --dev` / `uv pip install -r requirements-dev.txt`      |
| Install production only              | `uv sync --no-dev` / `uv pip install -r requirements.txt`       |
| Add a dev dependency                 | `uv add --dev pytest-cov`                                       |
| Run pytest                           | `uv run pytest tests/`                                          |
| Update all dev dependencies          | `uv update --dev`                                               |
| Freeze dev dependencies to lock file | `uv pip freeze -r requirements-dev.txt > requirements-dev.lock` |
| Clean up orphaned dependencies       | `uv clean`                                                      |
| Remove an unused dev dependency      | `uv remove --dev flake8-isort`                                  |

依赖安装超时报错，提醒：

```text
  help: If you want to add the package regardless of the failed resolution,     
        provide the `--frozen` flag to skip locking and syncing. 
```

使用 `uv add --frozen` 会跳过安装依赖，跳过锁文件的更新，直接更新 `pyproject.toml` 文件中的依赖，且不带依赖版本号。后续通过 `uv sync` 或 `uv add` 安装依赖，但 `pyproject.toml` 中不会变，依然没有版本号信息。

这时候想要更新 `pyproject.toml` 中的依赖版本号，需要删除 toml 文件中的依赖，然后再执行一下 `uv add`。

## 报错/警告与解决

### Python依赖冲突

#### step1. 检查依赖

```bash
# For projects with pyproject.toml (Poetry/Pep621 format)
uv sync --dry-run
```

- --dry-run: Simulates the installation without modifying your environment (safe for checking conflicts).
- If conflicts exist, `uv` will output a detailed error message like this:

```plaintext
Error: Conflict detected:
- requests 2.28.0 requires urllib3 < 1.27, >= 1.21.1
- httpx 0.24.0 requires urllib3 >= 2.0.0
Cannot find a version of urllib3 that satisfies both constraints.
```

#### step2. 解决冲突

```bash
# sync dependencies with strict resolution (found confict)
uv sync --strict
# Show dependency tree (find which package is pulling in conflicting versions)
uv pip tree
# Update `pyproject.toml` to loosen constraints
vim pyproject.toml
# then, sync dependencies with auto-resolution
uv sync
```

- 不要指定严格版本号
- 重新安装正确的版本，--force-reinstall
- 使用虚拟环境 `venv`

### `hardlink` 失败告警

- 参考文章：<https://www.cnblogs.com/LexLuc/p/19429840>

在 Windows 环境下使用 `uv add` 安装 Python 依赖时，很多人都会遇到类似下面的警告：

```text
warning: Failed to hardlink files; falling back to full copy.
This may lead to degraded performance.
```

`uv`使用 `hardlink` 的方式提高安装性能，如果失败则使用完整复制，并发出上面的警告。Windows 上报错是因为不同盘之间不能链接。

解决方法：将缓存目录放到项目所在的盘。

```bash
# 查看缓存目录
uv cache dir
# 修改 uv 缓存目录
setx UV_CACHE_DIR D:\uv-cache
```

PS. windows 更新环境变量后，vscode 的 terminal 重开不生效。reload window 也不行。关闭 IDE 再打开，还是不行。

- 原因是我还打开着其他窗口，将 vscode 整体关掉，再打开才行。

---

## 参考

- 视频：程序员老王/B站 [让 uv 管理一切](https://www.bilibili.com/video/BV1Stwfe1E7s/)
- 博客文章：[From pyenv to uv](https://rob.cogit8.org/posts/2024-09-19-pyenv-to-uv/) ，讲如何作者是如何从 `pyenv` 切换到 `uv` 的。
- 播客文章： <https://www.cnblogs.com/haima/p/18928947> ，整体使用。
