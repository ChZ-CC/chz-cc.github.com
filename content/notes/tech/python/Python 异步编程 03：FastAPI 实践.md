+++
title = "Python 异步编程 03：FastAPI 实践"
author = "CC"
date = 2026-03-25T00:00:00
tags = ["asyncio", "python", "fastapi"]
categories = ["note"]
draft = false
toc = true
+++

FastAPI是一个现代、快速的Web框架，基于Starlette和Pydantic，提供了出色的异步支持和自动API文档生成功能。

- **类型提示优先**：利用Python的类型提示系统提供自动验证和文档生成
- **异步优先**：基于Starlette，原生支持异步操作
- **简洁明了**：API设计简洁直观，减少样板代码
- **标准兼容**：遵循OpenAPI和JSON Schema标准

<!--more-->

## 使用 FastAPI 创建异步 API 应用

### 基础使用

在 `main.py` 文件中创建一个应用实例：

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

使用 `async def` 定义异步路径操作函数：

```python
import asyncio
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    # 执行异步操作
    await asyncio.sleep(1)
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

使用 [`FastAPI CLI`](https://fastapi.org.cn/fastapi-cli/) 启动应用：

```bash
fastapi dev

# 生产环境
fastapi run
```

`fastapi` CLI 会尝试自动检测要运行的 `FastAPI` 应用，默认假设该应用是一个名为 `app` 的对象，位于 main.py 文件中（或其他几种变体）。也可以显式地在配置文件 `pyproject.toml` 中的 `[tool.fastapi]` 中进行设置。

```toml
[tool.fastapi]
entrypoint = "main:app"
```

服务启动后，可以通过浏览器访问 `http://127.0.0.1:8000/items/5?q=somequery` 查看接口返回结果。

访问 `http://127.0.0.1:8000/docs` 查看交互式 API 文档（由 Swagger UI 提供）。

### 类型声明

使用 `Pydantic` 定义请求体参数和响应体的模型：

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}
```

## 依赖注入：异步环境下的高级应用与测试

FastAPI的依赖注入系统非常强大，支持同步和异步依赖，并且可以轻松进行测试。

依赖注入可以实现以下功能：

- 拥有共享逻辑（重复使用相同的代码逻辑）。
- 共享数据库连接。
- 强制执行安全性、身份验证、角色要求等。

### 基本依赖注入

```python
from fastapi import FastAPI, Depends

app = FastAPI()

def get_db():
    db = "Database connection"
    try:
        yield db
    finally:
        # 关闭数据库连接
        pass

@app.get("/items/")
async def read_items(db: str = Depends(get_db)):
    return {"db": db, "items": ["item1", "item2"]}
```

### 4.2.2 异步依赖

```python
from fastapi import FastAPI, Depends
import asyncio

app = FastAPI()

async def get_async_db():
    db = "Async database connection"
    try:
        # 模拟异步数据库连接
        await asyncio.sleep(0.1)
        yield db
    finally:
        # 关闭数据库连接
        await asyncio.sleep(0.1)

@app.get("/items/")
async def read_items(db: str = Depends(get_async_db)):
    return {"db": db, "items": ["item1", "item2"]}
```

### 依赖注入的高级应用

- **嵌套依赖**：依赖可以依赖于其他依赖
- **路径操作装饰器依赖**：为整个路径操作添加依赖
- **全局依赖**：为所有路径操作添加依赖

### 依赖注入与测试

```python
from fastapi.testclient import TestClient
from main import app, get_db

# 测试用依赖
def override_get_db():
    return "Test database"

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_read_items():
    response = client.get("/items/")
    assert response.status_code == 200
    assert response.json() == {"db": "Test database", "items": ["item1", "item2"]}
```

## 后台任务、流式响应与长轮询实现

FastAPI提供了多种高级功能，如后台任务、流式响应和长轮询。

### 后台任务

```python
from fastapi import FastAPI, BackgroundTasks
import time

app = FastAPI()

def process_data(data: str):
    """后台处理数据"""
    time.sleep(5)  # 模拟长时间处理
    print(f"Processed data: {data}")

@app.post("/items/")
async def create_item(item: str, background_tasks: BackgroundTasks):
    # 添加后台任务
    background_tasks.add_task(process_data, item)
    return {"message": "Item created, processing in background"}
```

### 流式响应

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

async def generate_data():
    for i in range(10):
        yield f"Data {i}\n"
        await asyncio.sleep(1)

@app.get("/stream/")
async def stream_data():
    return StreamingResponse(generate_data(), media_type="text/plain")
```

### 长轮询实现

```python
from fastapi import FastAPI, Request
import asyncio

app = FastAPI()

async def wait_for_event():
    # 模拟等待事件
    await asyncio.sleep(10)
    return {"event": "something happened"}

@app.get("/long-poll/")
async def long_poll(request: Request):
    try:
        result = await asyncio.wait_for(wait_for_event(), timeout=30)
        return result
    except asyncio.TimeoutError:
        return {"message": "No event occurred within timeout"}
```

## Pydantic深度集成：数据验证、序列化与文档生成

FastAPI与Pydantic深度集成，提供了强大的数据验证和序列化功能。

### 基本数据模型

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

### 高级数据验证

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

app = FastAPI()

class Item(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="Item name")
    price: float = Field(..., gt=0, description="Item price")
    tax: float | None = Field(None, ge=0, description="Tax rate")
    
    @validator('name')
    def name_must_not_contain_space(cls, v):
        if ' ' in v:
            raise ValueError('Name must not contain spaces')
        return v

@app.post("/items/")
async def create_item(item: Item):
    return item
```

### 自动文档生成

FastAPI会自动为您的API生成交互式文档：

- **Swagger UI**：访问 `/docs`
- **ReDoc**：访问 `/redoc`

## FastAPI性能优化：中间件、缓存与异步数据库集成概述

### 中间件

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

### 缓存

```python
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
import redis

app = FastAPI()

# 初始化缓存
redis_client = redis.Redis(host="localhost", port=6379)
FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")

@app.get("/items/{item_id}")
@cache(expire=60)
async def read_item(item_id: int):
    # 模拟数据库查询
    await asyncio.sleep(0.5)
    return {"item_id": item_id, "name": f"Item {item_id}"}
```

### 异步数据库集成

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

app = FastAPI()

# 数据库配置
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)

# 依赖项
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@app.get("/items/")
async def read_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    items = result.scalars().all()
    return items
```

## FastAPI与其他异步框架的对比

### FastAPI vs Starlette

- **Starlette**：轻量级ASGI框架，提供基本的Web功能
- **FastAPI**：基于Starlette，添加了数据验证、文档生成等功能

### FastAPI vs Django Async

- **Django**：全功能Web框架，支持ORM、Admin等
- **FastAPI**：更专注于API开发，性能更高，文档更完善

### FastAPI vs Flask

- **Flask**：轻量级框架，同步为主
- **FastAPI**：原生支持异步，性能更高，类型提示更完善

---

## 参考文档

- [FastAPI官方文档](https://fastapi.tiangolo.com)
- [Pydantic官方文档](https://pydantic-docs.helpmanual.io/usage)
