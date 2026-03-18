+++
title = "Socket"
author = "CC"
date = 2023-11-24T00:00:00
tags = ["socket"]
categories = ["note"]
draft = false
toc = true
+++

Socket是进程间通信的端点，通过IP地址+端口标识。Unix域套接字用于同一主机进程通信，比网络套接字高效，使用文件系统路径而非IP地址，提供可靠的面向连接或数据报服务。
<!--more-->

## Socket {#socket}

[IPC - Unix Domain Sockets](https://goodyduru.github.io/os/2023/10/03/ipc-unix-domain-sockets.html)

- IPC: inter-process communication
- BSD: Berkeley Software Distribution: a UNIX-based computer operating system

### Socket API {#socket-api}

- `socket()`: 创建一个 socket/endpoint 用于通信。设置通信终端的域名/domain 和语义（TCP、UDP、raw）。可以是 integer 或 对象（不同语言而定）。
  - python: `sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)`
- `bind()`: server 端使用。给 socket 映射到一个引用(referrence)，引用通常是 IP:Port 或文件，用于进程间通信（IPC）。
  - python: `sock.bind("ip:port or filename")`
- `listen()`: server 端使用。表示准备好接进来的连接。
  - python: `scok.listen(1)` 1 表示等待连接的队列长度为 1。
- `connect()`: client 端使用。将客户端 socket 与服务端关联起来，使之可以通信。三次握手发生在这里。这里的引用也是 IP:Port 或文件。
- `accept()`: server 端使用。接受一个进来的连接，创建一个新的 socket。这个 socket 用来传递信息。
- `send()` and `recv()`: 在节点之间传递信息。发送 bytes， `"msgContent".encode()` 。
- `close()`: 释放资源，发起四次挥手。
