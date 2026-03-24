+++
title = "DeepWiki"
author = "CC"
date = 2026-03-20T00:00:00
tags = ["git"]
categories = ["tool"]
draft = false
toc = false
+++

![](https://cdn.jsdelivr.net/gh/ChZ-CC/PicCDN@picgo/src/pic/20260324203631902.png)

`DeepWiki` 是一个基于大模型的文档工具，可以给 `git` 仓库自动生成文档。学习/阅读开源项目的时候非常有用。

1. 首先找到一个 `git` 仓库，将 `url` 中的 `github` 替换为 `deepwiki`，回车。如果项目已经有 wiki 就可以直接看到。
2. 如果没有，可以申请创建索引。填入邮箱，点击 `Index Repository` 即可。提示等待十分钟左右，完成后会发邮件通知你。

例如，项目仓库是 `https://github.com/astral-sh/python-build-standalone`, 改为 `https://deepwiki.com/astral-sh/python-build-standalone` 直接访问寄了。

PS. 学习源码的思路：生成学习指南 > 拆分为课程大纲 > 细化生成每一课的学习内容。
