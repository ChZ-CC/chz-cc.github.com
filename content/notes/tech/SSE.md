+++
title = "SSE"
author = "CC"
date = 2023-11-24T00:00:00
tags = ["sse"]
categories = ["note"]
draft = false
toc = true
+++

SSE（Server-Sent Events）是一种基于HTTP的单向服务器推送技术，允许服务器主动向客户端发送实时数据。相比WebSocket，SSE更简单轻量，天然支持断线重连，适合新闻推送、股票行情等服务器主导的实时场景，但不支持客户端向服务器发送数据。
<!--more-->

## SSE {#sse}

- SSE(Server-Sent Events) 服务端推送事件
  - 单向通道：服务端向客户端
  - http 协议
- 建立连接
  - 客户端发起请求，header `Accept: text/event-stream`
  - 服务端相应，header `Content-Type: text/event-stream`
  - 此后保持连接，服务端可以向客户端发送消息。如果断开，客户端会进行重连。
- 发送消息
  - data 消息体。
  - id(optional) 用于重连。
  - event(optional) 事件类型，客户端用来区分消息。
  - retry(optional) 自动重连等待时间。
  - 只能发送文本信息。

[chatfairy](https://github.com/yuxiaoy1/chatfairy) 使用 SSE 实现聊天。

1. 客户端通过普通的 http 请求发送数据到服务端。
2. 客户端与服务端建立 SSE 连接。
3. 服务端通过 SSE 连接，将收到的所有消息按顺序返回到客户端。

---

参考：

- [阮一峰:SSE教程](https://www.ruanyifeng.com/blog/2017/05/server-sent_events.html)
- [【公众号】解密 SSE，像 ChatGPT 一样返回流式响应](https://mp.weixin.qq.com/s/YzcyKsb1Uh3OOB_WHly9SQ)
